import argparse
import base64
import json
import os
import re
import subprocess
import tempfile
import time
import wave
from pathlib import Path

from ergosense.voice.commands import COMMANDS, normalize, resolve_command
from ergosense.voice.recognizer import create_dictation_recognizer, create_recognizer

LONG_SAMPLES = (
    "necesito buscar información sobre ejercicios para aliviar el dolor de espalda",
    "cómo puedo mejorar mi postura cuando trabajo frente al computador",
    "quiero encontrar una silla cómoda para trabajar desde mi casa",
    "mañana tengo que presentar el proyecto de título en la universidad",
    "abre el navegador y busca recetas de comida saludable",
    "el reconocimiento de voz debe escribir exactamente lo que estoy diciendo",
    "estoy probando el dictado para escribir sin usar el teclado",
    "quiero buscar videos sobre programación en python y bases de datos",
    "mi nombre es alejandro y estoy desarrollando una aplicación de escritorio",
    "dónde puedo encontrar los documentos del proyecto ergosense",
)


def words(text):
    return re.findall(r"\w+", normalize(text))


def word_errors(expected, actual):
    previous = list(range(len(actual) + 1))
    for index, word in enumerate(expected, 1):
        current = [index]
        for offset, other in enumerate(actual, 1):
            current.append(min(
                current[-1] + 1, previous[offset] + 1,
                previous[offset - 1] + (word != other),
            ))
        previous = current
    return previous[-1]

SPEAK = """
$ErrorActionPreference = 'Stop'
$speaker = New-Object -ComObject SAPI.SpVoice
$spanish = @($speaker.GetVoices() | Where-Object { $_.GetAttribute('Language') -eq '80A' })
if ($spanish.Count -eq 0) { throw 'Falta una voz SAPI en español' }
$speaker.Voice = $spanish[0]
$stream = New-Object -ComObject SAPI.SpFileStream
$stream.Format.Type = 18
$stream.Open($env:ERGOSENSE_SAMPLE_PATH, 3, $false)
try {
    $speaker.AudioOutputStream = $stream
    $null = $speaker.Speak($env:ERGOSENSE_SAMPLE_PHRASE)
} finally { $stream.Close() }
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dictation", action="store_true")
    parser.add_argument("--dictation-long", action="store_true")
    parser.add_argument("--compare-previous", action="store_true")
    parser.add_argument("--noise-snr", type=float)
    parser.add_argument("--gain", type=float, default=1.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.gain <= 0:
        parser.error("--gain debe ser positivo")
    args.dictation = args.dictation or args.dictation_long
    if os.name != "nt":
        raise SystemExit("Esta prueba requiere Windows y una voz SAPI en español")
    encoded = base64.b64encode(SPEAK.encode("utf-16le")).decode("ascii")
    results = []
    samples = (
        ("buscar información sobre ergonomía", "ejercicios para las manos",
         "cómo mejorar la postura", "clic izquierdo", "abrir correo",
         "terminar dictado", "enviar texto", "borrar palabra", "nueva línea",
         "punto", "coma")
        if args.dictation else
        (*COMMANDS, "buenos dias como estas", "necesito terminar este trabajo")
    )
    if args.dictation_long:
        samples = LONG_SAMPLES
    old_model = None
    if args.compare_previous:
        from ergosense.voice.recognizer import load_model
        old_model = load_model()
    with tempfile.TemporaryDirectory(prefix="ergosense-voice-qa-") as folder:
        for phrase in samples:
            path = Path(folder) / "sample.wav"
            env = {**os.environ, "ERGOSENSE_SAMPLE_PATH": str(path),
                   "ERGOSENSE_SAMPLE_PHRASE": phrase}
            subprocess.run(["powershell", "-NoProfile", "-NonInteractive",
                "-EncodedCommand", encoded], check=True, capture_output=True,
                env=env, timeout=20)
            recognizer = (
                create_dictation_recognizer() if args.dictation else create_recognizer()
            )
            with wave.open(str(path), "rb") as audio:
                assert (audio.getframerate(), audio.getnchannels(), audio.getsampwidth()) == (16000, 1, 2)
                data = audio.readframes(audio.getnframes())
            if args.gain != 1.0 or args.noise_snr is not None:
                import numpy as np

                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768
                if args.noise_snr is not None:
                    noise = np.random.default_rng(len(results) + 100).normal(0, 1, samples.size)
                    samples += noise * np.sqrt(np.mean(samples * samples)) / (10 ** (args.noise_snr / 20))
                samples *= args.gain
                data = (np.clip(samples, -.99, .99) * 32767).astype(np.int16).tobytes()
            started = time.perf_counter()
            recognizer.AcceptWaveform(data + bytes(16000 * 2))
            text = json.loads(recognizer.FinalResult()).get("text", "")
            passed = (
                words(phrase) == words(text) if args.dictation else
                resolve_command(phrase) == resolve_command(text)
            )
            result = {
                "sample": phrase, "recognized": text, "passed": passed,
                "seconds": round(time.perf_counter() - started, 3),
                "word_errors": word_errors(words(phrase), words(text)),
                "word_count": len(words(phrase)),
            }
            if old_model is not None:
                import vosk
                previous = vosk.KaldiRecognizer(old_model, 16000)
                previous.AcceptWaveform(data + bytes(16000 * 2))
                old_text = json.loads(previous.FinalResult()).get("text", "")
                result.update(previous=old_text,
                    previous_word_errors=word_errors(words(phrase), words(old_text)))
            results.append(result)
    report = {"source": "SAPI Spanish Mexico", "human_microphone_test": False,
              "mode": "dictation" if args.dictation else "commands",
              "gain": args.gain, "noise_snr_db": args.noise_snr, "results": results}
    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
