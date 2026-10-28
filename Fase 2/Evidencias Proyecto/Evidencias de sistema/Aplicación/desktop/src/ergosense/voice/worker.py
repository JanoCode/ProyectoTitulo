"""Captura acotada de audio y reconocimiento remoto fuera del hilo de interfaz."""

import queue
import threading

import sounddevice as sd
import speech_recognition as sr
from PySide6.QtCore import QObject, Signal, Slot


class _AudioStopped(Exception):
    pass


class _AudioInput(sr.AudioSource):
    """Adapta bloques PCM a la detección de frases y silencios del reconocedor."""

    def __init__(self, chunks, stopped):
        self.CHUNK = 4000
        self.SAMPLE_RATE = 16000
        self.SAMPLE_WIDTH = 2
        self.stream = self
        self._chunks = chunks
        self._stopped = stopped

    def read(self, size):
        while not self._stopped.is_set():
            try:
                return self._chunks.get(timeout=0.25)
            except queue.Empty:
                continue
        raise _AudioStopped

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class VoiceWorker(QObject):
    recognized = Signal(str)
    status_changed = Signal(str)
    _result = Signal(int, str)
    _status = Signal(int, str)

    def __init__(self):
        super().__init__()
        self._stop = threading.Event()
        self._thread = None
        self._stream = None
        self._generation = 0
        self._result.connect(self._deliver_result)
        self._status.connect(self._deliver_status)

    @Slot(int, str)
    def _deliver_result(self, generation, text):
        if generation == self._generation and not self._stop.is_set():
            self.recognized.emit(text)

    @Slot(int, str)
    def _deliver_status(self, generation, text):
        if generation == self._generation and not self._stop.is_set():
            self.status_changed.emit(text)

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
        self.status_changed.emit("Iniciando micrófono...")
        self._thread = threading.Thread(
            target=self._run, args=(self._generation, self._stop), daemon=True
        )
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._generation += 1
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.abort()
                stream.close()
            except sd.PortAudioError:
                pass
        self.status_changed.emit("Desactivado")

    def _run(self, generation=None, stopped=None):
        generation = self._generation if generation is None else generation
        stopped = self._stop if stopped is None else stopped
        chunks = queue.Queue(maxsize=40)

        def capture(data, frames, timing, status):
            if not stopped.is_set():
                try:
                    chunks.put_nowait(bytes(data))
                except queue.Full:
                    pass

        recognizer = sr.Recognizer()
        recognizer.operation_timeout = 5
        try:
            with sd.RawInputStream(
                samplerate=16000,
                channels=1,
                dtype="int16",
                blocksize=4000,
                callback=capture,
            ) as stream:
                if stopped.is_set():
                    return
                self._stream = stream
                self._status.emit(generation, "Activo · micrófono en uso")
                source = _AudioInput(chunks, stopped)
                while not stopped.is_set():
                    try:
                        audio = recognizer.listen(
                            source, timeout=1, phrase_time_limit=5
                        )
                        if stopped.is_set():
                            break
                        text = recognizer.recognize_google(
                            audio,
                            language="es-CL",
                            endpoint="https://www.google.com/speech-api/v2/recognize",
                        )
                        if not stopped.is_set():
                            self._result.emit(generation, text)
                        self._status.emit(generation, "Activo · micrófono en uso")
                    except (sr.UnknownValueError, sr.WaitTimeoutError):
                        continue
                    except (sr.RequestError, TimeoutError):
                        self._status.emit(
                            generation,
                            "Sin conexión al reconocimiento de voz · micrófono en uso",
                        )
                    # Evita ejecutar audio acumulado mientras se consultaba el servicio.
                    while not chunks.empty():
                        try:
                            chunks.get_nowait()
                        except queue.Empty:
                            break
        except _AudioStopped:
            pass
        except (sd.PortAudioError, OSError, ValueError):
            if not stopped.is_set():
                self._status.emit(generation, "Micrófono no disponible")
        finally:
            if generation == self._generation:
                self._stream = None
