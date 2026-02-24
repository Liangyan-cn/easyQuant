import logging
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.models.stock_pool import StockPool, StockPoolType
from app.repositories.stock_pool_repo import StockPoolRepository
from app.schemas.stock_pool import (
    StockPoolCreate,
    StockPoolDetailResponse,
    StockPoolItemCreate,
    StockPoolItemResponse,
    StockPoolResponse,
    StockPoolUpdate,
)

logger = logging.getLogger(__name__)


class StockPoolService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = StockPoolRepository(db)

    async def create_pool(self, data: StockPoolCreate, user_id: int) -> StockPoolResponse:
        existing = await self.repo.get_by_code(data.code)
        if existing:
            raise ConflictException(f"Stock pool with code '{data.code}' already exists")
        pool = await self.repo.create(data, user_id)
        return self._to_response(pool)

    async def get_pool(self, pool_id: int, user_id: int) -> StockPoolDetailResponse:
        pool = await self.repo.get_by_id(pool_id)
        if not pool:
            raise NotFoundException("Stock pool not found")
        if not self._can_view(pool, user_id):
            raise ForbiddenException("Access denied")
        return self._to_detail_response(pool)

    async def get_pools(
        self, user_id: int, page: int = 1, size: int = 20, pool_type: Optional[str] = None
    ) -> Tuple[List[StockPoolResponse], int]:
        pools, total = await self.repo.get_list(user_id, page, size, pool_type)
        return [self._to_response(p) for p in pools], total

    async def update_pool(self, pool_id: int, data: StockPoolUpdate, user_id: int) -> StockPoolResponse:
        pool = await self.repo.get_by_id(pool_id)
        if not pool:
            raise NotFoundException("Stock pool not found")
        if not self._can_modify(pool, user_id):
            raise ForbiddenException("Cannot modify this stock pool")
        updated = await self.repo.update(pool_id, data)
        return self._to_response(updated)

    async def delete_pool(self, pool_id: int, user_id: int) -> bool:
        pool = await self.repo.get_by_id(pool_id)
        if not pool:
            raise NotFoundException("Stock pool not found")
        if not self._can_modify(pool, user_id):
            raise ForbiddenException("Cannot delete this stock pool")
        return await self.repo.delete(pool_id)

    async def add_stock(self, pool_id: int, data: StockPoolItemCreate, user_id: int) -> StockPoolItemResponse:
        pool = await self.repo.get_by_id(pool_id)
        if not pool:
            raise NotFoundException("Stock pool not found")
        if not self._can_modify(pool, user_id):
            raise ForbiddenException("Cannot modify this stock pool")
        existing = await self.repo.get_stock_item(pool_id, data.stock_code)
        if existing:
            raise ConflictException(f"Stock '{data.stock_code}' already in pool")
        item = await self.repo.add_stock(pool_id, data)
        return StockPoolItemResponse.model_validate(item)

    async def remove_stock(self, pool_id: int, stock_code: str, user_id: int) -> bool:
        pool = await self.repo.get_by_id(pool_id)
        if not pool:
            raise NotFoundException("Stock pool not found")
        if not self._can_modify(pool, user_id):
            raise ForbiddenException("Cannot modify this stock pool")
        return await self.repo.remove_stock(pool_id, stock_code)

    async def import_index(self, pool_id: int, index_code: str, user_id: int) -> int:
        pool = await self.repo.get_by_id(pool_id)
        if not pool:
            raise NotFoundException("Stock pool not found")
        if not self._can_modify(pool, user_id):
            raise ForbiddenException("Cannot modify this stock pool")

        stocks = self._fetch_index_stocks(index_code)
        if not stocks:
            raise NotFoundException(f"Index '{index_code}' not found or no stocks")

        await self.repo.clear_stocks(pool_id)
        count = await self.repo.add_stocks_bulk(pool_id, stocks)
        logger.info(f"Imported {count} stocks from index {index_code} to pool {pool_id}")
        return count

    def _fetch_index_stocks(self, index_code: str) -> List[dict]:
        try:
            import akshare as ak
            df = ak.index_stock_cons(symbol=index_code)
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    "stock_code": str(row.get("品种代码", row.get("constituent_code", ""))),
                    "stock_name": str(row.get("品种名称", row.get("constituent_name", ""))),
                })
            return stocks
        except ImportError:
            raise RuntimeError("AKShare not installed")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch index stocks: {e}")

    def _can_view(self, pool: StockPool, user_id: int) -> bool:
        return pool.pool_type == StockPoolType.SYSTEM.value or pool.user_id == user_id

    def _can_modify(self, pool: StockPool, user_id: int) -> bool:
        return pool.pool_type == StockPoolType.USER.value and pool.user_id == user_id

    def _to_response(self, pool: StockPool) -> StockPoolResponse:
        if hasattr(pool, "stock_count"):
            stock_count = pool.stock_count
        elif "items" in pool.__dict__ and pool.items is not None:
            stock_count = len(pool.items)
        else:
            stock_count = 0
        return StockPoolResponse(
            id=pool.id,
            name=pool.name,
            code=pool.code,
            pool_type=pool.pool_type,
            description=pool.description,
            stock_count=stock_count,
            created_at=pool.created_at,
            updated_at=pool.updated_at,
        )

    def _to_detail_response(self, pool: StockPool) -> StockPoolDetailResponse:
        return StockPoolDetailResponse(
            id=pool.id,
            name=pool.name,
            code=pool.code,
            pool_type=pool.pool_type,
            description=pool.description,
            stock_count=len(pool.items) if pool.items else 0,
            created_at=pool.created_at,
            updated_at=pool.updated_at,
            items=[StockPoolItemResponse.model_validate(item) for item in (pool.items or [])],
        )
