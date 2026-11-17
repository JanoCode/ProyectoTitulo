import json
import os
import threading
from collections import deque
from pathlib import Path

import numpy as np
import webrtcvad

from ergosense.app.resources import portable_model
from ergosense.voice.acceleration import cuda_available

SAMPLE_RATE = 16000
FRAME_BYTES = 640
MODEL_REPOSITORY = "mobiuslabsgmbh/faster-whisper-large-v3-turbo"
MODEL_REVISION = "0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf"
MODEL_FOLDER = "whisper-large-v3-turbo"
MODEL_FILES = ("model.bin", "config.json", "tokenizer.json", "vocabulary.json", "preprocessor_config.json")
SILENCE_FRAMES = 50
MAX_SECONDS = 20
_model = None
_model_lock = threading.Lock()


def dictation_model_path():
    custom = os.environ.get("ERGOSENSE_DICTATION_MODEL")
    if custom:
        return Path(custom)
    portable = portable_model(MODEL_FOLDER)
    if portable:
        return portable
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "ErgoSense" / "models" / MODEL_FOLDER


def load_dictation_model():
    from faster_whisper import WhisperModel
    from huggingface_hub import snapshot_download

    global _model
    with _model_lock:
        if _model is None:
            path = dictation_model_path()
            required = MODEL_FILES
            custom = os.environ.get("ERGOSENSE_DICTATION_MODEL")
            if custom and not all((path / name).is_file() for name in ("model.bin", "config.json", "tokenizer.json")):
                raise RuntimeError("La carpeta del modelo de dictado está incompleta.")
            if not custom and not all((path / name).is_file() for name in required):
                snapshot_download(
                    MODEL_REPOSITORY, revision=MODEL_REVISION, local_dir=path,
                    allow_patterns=list(required),
                )
            if os.environ.get("ERGOSENSE_DICTATION_DEVICE", "auto") != "cpu" and cuda_available():
                try:
                    candidate = WhisperModel(str(path), device="cuda", compute_type="int8_float16",
                                             num_workers=1, local_files_only=True)
                    segments, _ = candidate.transcribe(np.zeros(SAMPLE_RATE, dtype=np.float32),
                                                       language="es", beam_size=1, vad_filter=False)
                    list(segments)
                    _model = candidate
                except (OSError, RuntimeError, ValueError):
                    candidate = None
            if _model is None:
                _model = WhisperModel(
                    str(path), device="cpu", compute_type="int8",
                    cpu_threads=4, num_workers=1, local_files_only=True,
                )
        return _model


class DictationRecognizer:
    def __init__(self, model=None, vad=None):
        self._model = model if model is not None else load_dictation_model()
        self._vad = vad if vad is not None else webrtcvad.Vad(1)
        self._pending = bytearray()
        self._lead = deque(maxlen=15)
        self._audio = bytearray()
        self._silence = 0
        self._voiced = 0
        self._results = deque()
        self._state = lambda state: None
        self._quality = lambda message: None
        self._warnings = set()

    def set_state_callback(self, callback):
        self._state = callback

    def set_quality_callback(self, callback):
        self._quality = callback

    def _warn(self, key, message):
        if key not in self._warnings:
            self._warnings.add(key)
            self._quality(message)

    def _samples(self, audio):
        samples = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768
        if np.mean(np.abs(samples) >= .995) > .005:
            self._warn("clipping", "El micrófono está saturando. Baja su volumen de entrada para mejorar el dictado.")
        samples -= samples.mean()
        peak = float(np.max(np.abs(samples)))
        rms = float(np.sqrt(np.mean(samples * samples)))
        if rms < 1e-6:
            return None
        if peak < .02:
            self._warn("quiet", "Tu voz llega muy baja. Acércate al micrófono o elige otro en Configuración.")
        samples *= min(8.0, .06 / rms, .95 / peak)
        return samples

    def AcceptWaveform(self, data):
        self._pending.extend(data)
        while len(self._pending) >= FRAME_BYTES:
            frame = bytes(self._pending[:FRAME_BYTES])
            del self._pending[:FRAME_BYTES]
            speech = self._vad.is_speech(frame, SAMPLE_RATE)
            if not self._audio:
                self._lead.append(frame)
                if not speech:
                    continue
                self._audio.extend(b"".join(self._lead))
                self._lead.clear()
                self._voiced = 1
                continue
            self._audio.extend(frame)
            self._voiced += int(speech)
            self._silence = 0 if speech else self._silence + 1
            if self._silence >= SILENCE_FRAMES or len(self._audio) >= SAMPLE_RATE * 2 * MAX_SECONDS:
                self._finish_phrase()
        return bool(self._results)

    def _finish_phrase(self):
        audio = bytes(self._audio)
        voiced = self._voiced
        self._audio.clear()
        self._voiced = self._silence = 0
        if voiced < 5:
            return
        samples = self._samples(audio)
        if samples is None:
            return
        self._state("processing")
        try:
            segments, _ = self._model.transcribe(
                samples, language="es", task="transcribe", beam_size=5,
                temperature=0, condition_on_previous_text=False, vad_filter=True,
                no_speech_threshold=0.6,
                vad_parameters={"threshold": .35, "min_speech_duration_ms": 80,
                                "min_silence_duration_ms": 250, "speech_pad_ms": 350},
            )
            text = " ".join(segment.text.strip() for segment in segments).strip()
            if text:
                self._results.append(text)
        finally:
            self._state("listening")

    def Result(self):
        text = self._results.popleft() if self._results else ""
        return json.dumps({"text": text}, ensure_ascii=False)

    def FinalResult(self):
        if self._audio:
            self._finish_phrase()
        text = " ".join(self._results)
        self._results.clear()
        return json.dumps({"text": text}, ensure_ascii=False)
