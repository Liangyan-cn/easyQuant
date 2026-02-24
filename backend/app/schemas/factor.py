from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FactorCategory(str, Enum):
    MOMENTUM = "momentum"
    VALUE = "value"
    QUALITY = "quality"
    GROWTH = "growth"
    VOLATILITY = "volatility"
    LIQUIDITY = "liquidity"
    SIZE = "size"
    TECHNICAL = "technical"
    CUSTOM = "custom"


class FactorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    category: FactorCategory = FactorCategory.CUSTOM
    description: Optional[str] = None
    formula: Optional[str] = None


class FactorCreate(FactorBase):
    pass


class FactorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    category: Optional[FactorCategory] = None
    description: Optional[str] = None
    formula: Optional[str] = None


class FactorResponse(FactorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_builtin: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class FactorListResponse(BaseModel):
    items: List[FactorResponse]
    total: int
    page: int
    size: int


class FactorValueCreate(BaseModel):
    stock_code: str
    date: date
    value: Optional[float] = None


class FactorValueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    factor_id: int
    stock_code: str
    date: datetime
    value: Optional[float] = None


class FactorValueListResponse(BaseModel):
    items: List[FactorValueResponse]
    total: int


class FactorCalculateRequest(BaseModel):
    factor_id: int
    stock_codes: Optional[List[str]] = None
    start_date: date
    end_date: date


class FactorCalculateResponse(BaseModel):
    factor_id: int
    total_stocks: int
    total_dates: int
    calculated_count: int
    status: str


class FactorEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    factor_id: int
    start_date: datetime
    end_date: datetime
    ic_mean: Optional[float] = None
    ic_std: Optional[float] = None
    ir: Optional[float] = None
    ic_positive_ratio: Optional[float] = None
    turnover: Optional[float] = None
    created_at: datetime


class FactorEvaluationRequest(BaseModel):
    factor_id: int
    start_date: date
    end_date: date
    benchmark: Optional[str] = "000300"


class GroupReturnItem(BaseModel):
    group: int
    return_value: float
    stock_count: int


class FactorEvaluationDetailResponse(BaseModel):
    evaluation: FactorEvaluationResponse
    ic_series: List[dict]
    group_returns: List[GroupReturnItem]


class FactorCategoryStats(BaseModel):
    category: FactorCategory
    count: int


class FactorAnalyzeRequest(BaseModel):
    factor_id: int
    start_date: date
    end_date: date
    stock_codes: Optional[List[str]] = None
    force_recalculate: bool = False


class FactorAnalyzeResponse(BaseModel):
    factor_id: int
    calculated_count: int
    evaluation: FactorEvaluationResponse
    ic_series: List[dict]
    group_returns: List[GroupReturnItem]
