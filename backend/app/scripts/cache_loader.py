import argparse
import asyncio
import logging
import sys
from datetime import date, timedelta

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def preload_ohlcv():
    from app.core.database import async_session_maker
    from app.repositories.stock_pool_repo import StockPoolRepository
    from app.services.cache_service import CacheService

    logger.info("Starting OHLCV preload...")
    cache = CacheService()

    async with async_session_maker() as db:
        repo = StockPoolRepository(db)

        for pool_code in ["hs300", "zz500"]:
            pool = await repo.get_by_code(pool_code)
            if not pool:
                logger.warning(f"Pool {pool_code} not found, skipping")
                continue

            pool_with_items = await repo.get_by_id(pool.id)
            stocks = pool_with_items.items if pool_with_items else []
            logger.info(f"Loading {len(stocks)} stocks from {pool_code}")

            for i, item in enumerate(stocks):
                try:
                    import akshare as ak

                    end_date = date.today()
                    start_date = end_date - timedelta(days=730)

                    df = ak.stock_zh_a_hist(
                        symbol=item.stock_code,
                        period="daily",
                        start_date=start_date.strftime("%Y%m%d"),
                        end_date=end_date.strftime("%Y%m%d"),
                        adjust="qfq",
                    )

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

                    if (i + 1) % 50 == 0:
                        logger.info(f"Progress: {i + 1}/{len(stocks)}")

                except Exception as e:
                    logger.error(f"Error loading {item.stock_code}: {e}")

    logger.info("OHLCV preload completed")


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
    args = parser.parse_args()

    if args.command == "preload":
        asyncio.run(preload_ohlcv())
    elif args.command == "update":
        asyncio.run(preload_ohlcv())
    elif args.command == "status":
        show_status()


if __name__ == "__main__":
    main()
