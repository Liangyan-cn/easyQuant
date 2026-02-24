from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, verify_resource_ownership
from app.models.user import User
from app.schemas.factor import (
    FactorAnalyzeRequest,
    FactorAnalyzeResponse,
    FactorCalculateRequest,
    FactorCalculateResponse,
    FactorCategoryStats,
    FactorCreate,
    FactorEvaluationDetailResponse,
    FactorEvaluationRequest,
    FactorEvaluationResponse,
    FactorListResponse,
    FactorResponse,
    FactorUpdate,
    FactorValueListResponse,
)
from app.services.factor_analyzer import FactorAnalyzer
from app.services.factor_calculator import FactorCalculator
from app.services.factor_evaluator import FactorEvaluator
from app.services.factor_service import FactorService

router = APIRouter()


@router.get("", response_model=FactorListResponse)
async def list_factors(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FactorService(db)
    return await service.list_factors(page, size, category, keyword, user_id=current_user.id)


@router.post("", response_model=FactorResponse, status_code=201)
async def create_factor(
    factor_data: FactorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FactorService(db)
    return await service.create_factor(factor_data, current_user.id)


@router.get("/categories", response_model=List[FactorCategoryStats])
async def get_category_stats(
    db: AsyncSession = Depends(get_db),
):
    service = FactorService(db)
    return await service.get_category_stats()


@router.get("/{factor_id}", response_model=FactorResponse)
async def get_factor(
    factor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FactorService(db)
    factor = await service.get_factor(factor_id)
    verify_resource_ownership(factor, current_user, "Factor")
    return factor


@router.put("/{factor_id}", response_model=FactorResponse)
async def update_factor(
    factor_id: int,
    factor_data: FactorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FactorService(db)
    factor = await service.get_factor(factor_id)
    verify_resource_ownership(factor, current_user, "Factor")
    return await service.update_factor(factor_id, factor_data)


@router.delete("/{factor_id}", status_code=204)
async def delete_factor(
    factor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FactorService(db)
    factor = await service.get_factor(factor_id)
    verify_resource_ownership(factor, current_user, "Factor")
    await service.delete_factor(factor_id)


@router.post("/init-builtin", response_model=dict)
async def init_builtin_factors(
    db: AsyncSession = Depends(get_db),
):
    service = FactorService(db)
    count = await service.init_builtin_factors()
    return {"message": f"Initialized {count} built-in factors", "count": count}


@router.post("/calculate", response_model=FactorCalculateResponse)
async def calculate_factor(
    request: FactorCalculateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import HTTPException
    calculator = FactorCalculator(db)
    try:
        return await calculator.calculate_factor(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/evaluate", response_model=FactorEvaluationDetailResponse)
async def evaluate_factor(
    request: FactorEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import HTTPException
    evaluator = FactorEvaluator(db)
    try:
        return await evaluator.evaluate_factor(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{factor_id}/evaluations", response_model=List[FactorEvaluationResponse])
async def get_factor_evaluations(
    factor_id: int,
    db: AsyncSession = Depends(get_db),
):
    evaluator = FactorEvaluator(db)
    return await evaluator.get_evaluation_history(factor_id)


@router.post("/analyze", response_model=FactorAnalyzeResponse)
async def analyze_factor(
    request: FactorAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import HTTPException
    analyzer = FactorAnalyzer(db)
    try:
        return await analyzer.analyze_factor(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{factor_id}/latest-evaluation", response_model=Optional[FactorEvaluationResponse])
async def get_latest_evaluation(
    factor_id: int,
    db: AsyncSession = Depends(get_db),
):
    analyzer = FactorAnalyzer(db)
    return await analyzer.get_latest_evaluation(factor_id)
