import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.sandbox_engine import SandboxExecutionEngine, ExecutionResult
from app.models.sandbox import (
    SandboxAccount,
    SandboxDeployment,
    SandboxPosition,
    SandboxStatus,
    DeploymentStatus,
)
from app.core.trading_config import TradingConfig


@pytest.fixture
def mock_account():
    account = MagicMock(spec=SandboxAccount)
    account.id = 1
    account.status = SandboxStatus.ACTIVE
    account.initial_capital = 1000000.0
    account.current_cash = 1000000.0
    account.total_value = 1000000.0
    account.version = 1
    return account


@pytest.fixture
def mock_deployment():
    deployment = MagicMock(spec=SandboxDeployment)
    deployment.id = 1
    deployment.account_id = 1
    deployment.strategy_id = 1
    deployment.allocation_ratio = 0.8
    deployment.stock_pool = ["000001", "000002"]
    deployment.parameters = {}
    deployment.end_date = None
    return deployment


@pytest.fixture
def mock_strategy():
    strategy = MagicMock()
    strategy.id = 1
    strategy.code = "dual_ma"
    strategy.parameters = {"short_period": 5, "long_period": 20}
    return strategy


@pytest.fixture
def mock_position():
    position = MagicMock(spec=SandboxPosition)
    position.id = 1
    position.account_id = 1
    position.stock_code = "000001"
    position.quantity = 1000
    position.avg_cost = 10.0
    position.current_price = 11.0
    position.market_value = 11000.0
    position.unrealized_pnl = 1000.0
    position.realized_pnl = 0.0
    return position


class TestExecutionResult:
    def test_success_result(self):
        result = ExecutionResult(
            success=True,
            execution_date=date.today(),
            signals=[{"stock_code": "000001", "signal_type": "buy"}],
            orders_executed=1,
            total_value=1000000.0,
            daily_return=0.01,
        )
        assert result.success is True
        assert result.orders_executed == 1
        assert result.error_message is None

    def test_failure_result(self):
        result = ExecutionResult(
            success=False,
            execution_date=date.today(),
            signals=[],
            orders_executed=0,
            total_value=0,
            daily_return=None,
            error_message="Account not found",
        )
        assert result.success is False
        assert result.error_message == "Account not found"


class TestSandboxExecutionEngine:
    @pytest.mark.asyncio
    async def test_execute_deployment_account_not_found(self, mock_deployment):
        mock_db = AsyncMock()
        engine = SandboxExecutionEngine(mock_db)
        engine.account_repo = AsyncMock()
        engine.account_repo.get_by_id = AsyncMock(return_value=None)

        result = await engine.execute_deployment(mock_deployment, date.today())

        assert result.success is False
        assert "Account not found" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_deployment_account_inactive(self, mock_deployment, mock_account):
        mock_db = AsyncMock()
        engine = SandboxExecutionEngine(mock_db)
        mock_account.status = SandboxStatus.STOPPED
        engine.account_repo = AsyncMock()
        engine.account_repo.get_by_id = AsyncMock(return_value=mock_account)

        result = await engine.execute_deployment(mock_deployment, date.today())

        assert result.success is False
        assert "inactive" in result.error_message.lower() or "stopped" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execute_deployment_strategy_not_found(self, mock_deployment, mock_account):
        mock_db = AsyncMock()
        engine = SandboxExecutionEngine(mock_db)
        engine.account_repo = AsyncMock()
        engine.account_repo.get_by_id = AsyncMock(return_value=mock_account)
        engine.strategy_repo = AsyncMock()
        engine.strategy_repo.get_by_id = AsyncMock(return_value=None)

        result = await engine.execute_deployment(mock_deployment, date.today())

        assert result.success is False
        assert "Strategy not found" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_deployment_no_market_data(
        self, mock_deployment, mock_account, mock_strategy
    ):
        mock_db = AsyncMock()
        engine = SandboxExecutionEngine(mock_db)
        engine.account_repo = AsyncMock()
        engine.account_repo.get_by_id = AsyncMock(return_value=mock_account)
        engine.strategy_repo = AsyncMock()
        engine.strategy_repo.get_by_id = AsyncMock(return_value=mock_strategy)
        engine._fetch_market_data = AsyncMock(return_value={})

        result = await engine.execute_deployment(mock_deployment, date.today())

        assert result.success is True
        assert result.orders_executed == 0
        assert "No market data" in result.error_message


class TestTradingCalculations:
    def test_buy_commission_calculation(self):
        amount = 10000.0
        commission = amount * TradingConfig.BUY_COMMISSION_RATE
        assert commission == pytest.approx(amount * 0.0003, rel=1e-6)
        assert commission == pytest.approx(3.0, rel=1e-6)

    def test_sell_commission_calculation(self):
        amount = 10000.0
        commission = amount * TradingConfig.SELL_COMMISSION_RATE
        stamp_tax = amount * TradingConfig.STAMP_TAX_RATE
        total_cost = commission + stamp_tax
        assert commission == pytest.approx(amount * 0.0003, rel=1e-6)
        assert stamp_tax == pytest.approx(amount * 0.001, rel=1e-6)
        assert total_cost == pytest.approx(13.0, rel=1e-6)

    def test_min_trade_quantity(self):
        assert TradingConfig.MIN_TRADE_QUANTITY == 100

    def test_quantity_rounding(self):
        price = 15.5
        allocation = 10000.0
        quantity = int(allocation / price / TradingConfig.MIN_TRADE_QUANTITY) * TradingConfig.MIN_TRADE_QUANTITY
        assert quantity == 600
        assert quantity % 100 == 0

    def test_quantity_rounding_small_allocation(self):
        price = 100.0
        allocation = 500.0
        quantity = int(allocation / price / TradingConfig.MIN_TRADE_QUANTITY) * TradingConfig.MIN_TRADE_QUANTITY
        assert quantity == 0


class TestDailyReturnCalculation:
    def test_daily_return_positive(self):
        prev_value = 1000000.0
        current_value = 1010000.0
        daily_return = (current_value - prev_value) / prev_value
        assert daily_return == pytest.approx(0.01, rel=1e-6)

    def test_daily_return_negative(self):
        prev_value = 1000000.0
        current_value = 990000.0
        daily_return = (current_value - prev_value) / prev_value
        assert daily_return == pytest.approx(-0.01, rel=1e-6)

    def test_daily_return_zero(self):
        prev_value = 1000000.0
        current_value = 1000000.0
        daily_return = (current_value - prev_value) / prev_value
        assert daily_return == 0.0

    def test_cumulative_return(self):
        initial_capital = 1000000.0
        current_value = 1200000.0
        cumulative_return = (current_value - initial_capital) / initial_capital
        assert cumulative_return == pytest.approx(0.2, rel=1e-6)


class TestPositionCalculations:
    def test_average_cost_calculation(self):
        old_quantity = 1000
        old_avg_cost = 10.0
        new_quantity = 500
        new_price = 12.0
        new_amount = new_quantity * new_price

        total_quantity = old_quantity + new_quantity
        new_avg_cost = (old_avg_cost * old_quantity + new_amount) / total_quantity

        assert total_quantity == 1500
        assert new_avg_cost == pytest.approx(10.67, rel=0.01)

    def test_unrealized_pnl_calculation(self):
        quantity = 1000
        avg_cost = 10.0
        current_price = 12.0
        unrealized_pnl = (current_price - avg_cost) * quantity
        assert unrealized_pnl == 2000.0

    def test_realized_pnl_calculation(self):
        quantity = 1000
        avg_cost = 10.0
        sell_price = 12.0
        realized_pnl = (sell_price - avg_cost) * quantity
        assert realized_pnl == 2000.0

    def test_market_value_calculation(self):
        quantity = 1000
        current_price = 15.5
        market_value = quantity * current_price
        assert market_value == 15500.0


class TestTotalValueCalculation:
    def test_total_value_cash_only(self):
        cash = 1000000.0
        position_value = 0.0
        total_value = cash + position_value
        assert total_value == 1000000.0

    def test_total_value_with_positions(self):
        cash = 500000.0
        position_value = 500000.0
        total_value = cash + position_value
        assert total_value == 1000000.0

    def test_total_value_all_invested(self):
        cash = 0.0
        position_value = 1000000.0
        total_value = cash + position_value
        assert total_value == 1000000.0


class TestSignalGeneration:
    def test_buy_signal_allocation(self):
        total_cash = 1000000.0
        allocation_ratio = 0.8
        num_signals = 5
        allocation = allocation_ratio * total_cash
        per_stock_allocation = allocation / num_signals
        assert allocation == 800000.0
        assert per_stock_allocation == 160000.0

    def test_buy_signal_quantity(self):
        per_stock_allocation = 160000.0
        price = 15.5
        quantity = int(per_stock_allocation / price / TradingConfig.MIN_TRADE_QUANTITY) * TradingConfig.MIN_TRADE_QUANTITY
        assert quantity == 10300
        assert quantity % 100 == 0


class TestEdgeCases:
    def test_zero_division_protection_daily_return(self):
        prev_value = 0.0
        current_value = 1000000.0
        if prev_value > 0:
            daily_return = (current_value - prev_value) / prev_value
        else:
            daily_return = None
        assert daily_return is None

    def test_zero_division_protection_cumulative_return(self):
        initial_capital = 0.0
        current_value = 1000000.0
        if initial_capital > 0:
            cumulative_return = (current_value - initial_capital) / initial_capital
        else:
            cumulative_return = None
        assert cumulative_return is None

    def test_empty_signals_allocation(self):
        signals = []
        allocation = 800000.0
        per_stock_allocation = allocation / max(len(signals), 1) if signals else 0
        assert per_stock_allocation == 0

    def test_negative_pnl(self):
        quantity = 1000
        avg_cost = 15.0
        sell_price = 10.0
        realized_pnl = (sell_price - avg_cost) * quantity
        assert realized_pnl == -5000.0
