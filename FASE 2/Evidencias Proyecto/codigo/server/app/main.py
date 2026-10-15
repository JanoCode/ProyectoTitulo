from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.breaks import router as breaks_router
from app.api.health import router as health_router
from app.api.settings import router as settings_router
from app.api.usage_sessions import router as usage_sessions_router
from app.api.users import router as users_router
from app.core.config import get_settings

settings = get_settings()
development = settings.environment == "development"

app = FastAPI(
    title="ErgoSense API",
    version="0.2.0",
    docs_url="/docs" if development else None,
    redoc_url=None,
    openapi_url="/openapi.json" if development else None,
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, error: RequestValidationError):
    """Entrega un mensaje general en español y conserva el detalle técnico."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Los datos enviados no son válidos.",
            "errors": jsonable_encoder(error.errors()),
        },
    )

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Usuarios"])
app.include_router(settings_router, prefix="/api/v1/settings", tags=["Configuración"])
app.include_router(
    usage_sessions_router,
    prefix="/api/v1/usage-sessions",
    tags=["Sesiones de uso"],
)
app.include_router(breaks_router, prefix="/api/v1/breaks", tags=["Pausas"])
