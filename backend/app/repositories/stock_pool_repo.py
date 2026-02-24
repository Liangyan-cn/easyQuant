from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.stock_pool import StockPool, StockPoolItem, StockPoolType
from app.schemas.stock_pool import StockPoolCreate, StockPoolItemCreate, StockPoolUpdate


class StockPoolRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: StockPoolCreate, user_id: int) -> StockPool:
        pool = StockPool(
            name=data.name,
            code=data.code,
            description=data.description,
            pool_type=StockPoolType.USER.value,
            user_id=user_id,
        )
        self.db.add(pool)
        await self.db.commit()
        await self.db.refresh(pool)
        return pool

    async def create_system_pool(self, name: str, code: str, description: str) -> StockPool:
        pool = StockPool(
            name=name,
            code=code,
            description=description,
            pool_type=StockPoolType.SYSTEM.value,
            user_id=None,
        )
        self.db.add(pool)
        await self.db.commit()
        await self.db.refresh(pool)
        return pool

    async def get_by_id(self, pool_id: int) -> Optional[StockPool]:
        result = await self.db.execute(
            select(StockPool).options(selectinload(StockPool.items)).where(StockPool.id == pool_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[StockPool]:
        result = await self.db.execute(select(StockPool).where(StockPool.code == code))
        return result.scalar_one_or_none()

    async def get_list(
        self, user_id: int, page: int = 1, size: int = 20, pool_type: Optional[str] = None
    ) -> Tuple[List[StockPool], int]:
        base_query = select(StockPool).where(
            or_(StockPool.pool_type == StockPoolType.SYSTEM.value, StockPool.user_id == user_id)
        )
        if pool_type:
            base_query = base_query.where(StockPool.pool_type == pool_type)

        count_result = await self.db.execute(select(func.count()).select_from(base_query.subquery()))
        total = count_result.scalar() or 0

        result = await self.db.execute(
            base_query.order_by(StockPool.created_at.desc()).offset((page - 1) * size).limit(size)
        )
        pools = list(result.scalars().all())

        for pool in pools:
            item_count = await self.db.execute(
                select(func.count()).where(StockPoolItem.pool_id == pool.id)
            )
            pool.stock_count = item_count.scalar() or 0

        return pools, total

    async def update(self, pool_id: int, data: StockPoolUpdate) -> Optional[StockPool]:
        pool = await self.get_by_id(pool_id)
        if not pool:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(pool, key, value)
        pool.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(pool)
        return pool

    async def delete(self, pool_id: int) -> bool:
        pool = await self.get_by_id(pool_id)
        if not pool:
            return False
        await self.db.delete(pool)
        await self.db.commit()
        return True

    async def add_stock(self, pool_id: int, data: StockPoolItemCreate) -> StockPoolItem:
        item = StockPoolItem(
            pool_id=pool_id,
            stock_code=data.stock_code,
            stock_name=data.stock_name,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def add_stocks_bulk(self, pool_id: int, stocks: List[dict]) -> int:
        items = [
            StockPoolItem(pool_id=pool_id, stock_code=s["stock_code"], stock_name=s.get("stock_name"))
            for s in stocks
        ]
        self.db.add_all(items)
        await self.db.commit()
        return len(items)

    async def remove_stock(self, pool_id: int, stock_code: str) -> bool:
        result = await self.db.execute(
            select(StockPoolItem).where(
                StockPoolItem.pool_id == pool_id, StockPoolItem.stock_code == stock_code
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return False
        await self.db.delete(item)
        await self.db.commit()
        return True

    async def get_stock_item(self, pool_id: int, stock_code: str) -> Optional[StockPoolItem]:
        result = await self.db.execute(
            select(StockPoolItem).where(
                StockPoolItem.pool_id == pool_id, StockPoolItem.stock_code == stock_code
            )
        )
        return result.scalar_one_or_none()

    async def clear_stocks(self, pool_id: int) -> int:
        result = await self.db.execute(select(StockPoolItem).where(StockPoolItem.pool_id == pool_id))
        items = result.scalars().all()
        count = len(items)
        for item in items:
            await self.db.delete(item)
        await self.db.commit()
        return count
