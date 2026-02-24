import argparse
import asyncio
import logging
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

REQUEST_DELAY = 0.5
MAX_RETRIES = 3
RETRY_DELAY = 5


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


async def preload_ohlcv(force: bool = False):
    from app.core.database import async_session_maker
    from app.repositories.stock_pool_repo import StockPoolRepository
    from app.services.cache_service import CacheService

    logger.info(f"Starting OHLCV preload (force={force})...")
    cache = CacheService()

    cached_stocks = set()
    if not force:
        cached_df = cache._get_all_ohlcv_stocks()
        if cached_df is not None:
            cached_stocks = set(cached_df)
            logger.info(f"Found {len(cached_stocks)} stocks already cached")

    async with async_session_maker() as db:
        repo = StockPoolRepository(db)
        success_count = 0
        error_count = 0

        for pool_code in ["hs300", "zz500"]:
            pool = await repo.get_by_code(pool_code)
            if not pool:
                logger.warning(f"Pool {pool_code} not found, skipping")
                continue

            pool_with_items = await repo.get_by_id(pool.id)
            stocks = pool_with_items.items if pool_with_items else []
            logger.info(f"Processing {len(stocks)} stocks from {pool_code}")

            for i, item in enumerate(stocks):
                if not force and item.stock_code in cached_stocks:
                    continue

                try:
                    end_date = date.today()
                    start_date = end_date - timedelta(days=730)

                    df = fetch_stock_data(item.stock_code, start_date, end_date)

                    if df.empty:
                        logger.warning(f"No data for {item.stock_code}")
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

                    cache.save_ohlcv(item.stock_code, df)
                    success_count += 1

                    if success_count % 50 == 0:
                        logger.info(f"Progress: {success_count} stocks loaded")

                    time.sleep(REQUEST_DELAY)

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error loading {item.stock_code}: {e}")

    logger.info(f"OHLCV preload completed: {success_count} success, {error_count} errors")


async def update_ohlcv():
    from app.core.database import async_session_maker
    from app.repositories.stock_pool_repo import StockPoolRepository
    from app.services.cache_service import CacheService

    logger.info("Starting OHLCV incremental update...")
    cache = CacheService()

    metadata = cache._metadata.get("ohlcv", {})
    last_date_str = metadata.get("date_range", [None, None])[1] if metadata else None

    if last_date_str:
        last_date = date.fromisoformat(last_date_str)
        start_date = last_date + timedelta(days=1)
    else:
        logger.warning("No existing cache, running full preload instead")
        await preload_ohlcv(force=False)
        return

    end_date = date.today()
    if start_date > end_date:
        logger.info("Cache is already up to date")
        return

    logger.info(f"Updating data from {start_date} to {end_date}")

    async with async_session_maker() as db:
        repo = StockPoolRepository(db)
        success_count = 0
        error_count = 0

        for pool_code in ["hs300", "zz500"]:
            pool = await repo.get_by_code(pool_code)
            if not pool:
                continue

            pool_with_items = await repo.get_by_id(pool.id)
            stocks = pool_with_items.items if pool_with_items else []

            for item in stocks:
                try:
                    df = fetch_stock_data(item.stock_code, start_date, end_date)

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

                    cache.append_ohlcv(item.stock_code, df)
                    success_count += 1

                    time.sleep(REQUEST_DELAY)

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error updating {item.stock_code}: {e}")

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
        print(f"\nOHLCV:")
        print(f"  Stocks: {ohlcv.get('stock_count', 0)}")
        print(f"  Records: {ohlcv.get('record_count', 0)}")
        print(f"  Date range: {ohlcv.get('date_range')}")
        print(f"  File size: {ohlcv.get('file_size_mb', 0)} MB")


def main():
    parser = argparse.ArgumentParser(description="Cache management tool")
    parser.add_argument("command", choices=["preload", "update", "status"], help="Command to run")
    parser.add_argument("--force", action="store_true", help="Force full reload (ignore existing cache)")
    args = parser.parse_args()

    if args.command == "preload":
        asyncio.run(preload_ohlcv(force=args.force))
    elif args.command == "update":
        asyncio.run(update_ohlcv())
    elif args.command == "status":
        show_status()


if __name__ == "__main__":
    main()
