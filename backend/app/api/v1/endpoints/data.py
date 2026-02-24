from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.stock import (
    StockHistoryResponse,
    StockListResponse,
    BalanceSheetResponse,
    IncomeStatementResponse,
    CashFlowResponse,
    FinancialIndicatorResponse,
    ValuationResponse,
    DividendResponse,
)
from app.services.data_service import (
    get_stock_history,
    get_stock_list,
    get_balance_sheet,
    get_income_statement,
    get_cash_flow,
    get_financial_indicators,
    get_valuation,
    get_dividend,
)

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


@router.get("/stocks/{code}/balance-sheet", response_model=BalanceSheetResponse)
async def balance_sheet(
    code: str,
    limit: int = Query(8, ge=1, le=20, description="返回记录数量"),
) -> BalanceSheetResponse:
    return get_balance_sheet(code=code, limit=limit)


@router.get("/stocks/{code}/income-statement", response_model=IncomeStatementResponse)
async def income_statement(
    code: str,
    limit: int = Query(8, ge=1, le=20, description="返回记录数量"),
) -> IncomeStatementResponse:
    return get_income_statement(code=code, limit=limit)


@router.get("/stocks/{code}/cash-flow", response_model=CashFlowResponse)
async def cash_flow(
    code: str,
    limit: int = Query(8, ge=1, le=20, description="返回记录数量"),
) -> CashFlowResponse:
    return get_cash_flow(code=code, limit=limit)


@router.get("/stocks/{code}/financial-indicators", response_model=FinancialIndicatorResponse)
async def financial_indicators(
    code: str,
    limit: int = Query(8, ge=1, le=20, description="返回记录数量"),
) -> FinancialIndicatorResponse:
    return get_financial_indicators(code=code, limit=limit)


@router.get("/stocks/{code}/valuation", response_model=ValuationResponse)
async def valuation(
    code: str,
    limit: int = Query(30, ge=1, le=100, description="返回记录数量"),
) -> ValuationResponse:
    return get_valuation(code=code, limit=limit)


@router.get("/stocks/{code}/dividend", response_model=DividendResponse)
async def dividend(
    code: str,
    limit: int = Query(10, ge=1, le=50, description="返回记录数量"),
) -> DividendResponse:
    return get_dividend(code=code, limit=limit)
