import pytest
import numpy as np
import pandas as pd
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.factor_calculator import FactorCalculator, BUILTIN_FORMULAS
from app.models.factor import Factor, FactorCategory


@pytest.fixture
def sample_df():
    dates = pd.date_range(start="2025-01-01", periods=30, freq="D")
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(30) * 2)
    return pd.DataFrame({
        "date": dates,
        "open": close_prices - np.random.rand(30),
        "high": close_prices + np.random.rand(30) * 2,
        "low": close_prices - np.random.rand(30) * 2,
        "close": close_prices,
        "volume": np.random.randint(1000000, 5000000, 30),
        "returns": pd.Series(close_prices).pct_change(),
    })


@pytest.fixture
def mock_factor_momentum():
    factor = MagicMock(spec=Factor)
    factor.id = 1
    factor.code = "momentum_20d"
    factor.name = "20日动量"
    factor.formula = "(close - close.shift(20)) / close.shift(20)"
    factor.category = FactorCategory.MOMENTUM
    return factor


@pytest.fixture
def mock_factor_volatility():
    factor = MagicMock(spec=Factor)
    factor.id = 2
    factor.code = "volatility_20d"
    factor.name = "20日波动率"
    factor.formula = "returns.rolling(20).std()"
    factor.category = FactorCategory.VOLATILITY
    return factor


@pytest.fixture
def mock_factor_custom():
    factor = MagicMock(spec=Factor)
    factor.id = 3
    factor.code = "custom_factor"
    factor.name = "自定义因子"
    factor.formula = "(high - low) / close"
    factor.category = FactorCategory.CUSTOM
    return factor


class TestBuiltinFormulas:
    def test_momentum_20d_formula_exists(self):
        assert "momentum_20d" in BUILTIN_FORMULAS
        assert "close.shift(20)" in BUILTIN_FORMULAS["momentum_20d"]

    def test_momentum_60d_formula_exists(self):
        assert "momentum_60d" in BUILTIN_FORMULAS
        assert "close.shift(60)" in BUILTIN_FORMULAS["momentum_60d"]

    def test_volatility_20d_formula_exists(self):
        assert "volatility_20d" in BUILTIN_FORMULAS
        assert "rolling(20).std()" in BUILTIN_FORMULAS["volatility_20d"]

    def test_turnover_rate_formula_exists(self):
        assert "turnover_rate" in BUILTIN_FORMULAS
        assert "volume" in BUILTIN_FORMULAS["turnover_rate"]

    def test_log_market_cap_formula_exists(self):
        assert "log_market_cap" in BUILTIN_FORMULAS
        assert "np.log" in BUILTIN_FORMULAS["log_market_cap"]


class TestMomentumCalculation:
    def test_momentum_20d_calculation(self, sample_df):
        close = sample_df["close"]
        momentum = (close - close.shift(20)) / close.shift(20)
        assert len(momentum) == 30
        assert pd.isna(momentum.iloc[:20]).all()
        assert not pd.isna(momentum.iloc[20:]).any()

    def test_momentum_60d_calculation(self, sample_df):
        close = sample_df["close"]
        momentum = (close - close.shift(60)) / close.shift(60)
        assert len(momentum) == 30
        assert pd.isna(momentum).all()

    def test_momentum_positive(self):
        close = pd.Series([100, 105, 110, 115, 120])
        momentum = (close - close.shift(2)) / close.shift(2)
        assert momentum.iloc[2] == pytest.approx(0.1, rel=1e-6)
        assert momentum.iloc[3] == pytest.approx(0.095238, rel=1e-4)

    def test_momentum_negative(self):
        close = pd.Series([100, 95, 90, 85, 80])
        momentum = (close - close.shift(2)) / close.shift(2)
        assert momentum.iloc[2] == pytest.approx(-0.1, rel=1e-6)
        assert momentum.iloc[3] == pytest.approx(-0.105263, rel=1e-4)


class TestVolatilityCalculation:
    def test_volatility_20d_calculation(self, sample_df):
        returns = sample_df["returns"]
        volatility = returns.rolling(20).std()
        assert len(volatility) == 30
        assert pd.isna(volatility.iloc[:20]).all()
        assert not pd.isna(volatility.iloc[20:]).any()

    def test_volatility_positive(self):
        returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02])
        volatility = returns.rolling(3).std()
        assert volatility.iloc[2] > 0
        assert volatility.iloc[3] > 0

    def test_volatility_zero_for_constant(self):
        returns = pd.Series([0.01, 0.01, 0.01, 0.01, 0.01])
        volatility = returns.rolling(3).std()
        assert volatility.iloc[2] == pytest.approx(0, abs=1e-10)


class TestTurnoverCalculation:
    def test_turnover_rate_calculation(self, sample_df):
        volume = sample_df["volume"]
        turnover = volume / volume.rolling(20).mean()
        assert len(turnover) == 30
        assert pd.isna(turnover.iloc[:19]).all()
        assert not pd.isna(turnover.iloc[19:]).any()

    def test_turnover_above_average(self):
        volume = pd.Series([100, 100, 100, 200])
        turnover = volume / volume.rolling(3).mean()
        assert turnover.iloc[3] > 1.0

    def test_turnover_below_average(self):
        volume = pd.Series([200, 200, 200, 100])
        turnover = volume / volume.rolling(3).mean()
        assert turnover.iloc[3] < 1.0


class TestLogMarketCapCalculation:
    def test_log_market_cap_calculation(self, sample_df):
        log_cap = np.log(sample_df["close"] * sample_df["volume"])
        assert len(log_cap) == 30
        assert not pd.isna(log_cap).any()
        assert (log_cap > 0).all()

    def test_log_market_cap_increases_with_price(self):
        close1 = pd.Series([100])
        close2 = pd.Series([200])
        volume = pd.Series([1000000])
        log_cap1 = np.log(close1 * volume)
        log_cap2 = np.log(close2 * volume)
        assert log_cap2.iloc[0] > log_cap1.iloc[0]


class TestCustomFormulaCalculation:
    def test_custom_formula_high_low_range(self, sample_df):
        result = (sample_df["high"] - sample_df["low"]) / sample_df["close"]
        assert len(result) == 30
        assert (result >= 0).all()

    def test_custom_formula_with_numpy(self, sample_df):
        result = np.log(sample_df["close"])
        assert len(result) == 30
        assert not pd.isna(result).any()

    def test_custom_formula_with_rolling(self, sample_df):
        result = sample_df["close"].rolling(5).mean()
        assert len(result) == 30
        assert pd.isna(result.iloc[:4]).all()
        assert not pd.isna(result.iloc[4:]).any()


class TestFactorCalculatorApplyFormula:
    def test_apply_formula_momentum_20d(self, sample_df, mock_factor_momentum):
        mock_db = AsyncMock()
        calculator = FactorCalculator(mock_db)
        result = calculator._apply_formula(mock_factor_momentum, sample_df)
        assert isinstance(result, pd.Series)
        assert len(result) == 30

    def test_apply_formula_volatility_20d(self, sample_df, mock_factor_volatility):
        mock_db = AsyncMock()
        calculator = FactorCalculator(mock_db)
        result = calculator._apply_formula(mock_factor_volatility, sample_df)
        assert isinstance(result, pd.Series)
        assert len(result) == 30

    def test_apply_formula_custom(self, sample_df, mock_factor_custom):
        mock_db = AsyncMock()
        calculator = FactorCalculator(mock_db)
        result = calculator._apply_formula(mock_factor_custom, sample_df)
        assert isinstance(result, pd.Series)
        assert len(result) == 30


class TestCustomFormulaEvaluation:
    def test_calculate_custom_formula_valid(self, sample_df):
        mock_db = AsyncMock()
        calculator = FactorCalculator(mock_db)
        result = calculator._calculate_custom_formula("close / open", sample_df)
        assert isinstance(result, pd.Series)
        assert len(result) == 30
        assert not pd.isna(result).any()

    def test_calculate_custom_formula_with_numpy(self, sample_df):
        mock_db = AsyncMock()
        calculator = FactorCalculator(mock_db)
        result = calculator._calculate_custom_formula("np.log(close)", sample_df)
        assert isinstance(result, pd.Series)
        assert len(result) == 30

    def test_calculate_custom_formula_invalid(self, sample_df):
        mock_db = AsyncMock()
        calculator = FactorCalculator(mock_db)
        result = calculator._calculate_custom_formula("invalid_variable", sample_df)
        assert isinstance(result, pd.Series)
        assert pd.isna(result).all()

    def test_calculate_custom_formula_empty(self, sample_df):
        mock_db = AsyncMock()
        calculator = FactorCalculator(mock_db)
        result = calculator._calculate_custom_formula("", sample_df)
        assert isinstance(result, pd.Series)
        assert pd.isna(result).all()

    def test_calculate_custom_formula_none(self, sample_df):
        mock_db = AsyncMock()
        calculator = FactorCalculator(mock_db)
        result = calculator._calculate_custom_formula(None, sample_df)
        assert isinstance(result, pd.Series)
        assert pd.isna(result).all()


class TestEdgeCases:
    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume", "returns"])
        mock_db = AsyncMock()
        calculator = FactorCalculator(mock_db)
        result = calculator._calculate_custom_formula("close / open", df)
        assert len(result) == 0

    def test_single_row_dataframe(self):
        df = pd.DataFrame({
            "date": [date.today()],
            "open": [100.0],
            "high": [105.0],
            "low": [95.0],
            "close": [102.0],
            "volume": [1000000],
            "returns": [0.02],
        })
        mock_db = AsyncMock()
        calculator = FactorCalculator(mock_db)
        result = calculator._calculate_custom_formula("close / open", df)
        assert len(result) == 1
        assert result.iloc[0] == pytest.approx(1.02, rel=1e-6)

    def test_division_by_zero_protection(self):
        df = pd.DataFrame({
            "date": [date.today()],
            "open": [0.0],
            "high": [105.0],
            "low": [95.0],
            "close": [102.0],
            "volume": [1000000],
            "returns": [0.02],
        })
        mock_db = AsyncMock()
        calculator = FactorCalculator(mock_db)
        result = calculator._calculate_custom_formula("close / open", df)
        assert len(result) == 1
        assert result.iloc[0] == float("inf") or pd.isna(result.iloc[0])

    def test_negative_values(self):
        df = pd.DataFrame({
            "date": [date.today()],
            "open": [100.0],
            "high": [105.0],
            "low": [95.0],
            "close": [98.0],
            "volume": [1000000],
            "returns": [-0.02],
        })
        mock_db = AsyncMock()
        calculator = FactorCalculator(mock_db)
        result = calculator._calculate_custom_formula("returns", df)
        assert result.iloc[0] == -0.02


class TestFactorCalculatorAsync:
    @pytest.mark.asyncio
    async def test_calculate_factor_not_found(self):
        mock_db = AsyncMock()
        calculator = FactorCalculator(mock_db)
        calculator.factor_repo = AsyncMock()
        calculator.factor_repo.get_by_id = AsyncMock(return_value=None)

        from app.schemas.factor import FactorCalculateRequest
        request = FactorCalculateRequest(
            factor_id=999,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
        )

        with pytest.raises(ValueError, match="not found"):
            await calculator.calculate_factor(request)
