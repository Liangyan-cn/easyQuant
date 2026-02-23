from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.stock import StockHistoryResponse, StockListResponse
from app.services.data_service import get_stock_history, get_stock_list

router = APIRouter()


@router.get("/stocks", response_model=StockListResponse)
async def list_stocks(
    keyword: Optional[str] = Query(None, description="搜索关键词（股票代码或名称）"),
    market: Optional[str] = Query(None, description="市场筛选（SH/SZ）"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> StockListResponse:
    return get_stock_list(keyword=keyword, market=market, page=page, size=size)


@router.get("/stocks/{code}/history", response_model=StockHistoryResponse)
async def stock_history(
    code: str,
    period: str = Query("daily", description="周期（daily/weekly/monthly）"),
    start: Optional[date] = Query(None, description="开始日期"),
    end: Optional[date] = Query(None, description="结束日期"),
) -> StockHistoryResponse:
    return get_stock_history(code=code, period=period, start=start, end=end)
