import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
METADATA_FILE = CACHE_DIR / "metadata.json"

FINANCIAL_CACHE_TTL_DAYS = 7


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
            "financial_indicators": self._metadata.get("financial_indicators"),
            "valuation": self._metadata.get("valuation"),
        }

    def clear_memory_cache(self):
        self._memory_cache.clear()

    def _get_all_ohlcv_stocks(self) -> Optional[list]:
        file_path = CACHE_DIR / "ohlcv.parquet"
        if file_path.exists():
            df = pd.read_parquet(file_path, columns=["stock_code"])
            return df["stock_code"].unique().tolist()
        return None

    def append_ohlcv(self, stock_code: str, df: pd.DataFrame):
        df = df.copy()
        df["stock_code"] = stock_code

        file_path = CACHE_DIR / "ohlcv.parquet"
        if file_path.exists():
            existing = pd.read_parquet(file_path)
            existing_stock = existing[existing["stock_code"] == stock_code]
            if not existing_stock.empty:
                existing_dates = set(pd.to_datetime(existing_stock["date"]).dt.date)
                df["date"] = pd.to_datetime(df["date"]).dt.date
                df = df[~df["date"].isin(existing_dates)]

            if not df.empty:
                df = pd.concat([existing, df], ignore_index=True)
            else:
                return
        
        df.to_parquet(file_path, index=False)
        self._memory_cache.pop(f"ohlcv_{stock_code}", None)
        self._update_ohlcv_metadata()

    def get_financial_indicators(self, stock_code: str) -> Optional[pd.DataFrame]:
        cache_key = f"financial_{stock_code}"
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        file_path = CACHE_DIR / "financial_indicators.parquet"
        if file_path.exists():
            df = pd.read_parquet(file_path)
            stock_df = df[df["stock_code"] == stock_code]
            if not stock_df.empty:
                cache_time = self._get_stock_cache_time("financial_indicators", stock_code)
                if cache_time and self._is_financial_cache_valid(cache_time):
                    self._memory_cache[cache_key] = stock_df
                    return stock_df
        return None

    def save_financial_indicators(self, stock_code: str, df: pd.DataFrame):
        df = df.copy()
        df["stock_code"] = stock_code
        df["cached_at"] = datetime.now().isoformat()

        file_path = CACHE_DIR / "financial_indicators.parquet"
        if file_path.exists():
            existing = pd.read_parquet(file_path)
            existing = existing[existing["stock_code"] != stock_code]
            df = pd.concat([existing, df], ignore_index=True)

        df.to_parquet(file_path, index=False)
        self._memory_cache[f"financial_{stock_code}"] = df[df["stock_code"] == stock_code]
        self._update_financial_metadata()

    def _update_financial_metadata(self):
        file_path = CACHE_DIR / "financial_indicators.parquet"
        if file_path.exists():
            df = pd.read_parquet(file_path)
            self._metadata["financial_indicators"] = {
                "stock_count": df["stock_code"].nunique(),
                "record_count": len(df),
                "file_size_mb": round(file_path.stat().st_size / 1024 / 1024, 2),
                "last_update": datetime.now().isoformat(),
            }
            self._save_metadata()

    def get_valuation(self, stock_code: str) -> Optional[pd.DataFrame]:
        cache_key = f"valuation_{stock_code}"
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        file_path = CACHE_DIR / "valuation.parquet"
        if file_path.exists():
            df = pd.read_parquet(file_path)
            stock_df = df[df["stock_code"] == stock_code]
            if not stock_df.empty:
                cache_time = self._get_stock_cache_time("valuation", stock_code)
                if cache_time and self._is_financial_cache_valid(cache_time):
                    self._memory_cache[cache_key] = stock_df
                    return stock_df
        return None

    def save_valuation(self, stock_code: str, df: pd.DataFrame):
        df = df.copy()
        df["stock_code"] = stock_code
        df["cached_at"] = datetime.now().isoformat()

        file_path = CACHE_DIR / "valuation.parquet"
        if file_path.exists():
            existing = pd.read_parquet(file_path)
            existing = existing[existing["stock_code"] != stock_code]
            df = pd.concat([existing, df], ignore_index=True)

        df.to_parquet(file_path, index=False)
        self._memory_cache[f"valuation_{stock_code}"] = df[df["stock_code"] == stock_code]
        self._update_valuation_metadata()

    def _update_valuation_metadata(self):
        file_path = CACHE_DIR / "valuation.parquet"
        if file_path.exists():
            df = pd.read_parquet(file_path)
            self._metadata["valuation"] = {
                "stock_count": df["stock_code"].nunique(),
                "record_count": len(df),
                "file_size_mb": round(file_path.stat().st_size / 1024 / 1024, 2),
                "last_update": datetime.now().isoformat(),
            }
            self._save_metadata()

    def _get_stock_cache_time(self, cache_type: str, stock_code: str) -> Optional[datetime]:
        file_map = {
            "financial_indicators": "financial_indicators.parquet",
            "valuation": "valuation.parquet",
        }
        file_path = CACHE_DIR / file_map.get(cache_type, "")
        if file_path.exists():
            df = pd.read_parquet(file_path)
            stock_df = df[df["stock_code"] == stock_code]
            if not stock_df.empty and "cached_at" in stock_df.columns:
                cached_at = stock_df["cached_at"].iloc[0]
                if isinstance(cached_at, str):
                    return datetime.fromisoformat(cached_at)
        return None

    def _is_financial_cache_valid(self, cache_time: datetime) -> bool:
        return (datetime.now() - cache_time).days < FINANCIAL_CACHE_TTL_DAYS

    def get_all_cached_stocks(self, cache_type: str) -> Optional[list]:
        file_map = {
            "ohlcv": "ohlcv.parquet",
            "financial_indicators": "financial_indicators.parquet",
            "valuation": "valuation.parquet",
        }
        file_path = CACHE_DIR / file_map.get(cache_type, "")
        if file_path.exists():
            df = pd.read_parquet(file_path, columns=["stock_code"])
            return df["stock_code"].unique().tolist()
        return None
