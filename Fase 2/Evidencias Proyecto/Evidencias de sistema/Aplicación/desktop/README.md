# ErgoSense – Aplicación de escritorio

ErgoSense es una aplicación de escritorio para Windows que monitorea el tiempo de uso del computador, recomienda pausas y permite controlar el equipo mediante gestos de la mano. En los Sprints siguientes se agregarán el control por voz y las macros.

## Estado actual: Sprint 03

| Sprint | Funcionalidad |
|---|---|
| 01 | Monitoreo de actividad de teclado y mouse, aviso de pausa a los 60 minutos (PB-01 a PB-06). |
| 02 | Cuentas, inicio de sesión, sesiones de uso y pausas por inactividad guardadas en el servidor (PB-32 a PB-35, PB-48 y PB-49). |
| 03 | Control mediante gestos con la cámara web y configuración del usuario (PB-07 a PB-13, PB-36 y PB-37). |

La ventana sigue siendo deliberadamente sencilla: la interfaz visual completa corresponde al Sprint 04.

**Privacidad:** la aplicación registra solo el momento de la última interacción, nunca qué tecla se presionó ni qué botón se usó (RNF-16). Las imágenes de la cámara se procesan en memoria: nunca se guardan en disco ni se envían al servidor (RNF-17).

## Requisitos

- Windows 10 u 11 de 64 bits.
- Una cámara web, para el control mediante gestos. Sin cámara, el resto de ErgoSense funciona igual.
- [uv](https://docs.astral.sh/uv/), que administra Python y las dependencias. Si falta Python 3.12, uv lo descarga solo.
- El servidor de ErgoSense en Docker (ver `../server/README.md`).

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

El modelo de detección de la mano (`src/ergosense/gestures/models/hand_landmarker.task`, de MediaPipe, licencia Apache 2.0) viene incluido en el repositorio, así que no hay que descargar nada más.

## Ejecutar la aplicación

1. Abre Docker Desktop y levanta el servidor. Desde la carpeta `desktop`:

   ```powershell
   docker compose -f ../docker-compose.yml up -d
   ```

2. Abre la aplicación:

   ```powershell
   uv run ergosense
   ```

Al abrirse, ErgoSense intenta recuperar una sesión guardada. Si no existe, muestra el inicio de sesión y permite abrir el formulario de registro. Después de autenticarse crea una sesión de uso remota, carga la configuración de la cuenta y, si los gestos están activados, enciende la cámara.

La aplicación se conecta a `http://127.0.0.1:8000/api/v1`. Para usar otra dirección del servidor, indica la URL completa de la API, incluido el prefijo `/api/v1`:

```powershell
$env:ERGOSENSE_API_URL = "http://192.168.1.20:8000/api/v1"
uv run ergosense
```

Si aparece `Failed to spawn: ergosense`, la terminal no está en la carpeta `desktop`.

## Control mediante gestos

Los gestos se hacen con la **palma de frente a la cámara**, partiendo de la mano abierta. El pulgar funciona como el botón izquierdo y el índice como el derecho.

| Gesto | Cómo se hace | Acción |
|---|---|---|
| Mano abierta | Los cinco dedos estirados | Mover el cursor. |
| Pulgar adentro | Desde la mano abierta, se dobla solo el pulgar hacia la palma | Click izquierdo; si se mantiene 0,4 s o más, arrastre. |
| Índice abajo | Desde la mano abierta, se dobla solo el índice | Click derecho. |
| Dos dedos | Índice y medio estirados, el resto doblado | Scroll: subir o bajar la mano. |
| Puño y "L" | — | Reservados para activar macros en el Sprint 05. |

El cursor sigue el centro de la palma, que no se mueve al doblar el pulgar o el índice, y se mueve solo dentro del monitor principal. Para evitar activaciones accidentales (PB-13), un gesto debe mantenerse unos 0,1 s para contar, cada click se ejecuta una sola vez y las poses que no corresponden a un gesto no hacen nada.

La fila **Gestos** de la ventana muestra si el control está desactivado, si no hay cámara o qué gesto se reconoce.

Los umbrales de cada gesto están en `src/ergosense/gestures/classifier.py` y se calibraron con una mano real. Para calibrarlos con otra mano, ejecuta `uv run python scripts/calibrate_gestures.py`, sigue las instrucciones en pantalla y ajusta las constantes con los valores que muestra.

## Configuración

El botón **Configuración** de la ventana permite:

- cambiar el tiempo de inactividad para registrar una pausa, en minutos enteros entre 1 y 480 (10 por defecto);
- activar o desactivar el control mediante gestos;
- activar o desactivar el control por voz, que se usará desde el Sprint 04.

Los cambios se guardan en el servidor, asociados a la cuenta, y se aplican de inmediato, sin reiniciar. El aviso de pausa de 60 minutos no es configurable.

## Variables solo para desarrollo

Permiten probar sin esperar los tiempos reales. El usuario final nunca las usa.

| Variable | Efecto |
|---|---|
| `ERGOSENSE_LIMIT_SECONDS` | Acorta el período de aviso de 60 minutos. |
| `ERGOSENSE_INACTIVITY_SECONDS` | Acorta el tiempo de inactividad; tiene prioridad sobre la configuración de la cuenta. |

```powershell
$env:ERGOSENSE_LIMIT_SECONDS = "30"
$env:ERGOSENSE_INACTIVITY_SECONDS = "10"
uv run ergosense
```

Al terminar, bórralas para volver a los tiempos reales:

```powershell
Remove-Item Env:ERGOSENSE_LIMIT_SECONDS
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

Las pruebas no necesitan cámara, servidor ni pantalla: usan relojes, cámaras, manos y mouse falsos, y las ventanas se crean sin mostrarse. Cada prueba indica en su nombre el caso del Plan de pruebas que verifica, por ejemplo `test_cp_03_07_...`.

Los casos que requieren interacción real se prueban de forma manual con los scripts de `scripts/`:

| Script | Casos |
|---|---|
| `demo_input_listener.py` | CP-01-03 y CP-01-04: escucha de teclado y mouse. |
| `demo_main_window.py` | Ventana con datos de ejemplo. |
| `demo_camera.py` | CP-03-01 y CP-03-02: cámara en espejo y cuadros por segundo. |
| `demo_hand_tracker.py` | CP-03-03: los 21 puntos de la mano. |
| `demo_gestures.py` | CP-03-04 y CP-03-10: gesto reconocido y medidas de la mano. |
| `demo_cursor.py` | CP-03-05: movimiento del cursor. |
| `demo_control.py` | CP-03-05 a CP-03-10: control completo. Los clicks son reales; se sale con Esc. |
| `calibrate_gestures.py` | Calibración de los umbrales de los gestos. |
| `measure_gestures.py` | RNF-05, RNF-06 y RNF-08: cuadros por segundo, tiempo entre el gesto y el click, y uso de CPU. |

Se ejecutan desde la carpeta `desktop`, por ejemplo `uv run python scripts/demo_control.py`.

## Estructura

```text
desktop/
├── src/ergosense/
│   ├── actions/      # acciones del mouse y ejecutor único con cola (clicks y scroll)
│   ├── api_client/   # solicitudes HTTP, tokens y almacén seguro
│   ├── app/          # arranque, controlador del monitoreo y aplicación de la configuración
│   ├── gestures/     # cámara, detección de la mano, gestos, cursor e hilo de gestos
│   ├── monitoring/   # actividad, período de 60 minutos e inactividad
│   └── ui/           # ventanas: acceso, principal y configuración
├── tests/            # pruebas automatizadas (pytest), con la misma estructura que src
├── scripts/          # pruebas manuales y calibración
└── pyproject.toml    # dependencias y configuración del proyecto
```

La organización en capas sigue el Documento de arquitectura:

- `monitoring` y la lógica de `gestures` (clasificador, cursor e intérprete) no conocen la interfaz ni el hardware, por lo que se prueban de forma aislada.
- `api_client` solo conversa con el servidor; `app` une los módulos y le indica a la ventana qué mostrar.
- La aplicación usa varios hilos: la ventana y el temporizador de cada segundo corren en el hilo principal de Qt; la escucha de teclado y mouse, en los hilos de pynput; la cámara y los gestos, en el hilo `gestos`; y los clicks y el scroll, en el hilo `acciones`, de a uno y en orden. Los demás hilos se comunican con la ventana mediante señales de Qt, porque solo el hilo principal puede modificarla.
- Usar los gestos cuenta como actividad, por lo que no se registra una pausa mientras se controla el computador con la mano.

## Seguridad de la sesión

- La contraseña se envía únicamente al registrar o iniciar sesión y el servidor la transforma con bcrypt.
- El token de acceso dura poco tiempo y permanece en memoria.
- El token de renovación dura más y se guarda con `keyring`, que usa el administrador de credenciales del sistema.
- Si vence el acceso, el cliente solicita uno nuevo y repite una sola vez la operación original.
- Al cerrar sesión, el servidor revoca la renovación y el cliente la borra del equipo.
- Un cierre normal de la aplicación termina la sesión de uso, pero mantiene la sesión de usuario para poder recuperarla al volver a abrir.

## Flujo de trabajo

Cada integrante trabaja en su propia rama (`dev-<nombre>`). Los cambios pasan a `dev` mediante un pull request que revisa el otro integrante, y `dev` pasa a `main` al cerrar cada Sprint. Antes de cada pull request se ejecutan `uv run pytest` y `uv run ruff check`.
# Control por voz e interfaz del Sprint 04

La ventana principal permite activar gestos y voz por separado. Las preferencias
se guardan en la cuenta mediante la API y se aplican al iniciar la aplicación.
El monitoreo permanece activo y el aviso de descanso conserva sus 60 minutos.

El reconocimiento utiliza SpeechRecognition con Google y el idioma es-CL.
Requiere conexión a internet y envía audio del micrófono al servicio de
reconocimiento mientras la voz está activada. El audio no se guarda en archivos.
La captura usa sounddevice y se procesa fuera del hilo de la ventana.

Los comandos base son `clic izquierdo`, `clic derecho`, `subir`, `bajar`,
`activar gestos`, `desactivar gestos`, `activar voz`, `desactivar voz`,
`activar gestos y voz` y `desactivar gestos y voz`. Subir y bajar desplazan
la rueda un paso; los clics actúan en la posición actual del cursor.
Solo se acepta la frase completa, sin palabras adicionales ni coincidencias
parciales. Las acciones de voz y gestos pasan por el mismo ejecutor.

Al apagar la voz se cierra el micrófono y se descartan los comandos pendientes.
Para reactivarla se usa el botón de la ventana o la configuración. Un micrófono
apagado no puede reconocer el comando de reactivación. Esta es una limitación
del criterio que solicita reactivar por voz con el reconocimiento desactivado.
La falta de micrófono y los errores de conexión se muestran en la ventana.

## Validación con dispositivos

1. Iniciar la API y entrar a ErgoSense con una cuenta.
2. Activar voz y comprobar el indicador de micrófono en uso.
3. Pronunciar cada comando después de una pausa y comprobar una acción por frase.
4. Probar conversaciones, ruido y frases similares; no deben ejecutar acciones.
5. Activar y desactivar gestos, voz y ambos mediante los botones y comandos.
6. Apagar voz y comprobar que hablar ya no ejecuta acciones ni usa el micrófono.
7. Reiniciar y comprobar las preferencias de la cuenta.
8. Probar sin micrófono y sin internet; comprobar que monitoreo y gestos continúan.
9. Comprobar el aviso y el reinicio del período con el procedimiento de monitoreo.

Las pruebas automáticas utilizan dispositivos simulados; el reconocimiento real,
el ruido ambiental y la precisión de cámara requieren esta validación práctica.
