import json
import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.stock_pool_repo import StockPoolRepository

logger = logging.getLogger(__name__)

SYSTEM_POOLS = [
    {"code": "hs300", "name": "沪深300", "description": "沪深300指数成分股"},
    {"code": "zz500", "name": "中证500", "description": "中证500指数成分股"},
]

DATA_FILE = Path(__file__).parent.parent / "data" / "index_stocks.json"


def _load_index_stocks() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


async def init_system_pools(db: AsyncSession) -> None:
    repo = StockPoolRepository(db)
    index_data = _load_index_stocks()

    for pool_data in SYSTEM_POOLS:
        existing = await repo.get_by_code(pool_data["code"])
        if existing:
            logger.info(f"System pool '{pool_data['code']}' already exists, skipping")
            continue

        pool = await repo.create_system_pool(
            name=pool_data["name"],
            code=pool_data["code"],
            description=pool_data["description"],
        )
        logger.info(f"Created system pool: {pool_data['name']} (id={pool.id})")

        stocks = index_data.get(pool_data["code"], [])
        if stocks:
            count = await repo.add_stocks_bulk(pool.id, stocks)
            logger.info(f"Imported {count} stocks to pool '{pool_data['code']}'")
        else:
            logger.warning(f"No stock data found for '{pool_data['code']}'")
