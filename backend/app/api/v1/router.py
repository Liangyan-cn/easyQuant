from fastapi import APIRouter

from app.api.v1.endpoints import auth, cache, data, factor, health, sandbox, stock_pool, strategy

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(factor.router, prefix="/factors", tags=["factors"])
api_router.include_router(strategy.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(sandbox.router, prefix="/sandbox", tags=["sandbox"])
api_router.include_router(stock_pool.router, prefix="/stock-pools", tags=["stock-pools"])
api_router.include_router(cache.router)
