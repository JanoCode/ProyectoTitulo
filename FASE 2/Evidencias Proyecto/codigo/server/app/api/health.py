from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def get_health():
    """Confirma que la API se encuentra en ejecución."""
    return {"status": "ok"}