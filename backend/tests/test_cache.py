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
