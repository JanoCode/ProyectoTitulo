"""Cola de registros pendientes y estado de la conexión (PB-50; arquitectura, 5.7).

Las escrituras, como el inicio de una pausa, se agregan a una cola en memoria y se
envían en orden. Una operación solo sale de la cola cuando el servidor responde,
así que una interrupción no pierde registros mientras la aplicación esté abierta.
Sin conexión, se consulta GET /health cada 30 segundos y, al volver, se envía
todo lo pendiente.
"""

from collections import deque

from ergosense.api_client.client import ApiClientError

RETRY_SECONDS = 30


class PendingQueue:
    def __init__(self, check_connection, clock, on_connection_changed=None):
        # check_connection: consulta /health y devuelve True si el servidor responde.
        self._check_connection = check_connection
        self._clock = clock
        self._on_connection_changed = on_connection_changed or (lambda online: None)
        self._operations = deque()
        self.online = True
        self._last_check = None

    @property
    def pending(self):
        return len(self._operations)

    def submit(self, operation):
        """Agrega una operación (una función sin argumentos) y la envía si se puede."""
        self._operations.append(operation)
        if self.online:
            self.flush()

    def flush(self):
        """Envía en orden; se detiene en la primera que falla por falta de conexión."""
        while self._operations:
            try:
                self._operations[0]()
            except ApiClientError as error:
                if (error.status_code is None or error.status_code >= 500
                        or error.status_code in (408, 429)):
                    self.report_offline()
                    return
                # El servidor la rechazó: repetirla daría el mismo resultado.
            self._operations.popleft()

    def report_offline(self):
        """Cualquier módulo que no obtuvo respuesta del servidor lo informa aquí."""
        self._last_check = self._clock()
        if self.online:
            self.online = False
            self._on_connection_changed(False)

    def poll(self):
        """Se llama cada segundo. Sin conexión, consulta el servidor cada 30 s."""
        if not self.online and self._clock() - self._last_check >= RETRY_SECONDS:
            self.retry_now()

    def retry_now(self):
        """Consulta el servidor ahora; por ejemplo, al cerrar la aplicación."""
        if self.online:
            self.flush()
            return
        self._last_check = self._clock()
        if self._check_connection():
            self.online = True
            self._on_connection_changed(True)
            self.flush()
