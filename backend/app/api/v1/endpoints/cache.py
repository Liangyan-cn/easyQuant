from fastapi import APIRouter

from app.schemas.cache import CacheStats, CacheStatus
from app.services.cache_service import CacheService

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/status", response_model=CacheStatus)
async def get_cache_status():
    cache = CacheService()
    return cache.get_cache_status()


@router.get("/stats", response_model=CacheStats)
async def get_cache_stats():
    cache = CacheService()
    return cache.get_cache_stats()
