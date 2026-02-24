from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, verify_resource_ownership
from app.models.strategy import StrategyStatus, StrategyType
from app.models.user import User
from app.schemas.strategy import (
    BacktestCreate,
    BacktestDetailResponse,
    BacktestListResponse,
    BacktestResponse,
    OrderListResponse,
    OrderResponse,
    PositionListResponse,
    PositionResponse,
    StrategyCreate,
    StrategyListResponse,
    StrategyResponse,
    StrategyTypeStats,
    StrategyUpdate,
)
from app.services.strategy_service import StrategyService
from app.services.backtest_engine import BacktestEngine, BacktestConfig, get_strategy_class
from app.models.strategy import BacktestStatus

router = APIRouter()


@router.get("/", response_model=StrategyListResponse)
async def get_strategies(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    strategy_type: Optional[StrategyType] = None,
    status: Optional[StrategyStatus] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = StrategyService(db)
    strategies, total = await service.get_strategies(
        page, size, strategy_type, status, keyword, user_id=current_user.id
    )
    return StrategyListResponse(
        items=[StrategyResponse.model_validate(s) for s in strategies],
        total=total,
        page=page,
        size=size,
    )


@router.get("/types", response_model=List[StrategyTypeStats])
async def get_strategy_types(db: AsyncSession = Depends(get_db)):
    service = StrategyService(db)
    return await service.get_type_stats()


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = StrategyService(db)
    strategy = await service.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    if not strategy.is_builtin:
        verify_resource_ownership(strategy, current_user, "Strategy")
    return StrategyResponse.model_validate(strategy)


@router.post("/", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy_data: StrategyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = StrategyService(db)
    try:
        strategy = await service.create_strategy(strategy_data, user_id=current_user.id)
        return StrategyResponse.model_validate(strategy)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    strategy_data: StrategyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = StrategyService(db)
    existing_strategy = await service.get_strategy(strategy_id)
    if not existing_strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    verify_resource_ownership(existing_strategy, current_user, "Strategy")
    try:
        strategy = await service.update_strategy(strategy_id, strategy_data)
        return StrategyResponse.model_validate(strategy)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = StrategyService(db)
    existing_strategy = await service.get_strategy(strategy_id)
    if not existing_strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    verify_resource_ownership(existing_strategy, current_user, "Strategy")
    try:
        await service.delete_strategy(strategy_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{strategy_id}/clone", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def clone_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = StrategyService(db)
    try:
        cloned = await service.clone_strategy(strategy_id, user_id=current_user.id)
        return StrategyResponse.model_validate(cloned)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{strategy_id}/backtests", response_model=BacktestListResponse)
async def get_strategy_backtests(
    strategy_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = StrategyService(db)
    strategy = await service.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    if not strategy.is_builtin:
        verify_resource_ownership(strategy, current_user, "Strategy")

    backtests = await service.get_backtests_by_strategy(strategy_id, limit)
    return BacktestListResponse(
        items=[BacktestResponse.model_validate(b) for b in backtests],
        total=len(backtests),
    )


@router.post("/backtests", response_model=BacktestResponse, status_code=status.HTTP_201_CREATED)
async def create_backtest(
    backtest_data: BacktestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = StrategyService(db)
    strategy = await service.get_strategy(backtest_data.strategy_id)
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    if not strategy.is_builtin:
        verify_resource_ownership(strategy, current_user, "Strategy")
    try:
        backtest = await service.create_backtest(backtest_data)
        return BacktestResponse.model_validate(backtest)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/backtests/{backtest_id}", response_model=BacktestDetailResponse)
async def get_backtest(
    backtest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = StrategyService(db)
    backtest = await service.get_backtest(backtest_id)
    if not backtest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backtest not found")
    
    strategy = await service.get_strategy(backtest.strategy_id)
    if strategy and not strategy.is_builtin:
        verify_resource_ownership(strategy, current_user, "Strategy")

    result = backtest.result
    equity_curve = None
    if result and result.equity_curve:
        equity_curve = result.equity_curve

    return BacktestDetailResponse(
        backtest=BacktestResponse.model_validate(backtest),
        result=result,
        equity_curve=equity_curve,
    )


@router.delete("/backtests/{backtest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backtest(
    backtest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = StrategyService(db)
    backtest = await service.get_backtest(backtest_id)
    if not backtest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backtest not found")
    
    strategy = await service.get_strategy(backtest.strategy_id)
    if strategy and not strategy.is_builtin:
        verify_resource_ownership(strategy, current_user, "Strategy")
    
    await service.delete_backtest(backtest_id)


@router.get("/backtests/{backtest_id}/orders", response_model=OrderListResponse)
async def get_backtest_orders(
    backtest_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = StrategyService(db)
    backtest = await service.get_backtest(backtest_id)
    if not backtest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backtest not found")
    
    strategy = await service.get_strategy(backtest.strategy_id)
    if strategy and not strategy.is_builtin:
        verify_resource_ownership(strategy, current_user, "Strategy")

    orders, total = await service.get_backtest_orders(backtest_id, page, size)
    return OrderListResponse(
        items=[OrderResponse.model_validate(o) for o in orders],
        total=total,
    )


@router.get("/backtests/{backtest_id}/positions", response_model=PositionListResponse)
async def get_backtest_positions(
    backtest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = StrategyService(db)
    backtest = await service.get_backtest(backtest_id)
    if not backtest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backtest not found")
    
    strategy = await service.get_strategy(backtest.strategy_id)
    if strategy and not strategy.is_builtin:
        verify_resource_ownership(strategy, current_user, "Strategy")

    positions = await service.get_backtest_positions(backtest_id)
    return PositionListResponse(
        items=[PositionResponse.model_validate(p) for p in positions],
        total=len(positions),
    )


@router.post("/backtests/{backtest_id}/run")
async def run_backtest(
    backtest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = StrategyService(db)
    backtest = await service.get_backtest(backtest_id)
    if not backtest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backtest not found")

    strategy = await service.get_strategy(backtest.strategy_id)
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    if not strategy.is_builtin:
        verify_resource_ownership(strategy, current_user, "Strategy")

    if backtest.status == BacktestStatus.RUNNING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Backtest is already running")

    if backtest.status == BacktestStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Backtest already completed")

    if backtest.status == BacktestStatus.FAILED:
        from app.repositories.strategy_repo import BacktestResultRepository
        result_repo = BacktestResultRepository(db)
        await result_repo.delete_by_backtest_id(backtest_id)

    await service.update_backtest_status(backtest_id, BacktestStatus.RUNNING)

    try:
        config = BacktestConfig(
            initial_capital=backtest.initial_capital,
            commission_rate=backtest.commission_rate,
            slippage=backtest.slippage,
            benchmark=backtest.benchmark or "000300",
        )

        engine = BacktestEngine(config)
        strategy_class = get_strategy_class(strategy.code)
        strategy_instance = strategy_class(strategy.parameters or {})
        engine.set_strategy(strategy_instance)

        from datetime import datetime, timedelta
        import random

        start_date = backtest.start_date
        end_date = backtest.end_date
        stock_pool = backtest.stock_pool or ["000001.SZ", "000002.SZ", "600000.SH"]

        market_data = []
        current_date = start_date
        prices = {stock: 10.0 + random.random() * 20 for stock in stock_pool}

        while current_date <= end_date:
            if current_date.weekday() < 5:
                for stock in stock_pool:
                    change = (random.random() - 0.48) * 0.06
                    prices[stock] *= (1 + change)
                    market_data.append({
                        "date": current_date,
                        "stock_code": stock,
                        "open": prices[stock] * (1 + (random.random() - 0.5) * 0.02),
                        "high": prices[stock] * (1 + random.random() * 0.03),
                        "low": prices[stock] * (1 - random.random() * 0.03),
                        "close": prices[stock],
                        "volume": random.randint(1000000, 10000000),
                    })
            current_date += timedelta(days=1)

        result = engine.run(market_data)

        from app.repositories.strategy_repo import BacktestResultRepository
        result_repo = BacktestResultRepository(db)
        await result_repo.create({
            "backtest_id": backtest_id,
            "total_return": result.get("total_return"),
            "annual_return": result.get("annual_return"),
            "max_drawdown": result.get("max_drawdown"),
            "volatility": result.get("volatility"),
            "sharpe_ratio": result.get("sharpe_ratio"),
            "sortino_ratio": result.get("sortino_ratio"),
            "win_rate": result.get("win_rate"),
            "profit_loss_ratio": result.get("profit_loss_ratio"),
            "total_trades": result.get("total_trades"),
            "equity_curve": result.get("equity_curve"),
            "daily_returns": result.get("daily_returns"),
        })

        await service.update_backtest_status(backtest_id, BacktestStatus.COMPLETED)

        return {
            "status": "completed",
            "backtest_id": backtest_id,
            "result": {
                "total_return": result.get("total_return"),
                "annual_return": result.get("annual_return"),
                "max_drawdown": result.get("max_drawdown"),
                "sharpe_ratio": result.get("sharpe_ratio"),
                "total_trades": result.get("total_trades"),
            }
        }

    except Exception as e:
        await service.update_backtest_status(backtest_id, BacktestStatus.FAILED, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
