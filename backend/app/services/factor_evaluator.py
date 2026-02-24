import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.factor import FactorEvaluation
from app.repositories.factor_repo import FactorEvaluationRepository, FactorRepository, FactorValueRepository
from app.schemas.factor import (
    FactorEvaluationDetailResponse,
    FactorEvaluationRequest,
    FactorEvaluationResponse,
    GroupReturnItem,
)
from app.services.data_service import get_stock_history

logger = logging.getLogger(__name__)


class FactorEvaluator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.factor_repo = FactorRepository(db)
        self.value_repo = FactorValueRepository(db)
        self.eval_repo = FactorEvaluationRepository(db)

    async def evaluate_factor(self, request: FactorEvaluationRequest) -> FactorEvaluationDetailResponse:
        logger.info(f"Starting factor evaluation: factor_id={request.factor_id}")

        factor = await self.factor_repo.get_by_id(request.factor_id)
        if not factor:
            raise ValueError(f"Factor with id {request.factor_id} not found")

        factor_values = await self.value_repo.get_values(
            request.factor_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        if not factor_values:
            raise ValueError("未找到因子值数据，请先点击「计算因子值」按钮生成数据后再评估")

        df = pd.DataFrame([
            {
                "date": v.date,
                "stock_code": v.stock_code,
                "factor_value": v.value,
            }
            for v in factor_values
        ])
        df["date"] = pd.to_datetime(df["date"])

        returns_data = await self._get_returns_data(
            df["stock_code"].unique().tolist(),
            request.start_date,
            request.end_date,
        )
        if not returns_data.empty:
            returns_data["date"] = pd.to_datetime(returns_data["date"])

        df = df.merge(returns_data, on=["date", "stock_code"], how="inner")

        ic_series = self._calculate_ic_series(df)
        ic_mean = ic_series["ic"].mean() if not ic_series.empty else None
        ic_std = ic_series["ic"].std() if not ic_series.empty else None
        ir = ic_mean / ic_std if ic_std and ic_std > 0 else None
        ic_positive_ratio = (ic_series["ic"] > 0).mean() if not ic_series.empty else None

        group_returns = self._calculate_group_returns(df)

        evaluation_data = {
            "factor_id": request.factor_id,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "ic_mean": float(ic_mean) if ic_mean is not None else None,
            "ic_std": float(ic_std) if ic_std is not None else None,
            "ir": float(ir) if ir is not None else None,
            "ic_positive_ratio": float(ic_positive_ratio) if ic_positive_ratio is not None else None,
        }

        evaluation = await self.eval_repo.create(evaluation_data)
        logger.info(f"Factor evaluation completed: id={evaluation.id}")

        return FactorEvaluationDetailResponse(
            evaluation=FactorEvaluationResponse.model_validate(evaluation),
            ic_series=[{"date": str(row["date"]), "ic": row["ic"]} for _, row in ic_series.iterrows()],
            group_returns=group_returns,
        )

    async def _get_returns_data(
        self, stock_codes: List[str], start_date: date, end_date: date
    ) -> pd.DataFrame:
        all_returns = []

        for stock_code in stock_codes[:100]:
            try:
                history = get_stock_history(
                    stock_code,
                    period="daily",
                    start=start_date,
                    end=end_date,
                )

                if history.items:
                    df = pd.DataFrame([
                        {"date": item.date, "close": item.close}
                        for item in history.items
                    ])
                    df = df.sort_values("date")
                    df["returns"] = df["close"].pct_change()
                    df["stock_code"] = stock_code
                    all_returns.append(df[["date", "stock_code", "returns"]])
            except Exception as e:
                logger.warning(f"Error getting returns for {stock_code}: {e}")
                continue

        if all_returns:
            return pd.concat(all_returns, ignore_index=True)
        return pd.DataFrame(columns=["date", "stock_code", "returns"])

    def _calculate_ic_series(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "factor_value" not in df.columns or "returns" not in df.columns:
            return pd.DataFrame(columns=["date", "ic"])

        ic_list = []
        for dt, group in df.groupby("date"):
            if len(group) < 10:
                continue

            valid_data = group.dropna(subset=["factor_value", "returns"])
            if len(valid_data) < 10:
                continue

            ic = valid_data["factor_value"].corr(valid_data["returns"])
            if not np.isnan(ic):
                ic_list.append({"date": dt, "ic": ic})

        return pd.DataFrame(ic_list)

    def _calculate_group_returns(self, df: pd.DataFrame, n_groups: int = 5) -> List[GroupReturnItem]:
        if df.empty or "factor_value" not in df.columns or "returns" not in df.columns:
            return []

        group_returns = []

        for dt, group in df.groupby("date"):
            valid_data = group.dropna(subset=["factor_value", "returns"])
            if len(valid_data) < n_groups:
                continue

            try:
                valid_data["group"] = pd.qcut(
                    valid_data["factor_value"],
                    n_groups,
                    labels=range(1, n_groups + 1),
                    duplicates="drop",
                )
            except ValueError:
                continue

            for g in range(1, n_groups + 1):
                g_data = valid_data[valid_data["group"] == g]
                if not g_data.empty:
                    group_returns.append({
                        "date": dt,
                        "group": g,
                        "return": g_data["returns"].mean(),
                        "count": len(g_data),
                    })

        if not group_returns:
            return []

        group_df = pd.DataFrame(group_returns)
        result = []
        for g in range(1, n_groups + 1):
            g_data = group_df[group_df["group"] == g]
            if not g_data.empty:
                result.append(GroupReturnItem(
                    group=g,
                    return_value=float(g_data["return"].mean()),
                    stock_count=int(g_data["count"].mean()),
                ))

        return result

    async def get_evaluation_history(self, factor_id: int) -> List[FactorEvaluationResponse]:
        evaluations = await self.eval_repo.get_by_factor(factor_id)
        return [FactorEvaluationResponse.model_validate(e) for e in evaluations]
