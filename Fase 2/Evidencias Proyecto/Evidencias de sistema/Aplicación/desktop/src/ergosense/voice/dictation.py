import json
import os
import threading
from collections import deque
from pathlib import Path

import numpy as np
import webrtcvad

from ergosense.app.resources import portable_model

SAMPLE_RATE = 16000
FRAME_BYTES = 640
MODEL_REPOSITORY = "Systran/faster-whisper-small"
MODEL_REVISION = "536b0662742c02347bc0e980a01041f333bce120"
_model = None
_model_lock = threading.Lock()


def dictation_model_path():
    custom = os.environ.get("ERGOSENSE_DICTATION_MODEL")
    if custom:
        return Path(custom)
    portable = portable_model("whisper-small")
    if portable:
        return portable
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "ErgoSense" / "models" / "whisper-small"


def load_dictation_model():
    from faster_whisper import WhisperModel
    from huggingface_hub import snapshot_download

    global _model
    with _model_lock:
        if _model is None:
            path = dictation_model_path()
            required = ("model.bin", "config.json", "tokenizer.json", "vocabulary.txt")
            if not all((path / name).is_file() for name in required):
                snapshot_download(
                    MODEL_REPOSITORY, revision=MODEL_REVISION, local_dir=path,
                    allow_patterns=list(required),
                )
            _model = WhisperModel(
                str(path), device="cpu", compute_type="int8",
                cpu_threads=4, num_workers=1, local_files_only=True,
            )
        return _model


class DictationRecognizer:
    def __init__(self, model=None, vad=None):
        self._model = model if model is not None else load_dictation_model()
        self._vad = vad if vad is not None else webrtcvad.Vad(2)
        self._pending = bytearray()
        self._lead = deque(maxlen=12)
        self._audio = bytearray()
        self._silence = 0
        self._voiced = 0
        self._results = deque()
        self._state = lambda state: None

    def set_state_callback(self, callback):
        self._state = callback

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
            if self._silence >= 35 or len(self._audio) >= SAMPLE_RATE * 2 * 12:
                self._finish_phrase()
        return bool(self._results)

    def _finish_phrase(self):
        audio = bytes(self._audio)
        voiced = self._voiced
        self._audio.clear()
        self._voiced = self._silence = 0
        if voiced < 5:
            return
        self._state("processing")
        try:
            samples = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768
            segments, _ = self._model.transcribe(
                samples, language="es", task="transcribe", beam_size=5,
                temperature=0, condition_on_previous_text=False, vad_filter=True,
                no_speech_threshold=0.6,
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
