# Registro de validación del Sprint 06

Fecha: 10 de noviembre de 2026.

## Estado del incremento

El Sprint 05 dispone de gestión de macros, activadores, cinco tipos de acción,
aplicaciones por equipo, persistencia y recuperación de conexión. La revisión
comenzó desde `bf8356c`, con 275 pruebas de escritorio y 76 de API aprobadas.

El candidato del Sprint 06 corresponde al código `4d9149a`. Se preparó en
`feature/sprint-06-integracion-seguridad` y se identifica para aceptación en
`qa/sprint-06`. Su estado es candidato validado automáticamente, con aceptación
práctica pendiente. No se declara cumplida la Definition of Done completa.

## Resultados ejecutados

| Comprobación | Entorno | Resultado |
| --- | --- | --- |
| Suite del escritorio con integración habilitada | Windows, Python 3.12.10, Qt offscreen | 307 pruebas aprobadas, ninguna omitida |
| Cobertura del escritorio | pytest-cov, incluyendo cliente contra API real | 85 % |
| Suite de API | SQLite aislado con claves foráneas habilitadas | 93 pruebas aprobadas |
| Cobertura de API | pytest-cov | 95 % |
| Despliegue QA | Docker Desktop Linux y PostgreSQL 16 | Imagen construida, migraciones aplicadas, API y base saludables |
| Integración tras reconstruir la imagen final | Cliente HTTP real, PostgreSQL y simulación de monitoreo | 8 pruebas aprobadas |
| Reinicio de API | Reinicio real del contenedor QA | Preferencias y macros recuperadas mediante nuevo login |
| Análisis estático | Ruff en escritorio y API | Sin errores |
| Comandos y macros durante jornada simulada | Reloj controlado de 24 horas y ejecutor real sin dispositivos | 24 avisos, 5760 pasos ordenados y sin pausas falsas |

Las dos pruebas de cliente lógico representan equipos distintos mediante
identificadores QA-A y QA-B. No representan dos computadores físicos. La prueba
de reinicio conserva datos en PostgreSQL, pero no constituye despliegue externo.
La simulación de jornada no mide consumo de memoria ni precisión de hardware.

## Errores priorizados y correcciones

| Prioridad | Hallazgo | Corrección y regresión |
| --- | --- | --- |
| Alta | Los pasos de una macro podían intercalarse con acciones de otros módulos | Lotes indivisibles y prueba de concurrencia del ejecutor |
| Alta | Una aplicación faltante permitía ejecutar pasos posteriores en otro destino | Validación completa antes de encolar la macro |
| Alta | Una falla parcial de teclado podía dejar modificadores presionados | Liberación de las teclas ya presionadas en el bloque de cierre |
| Alta | Una excepción podía terminar el hilo de acciones | Error controlado, interrupción del lote y continuidad de acciones posteriores |
| Alta | Respuestas 5xx descartaban registros pendientes | Conservación de la operación y reintento, también para 408 y 429 |
| Alta | Una respuesta POST perdida rompía la referencia de sesión o pausa | Recuperación del registro por cuenta, sesión y momento de inicio |
| Alta | El cierre de sesión podía preceder al inicio de su pausa | Validación cronológica y rechazo sin alterar registros |
| Alta | Los errores de validación podían devolver los valores introducidos | Respuestas limitadas a ubicación, mensaje y tipo de error |
| Media | Una recarga incompleta mezclaba biblioteca nueva con aplicaciones anteriores | Sustitución de ambas colecciones solo tras completar la descarga |
| Media | Un rechazo permanente de registros se descartaba silenciosamente | Notificación visible al usuario y continuidad de la cola |
| Media | Nuevos eventos offline aplazaban el reintento | Conservación del plazo de 30 segundos |
| Media | Una respuesta HTTP inválida producía una excepción sin controlar | Error de cliente en español sin devolver datos privados |
| Media | Una falla al crear el detector retenía la cámara | Cierre garantizado de cámara y detector, con regresión |

## Trazabilidad y aceptación pendiente

| Tareas | Evidencia disponible | Comprobación pendiente |
| --- | --- | --- |
| SB06-T01 a T08 | Controladores integrados, casos unitarios, suite y guía reproducible | Demostración de la aplicación completa con dispositivos |
| SB06-T09 a T12 | Clasificador, interpretación, comandos y rechazo lógico probados | Precisión real de cada gesto y comando, ruido y movimientos ajenos |
| SB06-T13 a T15 | Actividad, umbral, reinicio y no repetición con reloj controlado | Teclado y mouse reales y aviso después de 60 minutos reales |
| SB06-T16 y T17 | Ejecutores compartidos, controles y preferencias probados | Voz, gestos y macros simultáneos con cámara y micrófono |
| SB06-T18 a T20 | Persistencia y relaciones probadas; reinicio real de API | Reinicio completo del desktop y pausas reales de 10 minutos y otro valor |
| SB06-T21 a T23 | Ambos activadores, cinco tipos de acción, orden y estado probados | Ejecución sobre aplicaciones reales con los dispositivos |
| SB06-T24 a T27 | Seguridad, reconexión, PostgreSQL y Docker probados | Segundo computador físico y despliegue en un equipo distinto |
| SB06-T28 a T30 | Hallazgos priorizados, correcciones y regresiones anteriores | Revalidar cualquier hallazgo nuevo de las pruebas físicas |
| SB06-T31 y T32 | Jornada simulada, fallos y cierre de recursos probados | Sesión prolongada real con todos los módulos y medición de recursos |
| SB06-T33 y T34 | Resultados y procedimiento documentados | Adjuntar evidencias prácticas y aprobar el incremento final |

## Reproducción

### Comprobaciones adicionales de dispositivos

Se verificó el acceso a una cámara real y al detector MediaPipe: se procesaron
30 cuadros en 1,33 segundos. La cámara y el micrófono funcionaron simultáneamente
durante una prueba posterior de 60,406 segundos, con 1773 cuadros procesados y
ningún error de cámara. No se detectaron manos ni se reconocieron frases durante
esa captura, por lo que no acredita precisión de gestos o voz humana. No se
ejecutaron acciones sobre el computador ni se guardaron imágenes o audio.

Se instaló el modelo Vosk oficial mediante el descargador del proyecto, con su
verificación de huella. El modelo se guardó en la carpeta local de la aplicación.
Los diez comandos base fueron reconocidos con muestras sintéticas de SAPI
Spanish Mexico; dos frases ajenas no se resolvieron como comandos. Esta evidencia
no representa una prueba de pronunciación humana ni de ruido ambiental real.

Los scripts `check_devices.py` y `check_voice_samples.py` permiten repetir estas
comprobaciones. La medición de una hora real sigue pendiente de ejecución.

El procedimiento y los comandos están en
[VALIDACION.md](../Evidencias%20de%20sistema/Aplicaci%C3%B3n/VALIDACION.md).
La instancia QA usa `compose.qa.yml`, puerto 18080 y un volumen separado.
Las pruebas no necesitan utilizar las cuentas ni la base del entorno habitual.

El candidato se promoverá como incremento aceptado después de registrar los
resultados prácticos pendientes y resolver los errores críticos que aparezcan.
