import argparse
import base64
import json
import os
import subprocess
import tempfile
import wave
from pathlib import Path

from ergosense.voice.commands import COMMANDS, normalize, resolve_command
from ergosense.voice.recognizer import create_dictation_recognizer, create_recognizer

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
    args = parser.parse_args()
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
            recognizer.AcceptWaveform(data + bytes(16000 * 2))
            text = json.loads(recognizer.FinalResult()).get("text", "")
            passed = (
                normalize(phrase) == normalize(text) if args.dictation else
                resolve_command(phrase) == resolve_command(text)
            )
            results.append({"sample": phrase, "recognized": text, "passed": passed})
    print(json.dumps({"source": "SAPI Spanish Mexico", "human_microphone_test": False,
                      "mode": "dictation" if args.dictation else "commands",
                      "results": results}, ensure_ascii=False))
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
