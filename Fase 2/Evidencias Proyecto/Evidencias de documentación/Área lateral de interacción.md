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

| Lado | Límites horizontales de la imagen | Límites verticales |
| --- | --- | --- |
| Derecho | 58 % a 94 % | 18 % a 82 % |
| Izquierdo | 6 % a 42 % | 18 % a 82 % |

Ambos recuadros cubren el monitor principal completo. El rectángulo se dibuja con
las mismas coordenadas normalizadas que utiliza el mapeo del cursor. El video se
ajusta completo, sin recorte, para evitar discrepancias al redimensionar la ventana.

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
