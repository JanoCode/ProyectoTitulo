"""Lista cerrada de frases que reconoce Vosk (PB-14, PB-16 y RNF-03).

Vosk solo elige entre las frases de esta lista. Si la lista tuviera únicamente los
comandos, cualquier frase se confundiría con el comando más parecido: en las
pruebas, "vamos a trabajar" se reconocía como "bajar" y "voy al supermercado" como
"subir". Por eso la lista incluye también palabras frecuentes del español que no
son comandos: cuando se habla de otra cosa, Vosk elige esas palabras y la frase se
descarta, porque solo se acepta un comando completo (ver commands.py).
"""

import json

from ergosense.voice.commands import COMMANDS

# Palabras frecuentes que no son comandos. Las que se parecen a un comando (por
# ejemplo "subiendo", "trabajar" o "derecha") son las más importantes. Se escriben
# como texto, separadas por espacios, para que la lista sea fácil de leer y ampliar.
FILLER_WORDS = """
a al algo algún alguien así aquí ahí ahora antes año años bien bueno buenos buenas
casa cosa cosas como cómo con cuando cuándo de del desde después día días dónde donde
el él ella ellos en entonces era es esa ese eso esta este esto está están estás
estoy fue gracias gran gusta gusto ha había hace hacer hacia hasta hay hola hoy hora
horas la las le les lo los luego mal más me mejor mi mis mucho muy nada ni no nos
nosotros o otra otro para pero poco por porque pues qué que quién quiero se sé ser si
sí sin sobre son su sus también tan tanto te tengo tiene tiempo todo todos tu tú un
una uno unos va vamos vez voy ya yo
abrir cerrar abajo arriba bajo baja bajando bajada subiendo subida sube trabajar
trabajo trabajando viajar viaje caja cajas hablar hablando ventana página archivo
pantalla mouse ratón teclado computador correo escribir leer mirar ver buscar
izquierda derecha directo listo clase claro cine gesto actividad actuar avisar
dos tres cuatro cinco escalera escuela café comer comida agua noche tarde mañana
semana
""".split()  # noqa: SIM905

# Palabra especial de Vosk para cualquier sonido que no se parece a nada de la lista.
UNKNOWN = "[unk]"


def phrases():
    """Los comandos y las palabras de relleno, sin repetir palabras de comandos."""
    command_words = {word for phrase in COMMANDS for word in phrase.split()}
    filler = sorted({word for word in FILLER_WORDS if word not in command_words})
    return [*COMMANDS, *filler, UNKNOWN]


def grammar_json():
    """La lista en el formato que recibe Vosk."""
    return json.dumps(phrases(), ensure_ascii=False)
