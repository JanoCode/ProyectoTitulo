# ErgoSense - Servidor API

Este proyecto contiene el servidor central de ErgoSense. Su responsabilidad es recibir solicitudes de la aplicación de escritorio, validar la identidad del usuario y guardar de forma persistente las cuentas, configuraciones, sesiones de uso y pausas de inactividad.

## Qué incluye el Sprint 02

- API REST construida con FastAPI y ejecutada por Uvicorn.
- PostgreSQL 16 como base de datos persistente.
- SQLAlchemy para trabajar con las tablas desde Python.
- Alembic para crear y versionar el esquema de la base de datos.
- Registro, inicio de sesión, renovación de sesión y cierre de sesión.
- Contraseñas protegidas con bcrypt, costo 12. La contraseña original nunca se guarda.
- Tokens JWT de acceso y renovación.
- Bloqueo temporal después de cinco intentos de inicio de sesión fallidos.
- Registro de sesiones de uso y pausas de inactividad.
- Aislamiento de datos: una cuenta no puede consultar ni modificar recursos de otra.
- Pruebas automatizadas y documentación interactiva OpenAPI/Swagger.

## Ejecutar todo con Docker

Desde la carpeta `codigo`:

```powershell
Copy-Item .env.example .env
```

Edita `.env` y reemplaza los valores de ejemplo. `POSTGRES_PASSWORD` protege PostgreSQL y `JWT_SECRET` firma los tokens. El archivo `.env` real está ignorado por Git; `.env.example` documenta las variables necesarias sin publicar secretos.

Después ejecuta:

```powershell
docker compose up --build -d
docker compose ps
```

Docker inicia dos contenedores:

- `db`: PostgreSQL y el volumen donde quedan los datos.
- `api`: migraciones de Alembic y servidor FastAPI en el puerto 8000.

Comprobaciones útiles:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
docker compose logs api
docker compose down
```

La documentación interactiva está disponible en `http://127.0.0.1:8000/docs` cuando `ENVIRONMENT=development`.

## Ejecutar solo el servidor durante el desarrollo

Desde esta carpeta:

```powershell
$env:UV_PROJECT_ENVIRONMENT = "C:\venvs\ergosense-server"
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

`uv sync` instala versiones reproducibles desde `uv.lock`. Alembic lleva la base de datos a la última versión. Uvicorn abre el proceso que escucha solicitudes HTTP y entrega cada una a FastAPI.

## Rutas principales

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/v1/health` | Confirma que la API responde. |
| POST | `/api/v1/auth/register` | Crea usuario y configuración predeterminada. |
| POST | `/api/v1/auth/login` | Valida credenciales y entrega tokens. |
| POST | `/api/v1/auth/refresh` | Renueva el token de acceso. |
| POST | `/api/v1/auth/logout` | Revoca el token de renovación. |
| GET | `/api/v1/users/me` | Devuelve la cuenta autenticada. |
| GET | `/api/v1/settings` | Consulta la configuración de la cuenta. Su modificación corresponde al Sprint 03. |
| POST | `/api/v1/usage-sessions` | Inicia una sesión de uso. |
| PATCH | `/api/v1/usage-sessions/{session_id}` | Finaliza una sesión de uso. |
| POST | `/api/v1/usage-sessions/{session_id}/breaks` | Inicia una pausa en la sesión indicada. |
| PATCH | `/api/v1/breaks/{break_id}` | Finaliza una pausa. |

Las rutas privadas exigen `Authorization: Bearer <access_token>`. El servidor obtiene `user_id` desde el token; no confía en un identificador enviado por el cliente.

## Estructura del código

```text
app/
|-- api/           # rutas HTTP y autenticación de solicitudes
|-- core/          # configuración, conexión de base de datos y seguridad
|-- models/        # tablas SQLAlchemy
|-- repositories/  # consultas y escrituras de datos
|-- schemas/       # validación de entradas y forma de las respuestas
|-- services/      # reglas del negocio y transacciones
`-- main.py        # crea FastAPI y conecta todos los routers
migrations/        # historial versionado del esquema de PostgreSQL
tests/             # pruebas automatizadas
```

El recorrido normal de una solicitud es `api -> service -> repository -> model -> PostgreSQL`. Separar esas responsabilidades permite probar las reglas sin mezclar toda la lógica en un solo archivo.

## Pruebas y calidad

```powershell
uv run python -m pytest
uv run python -m pytest --cov=app --cov-fail-under=70
uv run ruff check .
uv run alembic check
```

Las pruebas usan una base SQLite temporal y aislada. La verificación integrada adicional se realiza contra PostgreSQL dentro de Docker.
