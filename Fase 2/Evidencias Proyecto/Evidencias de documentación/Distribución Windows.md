# Distribución portable de ErgoSense para Windows

## Alcance

El cliente se distribuye como una carpeta con `ErgoSense.exe`, bibliotecas en
`_internal`, modelos en `models`, licencias e instrucciones. Se transporta en
`ErgoSense-Windows-x64.zip`. No requiere Python ni uv en el equipo de destino.
Windows 10/11 x64 es el destino de esta compilación; no es un binario universal
para otros sistemas o arquitecturas.

El ejecutable incorpora los avisos de estado sobre otras aplicaciones. Los
modelos de gestos, comandos Vosk y dictado Whisper están incluidos para evitar
una descarga al comenzar a utilizar esas funciones. La capacidad y latencia
dependen del procesador y de los dispositivos del computador.

## Dependencia del servidor

El paquete es el cliente de escritorio. Las cuentas, preferencias, sesiones,
pausas, aplicaciones registradas y macros continúan utilizando la API y
PostgreSQL existentes. El EXE no inicia Docker ni contiene contraseñas del
servidor. El servidor debe estar en funcionamiento y ser accesible.

La ventana de ingreso ofrece **Configurar conexión**. Comprueba la respuesta de
salud del servicio antes de guardar su URL. Si se cambia de servidor, elimina
las credenciales del servidor anterior. La configuración se guarda en
`%LOCALAPPDATA%/ErgoSense/connection.json`; las credenciales se conservan mediante
keyring en el almacén de Windows. La variable `ERGOSENSE_API_URL` mantiene
prioridad para los entornos de desarrollo.

Una URL con `127.0.0.1` siempre apunta al equipo actual. Otro PC necesita la
dirección de red del servidor y acceso permitido por su firewall; el acceso por
internet requiere publicación con HTTPS. No se incluyen tokens ni direcciones
privadas de una cuenta concreta en la distribución.

## Construcción reproducible

Desde `desktop`:

```powershell
uv sync --locked --group build
uv run --group build python scripts/build_windows.py --output C:\entregas\ergosense
```

El script requiere Windows x64, utiliza PyInstaller 6.22.3 y la resolución de
`uv.lock`. Genera el icono de la aplicación, recoge recursos y bibliotecas,
copia modelos y licencias, ejecuta la comprobación del EXE y produce el ZIP con
su huella SHA-256. No reemplaza automáticamente una distribución existente.
El workflow manual **Paquete Windows** permite repetir la construcción en
GitHub Actions y descargar el resultado como artefacto durante catorce días.

La especificación `packaging/ErgoSense.spec` fija los imports dinámicos de
Windows, los recursos de MediaPipe y las bibliotecas de voz. Utiliza el ICU
nativo de Windows para evitar que una DLL incompatible encontrada en el PATH
del equipo de compilación sustituya la dependencia que utiliza Qt.

El formato de carpeta evita extraer todos los componentes a un directorio
temporal en cada inicio. Los modelos se resuelven junto al EXE en la versión
compilada; al ejecutar desde código se mantiene la caché local existente. Una
variable explícita de ruta de modelo tiene prioridad.

## Verificación ejecutada

Se verificaron Ruff y la suite de escritorio: 386 pruebas aprobadas y siete
omitidas de integración externa. El ejecutable cargó Qt, la ventana de ingreso,
el panel y los avisos flotantes, el detector de mano, Vosk, el detector de voz,
Whisper y el backend de credenciales WinVaultKeyring.

La comprobación se repitió desde la distribución copiada al escritorio, con un
perfil local vacío, sin rutas de Python o de modelos en el entorno y con la
descarga de Hugging Face deshabilitada. Finalizó correctamente, utilizando los
componentes incluidos. No abrió la cámara ni modificó credenciales. Esta
verificación no sustituye el ensayo en un segundo computador físico ni las
validaciones de reconocimiento humano pendientes.

Las ventanas flotantes se verificaron además mediante los estilos nativos de
Windows y la conservación del foco. El procedimiento y sus límites están en
[Avisos de estado](Avisos%20de%20estado.md).

## Entrega y mantenimiento

Extraer el ZIP completo y ejecutar `ErgoSense.exe`. Mantener `_internal` y
`models` junto al archivo; mover solo el EXE rompe la distribución. Los archivos
binarios y modelos no se agregan al repositorio de código. La aplicación no
incluye firma con certificado comercial y Windows puede mostrar SmartScreen.

Los fallos de inicio se registran en
`%LOCALAPPDATA%/ErgoSense/logs/desktop.log`, con rotación limitada. Al actualizar,
cerrar la aplicación y extraer la nueva distribución en otra carpeta; la
configuración y credenciales del usuario se mantienen fuera del paquete.
