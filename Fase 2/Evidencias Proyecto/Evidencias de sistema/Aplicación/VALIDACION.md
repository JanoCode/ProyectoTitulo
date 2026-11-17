# Validación del MVP

## Entorno de pruebas

Ejecutar los comandos desde esta carpeta en PowerShell. Se requiere Python 3.12,
uv y Docker Desktop con contenedores Linux. La instancia QA usa el puerto local
18080 y un volumen propio; no utiliza el PostgreSQL del entorno habitual.

```powershell
Copy-Item .env.qa.example .env.qa
```

Editar `.env.qa` y sustituir ambas claves. Conservar esas claves mientras exista
el volumen de QA. El archivo está excluido de Git.

```powershell
docker compose --env-file .env.qa -f compose.qa.yml up --build --wait
```

## Pruebas de API y escritorio

```powershell
Push-Location server
uv sync --locked
uv run ruff check
uv run python -m pytest --cov=app --cov-report=term-missing
Pop-Location

Push-Location desktop
uv sync --locked
$env:QT_QPA_PLATFORM = 'offscreen'
uv run ruff check
uv run python -m pytest --cov=ergosense --cov-report=term-missing
Pop-Location
```

Las pruebas unitarias simulan los dispositivos. Las pruebas de integración que
requieren un servidor real se omiten hasta configurar su URL.

## Cliente real y PostgreSQL

Usar exclusivamente la instancia QA. Estas pruebas crean cuentas y datos de
prueba. La prueba de reinicio detiene y vuelve a iniciar únicamente el contenedor
`ergosense-qa-api-1`.

```powershell
Push-Location desktop
$env:ERGOSENSE_TEST_API_URL = 'http://127.0.0.1:18080/api/v1'
$env:ERGOSENSE_QA_API_CONTAINER = 'ergosense-qa-api-1'
uv run python -m pytest tests/integration -v
Remove-Item Env:ERGOSENSE_TEST_API_URL
Remove-Item Env:ERGOSENSE_QA_API_CONTAINER
Pop-Location
```

Para detener QA conservando sus datos:

```powershell
docker compose --env-file .env.qa -f compose.qa.yml stop
```

## Validación práctica pendiente

Para comprobar cámara y micrófono simultáneamente sin ejecutar acciones del
sistema ni guardar imágenes o sonido:

```powershell
Push-Location desktop
uv run python scripts/download_voice_model.py
uv run python scripts/check_devices.py --seconds 60
uv run python scripts/check_voice_samples.py
Pop-Location
```

La última orden requiere Windows con la voz SAPI Spanish Mexico. Genera muestras
de audio sintéticas en una carpeta temporal, verifica los diez comandos y dos
frases ajenas y retira las muestras al terminar. No utiliza la voz del usuario.

Para medir una hora de reloj real con los dispositivos activos:

```powershell
Push-Location desktop
uv run python scripts/check_devices.py --seconds 3601 --output "$env:TEMP\ergosense-hora-real.json"
Pop-Location
```

`real_timer_passed` indica si el temporizador independiente avisó al cumplirse
3600 segundos reales. Esta prueba no ejecuta acciones del sistema, no representa
actividad continua de una persona y no comprueba el reinicio por pausas del
controlador integrado. No sustituye los casos de aceptación de la tabla siguiente.

Ejecutar la aplicación con `uv run ergosense` desde `desktop`, sin la variable
`QT_QPA_PLATFORM=offscreen`. Para retirarla de la sesión de pruebas:

```powershell
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
```

Registrar fecha, equipo, resultado y evidencia para cada caso:

| Caso | Procedimiento | Resultado esperado |
| --- | --- | --- |
| Cámara y gestos | Probar cursor, clics, arrastre, scroll y macros con puño/L | Acciones correctas y liberación del arrastre al apagar |
| Voz y ruido | Probar cada comando, frases de macros, conversación y ruido | Una ejecución por activación válida y rechazo de expresiones ajenas |
| Uso simultáneo | Usar gestos, voz y macros con monitoreo activo | Sin intercalado de pasos ni bloqueo de la interfaz |
| Aviso real | Mantener actividad durante 60 minutos sin variables de aceleración | Un aviso y reinicio del período |
| Pausa real | Permanecer inactivo 10 minutos y repetir con otro valor configurado | Pausa persistida y reinicio del período al volver |
| Dos equipos físicos | Iniciar la misma cuenta en otro computador | Preferencias y macros disponibles; aplicaciones resueltas por equipo |
| Despliegue externo | Construir Docker en otro equipo con variables propias | Migraciones y API saludables |
| Uso prolongado real | Mantener módulos activos durante varias horas | Sin fallos, recursos retenidos ni acciones involuntarias |

La simulación automatizada de 24 horas verifica la lógica con reloj controlado;
no acredita 24 horas de uso real ni mide precisión de dispositivos. El Sprint 06
requiere completar y registrar las pruebas prácticas antes de su cierre total.

## Avisos y distribución portable

El cliente incluye avisos e indicadores sobre otras aplicaciones. La prueba
nativa `desktop/scripts/check_desktop_feedback.py` comprobó flags de ventana
superior, transparencia de entrada, ausencia de activación, conservación del foco
y cierre. La suite de escritorio obtuvo 386 aprobadas y siete omitidas.

Para validar la interacción completa, minimizar ErgoSense, activar dictado por
voz sobre un campo de otra aplicación y comprobar preparación, escucha,
procesamiento, escritura y desactivación sin cambio de foco. Repetir para gestos
y errores de dispositivo. La prueba nativa de ventanas no sustituye este ensayo
con cámara y micrófono reales.

La construcción portable ejecuta `ErgoSense.exe --self-test <archivo.json>` desde
la distribución y carga Qt, el seguimiento de mano, Vosk, VAD, Whisper y los avisos.
No abre la cámara ni envía credenciales en esa verificación. Tras trasladar el ZIP
a otro PC, extraerlo completo, configurar la URL del servidor y repetir el ensayo
de uso. La conexión local 127.0.0.1 no identifica al equipo de origen.

## Confirmación con Enter y mejora del dictado — 17 de noviembre de 2026

El gesto OK confirma con Enter después de tres cuadros estables y una permanencia
adicional de 0,35 segundos. Envía una sola pulsación y se rearma al volver al gesto
de apuntar. La pérdida de seguimiento no lo rearma. OK queda reservado y no se
puede asignar a una macro. La suite comprueba estas condiciones y la liberación
de la tecla aun cuando falle el controlador de entrada.

El dictado utiliza large-v3-turbo con normalización de nivel y selección local del
micrófono. La aceleración CUDA es opcional; sin un entorno compatible se utiliza
CPU. Las pérdidas de captura se detectan para evitar transcribir audio incompleto.
La regresión obtuvo 406 pruebas aprobadas y siete omitidas en el cliente, y 102
aprobadas en la API. Ruff no encontró incidencias.

En diez frases sintéticas (102 palabras por condición), la comparación reproducible
obtuvo un error tanto antes como después con audio limpio y con volumen reducido.
Con ruido sintético a 8 dB, pasó de dos errores a uno. El promedio de decodificación
fue de aproximadamente 2,1 s en el sistema anterior con CPU y 0,8 s con el nuevo
en GPU. La diferencia incluye el cambio de hardware de ejecución y no mide el
retardo total desde que una persona termina de hablar. Estas muestras no acreditan
precisión con voz humana ni condiciones reales de uso.

Siguen pendientes la aceptación con cámara y micrófono reales, los intentos
repetidos del gesto OK y las pruebas prolongadas y entre equipos físicos. Véanse
`Dictado por voz.md`, `Confirmación con Enter.md` y CP-06-22 a CP-06-27 del Plan de
pruebas para los criterios y límites de la evidencia.