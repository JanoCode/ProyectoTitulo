# Confirmación con Enter mediante gesto OK

## Alcance y uso

PB-53 permite confirmar una búsqueda, enviar un mensaje o aceptar el campo con
foco mediante la mano. No abre un buscador ni elige automáticamente el destino.
El efecto corresponde a la tecla Enter de la aplicación que está utilizando el
usuario.

Primero seleccionar el campo y esperar a que aparezca el texto dictado. Dentro
del área de acción, unir las puntas del pulgar y el índice con medio, anular y
meñique extendidos. Mantener el gesto durante 0,35 segundos. ErgoSense pulsa y
libera Enter una vez y muestra «Enter enviado» sobre la aplicación. Para repetir,
mostrar nuevamente la mano abierta antes de volver a OK.

El gesto congela el movimiento del cursor. Sostenerlo, relajar la mano o perder y
recuperar el seguimiento no provoca confirmaciones sucesivas. Un contacto breve
no confirma. Su uso con cámara real y diferentes manos permanece sujeto a
validación física.

## Reconocimiento y ejecución

`GestureClassifier` incorpora `Gesture.OK`. Mide la distancia tridimensional
entre los puntos 4 y 8, dividida por la escala de palma entre los puntos 0 y 9.
La entrada requiere una razón inferior a 0,16; un OK ya reconocido se conserva
hasta 0,24. La zona intermedia hasta 0,40 no se interpreta como clic. Se exigen
además los otros tres dedos extendidos, con la tolerancia de la transición desde
mano abierta. Los puntos degenerados no producen un gesto.

Se mantienen los tres cuadros de estabilización. `GestureInterpreter` exige el
mantenimiento de 0,35 s y conserva el bloqueo de repetición hasta volver a
`POINT`, incluso si el seguimiento se reinicia. La transición hacia OK cancela
un clic izquierdo que no llegó a arrastre. Si existía arrastre, libera el botón.

`Action.ENTER` pasa por el ejecutor FIFO y `ActionRunner` lo convierte en una
pulsación de teclado, con liberación incluso ante error. La confirmación visual
se solicita mediante una señal entregada al hilo Qt. No se emite Enter solo por
mostrar la etiqueta de gesto reconocido.

Los catálogos del cliente y la API reservan `ok` como gesto con acción propia.
La API rechaza con 409 el intento de asignarlo a una macro. Puño y L mantienen
su uso como activadores personalizados.

## Trazabilidad y verificación

Product Backlog: PB-53. Sprint 06: SB06-T41 y SB06-T42. Plan de pruebas:
CP-06-22 y CP-06-23. Las pruebas cubren escala y simetría, manos cerradas,
histéresis, mantenimiento, repetición, pérdida de seguimiento y envío/liberación
de Enter sin acciones del ratón.

Antes de aceptar el gesto físicamente, realizar intentos repetidos en campos de
prueba, medir activaciones correctas y accidentales y comprobar foco, ausencia de
dobles envíos y recuperación tras salir del área. No utilizar una conversación
o formulario con consecuencias reales como primer ensayo.
