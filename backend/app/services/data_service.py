import logging
import random
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Optional

from app.schemas.stock import (
    OHLCVItem,
    StockHistoryResponse,
    StockInfo,
    StockListResponse,
)

logger = logging.getLogger(__name__)

_stock_list_cache: Optional[list[StockInfo]] = None
_stock_list_cache_time: Optional[datetime] = None
_history_cache: dict[str, tuple[datetime, StockHistoryResponse]] = {}

CACHE_TTL_SECONDS = 300


def _get_mock_stock_list() -> list[StockInfo]:
    mock_stocks = [
        StockInfo(code="600519", name="贵州茅台", market="SH", industry="白酒"),
        StockInfo(code="000858", name="五粮液", market="SZ", industry="白酒"),
        StockInfo(code="601318", name="中国平安", market="SH", industry="保险"),
        StockInfo(code="000001", name="平安银行", market="SZ", industry="银行"),
        StockInfo(code="600036", name="招商银行", market="SH", industry="银行"),
        StockInfo(code="000333", name="美的集团", market="SZ", industry="家电"),
        StockInfo(code="600276", name="恒瑞医药", market="SH", industry="医药"),
        StockInfo(code="002415", name="海康威视", market="SZ", industry="电子"),
        StockInfo(code="601888", name="中国中免", market="SH", industry="零售"),
        StockInfo(code="000651", name="格力电器", market="SZ", industry="家电"),
        StockInfo(code="600900", name="长江电力", market="SH", industry="电力"),
        StockInfo(code="002594", name="比亚迪", market="SZ", industry="汽车"),
        StockInfo(code="601012", name="隆基绿能", market="SH", industry="光伏"),
        StockInfo(code="000725", name="京东方A", market="SZ", industry="电子"),
        StockInfo(code="600887", name="伊利股份", market="SH", industry="食品"),
    ]
    return mock_stocks


def _get_mock_history(code: str, period: str, start: date, end: date) -> list[OHLCVItem]:
    items = []
    current = start
    base_price = random.uniform(10, 100)
    
    if period == "weekly":
        delta = timedelta(days=7)
    elif period == "monthly":
        delta = timedelta(days=30)
    else:
        delta = timedelta(days=1)
    
    while current <= end:
        if current.weekday() < 5:
            change = random.uniform(-0.05, 0.05)
            open_price = base_price * (1 + random.uniform(-0.02, 0.02))
            close_price = base_price * (1 + change)
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))
            volume = random.uniform(1000000, 10000000)
            amount = volume * (open_price + close_price) / 2
            
            items.append(OHLCVItem(
                date=current,
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                volume=round(volume, 0),
                amount=round(amount, 2),
            ))
            base_price = close_price
        
        current += delta
    
    return items


def _fetch_stock_list_from_akshare() -> list[StockInfo]:
    try:
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
    except ImportError:
        logger.warning("AKShare not installed, using mock data")
        return _get_mock_stock_list()
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error parsing AKShare data: {e}")
        return _get_mock_stock_list()
    except Exception as e:
        logger.error(f"Unexpected error fetching stock list: {e}")
        return _get_mock_stock_list()


def _fetch_history_from_akshare(
    code: str, period: str, start: date, end: date
) -> list[OHLCVItem]:
    try:
        import akshare as ak
        
        period_map = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}
        ak_period = period_map.get(period, "daily")
        
        market = "sh" if code.startswith("6") else "sz"
        symbol = f"{market}{code}"
        
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
    except ImportError:
        logger.warning("AKShare not installed, using mock history data")
        return _get_mock_history(code, period, start, end)
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error parsing history data for {code}: {e}")
        return _get_mock_history(code, period, start, end)
    except Exception as e:
        logger.error(f"Unexpected error fetching history for {code}: {e}")
        return _get_mock_history(code, period, start, end)


def _is_cache_valid(cache_time: Optional[datetime]) -> bool:
    if cache_time is None:
        return False
    return (datetime.now() - cache_time).total_seconds() < CACHE_TTL_SECONDS


def get_stock_list(
    keyword: Optional[str] = None,
    market: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> StockListResponse:
    global _stock_list_cache, _stock_list_cache_time
    
    if not _is_cache_valid(_stock_list_cache_time) or _stock_list_cache is None:
        _stock_list_cache = _fetch_stock_list_from_akshare()
        _stock_list_cache_time = datetime.now()
    
    filtered = _stock_list_cache
    
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
    
    items = _fetch_history_from_akshare(code, period, start, end)
    
    response = StockHistoryResponse(code=code, period=period, items=items)
    _history_cache[cache_key] = (datetime.now(), response)
    
    return response
