import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sandbox import (
    DeploymentStatus,
    SandboxAccount,
    SandboxDeployment,
    SandboxPosition,
    SandboxStatus,
    TransactionType,
)
from app.repositories.sandbox_repo import (
    SandboxAccountRepository,
    SandboxDailyValueRepository,
    SandboxDeploymentRepository,
    SandboxPositionRepository,
    SandboxTransactionRepository,
)
from app.repositories.strategy_repo import StrategyRepository
from app.services.backtest_engine import (
    BacktestConfig,
    BacktestEngine,
    SignalType,
    get_strategy_class,
)
from app.services.data_service import get_stock_history, get_stock_list
from app.core.trading_config import TradingConfig, MIN_HISTORY_DAYS

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    success: bool
    execution_date: date
    signals: List[Dict[str, Any]]
    orders_executed: int
    total_value: float
    daily_return: Optional[float]
    error_message: Optional[str] = None


class SandboxExecutionEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_repo = SandboxAccountRepository(db)
        self.position_repo = SandboxPositionRepository(db)
        self.transaction_repo = SandboxTransactionRepository(db)
        self.deployment_repo = SandboxDeploymentRepository(db)
        self.daily_value_repo = SandboxDailyValueRepository(db)
        self.strategy_repo = StrategyRepository(db)

    async def execute_deployment(
        self, deployment: SandboxDeployment, execution_date: date
    ) -> ExecutionResult:
        logger.info(
            f"Executing deployment {deployment.id} for date {execution_date}"
        )

        try:
            account = await self.account_repo.get_by_id(deployment.account_id)
            if not account or account.status != SandboxStatus.ACTIVE:
                return ExecutionResult(
                    success=False,
                    execution_date=execution_date,
                    signals=[],
                    orders_executed=0,
                    total_value=0,
                    daily_return=None,
                    error_message="Account not found or inactive",
                )

            strategy = await self.strategy_repo.get_by_id(deployment.strategy_id)
            if not strategy:
                return ExecutionResult(
                    success=False,
                    execution_date=execution_date,
                    signals=[],
                    orders_executed=0,
                    total_value=0,
                    daily_return=None,
                    error_message="Strategy not found",
                )

            stock_pool = deployment.stock_pool or self._get_default_stock_pool()
            market_data = await self._fetch_market_data(stock_pool, execution_date)

            if not market_data:
                logger.info(f"No market data available for {execution_date}")
                return ExecutionResult(
                    success=True,
                    execution_date=execution_date,
                    signals=[],
                    orders_executed=0,
                    total_value=account.total_value,
                    daily_return=0,
                    error_message="No market data available (market closed?)",
                )

            signals = await self._generate_signals(
                strategy, deployment, market_data, execution_date
            )

            orders_executed = await self._execute_orders(
                account, deployment, signals, market_data
            )

            await self._update_positions(account, market_data)

            total_value = await self._calculate_total_value(account)

            daily_return = await self._record_daily_value(
                account, execution_date, total_value
            )

            return ExecutionResult(
                success=True,
                execution_date=execution_date,
                signals=signals,
                orders_executed=orders_executed,
                total_value=total_value,
                daily_return=daily_return,
            )

        except Exception as e:
            logger.error(f"Execution failed: {str(e)}")
            return ExecutionResult(
                success=False,
                execution_date=execution_date,
                signals=[],
                orders_executed=0,
                total_value=0,
                daily_return=None,
                error_message=str(e),
            )

    def _get_default_stock_pool(self) -> List[str]:
        stock_list = get_stock_list(page=1, size=TradingConfig.MAX_STOCK_POOL_SIZE)
        return [s.code for s in stock_list.items]

    async def _fetch_market_data(
        self, stock_pool: List[str], execution_date: date
    ) -> Dict[str, Dict[str, float]]:
        market_data = {}
        start_date = execution_date - timedelta(days=60)

        for stock_code in stock_pool[:TradingConfig.MAX_STOCK_POOL_SIZE]:
            try:
                history = get_stock_history(
                    stock_code,
                    period="daily",
                    start=start_date,
                    end=execution_date,
                )
                if history.items:
                    latest = history.items[-1]
                    market_data[stock_code] = {
                        "date": str(latest.date),
                        "open": latest.open,
                        "high": latest.high,
                        "low": latest.low,
                        "close": latest.close,
                        "volume": latest.volume,
                        "history": [
                            {
                                "date": str(item.date),
                                "close": item.close,
                                "volume": item.volume,
                            }
                            for item in history.items
                        ],
                    }
            except Exception as e:
                logger.warning(f"Failed to fetch data for {stock_code}: {e}")
                continue

        return market_data

    async def _generate_signals(
        self,
        strategy,
        deployment: SandboxDeployment,
        market_data: Dict[str, Dict],
        execution_date: date,
    ) -> List[Dict[str, Any]]:
        signals = []

        try:
            strategy_class = get_strategy_class(strategy.code)
            params = deployment.parameters or strategy.parameters or {}
            strategy_instance = strategy_class(params)

            for stock_code, data in market_data.items():
                try:
                    history = data.get("history", [])
                    if len(history) < MIN_HISTORY_DAYS:
                        continue

                    closes = [h["close"] for h in history]
                    signal = strategy_instance.generate_signal_from_prices(
                        stock_code, closes
                    )

                    if signal and signal.signal_type != SignalType.HOLD:
                        signals.append({
                            "stock_code": stock_code,
                            "signal_type": signal.signal_type.value,
                            "strength": signal.strength,
                            "reason": signal.reason,
                            "price": data["close"],
                        })
                except Exception as e:
                    logger.warning(f"Signal generation failed for {stock_code}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Strategy execution failed: {e}")

        return signals

    async def _execute_orders(
        self,
        account: SandboxAccount,
        deployment: SandboxDeployment,
        signals: List[Dict],
        market_data: Dict[str, Dict],
    ) -> int:
        orders_executed = 0
        allocation = deployment.allocation_ratio * account.current_cash
        per_stock_allocation = allocation / max(len(signals), 1) if signals else 0

        initial_version = account.version
        initial_cash = account.current_cash

        async with self.db.begin_nested():
            for signal in signals:
                stock_code = signal["stock_code"]
                signal_type = signal["signal_type"]
                price = signal["price"]

                try:
                    if signal_type == "buy":
                        quantity = int(per_stock_allocation / price / TradingConfig.MIN_TRADE_QUANTITY) * TradingConfig.MIN_TRADE_QUANTITY
                        if quantity >= TradingConfig.MIN_TRADE_QUANTITY and account.current_cash >= quantity * price:
                            amount = quantity * price
                            commission = amount * TradingConfig.BUY_COMMISSION_RATE

                            await self.transaction_repo.create(
                                account.id,
                                {
                                    "deployment_id": deployment.id,
                                    "transaction_type": TransactionType.BUY,
                                    "stock_code": stock_code,
                                    "quantity": quantity,
                                    "price": price,
                                    "amount": amount,
                                    "commission": commission,
                                    "description": f"Buy signal: {signal.get('reason', '')}",
                                },
                            )

                            position = await self.position_repo.get_by_stock(
                                account.id, stock_code
                            )
                            if position:
                                new_quantity = position.quantity + quantity
                                new_avg_cost = (
                                    (position.avg_cost * position.quantity + amount)
                                    / new_quantity
                                )
                                await self.position_repo.create_or_update(
                                    account.id,
                                    stock_code,
                                    {
                                        "quantity": new_quantity,
                                        "avg_cost": new_avg_cost,
                                        "current_price": price,
                                        "market_value": new_quantity * price,
                                    },
                                )
                            else:
                                await self.position_repo.create_or_update(
                                    account.id,
                                    stock_code,
                                    {
                                        "quantity": quantity,
                                        "avg_cost": price,
                                        "current_price": price,
                                        "market_value": quantity * price,
                                    },
                                )

                            account.current_cash -= (amount + commission)
                            orders_executed += 1

                    elif signal_type == "sell":
                        position = await self.position_repo.get_by_stock(
                            account.id, stock_code
                        )
                        if position and position.quantity > 0:
                            quantity = position.quantity
                            amount = quantity * price
                            commission = amount * TradingConfig.SELL_COMMISSION_RATE + amount * TradingConfig.STAMP_TAX_RATE

                            pnl = (price - position.avg_cost) * quantity

                            await self.transaction_repo.create(
                                account.id,
                                {
                                    "deployment_id": deployment.id,
                                    "transaction_type": TransactionType.SELL,
                                    "stock_code": stock_code,
                                    "quantity": quantity,
                                    "price": price,
                                    "amount": amount,
                                    "commission": commission,
                                    "description": f"Sell signal: {signal.get('reason', '')}. PnL: {pnl:.2f}",
                                },
                            )

                            await self.position_repo.create_or_update(
                                account.id,
                                stock_code,
                                {
                                    "quantity": 0,
                                    "market_value": 0,
                                    "realized_pnl": position.realized_pnl + pnl,
                                },
                            )

                            account.current_cash += (amount - commission)
                            orders_executed += 1

                except Exception as e:
                    logger.error(f"Order execution failed for {stock_code}: {e}")
                    continue

            if orders_executed > 0:
                await self.account_repo.update_with_lock(
                    account, {"current_cash": account.current_cash}, initial_version
                )
            elif account.current_cash != initial_cash:
                await self.account_repo.update(account, {"current_cash": account.current_cash})

        return orders_executed

    async def _update_positions(
        self, account: SandboxAccount, market_data: Dict[str, Dict]
    ) -> None:
        positions = await self.position_repo.get_by_account(account.id)
        for position in positions:
            if position.quantity > 0 and position.stock_code in market_data:
                current_price = market_data[position.stock_code]["close"]
                market_value = position.quantity * current_price
                unrealized_pnl = (current_price - position.avg_cost) * position.quantity

                await self.position_repo.create_or_update(
                    account.id,
                    position.stock_code,
                    {
                        "current_price": current_price,
                        "market_value": market_value,
                        "unrealized_pnl": unrealized_pnl,
                    },
                )

    async def _calculate_total_value(self, account: SandboxAccount) -> float:
        positions = await self.position_repo.get_by_account(account.id)
        position_value = sum(p.market_value for p in positions if p.quantity > 0)
        total_value = account.current_cash + position_value

        await self.account_repo.update(account, {"total_value": total_value})
        return total_value

    async def _record_daily_value(
        self, account: SandboxAccount, execution_date: date, total_value: float
    ) -> Optional[float]:
        positions = await self.position_repo.get_by_account(account.id)
        position_value = sum(p.market_value for p in positions if p.quantity > 0)

        prev_value = await self.daily_value_repo.get_latest(account.id)
        daily_return = None
        cumulative_return = None

        if prev_value:
            if prev_value.total_value > 0:
                daily_return = (total_value - prev_value.total_value) / prev_value.total_value
            if account.initial_capital > 0:
                cumulative_return = (total_value - account.initial_capital) / account.initial_capital
        else:
            if account.initial_capital > 0:
                cumulative_return = (total_value - account.initial_capital) / account.initial_capital

        await self.daily_value_repo.upsert(
            account.id,
            execution_date,
            {
                "total_value": total_value,
                "cash": account.current_cash,
                "position_value": position_value,
                "daily_return": daily_return,
                "cumulative_return": cumulative_return,
            },
        )

        return daily_return

    async def run_all_active_deployments(self, execution_date: Optional[date] = None) -> Dict[int, ExecutionResult]:
        if execution_date is None:
            execution_date = date.today()

        results = {}
        deployments = await self.deployment_repo.get_active_deployments()

        logger.info(f"Running {len(deployments)} active deployments for {execution_date}")

        for deployment in deployments:
            if deployment.end_date and execution_date > deployment.end_date:
                await self.deployment_repo.update(
                    deployment, {"status": DeploymentStatus.COMPLETED}
                )
                continue

            result = await self.execute_deployment(deployment, execution_date)
            results[deployment.id] = result

            if result.success:
                await self.deployment_repo.update(
                    deployment,
                    {
                        "last_run_date": execution_date,
                        "last_run_result": {
                            "signals": result.signals,
                            "orders_executed": result.orders_executed,
                            "total_value": result.total_value,
                            "daily_return": result.daily_return,
                        },
                    },
                )
            else:
                await self.deployment_repo.update(
                    deployment,
                    {
                        "status": DeploymentStatus.FAILED,
                        "error_message": result.error_message,
                    },
                )

        return results
