"""Captura de audio y reconocimiento de comandos fuera del hilo de la interfaz.

Los comandos usan Vosk y el dictado usa Whisper; el audio del micrófono se
procesa en este equipo, por bloques de 0,1 s, y nunca se guarda ni se envía a otro
servicio (RNF-17). Solo la primera descarga de cada modelo necesita internet.
"""

import json
import queue
import threading

import sounddevice as sd
from PySide6.QtCore import QObject, Signal, Slot

from ergosense.voice.recognizer import (
    SAMPLE_RATE,
    DownloadCancelled,
    ModelDownloadError,
    VoiceModelMissing,
    create_dictation_recognizer,
    create_recognizer,
    download_model,
)

# Estados que se informan a la ventana.
STARTING = "Iniciando micrófono..."
LISTENING = "Activo · micrófono en uso"
MICROPHONE_UNAVAILABLE = "Micrófono no disponible"
MODEL_MISSING = "Falta el modelo de voz"
DOWNLOADING = "Descargando voz"  # la primera vez; se agrega el avance: "· 45 %"
DOWNLOAD_FAILED = "No se pudo descargar"
DISABLED = "Desactivado"

# 0,1 s de audio por bloque: lo bastante corto para responder rápido (RNF-07).
BLOCK_FRAMES = SAMPLE_RATE // 10


class VoiceWorker(QObject):
    recognized = Signal(str)
    dictated = Signal(str)
    dictation_state_changed = Signal(str)
    dictation_failed = Signal(str)
    status_changed = Signal(str)
    microphone_changed = Signal(str)  # nombre del micrófono que se está usando
    _result = Signal(int, str)
    _status = Signal(int, str)
    _microphone = Signal(int, str)
    _scoped_result = Signal(int, int, str)
    _dictation_state = Signal(int, int, str)
    _dictation_failure = Signal(int, int, str)

    def __init__(
        self, recognizer_factory=create_recognizer, model_downloader=download_model,
        dictation_factory=create_dictation_recognizer,
    ):
        super().__init__()
        # En las pruebas se entregan un reconocedor y una descarga falsos.
        self._recognizer_factory = recognizer_factory
        self._model_downloader = model_downloader
        self._dictation_factory = dictation_factory
        self._mode = (0, False)
        # Frases de las macros activadas. Se reemplaza la tupla completa, y el hilo
        # de audio reconstruye la gramática cuando ve una nueva (arquitectura, 5.4).
        self._macro_phrases = ()
        self._stop = threading.Event()
        self._thread = None
        self._stream = None
        # Cada encendido tiene su número; lo que llegue de un encendido anterior se
        # descarta, para que una frase atrasada no ejecute nada al volver a activar.
        self._generation = 0
        self._result.connect(self._deliver_result)
        self._status.connect(self._deliver_status)
        self._microphone.connect(self._deliver_microphone)
        self._scoped_result.connect(self._deliver_scoped_result)
        self._dictation_state.connect(self._deliver_dictation_state)
        self._dictation_failure.connect(self._deliver_dictation_failure)

    @Slot(int, int, str)
    def _deliver_dictation_state(self, generation, revision, state):
        if (generation == self._generation and revision == self._mode[0]
                and self._mode[1] and not self._stop.is_set()):
            self.dictation_state_changed.emit(state)

    @Slot(int, int, str)
    def _deliver_dictation_failure(self, generation, revision, message):
        if (generation == self._generation and revision == self._mode[0]
                and not self._stop.is_set()):
            self.dictation_failed.emit(message)

    def _fail_dictation(self, generation, message, mode=None):
        if mode is not None and (mode != self._mode or generation != self._generation):
            return
        revision = self._mode[0] + 1
        self._mode = (revision, False)
        self._dictation_failure.emit(generation, revision, message)

    def set_dictation(self, active):
        revision, current = self._mode
        if current != active:
            self._mode = (revision + 1, bool(active))

    @Slot(int, int, str)
    def _deliver_scoped_result(self, generation, revision, text):
        if (
            generation == self._generation
            and revision == self._mode[0]
            and not self._stop.is_set()
        ):
            if self._mode[1]:
                self.dictated.emit(text)
            else:
                self._result.emit(generation, text)

    @Slot(int, str)
    def _deliver_result(self, generation, text):
        if generation == self._generation and not self._stop.is_set():
            self.recognized.emit(text)

    @Slot(int, str)
    def _deliver_status(self, generation, text):
        if generation == self._generation and not self._stop.is_set():
            self.status_changed.emit(text)

    @Slot(int, str)
    def _deliver_microphone(self, generation, name):
        if generation == self._generation and not self._stop.is_set():
            self.microphone_changed.emit(name)

    def set_macro_phrases(self, phrases):
        """Cada vez que se crea, edita, activa o desactiva una macro (PB-42)."""
        self._macro_phrases = tuple(phrases)

    @property
    def running(self):
        return (
            not self._stop.is_set()
            and self._thread is not None
            and self._thread.is_alive()
        )

    def start(self):
        if self.running:
            return
        self._generation += 1
        self._stop = threading.Event()
        self.status_changed.emit(STARTING)
        self._thread = threading.Thread(
            target=self._run, args=(self._generation, self._stop), daemon=True
        )
        self._thread.start()

    def stop(self):
        """Cierra el micrófono de inmediato, sin esperar al hilo."""
        self._stop.set()
        self.set_dictation(False)
        self._generation += 1
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.abort()
                stream.close()
            except sd.PortAudioError:
                pass
        self.status_changed.emit(DISABLED)

    def _run(self, generation=None, stopped=None):
        generation = self._generation if generation is None else generation
        stopped = self._stop if stopped is None else stopped
        applied = self._macro_phrases  # frases con las que se crea el reconocedor
        mode = self._mode
        recognizer = self._create_recognizer(generation, stopped, applied)
        if recognizer is None:
            # Sin modelo no se abre el micrófono; el resto de ErgoSense sigue igual.
            return

        chunks = queue.Queue(maxsize=150)
        overflow = threading.Event()

        def capture(data, frames, timing, status):
            if not stopped.is_set():
                try:
                    chunks.put_nowait(bytes(data))
                except queue.Full:
                    overflow.set()

        def clear_audio():
            while True:
                try:
                    chunks.get_nowait()
                except queue.Empty:
                    break
            overflow.clear()

        try:
            with sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=BLOCK_FRAMES,
                callback=capture,
            ) as stream:
                if stopped.is_set():
                    return
                self._stream = stream
                self._microphone.emit(generation, _input_device_name())
                self._status.emit(generation, LISTENING)
                while not stopped.is_set():
                    phrases = self._macro_phrases
                    requested_mode = self._mode
                    if requested_mode != mode:
                        mode = requested_mode
                        clear_audio()
                        if mode[1]:
                            self._dictation_state.emit(generation, mode[0], "preparing")
                            try:
                                recognizer = self._dictation_factory()
                            except (OSError, RuntimeError, ValueError):
                                self._fail_dictation(generation,
                                    "No se pudo preparar el dictado. Comprueba la conexión "
                                    "para descargar el modelo la primera vez y reintenta.", mode)
                                continue
                            if hasattr(recognizer, "set_state_callback"):
                                revision = mode[0]
                                recognizer.set_state_callback(
                                    lambda state, revision=revision:
                                    self._dictation_state.emit(generation, revision, state)
                                )
                            clear_audio()
                            self._dictation_state.emit(generation, mode[0], "listening")
                        else:
                            recognizer = self._recognizer_factory(phrases)
                        applied = phrases
                    elif phrases != applied and not mode[1]:
                        # Cambiaron las macros: reconocedor nuevo con la nueva lista.
                        recognizer = self._recognizer_factory(phrases)
                        applied = phrases
                    if overflow.is_set():
                        clear_audio()
                        if mode[1]:
                            self._fail_dictation(generation,
                                "El dictado se atrasó y se detuvo para no escribir "
                                "una frase incompleta. Vuelve a iniciarlo.", mode)
                        else:
                            recognizer = self._recognizer_factory(phrases)
                        continue
                    try:
                        data = chunks.get(timeout=0.25)
                    except queue.Empty:
                        continue
                    # True cuando termina una frase, al detectar el silencio siguiente.
                    try:
                        if recognizer.AcceptWaveform(data):
                            text = json.loads(recognizer.Result()).get("text", "")
                            if text and not stopped.is_set():
                                self._scoped_result.emit(generation, mode[0], text)
                    except (OSError, RuntimeError, ValueError):
                        if not mode[1]:
                            raise
                        self._fail_dictation(generation,
                            "No se pudo transcribir la frase. Vuelve a iniciar el dictado.", mode)
        except (sd.PortAudioError, OSError, ValueError):
            if not stopped.is_set():
                self._status.emit(generation, MICROPHONE_UNAVAILABLE)
        finally:
            if generation == self._generation:
                self._stream = None

    def _create_recognizer(self, generation, stopped, phrases):
        """Crea el reconocedor. La primera vez, antes descarga el modelo de voz."""
        try:
            return self._recognizer_factory(phrases)
        except VoiceModelMissing:
            pass
        if not self._download_model(generation, stopped):
            return None
        self._status.emit(generation, STARTING)
        try:
            return self._recognizer_factory(phrases)
        except VoiceModelMissing:
            self._status.emit(generation, MODEL_MISSING)
            return None

    def _download_model(self, generation, stopped):
        """Descarga el modelo e informa el avance. Devuelve True si quedó instalado."""
        shown = None

        def progress(percent):
            nonlocal shown
            if percent != shown:  # solo cuando cambia, para no saturar la ventana
                shown = percent
                self._status.emit(generation, f"{DOWNLOADING} · {percent} %")

        self._status.emit(generation, f"{DOWNLOADING}...")
        try:
            self._model_downloader(progress=progress, cancelled=stopped.is_set)
        except DownloadCancelled:
            return False  # se apagó la voz: no hay nada que informar
        except ModelDownloadError:
            self._status.emit(generation, DOWNLOAD_FAILED)
            return False
        return True


def _input_device_name():
    try:
        return sd.query_devices(kind="input")["name"]
    except (sd.PortAudioError, ValueError):
        return ""
