from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CacheDataStatus(BaseModel):
    stock_count: int
    record_count: int
    date_range: Optional[tuple[str, str]] = None
    file_size_mb: float
    last_update: Optional[datetime] = None


class CacheStatus(BaseModel):
    ohlcv: Optional[CacheDataStatus] = None
    balance_sheet: Optional[CacheDataStatus] = None
    income: Optional[CacheDataStatus] = None
    cash_flow: Optional[CacheDataStatus] = None
    indicators: Optional[CacheDataStatus] = None
    valuation: Optional[CacheDataStatus] = None
    dividend: Optional[CacheDataStatus] = None


class CacheStats(BaseModel):
    total_stocks: int
    cached_stocks: int
    memory_cache_count: int
    file_cache_exists: bool
    last_update: Optional[datetime] = None
