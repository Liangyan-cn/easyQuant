from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.sandbox import DeploymentStatus, SandboxStatus, TransactionType


class SandboxAccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    initial_capital: float = Field(default=1000000.0, ge=10000, le=100000000)


class SandboxAccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[SandboxStatus] = None


class SandboxAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    description: Optional[str]
    initial_capital: float
    current_cash: float
    total_value: float
    status: SandboxStatus
    created_at: datetime
    updated_at: datetime


class SandboxAccountListResponse(BaseModel):
    items: List[SandboxAccountResponse]
    total: int
    page: int
    size: int


class SandboxPositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    stock_code: str
    stock_name: Optional[str]
    quantity: int
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float
    updated_at: datetime


class SandboxTransactionCreate(BaseModel):
    transaction_type: TransactionType
    stock_code: Optional[str] = None
    stock_name: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[float] = None
    amount: float
    description: Optional[str] = None


class SandboxTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    deployment_id: Optional[int]
    transaction_type: TransactionType
    stock_code: Optional[str]
    stock_name: Optional[str]
    quantity: Optional[int]
    price: Optional[float]
    amount: float
    commission: float
    description: Optional[str]
    created_at: datetime


class SandboxDeploymentCreate(BaseModel):
    strategy_id: int
    name: str = Field(..., min_length=1, max_length=100)
    start_date: date
    end_date: Optional[date] = None
    stock_pool: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    allocation_ratio: float = Field(default=1.0, ge=0.0, le=1.0)


class SandboxDeploymentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[DeploymentStatus] = None
    end_date: Optional[date] = None
    stock_pool: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    allocation_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)


class SandboxDeploymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    strategy_id: int
    name: str
    status: DeploymentStatus
    start_date: date
    end_date: Optional[date]
    stock_pool: Optional[List[str]]
    parameters: Optional[Dict[str, Any]]
    allocation_ratio: float
    last_run_date: Optional[date]
    last_run_result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime


class SandboxDailyValueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    date: date
    total_value: float
    cash: float
    position_value: float
    daily_return: Optional[float]
    cumulative_return: Optional[float]
    benchmark_return: Optional[float]


class SandboxAccountDetailResponse(BaseModel):
    account: SandboxAccountResponse
    positions: List[SandboxPositionResponse]
    recent_transactions: List[SandboxTransactionResponse]
    deployments: List[SandboxDeploymentResponse]
    daily_values: List[SandboxDailyValueResponse]


class DepositRequest(BaseModel):
    amount: float = Field(..., gt=0, le=100000000)
    description: Optional[str] = None


class ResetAccountRequest(BaseModel):
    initial_capital: float = Field(default=1000000.0, ge=10000, le=100000000)


class StrategyCompareRequest(BaseModel):
    deployment_ids: List[int] = Field(..., min_length=2, max_length=10)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class StrategyCompareItem(BaseModel):
    deployment_id: int
    strategy_name: str
    total_return: Optional[float]
    annual_return: Optional[float]
    max_drawdown: Optional[float]
    sharpe_ratio: Optional[float]
    volatility: Optional[float]
    win_rate: Optional[float]
    total_trades: int
    daily_values: List[Dict[str, Any]]


class StrategyCompareResponse(BaseModel):
    items: List[StrategyCompareItem]
    start_date: date
    end_date: date


class RunDeploymentRequest(BaseModel):
    run_date: Optional[date] = None
