import argparse
import asyncio
import json
import logging
import time
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

REQUEST_DELAY = 1.5
MAX_RETRIES = 3
RETRY_DELAY = 10


def fetch_stock_data(stock_code: str, start_date: date, end_date: date) -> pd.DataFrame:
    import akshare as ak

    for attempt in range(MAX_RETRIES):
        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq",
            )
            return df
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Retry {attempt + 1}/{MAX_RETRIES} for {stock_code}: {e}")
                time.sleep(RETRY_DELAY)
            else:
                raise e
    return pd.DataFrame()


def fetch_financial_indicators(stock_code: str) -> pd.DataFrame:
    import akshare as ak

    for attempt in range(MAX_RETRIES):
        try:
            df = ak.stock_financial_analysis_indicator(symbol=stock_code)
            return df
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Retry {attempt + 1}/{MAX_RETRIES} for financial {stock_code}: {e}")
                time.sleep(RETRY_DELAY)
            else:
                raise e
    return pd.DataFrame()


def fetch_valuation(stock_code: str) -> pd.DataFrame:
    import akshare as ak

    for attempt in range(MAX_RETRIES):
        try:
            df = ak.stock_a_lg_indicator(symbol=stock_code)
            return df
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Retry {attempt + 1}/{MAX_RETRIES} for valuation {stock_code}: {e}")
                time.sleep(RETRY_DELAY)
            else:
                raise e
    return pd.DataFrame()


def get_pool_stocks(pool_code: str) -> List[str]:
    index_file = Path(__file__).parent.parent / "data" / "index_stocks.json"
    if index_file.exists():
        with open(index_file, "r") as f:
            data = json.load(f)
            if pool_code in data:
                return data[pool_code]
    return []


async def get_pool_stocks_from_db(pool_code: str) -> List[str]:
    from app.core.database import async_session_maker
    from app.repositories.stock_pool_repo import StockPoolRepository

    async with async_session_maker() as db:
        repo = StockPoolRepository(db)
        pool = await repo.get_by_code(pool_code)
        if not pool:
            return []
        pool_with_items = await repo.get_by_id(pool.id)
        return [item.stock_code for item in pool_with_items.items] if pool_with_items else []


async def resolve_stocks(pool: Optional[str] = None, stock: Optional[str] = None) -> List[str]:
    if stock:
        return [stock]
    
    if pool:
        stocks = get_pool_stocks(pool)
        if not stocks:
            stocks = await get_pool_stocks_from_db(pool)
        return stocks
    
    return get_pool_stocks("hs300")


async def preload_ohlcv(
    force: bool = False,
    pool: Optional[str] = None,
    stock: Optional[str] = None
):
    from app.services.cache_service import CacheService

    stocks = await resolve_stocks(pool, stock)
    if not stocks:
        logger.error("No stocks to process")
        return

    source = stock if stock else (pool if pool else "hs300")
    logger.info(f"Starting OHLCV preload for {source} ({len(stocks)} stocks, force={force})...")
    
    cache = CacheService()

    cached_stocks = set()
    if not force:
        cached_df = cache._get_all_ohlcv_stocks()
        if cached_df is not None:
            cached_stocks = set(cached_df)
            logger.info(f"Found {len(cached_stocks)} stocks already cached")

    success_count = 0
    error_count = 0
    skip_count = 0

    for i, stock_code in enumerate(stocks):
        if not force and stock_code in cached_stocks:
            skip_count += 1
            continue

        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=730)

            df = fetch_stock_data(stock_code, start_date, end_date)

            if df.empty:
                logger.warning(f"No data for {stock_code}")
                continue

            df = df.rename(columns={
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "涨跌幅": "change_percent",
            })
            df = df[["date", "open", "high", "low", "close", "volume", "amount", "change_percent"]]

            cache.save_ohlcv(stock_code, df)
            success_count += 1
            logger.info(f"[{i+1}/{len(stocks)}] Loaded {stock_code}: {len(df)} records")

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            error_count += 1
            logger.error(f"Error loading {stock_code}: {e}")

    logger.info(f"OHLCV preload completed: {success_count} success, {skip_count} skipped, {error_count} errors")


async def preload_financial(
    force: bool = False,
    pool: Optional[str] = None,
    stock: Optional[str] = None
):
    from app.services.cache_service import CacheService

    stocks = await resolve_stocks(pool, stock)
    if not stocks:
        logger.error("No stocks to process")
        return

    source = stock if stock else (pool if pool else "hs300")
    logger.info(f"Starting financial data preload for {source} ({len(stocks)} stocks, force={force})...")
    
    cache = CacheService()

    cached_financial = set(cache.get_all_cached_stocks("financial_indicators") or [])
    cached_valuation = set(cache.get_all_cached_stocks("valuation") or [])
    
    if not force:
        logger.info(f"Found {len(cached_financial)} stocks with financial indicators cached")
        logger.info(f"Found {len(cached_valuation)} stocks with valuation cached")

    success_count = 0
    error_count = 0
    skip_count = 0

    for i, stock_code in enumerate(stocks):
        has_financial = stock_code in cached_financial
        has_valuation = stock_code in cached_valuation
        
        if not force and has_financial and has_valuation:
            skip_count += 1
            continue

        try:
            if force or not has_financial:
                df = fetch_financial_indicators(stock_code)
                if not df.empty:
                    df = df.rename(columns={
                        "日期": "date",
                        "净资产收益率": "roe",
                        "总资产收益率": "roa",
                        "销售毛利率": "gross_margin",
                        "销售净利率": "net_margin",
                        "营业利润率": "operating_margin",
                        "总资产周转率": "asset_turnover",
                        "存货周转率": "inventory_turnover",
                        "应收账款周转率": "receivable_turnover",
                        "流动比率": "current_ratio",
                        "速动比率": "quick_ratio",
                        "资产负债率": "debt_to_equity",
                        "利息保障倍数": "interest_coverage",
                        "营业收入增长率": "revenue_growth",
                        "净利润增长率": "profit_growth",
                        "基本每股收益增长率": "eps_growth",
                    })
                    cache.save_financial_indicators(stock_code, df)
                    logger.info(f"[{i+1}/{len(stocks)}] Loaded financial indicators for {stock_code}")
                time.sleep(REQUEST_DELAY)

            if force or not has_valuation:
                df = fetch_valuation(stock_code)
                if not df.empty:
                    df = df.rename(columns={
                        "trade_date": "date",
                        "pe": "pe_ratio",
                        "pe_ttm": "pe_ttm",
                        "pb": "pb_ratio",
                        "ps": "ps_ratio",
                        "ps_ttm": "ps_ttm",
                        "dv_ratio": "dv_ratio",
                        "dv_ttm": "dv_ttm",
                        "total_mv": "market_cap",
                        "circ_mv": "circulating_market_cap",
                    })
                    cache.save_valuation(stock_code, df)
                    logger.info(f"[{i+1}/{len(stocks)}] Loaded valuation for {stock_code}")
                time.sleep(REQUEST_DELAY)

            success_count += 1

        except Exception as e:
            error_count += 1
            logger.error(f"Error loading financial data for {stock_code}: {e}")

    logger.info(f"Financial preload completed: {success_count} success, {skip_count} skipped, {error_count} errors")


async def preload_all(
    force: bool = False,
    pool: Optional[str] = None,
    stock: Optional[str] = None
):
    await preload_ohlcv(force=force, pool=pool, stock=stock)
    await preload_financial(force=force, pool=pool, stock=stock)


async def update_ohlcv(pool: Optional[str] = None, stock: Optional[str] = None):
    from app.services.cache_service import CacheService

    stocks = await resolve_stocks(pool, stock)
    if not stocks:
        logger.error("No stocks to process")
        return

    source = stock if stock else (pool if pool else "hs300")
    logger.info(f"Starting OHLCV incremental update for {source} ({len(stocks)} stocks)...")
    
    cache = CacheService()
    cached_stocks = set(cache._get_all_ohlcv_stocks() or [])
    
    stocks_not_cached = [s for s in stocks if s not in cached_stocks]
    stocks_to_update = [s for s in stocks if s in cached_stocks]
    
    if stocks_not_cached:
        logger.warning(f"These stocks are not in cache: {stocks_not_cached}")
        logger.warning("Use 'preload --stock <code>' to add them first")
        if not stocks_to_update:
            return

    metadata = cache._metadata.get("ohlcv", {})
    last_date_str = metadata.get("date_range", [None, None])[1] if metadata else None

    if not last_date_str:
        logger.warning("No cache metadata found")
        return

    last_date = date.fromisoformat(last_date_str)
    start_date = last_date + timedelta(days=1)
    end_date = date.today()
    
    if start_date > end_date:
        logger.info(f"Cache is already up to date (last date: {last_date})")
        return

    logger.info(f"Updating {len(stocks_to_update)} stocks from {start_date} to {end_date}")

    success_count = 0
    error_count = 0

    for i, stock_code in enumerate(stocks_to_update):
        try:
            df = fetch_stock_data(stock_code, start_date, end_date)

            if df.empty:
                continue

            df = df.rename(columns={
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "涨跌幅": "change_percent",
            })
            df = df[["date", "open", "high", "low", "close", "volume", "amount", "change_percent"]]

            cache.append_ohlcv(stock_code, df)
            success_count += 1
            logger.info(f"[{i+1}/{len(stocks_to_update)}] Updated {stock_code}: {len(df)} new records")

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            error_count += 1
            logger.error(f"Error updating {stock_code}: {e}")

    logger.info(f"OHLCV update completed: {success_count} success, {error_count} errors")


def show_status():
    from app.services.cache_service import CacheService

    cache = CacheService()
    stats = cache.get_cache_stats()
    status = cache.get_cache_status()

    print("\n=== Cache Status ===")
    print(f"File cache exists: {stats['file_cache_exists']}")
    print(f"Memory cache count: {stats['memory_cache_count']}")
    print(f"Last update: {stats['last_update']}")

    if status.get("ohlcv"):
        ohlcv = status["ohlcv"]
        print(f"\nOHLCV (行情数据):")
        print(f"  Stocks: {ohlcv.get('stock_count', 0)}")
        print(f"  Records: {ohlcv.get('record_count', 0)}")
        print(f"  Date range: {ohlcv.get('date_range')}")
        print(f"  File size: {ohlcv.get('file_size_mb', 0)} MB")

    if status.get("financial_indicators"):
        fi = status["financial_indicators"]
        print(f"\nFinancial Indicators (财务指标):")
        print(f"  Stocks: {fi.get('stock_count', 0)}")
        print(f"  Records: {fi.get('record_count', 0)}")
        print(f"  File size: {fi.get('file_size_mb', 0)} MB")

    if status.get("valuation"):
        val = status["valuation"]
        print(f"\nValuation (估值指标):")
        print(f"  Stocks: {val.get('stock_count', 0)}")
        print(f"  Records: {val.get('record_count', 0)}")
        print(f"  File size: {val.get('file_size_mb', 0)} MB")


def list_pools():
    index_file = Path(__file__).parent.parent / "data" / "index_stocks.json"
    print("\n=== Available Pools ===")
    if index_file.exists():
        with open(index_file, "r") as f:
            data = json.load(f)
            for pool_code, stocks in data.items():
                print(f"  {pool_code}: {len(stocks)} stocks")
    print("\n  (User-created pools can be accessed from database)")


def main():
    parser = argparse.ArgumentParser(
        description="Cache management tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # OHLCV data
  python cache_loader.py preload                         # Preload hs300 OHLCV
  python cache_loader.py preload --pool zz500           # Preload zz500 OHLCV
  python cache_loader.py preload --stock 000001         # Preload single stock OHLCV
  python cache_loader.py preload --pool hs300 --force   # Force reload
  python cache_loader.py update --stock 600036          # Update single stock
  
  # Financial data
  python cache_loader.py preload-financial --stock 000001  # Preload financial data
  python cache_loader.py preload-financial --pool hs300    # Preload pool financial data
  
  # All data
  python cache_loader.py preload-all --stock 000001     # Preload all data types
  
  # Status
  python cache_loader.py status                          # Show cache status
  python cache_loader.py list                            # List available pools
        """
    )
    parser.add_argument(
        "command",
        choices=["preload", "preload-financial", "preload-all", "update", "status", "list"],
        help="Command to run"
    )
    parser.add_argument(
        "--pool", "-p",
        type=str,
        help="Stock pool code (e.g., hs300, zz500, or user-created pool)"
    )
    parser.add_argument(
        "--stock", "-s",
        type=str,
        help="Single stock code (e.g., 000001, 600036)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force full reload (ignore existing cache)"
    )
    args = parser.parse_args()

    if args.command == "preload":
        asyncio.run(preload_ohlcv(force=args.force, pool=args.pool, stock=args.stock))
    elif args.command == "preload-financial":
        asyncio.run(preload_financial(force=args.force, pool=args.pool, stock=args.stock))
    elif args.command == "preload-all":
        asyncio.run(preload_all(force=args.force, pool=args.pool, stock=args.stock))
    elif args.command == "update":
        asyncio.run(update_ohlcv(pool=args.pool, stock=args.stock))
    elif args.command == "status":
        show_status()
    elif args.command == "list":
        list_pools()


if __name__ == "__main__":
    main()
