from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StrategyType(str, Enum):
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    TREND_FOLLOWING = "trend_following"
    FACTOR_BASED = "factor_based"
    CUSTOM = "custom"


class StrategyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class BacktestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class StrategyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    strategy_type: StrategyType = StrategyType.CUSTOM
    description: Optional[str] = None
    logic: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    strategy_type: Optional[StrategyType] = None
    status: Optional[StrategyStatus] = None
    description: Optional[str] = None
    logic: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class StrategyResponse(StrategyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: StrategyStatus
    is_builtin: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class StrategyListResponse(BaseModel):
    items: List[StrategyResponse]
    total: int
    page: int
    size: int


class BacktestCreate(BaseModel):
    strategy_id: int
    name: Optional[str] = None
    start_date: date
    end_date: date
    initial_capital: float = Field(default=1000000.0, gt=0)
    commission_rate: float = Field(default=0.0003, ge=0, le=0.01)
    slippage: float = Field(default=0.001, ge=0, le=0.05)
    benchmark: Optional[str] = "000300"
    stock_pool: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None


class BacktestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    strategy_id: int
    name: Optional[str] = None
    status: BacktestStatus
    start_date: datetime
    end_date: datetime
    initial_capital: float
    commission_rate: float
    slippage: float
    benchmark: Optional[str] = None
    stock_pool: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class BacktestListResponse(BaseModel):
    items: List[BacktestResponse]
    total: int


class BacktestResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    backtest_id: int
    total_return: Optional[float] = None
    annual_return: Optional[float] = None
    benchmark_return: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    volatility: Optional[float] = None
    win_rate: Optional[float] = None
    profit_loss_ratio: Optional[float] = None
    total_trades: Optional[int] = None
    avg_holding_days: Optional[float] = None
    created_at: datetime


class EquityCurvePoint(BaseModel):
    date: str
    equity: float
    benchmark: Optional[float] = None


class BacktestDetailResponse(BaseModel):
    backtest: BacktestResponse
    result: Optional[BacktestResultResponse] = None
    equity_curve: Optional[List[EquityCurvePoint]] = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    backtest_id: int
    stock_code: str
    side: OrderSide
    quantity: int
    price: float
    filled_price: Optional[float] = None
    filled_quantity: Optional[int] = None
    commission: Optional[float] = None
    order_time: datetime
    filled_time: Optional[datetime] = None
    signal_reason: Optional[str] = None


class OrderListResponse(BaseModel):
    items: List[OrderResponse]
    total: int


class PositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    backtest_id: int
    stock_code: str
    quantity: int
    avg_cost: float
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None


class PositionListResponse(BaseModel):
    items: List[PositionResponse]
    total: int


class StrategyTypeStats(BaseModel):
    strategy_type: StrategyType
    count: int
