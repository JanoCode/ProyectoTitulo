# Dictado por voz

## Alcance

PB-52 incorpora escritura libre en español para completar la interacción mediante
gestos y voz. Es una ampliación del Sprint 06 registrada el 16 de noviembre de
2026. El usuario selecciona el campo con un gesto y dicta el contenido. Se escribe
en el campo que tenga el foco; no se buscan ni seleccionan campos automáticamente.

## Uso

1. Activar el control por voz y esperar a que el micrófono esté listo.
2. Decir **iniciar dictado** o **activar dictado**, o usar el botón correspondiente.
3. Esperar el micrófono flotante verde y seleccionar el campo con un gesto.
4. Dictar una frase y hacer una pausa. Cada frase termina con un espacio para
   poder continuar la oración.
5. Decir **borrar palabra** para pulsar Ctrl+Retroceso si hace falta corregir.
6. Revisar el texto. El gesto **OK** mantenido confirma con Enter;
   [ver su uso](Confirmaci%C3%B3n%20con%20Enter.md). **Enviar texto** también pulsa Enter; por ejemplo, realiza una búsqueda
   en un buscador. Su efecto depende de la aplicación de destino.
7. Decir **terminar dictado** o **desactivar dictado** para volver a comandos.

Las órdenes se pronuncian como frases separadas. **Nueva línea** también pulsa
Enter; en un chat puede enviar el mensaje según la aplicación de destino.
**Punto**, **coma**, **dos puntos**, **punto y coma**, **abrir interrogación** y
**cerrar interrogación** insertan sus signos cuando se reconocen como frases
completas. No se reformatea ni se elimina texto previo automáticamente al puntuar.

Durante el dictado, frases como **clic izquierdo**, **subir** y los activadores de
macros de voz se escriben literalmente. Los gestos siguen disponibles para elegir
campos. **Desactivar voz** y **desactivar gestos y voz** conservan su función de
desactivación. Con el micrófono apagado, la voz se reactiva desde el interruptor.

## Implementación

`voice/recognizer.py` mantiene Vosk para comandos cortos. El dictado utiliza
large-v3-turbo mediante faster-whisper, con español fijo. Se conserva el modelo
local de la revisión `0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf` de
`mobiuslabsgmbh/faster-whisper-large-v3-turbo`, incluido en el catálogo del motor.
Ocupa aproximadamente 1,62 GB en
`%LOCALAPPDATA%/ErgoSense/models/whisper-large-v3-turbo`.

La carga prueba GPU NVIDIA con int8_float16 cuando las bibliotecas opcionales
están disponibles y utiliza CPU int8 con cuatro hilos como respaldo. La opción
`cuda` de dependencias instala las bibliotecas en el entorno, sin cambiar el
controlador del sistema. `ERGOSENSE_DICTATION_DEVICE=cpu` fuerza CPU. La ruta
`ERGOSENSE_DICTATION_MODEL` permite un modelo local compatible; una carpeta
personalizada incompleta produce un error y no se sobrescribe con descargas.

WebRTC VAD en modo 1 analiza cuadros de 20 ms, conserva 300 ms previos y termina
la frase tras un segundo de silencio, con un máximo de 20 s. Antes de transcribir
se elimina el desplazamiento continuo y se ajusta el nivel con ganancia máxima
ocho, limitado a amplitud 0,95. La detección secundaria utiliza umbral 0,35,
voz mínima 80 ms, silencio mínimo 250 ms y margen de 350 ms. No se reutiliza el
texto anterior ni se aplican reemplazos de palabras para disimular errores.

Configuración permite elegir un micrófono por nombre y backend. La selección
permanece en `audio.json` del equipo y se aplica reiniciando la captura. La voz
muy baja o saturada produce un aviso limitado. El desbordamiento de PortAudio se
trata como pérdida de captura; se detiene el dictado en vez de transcribir una
frase incompleta. El modelo instalado procesa audio localmente.

`voice/worker.py` cambia de reconocedor fuera del hilo de la interfaz y vacía el
audio pendiente al cambiar de modo. Cada resultado lleva la generación del
micrófono y la revisión del modo; una señal atrasada se descarta incluso si se
terminó y volvió a iniciar el dictado rápidamente.

`voice/controller.py` separa texto, órdenes de edición y comandos. Envía objetos
`TextInput` al ejecutor FIFO compartido. `macros/runner.py` escribe Unicode con
pynput o pulsa las teclas de edición, sin utilizar el portapapeles. La interfaz
muestra el estado y permite iniciar o terminar el dictado con un botón.

`ui/dictation_indicator.py` muestra un solo micrófono de 44 por 44 píxeles,
semitransparente, arriba a la derecha de la pantalla donde está el cursor al
activar el modo. Permanece sobre las ventanas normales y deja pasar los clics.
No toma el foco de escritura. Ámbar indica preparación, verde escucha y azul
transcripción. Terminar el dictado, apagar la voz o cerrar la aplicación lo oculta.
Los estados atrasados de una sesión anterior no vuelven a mostrarlo.

No se necesitan migraciones ni nuevos endpoints. El servidor reserva las frases
de activación para que no se asignen a macros nuevas. Las macros ya existentes
con esos activadores deben cambiar su frase: la orden base tiene prioridad.

## Privacidad y ciclo de vida

El dictado es temporal y empieza desactivado. Apagar la voz, perder el micrófono o
cerrar la aplicación lo cancela. La preferencia general de voz sigue guardándose
en la cuenta, pero el modo de dictado y su contenido no se sincronizan. No se
guardan grabaciones ni transcripciones en ErgoSense. El texto escrito queda bajo
el comportamiento de la aplicación de destino.

Con el modelo instalado, el dictado no utiliza internet. El inicio de sesión y la
descarga inicial del modelo mantienen sus requisitos actuales de conexión.

## Verificación

El escritorio cuenta con 359 pruebas aprobadas y 7 de integración externa omitidas
en la ejecución habitual. El servidor cuenta con 101 pruebas aprobadas. Ruff pasa
en ambos proyectos. Las pruebas nuevas cubren separación de comandos y macros,
edición, texto Unicode, cierre del micrófono, resultados atrasados, cambio de
reconocedor en el hilo de audio, cancelación de escritura en cola, error de escritura
y reserva de activadores. También cubren detección de silencio, fragmentos PCM
incompletos, duración máxima, cambio de estado, errores de preparación y flags
de ventana del indicador.

En la versión inicial con Vosk para dictado, la prueba con SAPI reconoció los 12 comandos base y
descartó como comandos las 2 frases de conversación. En dictado libre coincidieron
9 de 11 muestras normalizadas: «buscar información sobre ergonomía» se transcribió
como «buscar y formación sobre ergonomía» y «coma» como «come». Las órdenes de
terminar dictado, enviar texto, borrar palabra y nueva línea se reconocieron
correctamente.

La comparación posterior con diez frases largas, sintetizadas con la misma voz,
redujo los errores de palabras de 6 a 1 sobre 102 palabras, ignorando mayúsculas,
tildes y puntuación. Se pasó de 7 a 9 frases completas coincidentes. El nuevo
dictado corrigió «información» y «ErgoSense»; «Python» se transcribió como «Paytan».
La decodificación tardó de 2,3 a 2,8 segundos por muestra en el Ryzen 5 5500 del
equipo, además del tiempo para detectar la pausa. No es una medición de latencia
con micrófono real ni una garantía de precisión para cualquier voz o entorno.

En las once muestras cortas el nuevo motor coincidió en 9: reconoció «clic
izquierdo» como «Clique izquierdo» y «coma» como «¿Cómo?». Las órdenes de terminar,
enviar texto, borrar palabra y nueva línea se reconocieron. No se agregaron
sustituciones arbitrarias de palabras para ocultar esos errores.

En Windows se verificaron los estilos nativos de ventana superior, entrada
transparente y ausencia de activación. El foco se conservó al mostrar el icono y
este se ocultó al terminar. Estas comprobaciones no sustituyen la prueba de uso
simultáneo con gestos y dictado humano.

Pendiente de aceptación manual: CP-06-14 y CP-06-20, junto con los componentes
manuales de CP-06-13, CP-06-15 a CP-06-19 y CP-06-21. Probar búsquedas y edición en una
aplicación real, con gestos y micrófono, registrar el ruido y los errores y
comprobar que no sea necesario usar el teclado físico. No dar PB-52 por aceptado
solo por aprobar pruebas automatizadas.

## Documentos relacionados

La mejora de visibilidad fuera de la aplicación se describe en
[Avisos de estado](Avisos%20de%20estado.md). El panel flotante ahora reúne gestos,
voz y dictado, muestra preparación, escucha y procesamiento, y acompaña cada
cambio de modo con una confirmación visible sobre otras ventanas sin alterar
el foco del campo de escritura.

El Product Backlog incorpora PB-52. El Sprint Backlog 06 agrega las tareas
SB06-T35 a SB06-T40 como ampliación del alcance. El Documento de arquitectura
describe el reconocimiento libre y la entrega al ejecutor. El Plan de pruebas
incorpora CP-06-13 a CP-06-21 y su matriz de trazabilidad. El README del escritorio
y la ayuda de la aplicación contienen las instrucciones de uso.


## Comparación de la ampliación de dictado

Se repitieron diez frases SAPI en español de México, 102 palabras por condición,
con la misma señal en ambos sistemas. Se comparó la versión anterior small en
CPU int8, cuatro hilos, con la actual large-v3-turbo en GPU int8_float16. El equipo
utiliza Ryzen 5 5500 y RTX 3050 de 6 GB. La voz sintetizada no representa una
medición de reconocimiento con hablantes humanos.

| Condición | Errores anteriores | Errores actuales | Decodificación media anterior | Actual |
| --- | --- | --- | --- | --- |
| Señal original | 1/102 | 1/102 | 2,123 s | 0,787 s |
| Amplitud multiplicada por 0,025 | 1/102 | 1/102 | 2,114 s | 0,811 s |
| Ruido gaussiano con relación señal/ruido de 8 dB | 2/102 | 1/102 | 2,158 s | 0,812 s |

La muestra limpia no demuestra mejora de precisión agregada; la condición de
ruido redujo un error. El modelo nuevo corrigió Python en estas frases, pero
persistieron errores en otros términos. La comparación de latencia también
cambia CPU por GPU y no se atribuye solo al modelo. No incluye el segundo de
silencio ni la carga inicial. En otra prueba sintetizada del modelo nuevo en CPU,
la decodificación promedió 8,48 s sobre quince frases: el respaldo CPU conserva
funcionamiento, con mayor latencia.

El escritorio obtuvo 406 pruebas aprobadas y siete omitidas de integración
externa; la API, 102 aprobadas. Se cubren micrófono elegido, nivel, saturación,
modelo personalizado sin sobrescritura y fallo CUDA con respaldo CPU. La
aceptación con micrófono humano y el gesto físico sigue pendiente.

Muestras reproducibles del sistema actual:

```powershell
uv run --extra cuda python scripts/check_voice_samples.py --dictation-long --output "$env:TEMP\dictado-limpio.json"
uv run --extra cuda python scripts/check_voice_samples.py --dictation-long --noise-snr 8 --output "$env:TEMP\dictado-ruido.json"
uv run --extra cuda python scripts/check_voice_samples.py --dictation-long --gain 0.025 --output "$env:TEMP\dictado-bajo.json"
```
