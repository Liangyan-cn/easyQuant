from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, verify_resource_ownership
from app.models.user import User
from app.schemas.sandbox import (
    DepositRequest,
    ResetAccountRequest,
    SandboxAccountCreate,
    SandboxAccountDetailResponse,
    SandboxAccountListResponse,
    SandboxAccountResponse,
    SandboxAccountUpdate,
    SandboxDeploymentCreate,
    SandboxDeploymentResponse,
    SandboxTransactionResponse,
    StrategyCompareRequest,
    StrategyCompareResponse,
    RunDeploymentRequest,
)
from app.services.sandbox_service import SandboxService
from app.repositories.sandbox_repo import SandboxAccountRepository, SandboxDeploymentRepository
from app.core.exceptions import NotFoundException

router = APIRouter()


@router.get("/accounts", response_model=SandboxAccountListResponse)
async def get_accounts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SandboxService(db)
    return await service.list_accounts(current_user.id, page, size)


@router.post("/accounts", response_model=SandboxAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: SandboxAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SandboxService(db)
    return await service.create_account(current_user.id, account_data)


async def get_account_with_ownership_check(
    account_id: int,
    db: AsyncSession,
    current_user: User,
) -> None:
    account_repo = SandboxAccountRepository(db)
    account = await account_repo.get_by_id(account_id)
    if not account:
        raise NotFoundException(detail="Account not found")
    verify_resource_ownership(account, current_user, "Account")


@router.get("/accounts/{account_id}", response_model=SandboxAccountDetailResponse)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_account_with_ownership_check(account_id, db, current_user)
    service = SandboxService(db)
    return await service.get_account_detail(account_id)


@router.put("/accounts/{account_id}", response_model=SandboxAccountResponse)
async def update_account(
    account_id: int,
    account_data: SandboxAccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_account_with_ownership_check(account_id, db, current_user)
    service = SandboxService(db)
    return await service.update_account(account_id, account_data)


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_account_with_ownership_check(account_id, db, current_user)
    service = SandboxService(db)
    await service.delete_account(account_id)


@router.post("/accounts/{account_id}/deposit", response_model=SandboxAccountResponse)
async def deposit(
    account_id: int,
    deposit_data: DepositRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_account_with_ownership_check(account_id, db, current_user)
    service = SandboxService(db)
    return await service.deposit(account_id, deposit_data)


@router.post("/accounts/{account_id}/reset", response_model=SandboxAccountResponse)
async def reset_account(
    account_id: int,
    reset_data: ResetAccountRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_account_with_ownership_check(account_id, db, current_user)
    service = SandboxService(db)
    return await service.reset_account(account_id, reset_data)


@router.post("/accounts/{account_id}/deployments", response_model=SandboxDeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    account_id: int,
    deployment_data: SandboxDeploymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_account_with_ownership_check(account_id, db, current_user)
    service = SandboxService(db)
    return await service.create_deployment(account_id, deployment_data)


async def get_deployment_with_ownership_check(
    deployment_id: int,
    db: AsyncSession,
    current_user: User,
) -> None:
    deployment_repo = SandboxDeploymentRepository(db)
    deployment = await deployment_repo.get_by_id(deployment_id)
    if not deployment:
        raise NotFoundException(detail="Deployment not found")
    account_repo = SandboxAccountRepository(db)
    account = await account_repo.get_by_id(deployment.account_id)
    if not account:
        raise NotFoundException(detail="Account not found")
    verify_resource_ownership(account, current_user, "Account")


@router.get("/deployments/{deployment_id}", response_model=SandboxDeploymentResponse)
async def get_deployment(
    deployment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_deployment_with_ownership_check(deployment_id, db, current_user)
    service = SandboxService(db)
    return await service.get_deployment(deployment_id)


@router.post("/deployments/{deployment_id}/run", response_model=SandboxDeploymentResponse)
async def run_deployment(
    deployment_id: int,
    run_data: Optional[RunDeploymentRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_deployment_with_ownership_check(deployment_id, db, current_user)
    service = SandboxService(db)
    run_date = run_data.run_date if run_data else None
    return await service.run_deployment(deployment_id, run_date)


@router.post("/deployments/{deployment_id}/start", response_model=SandboxDeploymentResponse)
async def start_deployment(
    deployment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_deployment_with_ownership_check(deployment_id, db, current_user)
    service = SandboxService(db)
    return await service.start_deployment(deployment_id)


@router.post("/deployments/{deployment_id}/stop", response_model=SandboxDeploymentResponse)
async def stop_deployment(
    deployment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_deployment_with_ownership_check(deployment_id, db, current_user)
    service = SandboxService(db)
    return await service.stop_deployment(deployment_id)


@router.delete("/deployments/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deployment(
    deployment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_deployment_with_ownership_check(deployment_id, db, current_user)
    service = SandboxService(db)
    await service.delete_deployment(deployment_id)


@router.post("/compare", response_model=StrategyCompareResponse)
async def compare_strategies(
    compare_data: StrategyCompareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SandboxService(db)
    return await service.compare_strategies(compare_data)
