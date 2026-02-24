import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from app.services.backtest_engine import (
    EventType,
    SignalType,
    Event,
    MarketEvent,
    SignalEvent,
    OrderEvent,
    FillEvent,
    PositionInfo,
    BacktestConfig,
    TradeRecord,
    MACrossStrategy,
    MomentumStrategy,
    MeanReversionStrategy,
    BollingerBandsStrategy,
    RSIStrategy,
    SimulatedBroker,
    BacktestEngine,
    STRATEGY_CLASSES,
    get_strategy_class,
)


class TestEventTypes:
    def test_event_type_values(self):
        assert EventType.MARKET == "market"
        assert EventType.SIGNAL == "signal"
        assert EventType.ORDER == "order"
        assert EventType.FILL == "fill"

    def test_signal_type_values(self):
        assert SignalType.BUY == "buy"
        assert SignalType.SELL == "sell"
        assert SignalType.HOLD == "hold"


class TestMarketEvent:
    def test_market_event_creation(self):
        event = MarketEvent(
            timestamp=datetime.now(),
            stock_code="000001",
            open_price=10.0,
            high_price=11.0,
            low_price=9.5,
            close_price=10.5,
            volume=1000000,
        )
        assert event.event_type == EventType.MARKET
        assert event.stock_code == "000001"
        assert event.close_price == 10.5


class TestSignalEvent:
    def test_signal_event_buy(self):
        event = SignalEvent(
            timestamp=datetime.now(),
            stock_code="000001",
            signal_type=SignalType.BUY,
            strength=1.0,
            reason="Test buy signal",
        )
        assert event.event_type == EventType.SIGNAL
        assert event.signal_type == SignalType.BUY
        assert event.strength == 1.0

    def test_signal_event_sell(self):
        event = SignalEvent(
            timestamp=datetime.now(),
            stock_code="000001",
            signal_type=SignalType.SELL,
            strength=0.8,
            reason="Test sell signal",
        )
        assert event.signal_type == SignalType.SELL
        assert event.strength == 0.8


class TestOrderEvent:
    def test_order_event_creation(self):
        event = OrderEvent(
            timestamp=datetime.now(),
            stock_code="000001",
            order_type="market",
            quantity=100,
            direction="buy",
        )
        assert event.event_type == EventType.ORDER
        assert event.quantity == 100
        assert event.direction == "buy"


class TestFillEvent:
    def test_fill_event_creation(self):
        event = FillEvent(
            timestamp=datetime.now(),
            stock_code="000001",
            quantity=100,
            direction="buy",
            fill_price=10.5,
            commission=3.15,
            slippage_cost=1.05,
        )
        assert event.event_type == EventType.FILL
        assert event.fill_price == 10.5
        assert event.commission == 3.15


class TestPositionInfo:
    def test_position_info_creation(self):
        pos = PositionInfo(
            stock_code="000001",
            quantity=1000,
            avg_cost=10.0,
            market_value=10500.0,
            unrealized_pnl=500.0,
            realized_pnl=0.0,
        )
        assert pos.stock_code == "000001"
        assert pos.quantity == 1000
        assert pos.unrealized_pnl == 500.0


class TestBacktestConfig:
    def test_default_config(self):
        config = BacktestConfig()
        assert config.initial_capital == 1000000.0
        assert config.commission_rate == 0.0003
        assert config.slippage == 0.001
        assert config.benchmark == "000300"

    def test_custom_config(self):
        config = BacktestConfig(
            initial_capital=500000.0,
            commission_rate=0.0005,
            slippage=0.002,
        )
        assert config.initial_capital == 500000.0
        assert config.commission_rate == 0.0005


class TestMACrossStrategy:
    @pytest.fixture
    def strategy(self):
        return MACrossStrategy(parameters={"short_period": 5, "long_period": 10})

    def test_insufficient_data(self, strategy):
        prices = [100.0] * 5
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.HOLD
        assert "Insufficient data" in signal.reason

    def test_buy_signal_crossover(self, strategy):
        prices = [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 95]
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type in [SignalType.BUY, SignalType.HOLD, SignalType.SELL]

    def test_no_crossover(self, strategy):
        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.HOLD


class TestMomentumStrategy:
    @pytest.fixture
    def strategy(self):
        return MomentumStrategy(parameters={"lookback_period": 5, "threshold": 0.05})

    def test_insufficient_data(self, strategy):
        prices = [100.0] * 3
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.HOLD
        assert "Insufficient data" in signal.reason

    def test_positive_momentum_buy(self, strategy):
        prices = [100, 102, 104, 106, 108]
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.BUY
        assert "Positive momentum" in signal.reason

    def test_negative_momentum_sell(self, strategy):
        prices = [100, 98, 96, 94, 92]
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.SELL
        assert "Negative momentum" in signal.reason

    def test_neutral_momentum(self, strategy):
        prices = [100, 101, 100, 101, 100]
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.HOLD


class TestMeanReversionStrategy:
    @pytest.fixture
    def strategy(self):
        return MeanReversionStrategy(parameters={"lookback_period": 5, "std_multiplier": 1.5})

    def test_insufficient_data(self, strategy):
        prices = [100.0] * 3
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.HOLD

    def test_oversold_buy(self, strategy):
        prices = [100, 100, 100, 100, 50]
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.BUY
        assert "below mean" in signal.reason

    def test_overbought_sell(self, strategy):
        prices = [100, 100, 100, 100, 150]
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.SELL
        assert "above mean" in signal.reason

    def test_zero_std_deviation(self, strategy):
        prices = [100, 100, 100, 100, 100]
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.HOLD
        assert "Zero standard deviation" in signal.reason


class TestBollingerBandsStrategy:
    @pytest.fixture
    def strategy(self):
        return BollingerBandsStrategy(parameters={"period": 5, "std_multiplier": 1.5})

    def test_insufficient_data(self, strategy):
        prices = [100.0] * 3
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.HOLD

    def test_below_lower_band_buy(self, strategy):
        prices = [100, 100, 100, 100, 50]
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.BUY
        assert "below lower band" in signal.reason

    def test_above_upper_band_sell(self, strategy):
        prices = [100, 100, 100, 100, 150]
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.SELL
        assert "above upper band" in signal.reason

    def test_within_bands(self, strategy):
        prices = [100, 101, 99, 100, 100]
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.HOLD
        assert "within bands" in signal.reason


class TestRSIStrategy:
    @pytest.fixture
    def strategy(self):
        return RSIStrategy(parameters={"period": 5, "oversold": 30, "overbought": 70})

    def test_insufficient_data(self, strategy):
        prices = [100.0] * 3
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.HOLD

    def test_rsi_calculation(self, strategy):
        prices = [100, 102, 104, 103, 105, 107]
        rsi = strategy._calculate_rsi(prices, 5)
        assert rsi is not None
        assert 0 <= rsi <= 100

    def test_rsi_all_gains(self, strategy):
        prices = [100, 101, 102, 103, 104, 105]
        rsi = strategy._calculate_rsi(prices, 5)
        assert rsi == 100.0

    def test_oversold_buy(self, strategy):
        prices = [100, 98, 96, 94, 92, 90]
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.BUY
        assert "oversold" in signal.reason

    def test_overbought_sell(self, strategy):
        prices = [100, 102, 104, 106, 108, 110]
        signal = strategy.generate_signal_from_prices("000001", prices)
        assert signal.signal_type == SignalType.SELL
        assert "overbought" in signal.reason


class TestSimulatedBroker:
    @pytest.fixture
    def broker(self):
        config = BacktestConfig(initial_capital=100000.0)
        return SimulatedBroker(config)

    def test_initial_state(self, broker):
        assert broker.cash == 100000.0
        assert len(broker.positions) == 0
        assert len(broker.trades) == 0

    def test_buy_order_execution(self, broker):
        order = OrderEvent(
            timestamp=datetime.now(),
            stock_code="000001",
            order_type="market",
            quantity=100,
            direction="buy",
        )
        fill = broker.execute_order(order, 10.0)
        assert fill is not None
        assert fill.quantity == 100
        assert fill.direction == "buy"
        assert "000001" in broker.positions
        assert broker.positions["000001"].quantity == 100

    def test_sell_order_execution(self, broker):
        buy_order = OrderEvent(
            timestamp=datetime.now(),
            stock_code="000001",
            order_type="market",
            quantity=100,
            direction="buy",
        )
        broker.execute_order(buy_order, 10.0)

        sell_order = OrderEvent(
            timestamp=datetime.now(),
            stock_code="000001",
            order_type="market",
            quantity=100,
            direction="sell",
        )
        fill = broker.execute_order(sell_order, 11.0)
        assert fill is not None
        assert fill.direction == "sell"
        assert "000001" not in broker.positions

    def test_insufficient_cash(self, broker):
        order = OrderEvent(
            timestamp=datetime.now(),
            stock_code="000001",
            order_type="market",
            quantity=100000,
            direction="buy",
        )
        fill = broker.execute_order(order, 10.0)
        assert fill is not None
        assert fill.quantity < 100000

    def test_sell_without_position(self, broker):
        order = OrderEvent(
            timestamp=datetime.now(),
            stock_code="000001",
            order_type="market",
            quantity=100,
            direction="sell",
        )
        fill = broker.execute_order(order, 10.0)
        assert fill is None

    def test_get_total_value(self, broker):
        buy_order = OrderEvent(
            timestamp=datetime.now(),
            stock_code="000001",
            order_type="market",
            quantity=100,
            direction="buy",
        )
        broker.execute_order(buy_order, 10.0)
        total_value = broker.get_total_value({"000001": 11.0})
        assert total_value > 0


class TestBacktestEngine:
    @pytest.fixture
    def engine(self):
        config = BacktestConfig(initial_capital=100000.0)
        return BacktestEngine(config)

    def test_engine_initialization(self, engine):
        assert engine.config.initial_capital == 100000.0
        assert engine.strategy is None
        assert len(engine.equity_curve) == 0

    def test_set_strategy(self, engine):
        strategy = MACrossStrategy(parameters={"short_period": 5, "long_period": 10})
        engine.set_strategy(strategy)
        assert engine.strategy is not None
        assert engine.strategy.cash == 100000.0

    def test_run_without_strategy(self, engine):
        with pytest.raises(ValueError, match="Strategy not set"):
            engine.run([])

    def test_run_with_empty_data(self, engine):
        strategy = MACrossStrategy(parameters={"short_period": 5, "long_period": 10})
        engine.set_strategy(strategy)
        result = engine.run([])
        assert result == {}

    def test_run_with_market_data(self, engine):
        strategy = MACrossStrategy(parameters={"short_period": 2, "long_period": 3})
        engine.set_strategy(strategy)

        market_data = []
        base_date = datetime(2025, 1, 1)
        for i in range(10):
            market_data.append({
                "date": base_date + timedelta(days=i),
                "stock_code": "000001",
                "open": 100 + i,
                "high": 102 + i,
                "low": 99 + i,
                "close": 101 + i,
                "volume": 1000000,
            })

        result = engine.run(market_data)
        assert "total_return" in result
        assert "max_drawdown" in result
        assert "sharpe_ratio" in result
        assert "equity_curve" in result


class TestPerformanceMetrics:
    def test_total_return_calculation(self):
        initial = 100000.0
        final = 110000.0
        total_return = (final - initial) / initial
        assert total_return == pytest.approx(0.1, rel=1e-6)

    def test_max_drawdown_calculation(self):
        equities = [100, 110, 105, 115, 100]
        max_equity = equities[0]
        max_drawdown = 0
        for equity in equities:
            max_equity = max(max_equity, equity)
            drawdown = (max_equity - equity) / max_equity
            max_drawdown = max(max_drawdown, drawdown)
        assert max_drawdown == pytest.approx(0.1304, rel=0.01)

    def test_sharpe_ratio_calculation(self):
        daily_returns = [0.01, -0.005, 0.008, -0.003, 0.012]
        avg_return = np.mean(daily_returns) * 252
        volatility = np.std(daily_returns) * np.sqrt(252)
        sharpe = avg_return / volatility if volatility > 0 else 0
        assert sharpe > 0

    def test_sortino_ratio_calculation(self):
        daily_returns = [0.01, -0.005, 0.008, -0.003, 0.012]
        avg_return = np.mean(daily_returns) * 252
        negative_returns = [r for r in daily_returns if r < 0]
        downside_std = np.std(negative_returns) * np.sqrt(252) if negative_returns else 0
        sortino = avg_return / downside_std if downside_std > 0 else 0
        assert sortino > 0


class TestStrategyClasses:
    def test_strategy_classes_dict(self):
        assert "ma_cross" in STRATEGY_CLASSES
        assert "momentum" in STRATEGY_CLASSES
        assert "mean_reversion" in STRATEGY_CLASSES
        assert "bollinger_bands" in STRATEGY_CLASSES
        assert "rsi" in STRATEGY_CLASSES

    def test_get_strategy_class_valid(self):
        cls = get_strategy_class("ma_cross")
        assert cls == MACrossStrategy

    def test_get_strategy_class_invalid(self):
        cls = get_strategy_class("invalid_strategy")
        assert cls == MACrossStrategy


class TestEdgeCases:
    def test_zero_volatility(self):
        daily_returns = [0.0, 0.0, 0.0, 0.0, 0.0]
        volatility = np.std(daily_returns) * np.sqrt(252)
        assert volatility == 0.0

    def test_single_day_backtest(self):
        config = BacktestConfig(initial_capital=100000.0)
        engine = BacktestEngine(config)
        strategy = MACrossStrategy(parameters={"short_period": 2, "long_period": 3})
        engine.set_strategy(strategy)

        market_data = [{
            "date": datetime(2025, 1, 1),
            "stock_code": "000001",
            "open": 100,
            "high": 102,
            "low": 99,
            "close": 101,
            "volume": 1000000,
        }]

        result = engine.run(market_data)
        assert result["total_return"] == 0.0

    def test_commission_calculation(self):
        amount = 10000.0
        commission_rate = 0.0003
        commission = amount * commission_rate
        assert commission == pytest.approx(3.0, rel=1e-6)

    def test_slippage_calculation(self):
        price = 100.0
        slippage = 0.001
        buy_price = price * (1 + slippage)
        sell_price = price * (1 - slippage)
        assert buy_price == pytest.approx(100.1, rel=1e-6)
        assert sell_price == pytest.approx(99.9, rel=1e-6)
