from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.strategy import (
    Backtest,
    BacktestResult,
    BacktestStatus,
    Order,
    Position,
    Strategy,
    StrategyStatus,
    StrategyType,
)
from app.schemas.strategy import BacktestCreate, StrategyCreate, StrategyUpdate


class StrategyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, strategy_data: StrategyCreate, user_id: Optional[int] = None) -> Strategy:
        strategy = Strategy(
            name=strategy_data.name,
            code=strategy_data.code,
            strategy_type=strategy_data.strategy_type,
            description=strategy_data.description,
            logic=strategy_data.logic,
            parameters=strategy_data.parameters,
            created_by=user_id,
        )
        self.db.add(strategy)
        await self.db.commit()
        await self.db.refresh(strategy)
        return strategy

    async def get_by_id(self, strategy_id: int) -> Optional[Strategy]:
        result = await self.db.execute(select(Strategy).where(Strategy.id == strategy_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Strategy]:
        result = await self.db.execute(select(Strategy).where(Strategy.code == code))
        return result.scalar_one_or_none()

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        strategy_type: Optional[StrategyType] = None,
        status: Optional[StrategyStatus] = None,
        keyword: Optional[str] = None,
    ) -> Tuple[List[Strategy], int]:
        query = select(Strategy)
        count_query = select(func.count(Strategy.id))

        if strategy_type:
            query = query.where(Strategy.strategy_type == strategy_type)
            count_query = count_query.where(Strategy.strategy_type == strategy_type)

        if status:
            query = query.where(Strategy.status == status)
            count_query = count_query.where(Strategy.status == status)

        if keyword:
            keyword_filter = Strategy.name.ilike(f"%{keyword}%") | Strategy.code.ilike(f"%{keyword}%")
            query = query.where(keyword_filter)
            count_query = count_query.where(keyword_filter)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        query = query.order_by(Strategy.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        strategies = result.scalars().all()

        return list(strategies), total

    async def update(self, strategy_id: int, strategy_data: StrategyUpdate) -> Optional[Strategy]:
        strategy = await self.get_by_id(strategy_id)
        if not strategy:
            return None

        update_data = strategy_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(strategy, field, value)

        await self.db.commit()
        await self.db.refresh(strategy)
        return strategy

    async def delete(self, strategy_id: int) -> bool:
        strategy = await self.get_by_id(strategy_id)
        if not strategy:
            return False

        await self.db.delete(strategy)
        await self.db.commit()
        return True

    async def get_type_stats(self) -> List[Tuple[StrategyType, int]]:
        query = select(Strategy.strategy_type, func.count(Strategy.id)).group_by(Strategy.strategy_type)
        result = await self.db.execute(query)
        return result.all()


class BacktestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, backtest_data: BacktestCreate) -> Backtest:
        backtest = Backtest(
            strategy_id=backtest_data.strategy_id,
            name=backtest_data.name,
            start_date=backtest_data.start_date,
            end_date=backtest_data.end_date,
            initial_capital=backtest_data.initial_capital,
            commission_rate=backtest_data.commission_rate,
            slippage=backtest_data.slippage,
            benchmark=backtest_data.benchmark,
            stock_pool=backtest_data.stock_pool,
            parameters=backtest_data.parameters,
        )
        self.db.add(backtest)
        await self.db.commit()
        await self.db.refresh(backtest)
        return backtest

    async def get_by_id(self, backtest_id: int) -> Optional[Backtest]:
        result = await self.db.execute(
            select(Backtest)
            .options(selectinload(Backtest.result))
            .where(Backtest.id == backtest_id)
        )
        return result.scalar_one_or_none()

    async def get_by_strategy(
        self,
        strategy_id: int,
        limit: int = 10,
    ) -> List[Backtest]:
        query = (
            select(Backtest)
            .options(selectinload(Backtest.result))
            .where(Backtest.strategy_id == strategy_id)
            .order_by(Backtest.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        backtest_id: int,
        status: BacktestStatus,
        error_message: Optional[str] = None,
    ) -> Optional[Backtest]:
        backtest = await self.get_by_id(backtest_id)
        if not backtest:
            return None

        backtest.status = status
        if error_message:
            backtest.error_message = error_message
        if status == BacktestStatus.COMPLETED:
            backtest.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(backtest)
        return backtest

    async def delete(self, backtest_id: int) -> bool:
        backtest = await self.get_by_id(backtest_id)
        if not backtest:
            return False

        await self.db.delete(backtest)
        await self.db.commit()
        return True


class BacktestResultRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, result_data: dict) -> BacktestResult:
        result = BacktestResult(**result_data)
        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)
        return result

    async def get_by_backtest(self, backtest_id: int) -> Optional[BacktestResult]:
        result = await self.db.execute(
            select(BacktestResult).where(BacktestResult.backtest_id == backtest_id)
        )
        return result.scalar_one_or_none()

    async def delete_by_backtest_id(self, backtest_id: int) -> bool:
        result = await self.get_by_backtest(backtest_id)
        if result:
            await self.db.delete(result)
            await self.db.commit()
            return True
        return False


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create(self, orders: List[dict]) -> int:
        order_objs = [Order(**o) for o in orders]
        self.db.add_all(order_objs)
        await self.db.commit()
        return len(order_objs)

    async def get_by_backtest(
        self,
        backtest_id: int,
        page: int = 1,
        size: int = 50,
    ) -> Tuple[List[Order], int]:
        count_query = select(func.count(Order.id)).where(Order.backtest_id == backtest_id)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        query = (
            select(Order)
            .where(Order.backtest_id == backtest_id)
            .order_by(Order.order_time.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(query)
        orders = result.scalars().all()

        return list(orders), total


class PositionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create(self, positions: List[dict]) -> int:
        position_objs = [Position(**p) for p in positions]
        self.db.add_all(position_objs)
        await self.db.commit()
        return len(position_objs)

    async def get_by_backtest(self, backtest_id: int) -> List[Position]:
        query = (
            select(Position)
            .where(Position.backtest_id == backtest_id)
            .order_by(Position.market_value.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_or_create(self, backtest_id: int, stock_code: str, data: dict) -> Position:
        query = select(Position).where(
            Position.backtest_id == backtest_id,
            Position.stock_code == stock_code,
        )
        result = await self.db.execute(query)
        position = result.scalar_one_or_none()

        if position:
            for field, value in data.items():
                setattr(position, field, value)
        else:
            position = Position(backtest_id=backtest_id, stock_code=stock_code, **data)
            self.db.add(position)

        await self.db.commit()
        await self.db.refresh(position)
        return position
