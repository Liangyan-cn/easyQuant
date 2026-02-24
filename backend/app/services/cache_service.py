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
