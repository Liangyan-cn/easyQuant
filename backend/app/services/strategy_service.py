from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.strategy import Backtest, BacktestStatus, Strategy, StrategyStatus, StrategyType
from app.repositories.strategy_repo import (
    BacktestRepository,
    BacktestResultRepository,
    OrderRepository,
    PositionRepository,
    StrategyRepository,
)
from app.schemas.strategy import BacktestCreate, StrategyCreate, StrategyTypeStats, StrategyUpdate


class StrategyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.strategy_repo = StrategyRepository(db)
        self.backtest_repo = BacktestRepository(db)
        self.result_repo = BacktestResultRepository(db)
        self.order_repo = OrderRepository(db)
        self.position_repo = PositionRepository(db)

    async def create_strategy(
        self,
        strategy_data: StrategyCreate,
        user_id: Optional[int] = None,
    ) -> Strategy:
        existing = await self.strategy_repo.get_by_code(strategy_data.code)
        if existing:
            raise ValueError(f"Strategy with code '{strategy_data.code}' already exists")

        return await self.strategy_repo.create(strategy_data, user_id)

    async def get_strategy(self, strategy_id: int) -> Optional[Strategy]:
        return await self.strategy_repo.get_by_id(strategy_id)

    async def get_strategy_by_code(self, code: str) -> Optional[Strategy]:
        return await self.strategy_repo.get_by_code(code)

    async def get_strategies(
        self,
        page: int = 1,
        size: int = 20,
        strategy_type: Optional[StrategyType] = None,
        status: Optional[StrategyStatus] = None,
        keyword: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Tuple[List[Strategy], int]:
        return await self.strategy_repo.get_list(page, size, strategy_type, status, keyword, user_id)

    async def update_strategy(
        self,
        strategy_id: int,
        strategy_data: StrategyUpdate,
    ) -> Optional[Strategy]:
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            return None

        if strategy.is_builtin:
            raise ValueError("Cannot modify builtin strategy")

        if strategy_data.code:
            existing = await self.strategy_repo.get_by_code(strategy_data.code)
            if existing and existing.id != strategy_id:
                raise ValueError(f"Strategy with code '{strategy_data.code}' already exists")

        return await self.strategy_repo.update(strategy_id, strategy_data)

    async def delete_strategy(self, strategy_id: int) -> bool:
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            return False

        if strategy.is_builtin:
            raise ValueError("Cannot delete builtin strategy")

        return await self.strategy_repo.delete(strategy_id)

    async def clone_strategy(self, strategy_id: int, user_id: Optional[int] = None) -> Strategy:
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise ValueError(f"Strategy with id {strategy_id} not found")

        base_name = f"{strategy.name} (副本)"
        base_code = f"{strategy.code}_copy"

        new_code = base_code
        counter = 1
        while await self.strategy_repo.get_by_code(new_code):
            new_code = f"{base_code}_{counter}"
            counter += 1

        cloned_strategy = Strategy(
            name=base_name,
            code=new_code,
            strategy_type=strategy.strategy_type,
            status=strategy.status,
            description=strategy.description,
            logic=strategy.logic,
            parameters=strategy.parameters.copy() if strategy.parameters else None,
            is_builtin=0,
            created_by=user_id,
        )
        self.db.add(cloned_strategy)
        await self.db.commit()
        await self.db.refresh(cloned_strategy)
        return cloned_strategy

    async def get_type_stats(self) -> List[StrategyTypeStats]:
        stats = await self.strategy_repo.get_type_stats()
        return [StrategyTypeStats(strategy_type=s[0], count=s[1]) for s in stats]

    async def create_backtest(self, backtest_data: BacktestCreate) -> Backtest:
        strategy = await self.strategy_repo.get_by_id(backtest_data.strategy_id)
        if not strategy:
            raise ValueError(f"Strategy with id {backtest_data.strategy_id} not found")

        return await self.backtest_repo.create(backtest_data)

    async def get_backtest(self, backtest_id: int) -> Optional[Backtest]:
        return await self.backtest_repo.get_by_id(backtest_id)

    async def get_backtests_by_strategy(
        self,
        strategy_id: int,
        limit: int = 10,
    ) -> List[Backtest]:
        return await self.backtest_repo.get_by_strategy(strategy_id, limit)

    async def update_backtest_status(
        self,
        backtest_id: int,
        status: BacktestStatus,
        error_message: Optional[str] = None,
    ) -> Optional[Backtest]:
        return await self.backtest_repo.update_status(backtest_id, status, error_message)

    async def delete_backtest(self, backtest_id: int) -> bool:
        return await self.backtest_repo.delete(backtest_id)

    async def get_backtest_orders(
        self,
        backtest_id: int,
        page: int = 1,
        size: int = 50,
    ):
        return await self.order_repo.get_by_backtest(backtest_id, page, size)

    async def get_backtest_positions(self, backtest_id: int):
        return await self.position_repo.get_by_backtest(backtest_id)


BUILTIN_STRATEGIES = [
    {
        "name": "双均线策略",
        "code": "ma_cross",
        "strategy_type": StrategyType.TREND_FOLLOWING,
        "description": "当短期均线上穿长期均线时买入，下穿时卖出",
        "logic": "short_ma > long_ma => BUY; short_ma < long_ma => SELL",
        "parameters": {"short_period": 5, "long_period": 20},
        "is_builtin": 1,
    },
    {
        "name": "动量策略",
        "code": "momentum",
        "strategy_type": StrategyType.MOMENTUM,
        "description": "买入过去N日涨幅最大的股票，卖出涨幅最小的股票",
        "logic": "rank by momentum_N => BUY top K; SELL bottom K",
        "parameters": {"lookback_period": 20, "top_k": 10},
        "is_builtin": 1,
    },
    {
        "name": "均值回归策略",
        "code": "mean_reversion",
        "strategy_type": StrategyType.MEAN_REVERSION,
        "description": "当价格偏离均值超过阈值时反向交易",
        "logic": "price < ma - threshold => BUY; price > ma + threshold => SELL",
        "parameters": {"ma_period": 20, "threshold": 2.0},
        "is_builtin": 1,
    },
    {
        "name": "布林带策略",
        "code": "bollinger_bands",
        "strategy_type": StrategyType.MEAN_REVERSION,
        "description": "价格触及布林带下轨买入，触及上轨卖出",
        "logic": "price < lower_band => BUY; price > upper_band => SELL",
        "parameters": {"period": 20, "std_dev": 2.0},
        "is_builtin": 1,
    },
    {
        "name": "RSI策略",
        "code": "rsi_strategy",
        "strategy_type": StrategyType.MEAN_REVERSION,
        "description": "RSI超卖时买入，超买时卖出",
        "logic": "RSI < oversold => BUY; RSI > overbought => SELL",
        "parameters": {"period": 14, "oversold": 30, "overbought": 70},
        "is_builtin": 1,
    },
]


async def init_builtin_strategies(db: AsyncSession):
    repo = StrategyRepository(db)
    for strategy_data in BUILTIN_STRATEGIES:
        existing = await repo.get_by_code(strategy_data["code"])
        if not existing:
            strategy = Strategy(**strategy_data)
            db.add(strategy)
    await db.commit()
