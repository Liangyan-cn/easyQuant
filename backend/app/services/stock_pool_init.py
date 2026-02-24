import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.stock_pool_repo import StockPoolRepository

logger = logging.getLogger(__name__)

SYSTEM_POOLS = [
    {"code": "hs300", "name": "沪深300", "description": "沪深300指数成分股", "index_code": "000300"},
    {"code": "zz500", "name": "中证500", "description": "中证500指数成分股", "index_code": "000905"},
]


async def init_system_pools(db: AsyncSession) -> None:
    repo = StockPoolRepository(db)

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

        try:
            import akshare as ak
            df = ak.index_stock_cons(symbol=pool_data["index_code"])
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    "stock_code": str(row.get("品种代码", row.get("constituent_code", ""))),
                    "stock_name": str(row.get("品种名称", row.get("constituent_name", ""))),
                })
            if stocks:
                count = await repo.add_stocks_bulk(pool.id, stocks)
                logger.info(f"Imported {count} stocks to pool '{pool_data['code']}'")
        except ImportError:
            logger.warning("AKShare not installed, skipping stock import")
        except Exception as e:
            logger.error(f"Failed to import stocks for '{pool_data['code']}': {e}")
