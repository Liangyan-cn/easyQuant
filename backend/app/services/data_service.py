import logging
from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd

from app.services.cache_service import CacheService
from app.services.rate_limiter import akshare_api, get_akshare_limiter
from app.schemas.stock import (
    BalanceSheetItem,
    BalanceSheetResponse,
    CashFlowItem,
    CashFlowResponse,
    DividendItem,
    DividendResponse,
    FinancialIndicatorItem,
    FinancialIndicatorResponse,
    IncomeStatementItem,
    IncomeStatementResponse,
    OHLCVItem,
    StockHistoryResponse,
    StockInfo,
    StockListResponse,
    ValuationItem,
    ValuationResponse,
)

logger = logging.getLogger(__name__)

_stock_list_cache: Optional[list[StockInfo]] = None
_stock_list_cache_time: Optional[datetime] = None
_history_cache: dict[str, tuple[datetime, StockHistoryResponse]] = {}

_balance_sheet_cache: dict[str, tuple[datetime, BalanceSheetResponse]] = {}
_income_cache: dict[str, tuple[datetime, IncomeStatementResponse]] = {}
_cash_flow_cache: dict[str, tuple[datetime, CashFlowResponse]] = {}
_indicators_cache: dict[str, tuple[datetime, FinancialIndicatorResponse]] = {}
_valuation_cache: dict[str, tuple[datetime, ValuationResponse]] = {}
_dividend_cache: dict[str, tuple[datetime, DividendResponse]] = {}

CACHE_TTL_SECONDS = 300
FINANCIAL_CACHE_TTL_SECONDS = 3600


@akshare_api(timeout=60.0, max_retries=3)
def _fetch_stock_list_from_akshare() -> list[StockInfo]:
    import akshare as ak
    
    df = ak.stock_info_a_code_name()
    stocks = []
    for _, row in df.iterrows():
        code = str(row["code"])
        market = "SH" if code.startswith("6") else "SZ"
        stocks.append(StockInfo(
            code=code,
            name=row["name"],
            market=market,
            industry=None,
        ))
    logger.info(f"Fetched {len(stocks)} stocks from AKShare")
    return stocks


@akshare_api(timeout=30.0, max_retries=3)
def _fetch_history_from_akshare(
    code: str, period: str, start: date, end: date
) -> list[OHLCVItem]:
    import akshare as ak
    
    period_map = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}
    ak_period = period_map.get(period, "daily")
    
    df = ak.stock_zh_a_hist(
        symbol=code,
        period=ak_period,
        start_date=start.strftime("%Y%m%d"),
        end_date=end.strftime("%Y%m%d"),
        adjust="qfq",
    )
    
    items = []
    for _, row in df.iterrows():
        items.append(OHLCVItem(
            date=datetime.strptime(str(row["日期"]), "%Y-%m-%d").date(),
            open=float(row["开盘"]),
            high=float(row["最高"]),
            low=float(row["最低"]),
            close=float(row["收盘"]),
            volume=float(row["成交量"]),
            amount=float(row["成交额"]),
        ))
    logger.debug(f"Fetched {len(items)} history records for {code}")
    return items


def _is_cache_valid(cache_time: Optional[datetime]) -> bool:
    if cache_time is None:
        return False
    return (datetime.now() - cache_time).total_seconds() < CACHE_TTL_SECONDS


_pool_stocks_cache: dict[str, tuple[datetime, set[str]]] = {}


def _get_pool_stocks_from_json(pool_code: str) -> Optional[set[str]]:
    import json
    from pathlib import Path
    
    index_file = Path(__file__).parent.parent / "data" / "index_stocks.json"
    if index_file.exists():
        with open(index_file, "r") as f:
            data = json.load(f)
            if pool_code in data:
                return set(data[pool_code])
    return None


def _get_pool_stocks_from_db(pool_code: str) -> Optional[set[str]]:
    try:
        from sqlalchemy import create_engine, text
        from app.config import settings
        
        db_url = settings.DATABASE_URL.replace("+asyncpg", "").replace("postgresql://", "postgresql+psycopg2://")
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT spi.stock_code 
                FROM stock_pool_items spi
                JOIN stock_pools sp ON sp.id = spi.pool_id
                WHERE sp.code = :pool_code
            """), {"pool_code": pool_code})
            stocks = {row[0] for row in result}
            return stocks if stocks else None
    except Exception as e:
        logger.warning(f"Failed to get pool stocks from DB: {e}")
        return None


def _get_pool_stocks(pool_code: str) -> set[str]:
    if pool_code in _pool_stocks_cache:
        cache_time, cached_stocks = _pool_stocks_cache[pool_code]
        if _is_cache_valid(cache_time):
            return cached_stocks
    
    stocks = _get_pool_stocks_from_json(pool_code)
    if stocks is None:
        stocks = _get_pool_stocks_from_db(pool_code)
    
    if stocks:
        _pool_stocks_cache[pool_code] = (datetime.now(), stocks)
        return stocks
    
    return set()


def get_stock_list(
    keyword: Optional[str] = None,
    market: Optional[str] = None,
    pool_code: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> StockListResponse:
    global _stock_list_cache, _stock_list_cache_time
    
    if not _is_cache_valid(_stock_list_cache_time) or _stock_list_cache is None:
        _stock_list_cache = _fetch_stock_list_from_akshare()
        _stock_list_cache_time = datetime.now()
    
    filtered = _stock_list_cache
    
    if pool_code:
        pool_stocks = _get_pool_stocks(pool_code)
        if pool_stocks:
            filtered = [s for s in filtered if s.code in pool_stocks]
    
    if keyword:
        keyword_lower = keyword.lower()
        filtered = [
            s for s in filtered
            if keyword_lower in s.code.lower() or keyword_lower in s.name.lower()
        ]
    
    if market:
        market_upper = market.upper()
        filtered = [s for s in filtered if s.market == market_upper]
    
    total = len(filtered)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    items = filtered[start_idx:end_idx]
    
    return StockListResponse(items=items, total=total, page=page, size=size)


def get_stock_history(
    code: str,
    period: str = "daily",
    start: Optional[date] = None,
    end: Optional[date] = None,
) -> StockHistoryResponse:
    if end is None:
        end = date.today()
    if start is None:
        start = end - timedelta(days=365)
    
    cache_key = f"{code}_{period}_{start}_{end}"
    
    if cache_key in _history_cache:
        cache_time, cached_response = _history_cache[cache_key]
        if _is_cache_valid(cache_time):
            return cached_response
    
    cache = CacheService()
    cached_df = cache.get_ohlcv(code, start, end)
    
    if cached_df is not None and not cached_df.empty:
        items = [
            OHLCVItem(
                date=row["date"].isoformat() if hasattr(row["date"], "isoformat") else str(row["date"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=int(row["volume"]),
                amount=float(row["amount"]) if pd.notna(row.get("amount")) else None,
                change_percent=float(row["change_percent"]) if pd.notna(row.get("change_percent")) else None,
            )
            for _, row in cached_df.iterrows()
        ]
        response = StockHistoryResponse(code=code, period=period, items=items)
        _history_cache[cache_key] = (datetime.now(), response)
        logger.info(f"Cache hit for {code} from {start} to {end}")
        return response
    
    try:
        items = _fetch_history_from_akshare(code, period, start, end)
        response = StockHistoryResponse(code=code, period=period, items=items)
        _history_cache[cache_key] = (datetime.now(), response)
        return response
    except Exception as e:
        logger.warning(f"Failed to fetch history for {code}: {e}")
        return StockHistoryResponse(code=code, period=period, items=[])


@akshare_api(timeout=30.0, max_retries=3)
def _fetch_balance_sheet_from_akshare(code: str, limit: int) -> list[BalanceSheetItem]:
    import akshare as ak
    
    df = ak.stock_balance_sheet_by_report_em(symbol=code)
    items = []
    for idx, row in df.head(limit).iterrows():
        report_date = datetime.strptime(str(row.get("报告日期", row.get("REPORT_DATE", ""))), "%Y-%m-%d").date()
        items.append(BalanceSheetItem(
            date=report_date,
            total_assets=row.get("资产总计") or row.get("TOTAL_ASSETS"),
            total_liabilities=row.get("负债合计") or row.get("TOTAL_LIABILITIES"),
            total_equity=row.get("股东权益合计") or row.get("TOTAL_EQUITY"),
            current_assets=row.get("流动资产合计") or row.get("TOTAL_CURRENT_ASSETS"),
            non_current_assets=row.get("非流动资产合计") or row.get("TOTAL_NONCURRENT_ASSETS"),
            current_liabilities=row.get("流动负债合计") or row.get("TOTAL_CURRENT_LIAB"),
            non_current_liabilities=row.get("非流动负债合计") or row.get("TOTAL_NONCURRENT_LIAB"),
            cash_and_equivalents=row.get("货币资金") or row.get("MONETARYFUNDS"),
            accounts_receivable=row.get("应收账款") or row.get("ACCOUNTS_RECE"),
            inventory=row.get("存货") or row.get("INVENTORY"),
            fixed_assets=row.get("固定资产") or row.get("FIXED_ASSET"),
            intangible_assets=row.get("无形资产") or row.get("INTANGIBLE_ASSET"),
            accounts_payable=row.get("应付账款") or row.get("ACCOUNTS_PAYABLE"),
            short_term_debt=row.get("短期借款") or row.get("SHORT_LOAN"),
            long_term_debt=row.get("长期借款") or row.get("LONG_LOAN"),
            retained_earnings=row.get("未分配利润") or row.get("RETAINED_EARNING"),
        ))
    logger.debug(f"Fetched {len(items)} balance sheet records for {code}")
    return items


@akshare_api(timeout=30.0, max_retries=3)
def _fetch_income_from_akshare(code: str, limit: int) -> list[IncomeStatementItem]:
    import akshare as ak
    
    df = ak.stock_profit_sheet_by_report_em(symbol=code)
    items = []
    for idx, row in df.head(limit).iterrows():
        report_date = datetime.strptime(str(row.get("报告日期", row.get("REPORT_DATE", ""))), "%Y-%m-%d").date()
        items.append(IncomeStatementItem(
            date=report_date,
            total_revenue=row.get("营业总收入") or row.get("TOTAL_REVENUE"),
            operating_revenue=row.get("营业收入") or row.get("OPERATE_INCOME"),
            operating_cost=row.get("营业成本") or row.get("OPERATE_COST"),
            gross_profit=row.get("毛利润"),
            selling_expenses=row.get("销售费用") or row.get("SALE_EXPENSE"),
            admin_expenses=row.get("管理费用") or row.get("MANAGE_EXPENSE"),
            rd_expenses=row.get("研发费用") or row.get("RESEARCH_EXPENSE"),
            financial_expenses=row.get("财务费用") or row.get("FINANCE_EXPENSE"),
            operating_profit=row.get("营业利润") or row.get("OPERATE_PROFIT"),
            total_profit=row.get("利润总额") or row.get("TOTAL_PROFIT"),
            income_tax=row.get("所得税费用") or row.get("INCOME_TAX"),
            net_profit=row.get("净利润") or row.get("NETPROFIT"),
            net_profit_excluding_non_recurring=row.get("扣除非经常性损益后的净利润") or row.get("DEDUCT_PARENT_NETPROFIT"),
            eps=row.get("基本每股收益") or row.get("BASIC_EPS"),
            diluted_eps=row.get("稀释每股收益") or row.get("DILUTED_EPS"),
        ))
    logger.debug(f"Fetched {len(items)} income statement records for {code}")
    return items


@akshare_api(timeout=30.0, max_retries=3)
def _fetch_cash_flow_from_akshare(code: str, limit: int) -> list[CashFlowItem]:
    import akshare as ak
    
    df = ak.stock_cash_flow_sheet_by_report_em(symbol=code)
    items = []
    for idx, row in df.head(limit).iterrows():
        report_date = datetime.strptime(str(row.get("报告日期", row.get("REPORT_DATE", ""))), "%Y-%m-%d").date()
        items.append(CashFlowItem(
            date=report_date,
            operating_cash_flow=row.get("经营活动产生的现金流量净额") or row.get("NETCASH_OPERATE"),
            investing_cash_flow=row.get("投资活动产生的现金流量净额") or row.get("NETCASH_INVEST"),
            financing_cash_flow=row.get("筹资活动产生的现金流量净额") or row.get("NETCASH_FINANCE"),
            net_cash_flow=row.get("现金及现金等价物净增加额") or row.get("CCE_ADD"),
            cash_received_from_sales=row.get("销售商品、提供劳务收到的现金") or row.get("SALES_SERVICES"),
            cash_paid_to_suppliers=row.get("购买商品、接受劳务支付的现金") or row.get("BUY_SERVICES"),
            cash_paid_to_employees=row.get("支付给职工以及为职工支付的现金") or row.get("PAY_STAFF_CASH"),
            cash_paid_for_taxes=row.get("支付的各项税费") or row.get("PAY_ALL_TAX"),
            cash_paid_for_investments=row.get("购建固定资产、无形资产和其他长期资产支付的现金") or row.get("CONSTRUCT_LONG_ASSET"),
            cash_received_from_investments=row.get("处置固定资产、无形资产和其他长期资产收回的现金净额") or row.get("DISPOSAL_LONG_ASSET"),
            cash_received_from_borrowings=row.get("取得借款收到的现金") or row.get("RECEIVE_LOAN_CASH"),
            cash_paid_for_debt=row.get("偿还债务支付的现金") or row.get("PAY_DEBT_CASH"),
            cash_paid_for_dividends=row.get("分配股利、利润或偿付利息支付的现金") or row.get("PAY_OTHER_FINANCE"),
            free_cash_flow=None,
        ))
    logger.debug(f"Fetched {len(items)} cash flow records for {code}")
    return items


@akshare_api(timeout=30.0, max_retries=3)
def _fetch_indicators_from_akshare(code: str, limit: int) -> list[FinancialIndicatorItem]:
    import akshare as ak
    
    df = ak.stock_financial_analysis_indicator(symbol=code)
    items = []
    for idx, row in df.head(limit).iterrows():
        report_date = datetime.strptime(str(row.get("日期", row.get("报告日期", ""))), "%Y-%m-%d").date()
        items.append(FinancialIndicatorItem(
            date=report_date,
            roe=row.get("净资产收益率(%)") or row.get("加权净资产收益率(%)"),
            roa=row.get("总资产报酬率(%)") or row.get("总资产净利润率(%)"),
            gross_margin=row.get("销售毛利率(%)"),
            net_margin=row.get("销售净利率(%)"),
            operating_margin=row.get("营业利润率(%)"),
            asset_turnover=row.get("总资产周转率(次)"),
            inventory_turnover=row.get("存货周转率(次)"),
            receivable_turnover=row.get("应收账款周转率(次)"),
            current_ratio=row.get("流动比率"),
            quick_ratio=row.get("速动比率"),
            debt_to_equity=row.get("资产负债率(%)"),
            interest_coverage=row.get("利息保障倍数"),
            revenue_growth=row.get("营业收入同比增长率(%)") or row.get("主营业务收入增长率(%)"),
            profit_growth=row.get("净利润同比增长率(%)") or row.get("净利润增长率(%)"),
            eps_growth=row.get("基本每股收益同比增长率(%)"),
        ))
    logger.debug(f"Fetched {len(items)} financial indicator records for {code}")
    return items


@akshare_api(timeout=30.0, max_retries=3)
def _fetch_valuation_from_akshare(code: str, limit: int) -> list[ValuationItem]:
    import akshare as ak
    
    df = ak.stock_a_lg_indicator(symbol=code)
    items = []
    for idx, row in df.tail(limit).iloc[::-1].iterrows():
        trade_date = datetime.strptime(str(row.get("trade_date", "")), "%Y-%m-%d").date()
        items.append(ValuationItem(
            date=trade_date,
            pe_ratio=row.get("pe"),
            pe_ttm=row.get("pe_ttm"),
            pb_ratio=row.get("pb"),
            ps_ratio=row.get("ps"),
            ps_ttm=row.get("ps_ttm"),
            pcf_ratio=None,
            ev=None,
            ev_to_ebitda=None,
            market_cap=row.get("total_mv"),
            circulating_market_cap=row.get("circ_mv"),
            total_shares=None,
            circulating_shares=None,
        ))
    logger.debug(f"Fetched {len(items)} valuation records for {code}")
    return items


@akshare_api(timeout=30.0, max_retries=3)
def _fetch_dividend_from_akshare(code: str, limit: int) -> list[DividendItem]:
    import akshare as ak
    
    df = ak.stock_history_dividend_detail(symbol=code, indicator="分红")
    items = []
    for idx, row in df.head(limit).iterrows():
        ex_date_str = str(row.get("除权除息日", ""))
        if ex_date_str and ex_date_str != "nan" and ex_date_str != "":
            try:
                ex_date = datetime.strptime(ex_date_str, "%Y-%m-%d").date()
            except ValueError:
                ex_date = None
        else:
            ex_date = None
        
        record_date_str = str(row.get("股权登记日", ""))
        if record_date_str and record_date_str != "nan" and record_date_str != "":
            try:
                record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date()
            except ValueError:
                record_date = None
        else:
            record_date = None
        
        report_date_str = str(row.get("公告日期", ""))
        if report_date_str and report_date_str != "nan" and report_date_str != "":
            try:
                report_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
            except ValueError:
                report_date = date.today()
        else:
            report_date = date.today()
        
        items.append(DividendItem(
            date=report_date,
            announcement_date=report_date,
            ex_dividend_date=ex_date,
            record_date=record_date,
            payment_date=None,
            dividend_per_share=row.get("派息(每10股)") / 10 if row.get("派息(每10股)") else None,
            dividend_yield=None,
            bonus_shares_per_10=row.get("送股(每10股)"),
            transfer_shares_per_10=row.get("转增(每10股)"),
            cash_per_10=row.get("派息(每10股)"),
            total_dividend=None,
        ))
    logger.debug(f"Fetched {len(items)} dividend records for {code}")
    return items


def _is_financial_cache_valid(cache_time: Optional[datetime]) -> bool:
    if cache_time is None:
        return False
    return (datetime.now() - cache_time).total_seconds() < FINANCIAL_CACHE_TTL_SECONDS


def get_balance_sheet(code: str, limit: int = 8) -> BalanceSheetResponse:
    cache_key = f"{code}_{limit}"
    
    if cache_key in _balance_sheet_cache:
        cache_time, cached_response = _balance_sheet_cache[cache_key]
        if _is_financial_cache_valid(cache_time):
            return cached_response
    
    items = _fetch_balance_sheet_from_akshare(code, limit)
    response = BalanceSheetResponse(code=code, items=items)
    _balance_sheet_cache[cache_key] = (datetime.now(), response)
    
    return response


def get_income_statement(code: str, limit: int = 8) -> IncomeStatementResponse:
    cache_key = f"{code}_{limit}"
    
    if cache_key in _income_cache:
        cache_time, cached_response = _income_cache[cache_key]
        if _is_financial_cache_valid(cache_time):
            return cached_response
    
    items = _fetch_income_from_akshare(code, limit)
    response = IncomeStatementResponse(code=code, items=items)
    _income_cache[cache_key] = (datetime.now(), response)
    
    return response


def get_cash_flow(code: str, limit: int = 8) -> CashFlowResponse:
    cache_key = f"{code}_{limit}"
    
    if cache_key in _cash_flow_cache:
        cache_time, cached_response = _cash_flow_cache[cache_key]
        if _is_financial_cache_valid(cache_time):
            return cached_response
    
    items = _fetch_cash_flow_from_akshare(code, limit)
    response = CashFlowResponse(code=code, items=items)
    _cash_flow_cache[cache_key] = (datetime.now(), response)
    
    return response


def get_financial_indicators(code: str, limit: int = 8) -> FinancialIndicatorResponse:
    cache_key = f"{code}_{limit}"
    
    if cache_key in _indicators_cache:
        cache_time, cached_response = _indicators_cache[cache_key]
        if _is_financial_cache_valid(cache_time):
            return cached_response
    
    cache = CacheService()
    cached_df = cache.get_financial_indicators(code)
    if cached_df is not None and not cached_df.empty:
        items = _df_to_financial_indicator_items(cached_df.head(limit))
        response = FinancialIndicatorResponse(code=code, items=items)
        _indicators_cache[cache_key] = (datetime.now(), response)
        logger.info(f"Financial indicators cache hit for {code}")
        return response
    
    try:
        items = _fetch_indicators_from_akshare(code, limit)
        response = FinancialIndicatorResponse(code=code, items=items)
        _indicators_cache[cache_key] = (datetime.now(), response)
        
        if items:
            df = _financial_indicator_items_to_df(items)
            cache.save_financial_indicators(code, df)
        
        return response
    except Exception as e:
        logger.warning(f"Failed to fetch financial indicators for {code}: {e}")
        return FinancialIndicatorResponse(code=code, items=[])


def get_valuation(code: str, limit: int = 30) -> ValuationResponse:
    cache_key = f"{code}_{limit}"
    
    if cache_key in _valuation_cache:
        cache_time, cached_response = _valuation_cache[cache_key]
        if _is_financial_cache_valid(cache_time):
            return cached_response
    
    cache = CacheService()
    cached_df = cache.get_valuation(code)
    if cached_df is not None and not cached_df.empty:
        items = _df_to_valuation_items(cached_df.head(limit))
        response = ValuationResponse(code=code, items=items)
        _valuation_cache[cache_key] = (datetime.now(), response)
        logger.info(f"Valuation cache hit for {code}")
        return response
    
    try:
        items = _fetch_valuation_from_akshare(code, limit)
        response = ValuationResponse(code=code, items=items)
        _valuation_cache[cache_key] = (datetime.now(), response)
        
        if items:
            df = _valuation_items_to_df(items)
            cache.save_valuation(code, df)
        
        return response
    except Exception as e:
        logger.warning(f"Failed to fetch valuation for {code}: {e}")
        return ValuationResponse(code=code, items=[])


def get_dividend(code: str, limit: int = 10) -> DividendResponse:
    cache_key = f"{code}_{limit}"
    
    if cache_key in _dividend_cache:
        cache_time, cached_response = _dividend_cache[cache_key]
        if _is_financial_cache_valid(cache_time):
            return cached_response
    
    try:
        items = _fetch_dividend_from_akshare(code, limit)
        response = DividendResponse(code=code, items=items)
        _dividend_cache[cache_key] = (datetime.now(), response)
        return response
    except Exception as e:
        logger.warning(f"Failed to fetch dividend for {code}: {e}")
        return DividendResponse(code=code, items=[])


def _df_to_financial_indicator_items(df: pd.DataFrame) -> list[FinancialIndicatorItem]:
    items = []
    for _, row in df.iterrows():
        items.append(FinancialIndicatorItem(
            date=pd.to_datetime(row.get("date")).date() if pd.notna(row.get("date")) else None,
            roe=row.get("roe"),
            roa=row.get("roa"),
            gross_margin=row.get("gross_margin"),
            net_margin=row.get("net_margin"),
            operating_margin=row.get("operating_margin"),
            asset_turnover=row.get("asset_turnover"),
            inventory_turnover=row.get("inventory_turnover"),
            receivable_turnover=row.get("receivable_turnover"),
            current_ratio=row.get("current_ratio"),
            quick_ratio=row.get("quick_ratio"),
            debt_to_equity=row.get("debt_to_equity"),
            interest_coverage=row.get("interest_coverage"),
            revenue_growth=row.get("revenue_growth"),
            profit_growth=row.get("profit_growth"),
            eps_growth=row.get("eps_growth"),
        ))
    return items


def _financial_indicator_items_to_df(items: list[FinancialIndicatorItem]) -> pd.DataFrame:
    data = []
    for item in items:
        data.append({
            "date": item.date.isoformat() if item.date else None,
            "roe": item.roe,
            "roa": item.roa,
            "gross_margin": item.gross_margin,
            "net_margin": item.net_margin,
            "operating_margin": item.operating_margin,
            "asset_turnover": item.asset_turnover,
            "inventory_turnover": item.inventory_turnover,
            "receivable_turnover": item.receivable_turnover,
            "current_ratio": item.current_ratio,
            "quick_ratio": item.quick_ratio,
            "debt_to_equity": item.debt_to_equity,
            "interest_coverage": item.interest_coverage,
            "revenue_growth": item.revenue_growth,
            "profit_growth": item.profit_growth,
            "eps_growth": item.eps_growth,
        })
    return pd.DataFrame(data)


def _df_to_valuation_items(df: pd.DataFrame) -> list[ValuationItem]:
    items = []
    for _, row in df.iterrows():
        items.append(ValuationItem(
            date=pd.to_datetime(row.get("date")).date() if pd.notna(row.get("date")) else None,
            pe_ratio=row.get("pe_ratio"),
            pe_ttm=row.get("pe_ttm"),
            pb_ratio=row.get("pb_ratio"),
            ps_ratio=row.get("ps_ratio"),
            ps_ttm=row.get("ps_ttm"),
            pcf_ratio=row.get("pcf_ratio"),
            ev=row.get("ev"),
            ev_to_ebitda=row.get("ev_to_ebitda"),
            market_cap=row.get("market_cap"),
            circulating_market_cap=row.get("circulating_market_cap"),
            total_shares=row.get("total_shares"),
            circulating_shares=row.get("circulating_shares"),
        ))
    return items


def _valuation_items_to_df(items: list[ValuationItem]) -> pd.DataFrame:
    data = []
    for item in items:
        data.append({
            "date": item.date.isoformat() if item.date else None,
            "pe_ratio": item.pe_ratio,
            "pe_ttm": item.pe_ttm,
            "pb_ratio": item.pb_ratio,
            "ps_ratio": item.ps_ratio,
            "ps_ttm": item.ps_ttm,
            "pcf_ratio": item.pcf_ratio,
            "ev": item.ev,
            "ev_to_ebitda": item.ev_to_ebitda,
            "market_cap": item.market_cap,
            "circulating_market_cap": item.circulating_market_cap,
            "total_shares": item.total_shares,
            "circulating_shares": item.circulating_shares,
        })
    return pd.DataFrame(data)
