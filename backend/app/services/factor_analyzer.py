import logging
from datetime import date
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.factor_repo import FactorRepository, FactorValueRepository, FactorEvaluationRepository
from app.schemas.factor import (
    FactorAnalyzeRequest,
    FactorAnalyzeResponse,
    FactorCalculateRequest,
    FactorEvaluationRequest,
    FactorEvaluationResponse,
)
from app.services.factor_calculator import FactorCalculator
from app.services.factor_evaluator import FactorEvaluator

logger = logging.getLogger(__name__)


class FactorAnalyzer:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.factor_repo = FactorRepository(db)
        self.value_repo = FactorValueRepository(db)
        self.eval_repo = FactorEvaluationRepository(db)
        self.calculator = FactorCalculator(db)
        self.evaluator = FactorEvaluator(db)

    async def analyze_factor(self, request: FactorAnalyzeRequest) -> FactorAnalyzeResponse:
        logger.info(f"Starting factor analysis: factor_id={request.factor_id}")

        factor = await self.factor_repo.get_by_id(request.factor_id)
        if not factor:
            raise ValueError(f"Factor with id {request.factor_id} not found")

        existing_values = await self.value_repo.get_values(
            request.factor_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        calculated_count = len(existing_values)
        need_calculate = request.force_recalculate or calculated_count == 0

        if need_calculate:
            logger.info(f"Calculating factor values (force={request.force_recalculate}, existing={calculated_count})")
            calc_request = FactorCalculateRequest(
                factor_id=request.factor_id,
                stock_codes=request.stock_codes,
                start_date=request.start_date,
                end_date=request.end_date,
            )
            calc_result = await self.calculator.calculate_factor(calc_request)
            calculated_count = calc_result.calculated_count

        eval_request = FactorEvaluationRequest(
            factor_id=request.factor_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        eval_result = await self.evaluator.evaluate_factor(eval_request)

        return FactorAnalyzeResponse(
            factor_id=request.factor_id,
            calculated_count=calculated_count,
            evaluation=eval_result.evaluation,
            ic_series=eval_result.ic_series,
            group_returns=eval_result.group_returns,
        )

    async def get_latest_evaluation(self, factor_id: int) -> Optional[FactorEvaluationResponse]:
        evaluation = await self.eval_repo.get_latest(factor_id)
        if evaluation:
            return FactorEvaluationResponse.model_validate(evaluation)
        return None
