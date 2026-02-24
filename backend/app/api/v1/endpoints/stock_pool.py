from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.stock_pool import (
    ImportIndexRequest,
    StockPoolCreate,
    StockPoolDetailResponse,
    StockPoolItemCreate,
    StockPoolItemResponse,
    StockPoolListResponse,
    StockPoolResponse,
    StockPoolUpdate,
)
from app.services.stock_pool_service import StockPoolService

router = APIRouter()


@router.get("", response_model=StockPoolListResponse)
async def get_stock_pools(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    pool_type: Optional[str] = Query(None, description="Filter by pool type: system or user"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockPoolListResponse:
    service = StockPoolService(db)
    pools, total = await service.get_pools(current_user.id, page, size, pool_type)
    return StockPoolListResponse(items=pools, total=total, page=page, size=size)


@router.post("", response_model=StockPoolResponse)
async def create_stock_pool(
    data: StockPoolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockPoolResponse:
    service = StockPoolService(db)
    return await service.create_pool(data, current_user.id)


@router.get("/{pool_id}", response_model=StockPoolDetailResponse)
async def get_stock_pool(
    pool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockPoolDetailResponse:
    service = StockPoolService(db)
    return await service.get_pool(pool_id, current_user.id)


@router.put("/{pool_id}", response_model=StockPoolResponse)
async def update_stock_pool(
    pool_id: int,
    data: StockPoolUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockPoolResponse:
    service = StockPoolService(db)
    return await service.update_pool(pool_id, data, current_user.id)


@router.delete("/{pool_id}")
async def delete_stock_pool(
    pool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    service = StockPoolService(db)
    await service.delete_pool(pool_id, current_user.id)
    return {"message": "Stock pool deleted"}


@router.post("/{pool_id}/stocks", response_model=StockPoolItemResponse)
async def add_stock_to_pool(
    pool_id: int,
    data: StockPoolItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockPoolItemResponse:
    service = StockPoolService(db)
    return await service.add_stock(pool_id, data, current_user.id)


@router.delete("/{pool_id}/stocks/{stock_code}")
async def remove_stock_from_pool(
    pool_id: int,
    stock_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    service = StockPoolService(db)
    await service.remove_stock(pool_id, stock_code, current_user.id)
    return {"message": "Stock removed from pool"}


@router.post("/{pool_id}/import-index")
async def import_index_to_pool(
    pool_id: int,
    data: ImportIndexRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    service = StockPoolService(db)
    count = await service.import_index(pool_id, data.index_code, current_user.id)
    return {"message": f"Imported {count} stocks from index {data.index_code}"}
