import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.factor import Factor, FactorCategory
from app.repositories.factor_repo import FactorRepository, FactorValueRepository
from app.schemas.factor import FactorCalculateRequest, FactorCalculateResponse
from app.services.data_service import get_stock_history, get_stock_list

logger = logging.getLogger(__name__)


class FactorCalculator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.factor_repo = FactorRepository(db)
        self.value_repo = FactorValueRepository(db)

    async def calculate_factor(self, request: FactorCalculateRequest) -> FactorCalculateResponse:
        logger.info(f"Starting factor calculation: factor_id={request.factor_id}")

        factor = await self.factor_repo.get_by_id(request.factor_id)
        if not factor:
            raise ValueError(f"Factor with id {request.factor_id} not found")

        stock_codes = request.stock_codes
        if not stock_codes:
            stock_list = get_stock_list(page=1, size=500)
            stock_codes = [s.code for s in stock_list.items]

        logger.info(f"Calculating factor for {len(stock_codes)} stocks")

        calculated_values = []
        for stock_code in stock_codes:
            try:
                values = await self._calculate_single_stock(
                    factor, stock_code, request.start_date, request.end_date
                )
                calculated_values.extend(values)
            except Exception as e:
                logger.warning(f"Error calculating factor for {stock_code}: {e}")
                continue

        if calculated_values:
            await self.value_repo.replace_factor_values(request.factor_id, calculated_values)
            logger.info(f"Factor calculation completed: {len(calculated_values)} values")
        else:
            available_vars = "close, open, high, low, volume, returns"
            raise ValueError(
                f"因子计算失败：公式 '{factor.formula}' 无法计算。"
                f"当前支持的变量: {available_vars}。"
                f"财务类因子（如 ROE、PE 等）暂不支持计算。"
            )

        unique_dates = len(set(v["date"] for v in calculated_values))
        return FactorCalculateResponse(
            factor_id=request.factor_id,
            total_stocks=len(stock_codes),
            total_dates=unique_dates,
            calculated_count=len(calculated_values),
            status="completed",
        )

    async def _calculate_single_stock(
        self, factor: Factor, stock_code: str, start_date: date, end_date: date
    ) -> List[dict]:
        history = get_stock_history(
            stock_code,
            period="daily",
            start=start_date,
            end=end_date,
        )

        if not history.items:
            return []

        df = pd.DataFrame([
            {
                "date": item.date,
                "open": item.open,
                "high": item.high,
                "low": item.low,
                "close": item.close,
                "volume": item.volume,
            }
            for item in history.items
        ])

        if df.empty:
            return []

        df = df.sort_values("date")
        df["returns"] = df["close"].pct_change()

        values = self._apply_formula(factor, df)

        result = []
        for idx, row in df.iterrows():
            if idx in values.index and not pd.isna(values[idx]):
                result.append({
                    "stock_code": stock_code,
                    "date": row["date"],
                    "value": float(values[idx]),
                })

        return result

    def _apply_formula(self, factor: Factor, df: pd.DataFrame) -> pd.Series:
        code = factor.code

        if code == "momentum_20d":
            return (df["close"] - df["close"].shift(20)) / df["close"].shift(20)
        elif code == "momentum_60d":
            return (df["close"] - df["close"].shift(60)) / df["close"].shift(60)
        elif code == "volatility_20d":
            return df["returns"].rolling(20).std()
        elif code == "turnover_rate":
            return df["volume"] / df["volume"].rolling(20).mean()
        elif code == "log_market_cap":
            return np.log(df["close"] * df["volume"])
        else:
            return self._calculate_custom_formula(factor.formula, df)

    def _calculate_custom_formula(self, formula: str, df: pd.DataFrame) -> pd.Series:
        if not formula:
            return pd.Series([np.nan] * len(df), index=df.index)

        try:
            local_vars = {
                "close": df["close"],
                "open": df["open"],
                "high": df["high"],
                "low": df["low"],
                "volume": df["volume"],
                "returns": df["returns"],
                "np": np,
                "pd": pd,
            }
            result = eval(formula, {"__builtins__": {}}, local_vars)
            return result
        except Exception as e:
            logger.error(f"Error evaluating formula '{formula}': {e}")
            return pd.Series([np.nan] * len(df), index=df.index)


BUILTIN_FORMULAS: Dict[str, str] = {
    "momentum_20d": "(close - close.shift(20)) / close.shift(20)",
    "momentum_60d": "(close - close.shift(60)) / close.shift(60)",
    "volatility_20d": "returns.rolling(20).std()",
    "turnover_rate": "volume / volume.rolling(20).mean()",
    "log_market_cap": "np.log(close * volume)",
}
