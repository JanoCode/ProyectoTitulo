# ErgoSense – Aplicación de escritorio

ErgoSense es una aplicación de escritorio para Windows que monitorea el tiempo de uso del computador, recomienda pausas y, en los Sprints siguientes, permitirá controlar el equipo mediante gestos, voz y macros.

## Estado actual: Sprint 02

El Sprint 02 conserva el monitoreo del Sprint 01 y agrega el flujo completo de cuentas y persistencia:

| Funcionalidad | Resultado |
|---|---|
| Registro e inicio de sesión | La aplicación crea cuentas e inicia sesión mediante la API. |
| Tokens | El token de acceso vive en memoria y el de renovación se guarda en el almacén seguro de Windows mediante `keyring`. |
| Persistencia | Las sesiones de uso y pausas se guardan en PostgreSQL a través del servidor. |
| Inactividad | Teclado, clic, desplazamiento y movimiento del mouse cuentan como actividad. |
| Pausas | Después del umbral configurado se abre una pausa; al volver la actividad se cierra y empieza un nuevo período de 60 minutos. |
| Cierre seguro | Al cerrar la aplicación se finalizan la pausa y la sesión que hayan quedado abiertas. |

La ventana sigue siendo deliberadamente sencilla: la interfaz visual completa corresponde al Sprint 04.

## Requisito previo del Sprint 02

El servidor y PostgreSQL deben estar activos. Desde la carpeta `codigo` ejecuta:

```powershell
docker compose up --build -d
```

La aplicación se conecta de forma predeterminada a `http://127.0.0.1:8000`.

El incremento del Sprint 01, "Sistema de alerta y monitoreo de actividad", incluye:

| PB | Funcionalidad |
|---|---|
| PB-01 | Registro y visualización del tiempo del período de actividad. |
| PB-02 y PB-03 | Detección de la actividad del teclado y del mouse en todo el sistema. |
| PB-04 | Período de actividad de 60 minutos, no configurable por el usuario. |
| PB-05 | Aviso que recomienda una pausa al cumplirse el período. Si la ventana está minimizada o en segundo plano, el aviso también se muestra como notificación de Windows. |
| PB-06 | Un período nuevo comienza después de cada aviso. |

La ventana es básica a propósito: la interfaz completa se desarrolla en el Sprint 04.

**Privacidad (RNF-16):** la aplicación registra solo el momento de la última interacción. Nunca guarda qué tecla se presionó ni qué botón del mouse se usó.

## Requisitos

- Windows 10 u 11 de 64 bits.
- [uv](https://docs.astral.sh/uv/), que administra Python y las dependencias. Si falta Python 3.12, uv lo descarga solo.

Para instalar uv:

```powershell
winget install --id=astral-sh.uv -e
```

## Instalación

El proyecto está dentro de OneDrive. Por eso, el entorno virtual se crea **fuera** de esa carpeta, ya que OneDrive intenta sincronizar miles de archivos y puede bloquearlos.

1. Abre la carpeta `desktop` en VS Code. El archivo `.vscode/settings.json` ya define la variable `UV_PROJECT_ENVIRONMENT` para las terminales de VS Code. Si usas otra terminal, defínela tú en cada sesión:

   ```powershell
   $env:UV_PROJECT_ENVIRONMENT = "C:\venvs\ergosense-desktop"
   ```

2. Instala las dependencias:

   ```powershell
   uv sync
   ```

3. En VS Code, ejecuta **Python: Select Interpreter** y elige `C:\venvs\ergosense-desktop\Scripts\python.exe`.

## Ejecutar la aplicación

Desde la carpeta `desktop`:

```powershell
uv run ergosense
```

Al abrirse, ErgoSense intenta recuperar una sesión guardada. Si no existe, muestra el inicio de sesión y permite abrir el formulario de registro. Después de autenticarse crea una sesión de uso remota y carga la configuración de la cuenta.

Para usar otra dirección del servidor:

```powershell
$env:ERGOSENSE_API_URL = "http://192.168.1.20:8000"
uv run ergosense
```

Si aparece `Failed to spawn: ergosense`, la terminal no está en la carpeta `desktop`.

### Probar el aviso sin esperar 60 minutos

Solo para desarrollo, la variable `ERGOSENSE_LIMIT_SECONDS` acorta el período. El usuario final siempre tiene 60 minutos.

```powershell
$env:ERGOSENSE_LIMIT_SECONDS = "30"
uv run ergosense
```

Al terminar, borra la variable para volver a los 60 minutos:

```powershell
Remove-Item Env:ERGOSENSE_LIMIT_SECONDS
```

El umbral de inactividad se obtiene desde la configuración de la cuenta. Para comprobar el flujo de pausa rápidamente durante desarrollo:

```powershell
$env:ERGOSENSE_INACTIVITY_SECONDS = "10"
uv run ergosense
```

Al terminar:

```powershell
Remove-Item Env:ERGOSENSE_INACTIVITY_SECONDS
```

Si la notificación de Windows no aparece, revisa que el Asistente de concentración esté desactivado, en Configuración → Sistema.

## Pruebas y estilo

```powershell
uv run pytest                        # pruebas automatizadas
uv run pytest --cov=ergosense        # pruebas con reporte de cobertura
uv run ruff check                    # análisis de estilo
uv run ruff format                   # formato del código
```

Las pruebas usan un reloj falso (`FakeClock`), así que verifican el período de 60 minutos sin esperar. Las pruebas de la interfaz no abren ventanas en la pantalla. Cada prueba indica en su nombre el caso del Plan de pruebas que verifica, por ejemplo `test_cp_01_08_...`.

Los casos que requieren interacción real, como el teclado, el mouse o las notificaciones de Windows, se prueban de forma manual con los scripts de `scripts/`:

```powershell
uv run python scripts/demo_input_listener.py   # CP-01-03 y CP-01-04
uv run python scripts/demo_main_window.py      # ventana con datos de ejemplo
```

## Estructura

```
desktop/
├── src/ergosense/
│   ├── app/          # arranque y controlador: conecta el monitoreo con la ventana
│   ├── monitoring/   # período de actividad, registro y escucha de teclado y mouse
│   └── ui/           # ventana principal y formato del tiempo
├── tests/            # pruebas automatizadas (pytest), con la misma estructura que src
├── scripts/          # pruebas manuales
└── pyproject.toml    # dependencias y configuración del proyecto
```

La organización en capas sigue el Documento de arquitectura. `monitoring` no conoce la interfaz: el controlador de `app` revisa el período una vez por segundo y le indica a la ventana qué mostrar. La escucha de teclado y mouse corre en sus propios hilos y solo anota la actividad. La ventana se actualiza únicamente desde el hilo principal de Qt.

## Flujo de trabajo

Cada integrante trabaja en su propia rama (`dev-<nombre>`). Los cambios pasan a `dev` mediante un pull request que revisa el otro integrante, y `dev` pasa a `main` al cerrar cada Sprint. Antes de cada pull request se ejecutan `uv run pytest` y `uv run ruff check`.

## Componentes agregados en el Sprint 02

```text
src/ergosense/
|-- api_client/   # solicitudes HTTP, tokens y almacén seguro
|-- app/          # arranque y coordinación entre módulos
|-- monitoring/   # actividad, período e inactividad
`-- ui/           # acceso, registro, ventana y formato del tiempo
```

`monitoring` no conoce la interfaz ni la base de datos: detecta actividad y genera transiciones. `api_client` no decide reglas de inactividad: solamente conversa con el servidor. El controlador de `app` une ambas partes y le indica a la ventana qué mostrar.

## Seguridad de la sesión

- La contraseña se envía únicamente al registrar o iniciar sesión y el servidor la transforma con bcrypt.
- El token de acceso dura poco tiempo y permanece en memoria.
- El token de renovación dura más y se guarda con `keyring`, que usa el administrador de credenciales del sistema.
- Si vence el acceso, el cliente solicita uno nuevo y repite una sola vez la operación original.
- Al cerrar sesión, el servidor revoca la renovación y el cliente la borra del equipo.
- Un cierre normal de la aplicación termina la sesión de uso, pero mantiene la sesión de usuario para poder recuperarla al volver a abrir.
