# 数据缓存方案实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现基于 Parquet 文件的股票数据缓存系统，支持预加载和按需加载

**Architecture:** 三层缓存架构 (L1 内存 → L2 Parquet 文件 → L3 AKShare)，脚本驱动预加载系统股票池数据，按需加载其他股票

**Tech Stack:** Python, Pandas, PyArrow (Parquet), AKShare

---

## Task 1: 创建缓存 Schema

**Files:**
- Create: `backend/app/schemas/cache.py`

**Step 1: 创建缓存相关的 Pydantic Schema**

```python
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
```

**Step 2: 提交**

```bash
git add backend/app/schemas/cache.py
git commit -m "feat: add cache schemas"
```

---

## Task 2: 创建 CacheService 核心

**Files:**
- Create: `backend/app/services/cache_service.py`
- Create: `backend/app/data/cache/.gitkeep`

**Step 1: 创建缓存目录结构**

```bash
mkdir -p backend/app/data/cache
touch backend/app/data/cache/.gitkeep
```

**Step 2: 实现 CacheService**

```python
import json
import logging
import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
METADATA_FILE = CACHE_DIR / "metadata.json"


class CacheService:
    _instance: Optional["CacheService"] = None
    _memory_cache: dict[str, pd.DataFrame] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._load_metadata()

    def _load_metadata(self) -> dict:
        if METADATA_FILE.exists():
            with open(METADATA_FILE, "r") as f:
                self._metadata = json.load(f)
        else:
            self._metadata = {"version": "1.0", "last_update": None}
        return self._metadata

    def _save_metadata(self):
        self._metadata["last_update"] = datetime.now().isoformat()
        with open(METADATA_FILE, "w") as f:
            json.dump(self._metadata, f, indent=2, default=str)

    def get_ohlcv(
        self, stock_code: str, start_date: date, end_date: date
    ) -> Optional[pd.DataFrame]:
        cache_key = f"ohlcv_{stock_code}"
        if cache_key in self._memory_cache:
            df = self._memory_cache[cache_key]
            return self._filter_by_date(df, start_date, end_date)

        file_path = CACHE_DIR / "ohlcv.parquet"
        if file_path.exists():
            df = pd.read_parquet(file_path)
            stock_df = df[df["stock_code"] == stock_code]
            if not stock_df.empty:
                self._memory_cache[cache_key] = stock_df
                return self._filter_by_date(stock_df, start_date, end_date)

        return None

    def _filter_by_date(
        self, df: pd.DataFrame, start_date: date, end_date: date
    ) -> pd.DataFrame:
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    def save_ohlcv(self, stock_code: str, df: pd.DataFrame):
        df = df.copy()
        df["stock_code"] = stock_code

        file_path = CACHE_DIR / "ohlcv.parquet"
        if file_path.exists():
            existing = pd.read_parquet(file_path)
            existing = existing[existing["stock_code"] != stock_code]
            df = pd.concat([existing, df], ignore_index=True)

        df.to_parquet(file_path, index=False)
        self._memory_cache[f"ohlcv_{stock_code}"] = df[df["stock_code"] == stock_code]
        self._update_ohlcv_metadata()

    def _update_ohlcv_metadata(self):
        file_path = CACHE_DIR / "ohlcv.parquet"
        if file_path.exists():
            df = pd.read_parquet(file_path)
            self._metadata["ohlcv"] = {
                "stock_count": df["stock_code"].nunique(),
                "record_count": len(df),
                "date_range": [
                    df["date"].min().isoformat() if not df.empty else None,
                    df["date"].max().isoformat() if not df.empty else None,
                ],
                "file_size_mb": round(file_path.stat().st_size / 1024 / 1024, 2),
                "last_update": datetime.now().isoformat(),
            }
            self._save_metadata()

    def get_cache_stats(self) -> dict:
        file_path = CACHE_DIR / "ohlcv.parquet"
        return {
            "total_stocks": self._metadata.get("ohlcv", {}).get("stock_count", 0),
            "cached_stocks": self._metadata.get("ohlcv", {}).get("stock_count", 0),
            "memory_cache_count": len(self._memory_cache),
            "file_cache_exists": file_path.exists(),
            "last_update": self._metadata.get("last_update"),
        }

    def get_cache_status(self) -> dict:
        return {
            "ohlcv": self._metadata.get("ohlcv"),
            "balance_sheet": self._metadata.get("balance_sheet"),
            "income": self._metadata.get("income"),
            "cash_flow": self._metadata.get("cash_flow"),
            "indicators": self._metadata.get("indicators"),
            "valuation": self._metadata.get("valuation"),
            "dividend": self._metadata.get("dividend"),
        }

    def clear_memory_cache(self):
        self._memory_cache.clear()
```

**Step 3: 提交**

```bash
git add backend/app/services/cache_service.py backend/app/data/cache/.gitkeep
git commit -m "feat: add CacheService with Parquet support"
```

---

## Task 3: 创建预加载脚本

**Files:**
- Create: `backend/app/scripts/__init__.py`
- Create: `backend/app/scripts/cache_loader.py`

**Step 1: 创建脚本目录**

```bash
mkdir -p backend/app/scripts
touch backend/app/scripts/__init__.py
```

**Step 2: 实现预加载脚本**

```python
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

            pool_detail = await repo.get_with_items(pool.id)
            stocks = pool_detail.items if pool_detail else []
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
```

**Step 3: 提交**

```bash
git add backend/app/scripts/
git commit -m "feat: add cache preload script"
```

---

## Task 4: 创建缓存 API 端点

**Files:**
- Create: `backend/app/api/v1/endpoints/cache.py`
- Modify: `backend/app/api/v1/router.py`

**Step 1: 创建缓存 API**

```python
from fastapi import APIRouter

from app.schemas.cache import CacheStats, CacheStatus
from app.services.cache_service import CacheService

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/status", response_model=CacheStatus)
async def get_cache_status():
    cache = CacheService()
    return cache.get_cache_status()


@router.get("/stats", response_model=CacheStats)
async def get_cache_stats():
    cache = CacheService()
    return cache.get_cache_stats()
```

**Step 2: 注册路由**

在 `backend/app/api/v1/router.py` 中添加:

```python
from app.api.v1.endpoints import cache
api_router.include_router(cache.router)
```

**Step 3: 提交**

```bash
git add backend/app/api/v1/endpoints/cache.py backend/app/api/v1/router.py
git commit -m "feat: add cache status API endpoints"
```

---

## Task 5: 集成到 data_service

**Files:**
- Modify: `backend/app/services/data_service.py`

**Step 1: 修改 get_stock_history 函数使用缓存**

在 `_fetch_history_from_akshare` 函数前添加缓存检查:

```python
from app.services.cache_service import CacheService

def get_stock_history(stock_code: str, start_date: date, end_date: date, ...) -> StockHistoryResponse:
    cache = CacheService()
    cached_df = cache.get_ohlcv(stock_code, start_date, end_date)
    
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
        return StockHistoryResponse(stock_code=stock_code, items=items)
    
    # 原有逻辑: 调用 AKShare 并缓存结果
    ...
```

**Step 2: 提交**

```bash
git add backend/app/services/data_service.py
git commit -m "feat: integrate cache into data_service"
```

---

## Task 6: 编写测试

**Files:**
- Create: `backend/tests/test_cache.py`

**Step 1: 创建缓存测试**

```python
import pytest
from datetime import date, timedelta
import pandas as pd
from pathlib import Path
import shutil

from app.services.cache_service import CacheService, CACHE_DIR


@pytest.fixture
def cache_service():
    CacheService._instance = None
    CacheService._memory_cache = {}
    yield CacheService()
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
    CacheService._instance = None


class TestCacheService:
    def test_save_and_get_ohlcv(self, cache_service):
        df = pd.DataFrame({
            "date": [date.today() - timedelta(days=i) for i in range(5)],
            "open": [100.0] * 5,
            "high": [105.0] * 5,
            "low": [95.0] * 5,
            "close": [102.0] * 5,
            "volume": [1000000] * 5,
            "amount": [100000000.0] * 5,
            "change_percent": [2.0] * 5,
        })

        cache_service.save_ohlcv("600519", df)

        result = cache_service.get_ohlcv(
            "600519",
            date.today() - timedelta(days=10),
            date.today()
        )

        assert result is not None
        assert len(result) == 5

    def test_get_nonexistent_stock(self, cache_service):
        result = cache_service.get_ohlcv(
            "999999",
            date.today() - timedelta(days=10),
            date.today()
        )
        assert result is None

    def test_cache_stats(self, cache_service):
        stats = cache_service.get_cache_stats()
        assert "total_stocks" in stats
        assert "memory_cache_count" in stats

    def test_cache_status(self, cache_service):
        status = cache_service.get_cache_status()
        assert "ohlcv" in status
```

**Step 2: 运行测试**

```bash
cd backend && ./venv/bin/pytest tests/test_cache.py -v
```

**Step 3: 提交**

```bash
git add backend/tests/test_cache.py
git commit -m "test: add cache service tests"
```

---

## Task 7: 运行预加载并验证

**Step 1: 运行预加载脚本**

```bash
cd backend && ./venv/bin/python -m app.scripts.cache_loader preload
```

**Step 2: 查看缓存状态**

```bash
cd backend && ./venv/bin/python -m app.scripts.cache_loader status
```

**Step 3: 运行完整测试**

```bash
cd backend && ./venv/bin/pytest -v --tb=short
```

**Step 4: 最终提交**

```bash
git add -A
git commit -m "feat: complete data cache implementation"
```

---

## 验收检查

- [ ] CacheService 单例正常工作
- [ ] Parquet 文件正确读写
- [ ] 预加载脚本成功执行
- [ ] 缓存 API 返回正确状态
- [ ] data_service 集成缓存
- [ ] 所有测试通过
