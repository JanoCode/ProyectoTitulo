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
