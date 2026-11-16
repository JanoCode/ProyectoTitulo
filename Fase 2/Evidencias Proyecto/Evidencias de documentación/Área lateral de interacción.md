# Área lateral de interacción

Fecha: 10 de noviembre de 2026.

## Motivo y alcance

El mapeo central de la cámara obligaba a desplazar la mano por delante del rostro
para alcanzar el extremo opuesto del monitor. Se sustituye por una región lateral
que representa toda la pantalla. Esta decisión actualiza el comportamiento de
PB-09, PB-13 y PB-36 y sus tareas de sensibilidad, activación y configuración en
los Sprints 03 y 06. Los backlogs anteriores se conservan como planificación
histórica; los criterios de esta revisión se detallan a continuación.

## Comportamiento

El lado derecho de la imagen es el valor predeterminado. Configuración permite
elegir el lado izquierdo. Las referencias son siempre las de la imagen en espejo
mostrada por ErgoSense. No se cambia el conjunto de gestos ni los comandos de voz.

El centro de la palma, punto 9, debe encontrarse dentro de la región para ejecutar
acciones. Toda la mano se sigue detectando para mostrarla, pero la interpretación
de gestos y los activadores de macros quedan suspendidos fuera del recuadro.
Al salir se suelta un arrastre y se cancela un clic que todavía no se confirmó.
Al regresar se vuelve a exigir estabilidad. Cambiar de lado reinicia la posición
suavizada y el estado de los gestos anteriores.

El área es horizontal y mantiene proporción física 16:9, equivalente al monitor
soportado actualmente. Su altura se calcula a partir del ancho y de las
dimensiones reales del video; usar porcentajes verticales fijos distorsionaría
el recuadro cuando la cámara entrega una imagen 4:3.

| Lado | Límites horizontales habituales | Video de 640 × 480 | Video de 1280 × 720 |
| --- | --- | --- | --- |
| Derecho | 52 % a 94 % | Alto de 34,25 % a 65,75 % | Alto de 29 % a 71 % |
| Izquierdo | 6 % a 48 % | Alto de 34,25 % a 65,75 % | Alto de 29 % a 71 % |

Para un ancho de región W píxeles, la altura es W × 9 / 16. El recuadro se centra
verticalmente y se reduce si fuera necesario para permanecer dentro del video.
Esto adapta la región al formato de captura sin incorporar soporte para otras
proporciones de monitor.

Ambos recuadros cubren el monitor principal completo. El rectángulo se dibuja con
las mismas coordenadas normalizadas que utiliza el mapeo del cursor. El video se
ajusta completo, sin recorte, para evitar discrepancias al redimensionar la ventana.

### Margen para la mano

La guía interior punteada delimita el recorrido del centro de la palma que se
mapea a la pantalla completa. Se obtiene dejando un 16 % de margen en cada borde
del recuadro exterior. Ambas figuras conservan la proporción 16:9. La banda entre
ellas permite que los dedos permanezcan dentro de la captura cuando la palma
alcanza una esquina. Dentro de esa banda el cursor permanece en el extremo
correspondiente; los gestos siguen habilitados hasta salir del recuadro exterior.

El control de salida sigue usando el rectángulo exterior, mientras el mapeo usa
la guía interior. El suavizado se ajusta al píxel extremo cuando está a menos de
la zona muerta de ese borde, para que las esquinas sean accesibles sin un
desplazamiento adicional. La comodidad depende del tamaño y distancia de la mano;
esta corrección no representa una garantía de precisión del detector.

### Estabilización del cursor

La región exterior ocupa el 42 % del ancho de la captura. La guía interior ocupa
el 68 % de esa región, frente al 64 % de una región del 36 % anterior: el recorrido
útil aumenta aproximadamente un 24 % por eje y reduce la ganancia por movimiento.
El margen derecho para los dedos se conserva prácticamente igual.

Cuando se usa una región configurada y el suavizado está habilitado, la posición
se filtra mediante la mediana de los tres últimos cuadros. Los desplazamientos
pequeños usan mayor suavizado, y los grandes conservan una respuesta más rápida.
La zona muerta sigue evitando microdesplazamientos. Al salir, volver a entrar o
cambiar de lado se descarta el historial para no arrastrar posiciones antiguas.
El ajuste al borde permite seguir alcanzando los píxeles extremos de la pantalla.

Las pruebas controladas comprueban oscilaciones de un píxel en cámara con un
recorrido del cursor de como máximo dos píxeles, rechazo de un salto aislado,
respuesta a desplazamientos intencionales y acceso a las cuatro esquinas.
Estos resultados no equivalen a una medición del temblor de una persona.

## Persistencia y despliegue

`settings.gesture_control_side` admite `left` y `right`. La migración Alembic
`20261110_02`, posterior a `20261015_01`, incorpora la columna sin eliminar datos,
asigna `right` a las preferencias existentes y agrega una restricción de valores.
La API devuelve el campo al iniciar sesión y en GET/PATCH de configuración.
Las cuentas no comparten sus preferencias. El cambio se aplica sin reiniciar la
cámara al guardar desde Configuración.

Actualizar la API antes de ejecutar esta versión del escritorio. Docker aplica
la migración al iniciar; en ejecución manual usar `uv run alembic upgrade head`
desde `server`. La migración inversa elimina únicamente esta nueva preferencia.

## Criterios de aceptación

1. Cada lado permite alcanzar las cuatro esquinas y el centro de la pantalla.
2. Fuera del recuadro no se generan movimientos, clics, scroll o macros gestuales.
3. Salir durante un arrastre libera el botón sin producir un clic adicional.
4. Salir durante un clic pendiente lo cancela.
5. Volver a entrar o cambiar de lado exige un gesto estable nuevo.
6. La elección del lado se conserva al guardar y recuperar la configuración.
7. Un valor inválido no modifica la preferencia guardada.
8. El recuadro permanece alineado con el video en ventanas de distintas proporciones.

Las regresiones están en `tests/gestures/test_control_area.py`,
`tests/ui/test_settings_dialog.py` y `server/tests/test_gesture_area_settings.py`.
La comodidad y la precisión con una mano real requieren validación del usuario.
