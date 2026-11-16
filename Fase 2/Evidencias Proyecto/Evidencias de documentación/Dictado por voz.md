# Dictado por voz

## Alcance

PB-52 incorpora escritura libre en español para completar la interacción mediante
gestos y voz. Es una ampliación del Sprint 06 registrada el 16 de noviembre de
2026. El usuario selecciona el campo con un gesto y dicta el contenido. Se escribe
en el campo que tenga el foco; no se buscan ni seleccionan campos automáticamente.

## Uso

1. Activar el control por voz y esperar a que el micrófono esté listo.
2. Decir **iniciar dictado** o **activar dictado**, o usar el botón correspondiente.
3. Esperar el estado **Dictando** y seleccionar el campo con un gesto.
4. Dictar una frase y hacer una pausa. Cada frase termina con un espacio para
   poder continuar la oración.
5. Decir **borrar palabra** para pulsar Ctrl+Retroceso si hace falta corregir.
6. Revisar el texto. **Enviar texto** pulsa Enter; por ejemplo, realiza una búsqueda
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

`voice/recognizer.py` crea un reconocedor Vosk sin gramática restringida para
dictado y conserva la gramática de comandos en el modo habitual. Ambos reutilizan
el modelo local instalado. La separación entre reconocimiento libre y gramática
se corresponde con los [ejemplos oficiales de Vosk](https://github.com/alphacep/vosk-api/blob/master/python/example/test_text.py).

`voice/worker.py` cambia de reconocedor fuera del hilo de la interfaz y vacía el
audio pendiente al cambiar de modo. Cada resultado lleva la generación del
micrófono y la revisión del modo; una señal atrasada se descarta incluso si se
terminó y volvió a iniciar el dictado rápidamente.

`voice/controller.py` separa texto, órdenes de edición y comandos. Envía objetos
`TextInput` al ejecutor FIFO compartido. `macros/runner.py` escribe Unicode con
pynput o pulsa las teclas de edición, sin utilizar el portapapeles. La interfaz
muestra el estado y permite iniciar o terminar el dictado con un botón.

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

El escritorio cuenta con 348 pruebas aprobadas y 7 de integración externa omitidas
en la ejecución habitual. El servidor cuenta con 101 pruebas aprobadas. Ruff pasa
en ambos proyectos. Las pruebas nuevas cubren separación de comandos y macros,
edición, texto Unicode, cierre del micrófono, resultados atrasados, cambio de
reconocedor en el hilo de audio, cancelación de escritura en cola, error de escritura
y reserva de activadores.

La prueba reproducible con SAPI en español reconoció los 12 comandos base y
descartó como comandos las 2 frases de conversación. En dictado libre coincidieron
9 de 11 muestras normalizadas: «buscar información sobre ergonomía» se transcribió
como «buscar y formación sobre ergonomía» y «coma» como «come». Las órdenes de
terminar dictado, enviar texto, borrar palabra y nueva línea se reconocieron
correctamente. Son muestras sintetizadas; no miden precisión con micrófono real.

Pendiente de aceptación manual: CP-06-14 y CP-06-20, junto con los componentes
manuales de CP-06-13 y CP-06-15 a CP-06-19. Probar búsquedas y edición en una
aplicación real, con gestos y micrófono, registrar el ruido y los errores y
comprobar que no sea necesario usar el teclado físico. No dar PB-52 por aceptado
solo por aprobar pruebas automatizadas.

## Documentos relacionados

El Product Backlog incorpora PB-52. El Sprint Backlog 06 agrega las tareas
SB06-T35 a SB06-T39 como ampliación del alcance. El Documento de arquitectura
describe el reconocimiento libre y la entrega al ejecutor. El Plan de pruebas
incorpora CP-06-13 a CP-06-20 y su matriz de trazabilidad. El README del escritorio
y la ayuda de la aplicación contienen las instrucciones de uso.
