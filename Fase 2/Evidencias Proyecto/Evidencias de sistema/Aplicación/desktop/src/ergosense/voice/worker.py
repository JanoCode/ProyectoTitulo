"""Captura de audio y reconocimiento de comandos fuera del hilo de la interfaz.

El reconocimiento usa Vosk y funciona sin internet: el audio del micrófono se
procesa en este equipo, por bloques de 0,1 s, y nunca se guarda ni se envía a otro
servicio (RNF-17).
"""

import json
import queue
import threading

import sounddevice as sd
from PySide6.QtCore import QObject, Signal, Slot

from ergosense.voice.recognizer import SAMPLE_RATE, VoiceModelMissing, create_recognizer

# Estados que se informan a la ventana.
STARTING = "Iniciando micrófono..."
LISTENING = "Activo · micrófono en uso"
MICROPHONE_UNAVAILABLE = "Micrófono no disponible"
MODEL_MISSING = "Falta el modelo de voz"
DISABLED = "Desactivado"

# 0,1 s de audio por bloque: lo bastante corto para responder rápido (RNF-07).
BLOCK_FRAMES = SAMPLE_RATE // 10


class VoiceWorker(QObject):
    recognized = Signal(str)
    status_changed = Signal(str)
    microphone_changed = Signal(str)  # nombre del micrófono que se está usando
    _result = Signal(int, str)
    _status = Signal(int, str)
    _microphone = Signal(int, str)

    def __init__(self, recognizer_factory=create_recognizer):
        super().__init__()
        # En las pruebas se entrega un reconocedor falso, sin cargar el modelo.
        self._recognizer_factory = recognizer_factory
        self._stop = threading.Event()
        self._thread = None
        self._stream = None
        # Cada encendido tiene su número; lo que llegue de un encendido anterior se
        # descarta, para que una frase atrasada no ejecute nada al volver a activar.
        self._generation = 0
        self._result.connect(self._deliver_result)
        self._status.connect(self._deliver_status)
        self._microphone.connect(self._deliver_microphone)

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
        try:
            recognizer = self._recognizer_factory()
        except VoiceModelMissing:
            # Sin modelo no se abre el micrófono; el resto de ErgoSense sigue igual.
            self._status.emit(generation, MODEL_MISSING)
            return

        chunks = queue.Queue(maxsize=50)

        def capture(data, frames, timing, status):
            if not stopped.is_set():
                try:
                    chunks.put_nowait(bytes(data))
                except queue.Full:
                    pass  # si el reconocimiento se atrasa, se pierde ese bloque

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
                    try:
                        data = chunks.get(timeout=0.25)
                    except queue.Empty:
                        continue
                    # True cuando termina una frase, al detectar el silencio siguiente.
                    if recognizer.AcceptWaveform(data):
                        text = json.loads(recognizer.Result()).get("text", "")
                        if text and not stopped.is_set():
                            self._result.emit(generation, text)
        except (sd.PortAudioError, OSError, ValueError):
            if not stopped.is_set():
                self._status.emit(generation, MICROPHONE_UNAVAILABLE)
        finally:
            if generation == self._generation:
                self._stream = None


def _input_device_name():
    try:
        return sd.query_devices(kind="input")["name"]
    except (sd.PortAudioError, ValueError):
        return ""
