import logging
import statistics
from datetime import date, timedelta
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.core.trading_config import TradingConfig, MAX_RECENT_TRANSACTIONS
from app.models.sandbox import (
    DeploymentStatus,
    SandboxAccount,
    SandboxDailyValue,
    SandboxStatus,
    SandboxTransaction,
    TransactionType,
)
from app.repositories.sandbox_repo import (
    SandboxAccountRepository,
    SandboxDailyValueRepository,
    SandboxDeploymentRepository,
    SandboxPositionRepository,
    SandboxTransactionRepository,
)
from app.repositories.strategy_repo import StrategyRepository
from app.services.sandbox_engine import ExecutionResult, SandboxExecutionEngine
from app.schemas.sandbox import (
    DepositRequest,
    ResetAccountRequest,
    SandboxAccountCreate,
    SandboxAccountDetailResponse,
    SandboxAccountListResponse,
    SandboxAccountResponse,
    SandboxAccountUpdate,
    SandboxDailyValueResponse,
    SandboxDeploymentCreate,
    SandboxDeploymentResponse,
    SandboxDeploymentUpdate,
    SandboxPositionResponse,
    SandboxTransactionResponse,
    StrategyCompareItem,
    StrategyCompareRequest,
    StrategyCompareResponse,
)

logger = logging.getLogger(__name__)


class SandboxService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_repo = SandboxAccountRepository(db)
        self.position_repo = SandboxPositionRepository(db)
        self.transaction_repo = SandboxTransactionRepository(db)
        self.deployment_repo = SandboxDeploymentRepository(db)
        self.daily_value_repo = SandboxDailyValueRepository(db)
        self.strategy_repo = StrategyRepository(db)

    async def create_account(
        self, user_id: int, data: SandboxAccountCreate
    ) -> SandboxAccountResponse:
        logger.info(f"Creating sandbox account for user {user_id}: {data.name}")
        account = await self.account_repo.create(user_id, data.model_dump())
        logger.info(f"Sandbox account created: id={account.id}")
        return SandboxAccountResponse.model_validate(account)

    async def get_account(self, account_id: int) -> SandboxAccountResponse:
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise NotFoundException(detail=f"Sandbox account with id {account_id} not found")
        return SandboxAccountResponse.model_validate(account)

    async def get_account_detail(self, account_id: int) -> SandboxAccountDetailResponse:
        account = await self.account_repo.get_with_details(account_id)
        if not account:
            raise NotFoundException(detail=f"Sandbox account with id {account_id} not found")

        return SandboxAccountDetailResponse(
            account=SandboxAccountResponse.model_validate(account),
            positions=[SandboxPositionResponse.model_validate(p) for p in account.positions],
            recent_transactions=[
                SandboxTransactionResponse.model_validate(t)
                for t in sorted(account.transactions, key=lambda x: x.created_at, reverse=True)[:MAX_RECENT_TRANSACTIONS]
            ],
            deployments=[SandboxDeploymentResponse.model_validate(d) for d in account.deployments],
            daily_values=[SandboxDailyValueResponse.model_validate(v) for v in account.daily_values],
        )

    async def list_accounts(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> SandboxAccountListResponse:
        accounts, total = await self.account_repo.get_by_user(user_id, page, size)
        return SandboxAccountListResponse(
            items=[SandboxAccountResponse.model_validate(a) for a in accounts],
            total=total,
            page=page,
            size=size,
        )

    async def update_account(
        self, account_id: int, data: SandboxAccountUpdate
    ) -> SandboxAccountResponse:
        logger.info(f"Updating sandbox account: id={account_id}")
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise NotFoundException(detail=f"Sandbox account with id {account_id} not found")

        updated = await self.account_repo.update(account, data.model_dump(exclude_unset=True))
        logger.info(f"Sandbox account updated: id={account_id}")
        return SandboxAccountResponse.model_validate(updated)

    async def delete_account(self, account_id: int) -> bool:
        logger.info(f"Deleting sandbox account: id={account_id}")
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise NotFoundException(detail=f"Sandbox account with id {account_id} not found")

        result = await self.account_repo.delete(account)
        logger.info(f"Sandbox account deleted: id={account_id}")
        return result

    async def deposit(
        self, account_id: int, data: DepositRequest
    ) -> SandboxAccountResponse:
        logger.info(f"Depositing to account {account_id}: amount={data.amount}")
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise NotFoundException(detail=f"Sandbox account with id {account_id} not found")

        if account.status != SandboxStatus.ACTIVE:
            raise ConflictException(detail="Cannot deposit to inactive account")

        await self.transaction_repo.create(
            account_id,
            {
                "transaction_type": TransactionType.DEPOSIT,
                "amount": data.amount,
                "description": data.description or "Account deposit",
            },
        )

        new_cash = account.current_cash + data.amount
        new_total = account.total_value + data.amount
        updated = await self.account_repo.update(
            account, {"current_cash": new_cash, "total_value": new_total}
        )
        logger.info(f"Deposit completed: account={account_id}, new_cash={new_cash}")
        return SandboxAccountResponse.model_validate(updated)

    async def reset_account(
        self, account_id: int, data: ResetAccountRequest
    ) -> SandboxAccountResponse:
        logger.info(f"Resetting account {account_id} with capital={data.initial_capital}")
        account = await self.account_repo.get_with_details(account_id)
        if not account:
            raise NotFoundException(detail=f"Sandbox account with id {account_id} not found")

        running_deployments = [
            d for d in account.deployments if d.status == DeploymentStatus.RUNNING
        ]
        if running_deployments:
            raise ConflictException(
                detail="Cannot reset account with running deployments. Stop all deployments first."
            )

        for position in account.positions:
            await self.position_repo.delete(position)

        updated = await self.account_repo.update(
            account,
            {
                "initial_capital": data.initial_capital,
                "current_cash": data.initial_capital,
                "total_value": data.initial_capital,
                "status": SandboxStatus.ACTIVE,
            },
        )

        await self.transaction_repo.create(
            account_id,
            {
                "transaction_type": TransactionType.DEPOSIT,
                "amount": data.initial_capital,
                "description": f"Account reset with initial capital {data.initial_capital}",
            },
        )

        logger.info(f"Account reset completed: id={account_id}")
        return SandboxAccountResponse.model_validate(updated)

    async def create_deployment(
        self, account_id: int, data: SandboxDeploymentCreate
    ) -> SandboxDeploymentResponse:
        logger.info(f"Creating deployment for account {account_id}: {data.name}")
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise NotFoundException(detail=f"Sandbox account with id {account_id} not found")

        if account.status != SandboxStatus.ACTIVE:
            raise ConflictException(detail="Cannot create deployment for inactive account")

        strategy = await self.strategy_repo.get_by_id(data.strategy_id)
        if not strategy:
            raise NotFoundException(detail=f"Strategy with id {data.strategy_id} not found")

        if data.end_date and data.end_date < data.start_date:
            raise BadRequestException(detail="End date must be after start date")

        one_year_ago = date.today() - timedelta(days=365)
        if data.start_date < one_year_ago:
            logger.warning(f"Start date {data.start_date} is earlier than 1 year ago ({one_year_ago})")
            raise BadRequestException(detail=f"Start date cannot be earlier than 1 year ago ({one_year_ago})")

        deployment = await self.deployment_repo.create(
            account_id,
            {
                "strategy_id": data.strategy_id,
                "name": data.name,
                "start_date": data.start_date,
                "end_date": data.end_date,
                "stock_pool": data.stock_pool,
                "parameters": data.parameters,
                "allocation_ratio": data.allocation_ratio,
            },
        )
        logger.info(f"Deployment created: id={deployment.id}")
        return SandboxDeploymentResponse.model_validate(deployment)

    async def get_deployment(self, deployment_id: int) -> SandboxDeploymentResponse:
        deployment = await self.deployment_repo.get_by_id(deployment_id)
        if not deployment:
            raise NotFoundException(detail=f"Deployment with id {deployment_id} not found")
        return SandboxDeploymentResponse.model_validate(deployment)

    async def list_deployments(self, account_id: int) -> List[SandboxDeploymentResponse]:
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise NotFoundException(detail=f"Sandbox account with id {account_id} not found")

        deployments = await self.deployment_repo.get_by_account(account_id)
        return [SandboxDeploymentResponse.model_validate(d) for d in deployments]

    async def update_deployment(
        self, deployment_id: int, data: SandboxDeploymentUpdate
    ) -> SandboxDeploymentResponse:
        logger.info(f"Updating deployment: id={deployment_id}")
        deployment = await self.deployment_repo.get_by_id(deployment_id)
        if not deployment:
            raise NotFoundException(detail=f"Deployment with id {deployment_id} not found")

        if deployment.status == DeploymentStatus.COMPLETED:
            raise ConflictException(detail="Cannot update completed deployment")

        updated = await self.deployment_repo.update(
            deployment, data.model_dump(exclude_unset=True)
        )
        logger.info(f"Deployment updated: id={deployment_id}")
        return SandboxDeploymentResponse.model_validate(updated)

    async def delete_deployment(self, deployment_id: int) -> bool:
        logger.info(f"Deleting deployment: id={deployment_id}")
        deployment = await self.deployment_repo.get_by_id(deployment_id)
        if not deployment:
            raise NotFoundException(detail=f"Deployment with id {deployment_id} not found")

        if deployment.status == DeploymentStatus.RUNNING:
            raise ConflictException(detail="Cannot delete running deployment. Stop it first.")

        result = await self.deployment_repo.delete(deployment)
        logger.info(f"Deployment deleted: id={deployment_id}")
        return result

    async def start_deployment(self, deployment_id: int) -> SandboxDeploymentResponse:
        logger.info(f"Starting deployment: id={deployment_id}")
        deployment = await self.deployment_repo.get_by_id(deployment_id)
        if not deployment:
            raise NotFoundException(detail=f"Deployment with id {deployment_id} not found")

        if deployment.status not in [DeploymentStatus.PENDING, DeploymentStatus.PAUSED]:
            raise ConflictException(
                detail=f"Cannot start deployment with status {deployment.status}"
            )

        account = await self.account_repo.get_by_id(deployment.account_id)
        if account.status != SandboxStatus.ACTIVE:
            raise ConflictException(detail="Cannot start deployment for inactive account")

        updated = await self.deployment_repo.update(
            deployment, {"status": DeploymentStatus.RUNNING, "error_message": None}
        )
        logger.info(f"Deployment started: id={deployment_id}")
        return SandboxDeploymentResponse.model_validate(updated)

    async def stop_deployment(self, deployment_id: int) -> SandboxDeploymentResponse:
        logger.info(f"Stopping deployment: id={deployment_id}")
        deployment = await self.deployment_repo.get_by_id(deployment_id)
        if not deployment:
            raise NotFoundException(detail=f"Deployment with id {deployment_id} not found")

        if deployment.status != DeploymentStatus.RUNNING:
            raise ConflictException(detail="Deployment is not running")

        updated = await self.deployment_repo.update(
            deployment, {"status": DeploymentStatus.PAUSED}
        )
        logger.info(f"Deployment stopped: id={deployment_id}")
        return SandboxDeploymentResponse.model_validate(updated)

    async def run_deployment(
        self, deployment_id: int, run_date: Optional[date] = None
    ) -> SandboxDeploymentResponse:
        logger.info(f"Running deployment: id={deployment_id}, date={run_date}")
        deployment = await self.deployment_repo.get_by_id(deployment_id)
        if not deployment:
            raise NotFoundException(detail=f"Deployment with id {deployment_id} not found")

        if deployment.status not in [DeploymentStatus.PENDING, DeploymentStatus.RUNNING]:
            raise ConflictException(detail=f"Deployment cannot be run in {deployment.status} status")

        account = await self.account_repo.get_by_id(deployment.account_id)
        if account.status != SandboxStatus.ACTIVE:
            raise ConflictException(detail="Account is not active")

        if deployment.status == DeploymentStatus.PENDING:
            deployment = await self.deployment_repo.update(
                deployment, {"status": DeploymentStatus.RUNNING}
            )

        execution_date = run_date or date.today()

        if deployment.end_date and execution_date > deployment.end_date:
            await self.deployment_repo.update(
                deployment, {"status": DeploymentStatus.COMPLETED}
            )
            raise ConflictException(detail="Deployment has reached end date")

        engine = SandboxExecutionEngine(self.db)
        result = await engine.execute_deployment(deployment, execution_date)

        if result.success:
            updated = await self.deployment_repo.update(
                deployment,
                {
                    "last_run_date": execution_date,
                    "last_run_result": {
                        "execution_date": str(result.execution_date),
                        "signals": result.signals,
                        "orders_executed": result.orders_executed,
                        "total_value": result.total_value,
                        "daily_return": result.daily_return,
                    },
                    "error_message": None,
                },
            )
            logger.info(f"Deployment run completed: id={deployment_id}")
            return SandboxDeploymentResponse.model_validate(updated)
        else:
            logger.error(f"Deployment run failed: id={deployment_id}, error={result.error_message}")
            await self.deployment_repo.update(
                deployment,
                {
                    "status": DeploymentStatus.FAILED,
                    "error_message": result.error_message,
                },
            )
            raise BadRequestException(detail=f"Strategy execution failed: {result.error_message}")

    async def get_positions(self, account_id: int) -> List[SandboxPositionResponse]:
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise NotFoundException(detail=f"Sandbox account with id {account_id} not found")

        positions = await self.position_repo.get_by_account(account_id)
        return [SandboxPositionResponse.model_validate(p) for p in positions]

    async def get_transactions(
        self, account_id: int, limit: int = 50
    ) -> List[SandboxTransactionResponse]:
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise NotFoundException(detail=f"Sandbox account with id {account_id} not found")

        transactions = await self.transaction_repo.get_by_account(account_id, limit)
        return [SandboxTransactionResponse.model_validate(t) for t in transactions]

    async def get_daily_values(
        self,
        account_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[SandboxDailyValueResponse]:
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise NotFoundException(detail=f"Sandbox account with id {account_id} not found")

        daily_values = await self.daily_value_repo.get_by_account(
            account_id, start_date, end_date
        )
        return [SandboxDailyValueResponse.model_validate(v) for v in daily_values]

    async def get_active_deployments(self) -> List[SandboxDeploymentResponse]:
        deployments = await self.deployment_repo.get_active_deployments()
        return [SandboxDeploymentResponse.model_validate(d) for d in deployments]

    async def run_all_deployments(
        self, run_date: Optional[date] = None
    ) -> Dict[int, ExecutionResult]:
        execution_date = run_date or date.today()
        logger.info(f"Running all active deployments for date: {execution_date}")

        engine = SandboxExecutionEngine(self.db)
        results = await engine.run_all_active_deployments(execution_date)

        logger.info(
            f"Completed running {len(results)} deployments. "
            f"Success: {sum(1 for r in results.values() if r.success)}, "
            f"Failed: {sum(1 for r in results.values() if not r.success)}"
        )

        return results

    async def compare_strategies(
        self, request: StrategyCompareRequest
    ) -> StrategyCompareResponse:
        logger.info(f"Comparing strategies: deployment_ids={request.deployment_ids}")
        items: List[StrategyCompareItem] = []

        for deployment_id in request.deployment_ids:
            try:
                deployment = await self.deployment_repo.get_by_id(deployment_id)
                if not deployment:
                    continue

                daily_values = await self.daily_value_repo.get_by_account(
                    deployment.account_id,
                    request.start_date,
                    request.end_date,
                )

                transactions = await self.transaction_repo.get_by_deployment(deployment_id)
                sell_transactions = [
                    t for t in transactions
                    if t.transaction_type == TransactionType.SELL
                ]

                daily_values_data = [
                    {
                        "date": dv.date.isoformat(),
                        "total_value": dv.total_value,
                        "daily_return": dv.daily_return,
                        "cumulative_return": dv.cumulative_return,
                    }
                    for dv in daily_values
                ]

                metrics = self._calculate_metrics(daily_values, sell_transactions)

                items.append(
                    StrategyCompareItem(
                        deployment_id=deployment_id,
                        strategy_name=deployment.name,
                        total_return=metrics["total_return"],
                        annual_return=metrics["annual_return"],
                        max_drawdown=metrics["max_drawdown"],
                        sharpe_ratio=metrics["sharpe_ratio"],
                        volatility=metrics["volatility"],
                        win_rate=metrics["win_rate"],
                        total_trades=metrics["total_trades"],
                        daily_values=daily_values_data,
                    )
                )
            except Exception as e:
                logger.error(f"Error comparing deployment {deployment_id}: {e}")
                continue

        start_date = request.start_date or date.today()
        end_date = request.end_date or date.today()

        return StrategyCompareResponse(
            items=items,
            start_date=start_date,
            end_date=end_date,
        )

    def _calculate_metrics(
        self,
        daily_values: List[SandboxDailyValue],
        sell_transactions: List[SandboxTransaction],
    ) -> Dict[str, Optional[float]]:
        total_return = None
        annual_return = None
        max_drawdown = None
        sharpe_ratio = None
        volatility = None
        win_rate = None
        total_trades = len(sell_transactions)

        if daily_values and len(daily_values) > 1:
            first_value = daily_values[0].total_value
            last_value = daily_values[-1].total_value

            if first_value > 0:
                total_return = (last_value - first_value) / first_value

            first_date = daily_values[0].date
            last_date = daily_values[-1].date
            days = (last_date - first_date).days
            if days > 0 and total_return is not None:
                annual_return = ((1 + total_return) ** (365 / days)) - 1

            daily_returns = [dv.daily_return for dv in daily_values if dv.daily_return is not None]
            if daily_returns:
                mean_return = statistics.mean(daily_returns)
                if len(daily_returns) > 1:
                    std_return = statistics.stdev(daily_returns)
                    volatility = std_return * (252 ** 0.5)
                    if std_return > 0:
                        risk_free_rate = TradingConfig.RISK_FREE_RATE / 252
                        sharpe_ratio = ((mean_return - risk_free_rate) / std_return) * (252 ** 0.5)

            peak = daily_values[0].total_value
            max_dd = 0.0
            for dv in daily_values:
                if dv.total_value > peak:
                    peak = dv.total_value
                if peak > 0:
                    drawdown = (peak - dv.total_value) / peak
                    if drawdown > max_dd:
                        max_dd = drawdown
            max_drawdown = max_dd if max_dd > 0 else None

        if total_trades > 0:
            winning_trades = sum(
                1 for t in sell_transactions
                if t.description and "PnL:" in t.description and self._extract_pnl(t.description) > 0
            )
            win_rate = winning_trades / total_trades

        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "volatility": volatility,
            "win_rate": win_rate,
            "total_trades": total_trades,
        }

    def _extract_pnl(self, description: str) -> float:
        try:
            if "PnL:" in description:
                pnl_part = description.split("PnL:")[-1].strip()
                return float(pnl_part)
        except (ValueError, IndexError):
            pass
        return 0.0
