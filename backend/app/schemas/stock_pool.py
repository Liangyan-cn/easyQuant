from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StockPoolType(str, Enum):
    SYSTEM = "system"
    USER = "user"


class StockPoolItemInput(BaseModel):
    stock_code: str = Field(..., min_length=1, max_length=20)
    stock_name: Optional[str] = None


class StockPoolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z0-9_]+$")
    description: Optional[str] = None
    initial_stocks: Optional[List[StockPoolItemInput]] = None


class StockPoolUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class StockPoolItemCreate(BaseModel):
    stock_code: str = Field(..., min_length=1, max_length=20)
    stock_name: Optional[str] = None


class ImportIndexRequest(BaseModel):
    index_code: str = Field(..., description="指数代码，如 000300")


class StockPoolItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    stock_code: str
    stock_name: Optional[str]
    added_at: datetime


class StockPoolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str
    pool_type: StockPoolType
    description: Optional[str]
    stock_count: int = 0
    created_at: datetime
    updated_at: datetime


class StockPoolDetailResponse(StockPoolResponse):
    items: List[StockPoolItemResponse] = []


class StockPoolListResponse(BaseModel):
    items: List[StockPoolResponse]
    total: int
    page: int
    size: int
