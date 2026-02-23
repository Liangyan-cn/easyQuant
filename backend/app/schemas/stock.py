from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class StockInfo(BaseModel):
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: str = Field(..., description="市场（SH/SZ）")
    industry: Optional[str] = Field(None, description="所属行业")


class StockListResponse(BaseModel):
    items: list[StockInfo]
    total: int
    page: int
    size: int


class OHLCVItem(BaseModel):
    date: date = Field(..., description="日期")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")
    amount: float = Field(..., description="成交额")


class StockHistoryResponse(BaseModel):
    code: str = Field(..., description="股票代码")
    period: str = Field(..., description="周期（daily/weekly/monthly）")
    items: list[OHLCVItem]
