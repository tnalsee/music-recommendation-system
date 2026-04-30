from fastapi import APIRouter
from src.api import song

router = APIRouter()
router.include_router(song.router, prefix="/api", tags=["image"])

__all__ = ["router"]