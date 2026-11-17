# Avisos de estado sobre otras aplicaciones

## Objetivo y alcance

Permitir conocer el estado de ErgoSense mientras se trabaja con gestos y voz en
otra ventana, sin tener que abrir la aplicación para comprobar si un cambio fue
aplicado. Complementa los indicadores de captura y la interacción del dictado
PB-52. Forma parte del cliente de escritorio y de su distribución Windows.

## Comportamiento

Se conserva un único panel compacto en la esquina superior derecha de la pantalla
activa. Muestra la mano cuando los gestos están habilitados y el micrófono cuando
la voz está habilitada. Durante el dictado, el espacio del micrófono muestra su
estado, sin crear un segundo icono duplicado.

| Función | Estados visibles |
| --- | --- |
| Gestos | Preparando, sin mano, mano detectada o cámara no disponible |
| Voz | Preparando, lista, desactivada o no disponible |
| Dictado | Preparando, escuchando o procesando |

El verde indica mano detectada o reconocimiento listo; el ámbar, preparación o
espera; el azul, procesamiento del dictado; el rojo, un dispositivo no disponible.
Mano detectada indica detección visual, no garantiza que esté dentro del área de
acción ni que un gesto haya sido clasificado correctamente.

Los cambios de modo muestran una confirmación temporal. Las notificaciones
habituales permanecen 3,5 segundos y los errores seis segundos. Al decir
«activar dictado» aparece primero «Preparando dictado» y, cuando el trabajador
confirma el estado de escucha, «Dictado activo». La confirmación de escucha solo
se muestra una vez por activación; el procesamiento de cada frase actualiza el
panel sin producir una sucesión de mensajes.

Al detener el dictado se muestra su desactivación y se vuelve al estado de voz.
Al apagar gestos y voz se oculta el panel, manteniendo temporalmente el mensaje
de confirmación. Un error de cámara o micrófono se muestra sobre las demás
ventanas. Las confirmaciones de comandos de voz utilizan la misma ruta que los
interruptores de la interfaz, incluso cuando el cambio queda pendiente de
persistencia por un fallo de red.

## Implementación

`ui/desktop_feedback.py` contiene el coordinador `DesktopFeedback`, el panel
`ModeIndicator` y las notificaciones `DesktopNotice`. Son ventanas independientes
sin padre, con `WindowStaysOnTopHint`, `WindowTransparentForInput` y
`WindowDoesNotAcceptFocus`; usan además `WA_ShowWithoutActivating` y fondo
translúcido. No contienen botones ni reciben teclado o ratón.

`PreferencesController` informa las preferencias aplicadas antes de iniciar o
detener dispositivos. Las señales del trabajador de cámara actualizan la
disponibilidad y la detección de mano; las de voz actualizan su disponibilidad.
`VoiceController.dictation_changed` y los estados del trabajador de dictado
controlan las transiciones. Los resultados tardíos no reabren un dictado detenido.
`MainWindow.notification_requested` entrega las confirmaciones generales al
coordinador. El cierre detiene el temporizador y cierra ambas ventanas.

El indicador anterior exclusivo de dictado se sustituye en la composición por el
panel de modos, conservando la distinción de preparación, escucha y procesamiento.
No se modifica la captura de audio, el modelo de reconocimiento ni las acciones
de teclado o ratón.

## Verificación

La ejecución de la suite del escritorio produjo 386 pruebas aprobadas y siete
omitidas de integración externa. Las nuevas pruebas cubren visibilidad, flags,
transiciones, descarte de estados tardíos, ocultamiento, duración de mensajes,
errores de micrófono y entrega de mensajes desde la ventana minimizada.

En Windows se ejecutó además:

```powershell
uv run python scripts/check_desktop_feedback.py --output "$env:TEMP\ergosense-feedback.json"
```

Se comprobaron en ambas ventanas `WS_EX_TOPMOST`, `WS_EX_TRANSPARENT` y
`WS_EX_NOACTIVATE`, visibilidad, conservación de la ventana en primer plano y
ocultamiento al cerrar. Estas comprobaciones no simulan la precisión del habla
humana ni acreditan funcionamiento sobre el escritorio seguro de Windows.

## Comprobación de uso

1. Abrir una aplicación con un campo de texto y minimizar ErgoSense.
2. Activar o desactivar gestos y voz y comprobar la confirmación y el panel.
3. Decir «activar dictado» y esperar **Escuchando** antes de dictar.
4. Comprobar **Procesando** al terminar una frase y que el foco siga en el campo.
5. Decir «terminar dictado» y comprobar la confirmación y el retorno a voz.
6. Deshabilitar gestos y voz y confirmar que se oculta el panel.

Las ventanas se superponen a aplicaciones normales del escritorio. Los cuadros
de UAC, la pantalla de bloqueo, sesiones remotas restringidas y ciertos modos
de pantalla completa exclusiva pueden impedir que se dibujen sobre ellos.
