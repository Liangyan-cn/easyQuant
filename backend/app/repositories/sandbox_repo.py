from datetime import date
from typing import List, Optional

from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException
from app.models.sandbox import (
    SandboxAccount,
    SandboxPosition,
    SandboxTransaction,
    SandboxDeployment,
    SandboxDailyValue,
    SandboxStatus,
    DeploymentStatus,
    TransactionType,
)


class SandboxAccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, data: dict) -> SandboxAccount:
        account = SandboxAccount(
            user_id=user_id,
            name=data["name"],
            description=data.get("description"),
            initial_capital=data.get("initial_capital", 1000000.0),
            current_cash=data.get("initial_capital", 1000000.0),
            total_value=data.get("initial_capital", 1000000.0),
        )
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def get_by_id(self, account_id: int) -> Optional[SandboxAccount]:
        result = await self.db.execute(
            select(SandboxAccount).where(SandboxAccount.id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> tuple[List[SandboxAccount], int]:
        count_query = select(func.count(SandboxAccount.id)).where(
            SandboxAccount.user_id == user_id
        )
        total = (await self.db.execute(count_query)).scalar() or 0

        query = (
            select(SandboxAccount)
            .where(SandboxAccount.user_id == user_id)
            .order_by(SandboxAccount.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def update(self, account: SandboxAccount, data: dict) -> SandboxAccount:
        for key, value in data.items():
            if value is not None and hasattr(account, key):
                setattr(account, key, value)
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def update_with_lock(
        self, account: SandboxAccount, data: dict, expected_version: int
    ) -> SandboxAccount:
        if account.version != expected_version:
            raise ConflictException(
                f"Account version mismatch: expected {expected_version}, got {account.version}"
            )

        update_data = {}
        for key, value in data.items():
            if value is not None and hasattr(account, key):
                update_data[key] = value

        update_data["version"] = expected_version + 1

        stmt = (
            update(SandboxAccount)
            .where(
                and_(
                    SandboxAccount.id == account.id,
                    SandboxAccount.version == expected_version,
                )
            )
            .values(**update_data)
        )
        result = await self.db.execute(stmt)

        if result.rowcount == 0:
            raise ConflictException(
                "Account was modified by another transaction, please retry"
            )

        await self.db.refresh(account)
        return account

    async def delete(self, account: SandboxAccount) -> bool:
        await self.db.delete(account)
        await self.db.commit()
        return True

    async def get_with_details(self, account_id: int) -> Optional[SandboxAccount]:
        result = await self.db.execute(
            select(SandboxAccount)
            .options(
                selectinload(SandboxAccount.positions),
                selectinload(SandboxAccount.transactions),
                selectinload(SandboxAccount.deployments),
                selectinload(SandboxAccount.daily_values),
            )
            .where(SandboxAccount.id == account_id)
        )
        return result.scalar_one_or_none()


class SandboxPositionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_account(self, account_id: int) -> List[SandboxPosition]:
        result = await self.db.execute(
            select(SandboxPosition)
            .where(SandboxPosition.account_id == account_id)
            .order_by(SandboxPosition.market_value.desc())
        )
        return list(result.scalars().all())

    async def get_by_stock(
        self, account_id: int, stock_code: str
    ) -> Optional[SandboxPosition]:
        result = await self.db.execute(
            select(SandboxPosition).where(
                and_(
                    SandboxPosition.account_id == account_id,
                    SandboxPosition.stock_code == stock_code,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self, account_id: int, stock_code: str, data: dict
    ) -> SandboxPosition:
        position = await self.get_by_stock(account_id, stock_code)
        if position:
            for key, value in data.items():
                if hasattr(position, key):
                    setattr(position, key, value)
        else:
            position = SandboxPosition(
                account_id=account_id, stock_code=stock_code, **data
            )
            self.db.add(position)
        await self.db.commit()
        await self.db.refresh(position)
        return position

    async def delete(self, position: SandboxPosition) -> bool:
        await self.db.delete(position)
        await self.db.commit()
        return True


class SandboxTransactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, account_id: int, data: dict) -> SandboxTransaction:
        transaction = SandboxTransaction(account_id=account_id, **data)
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction

    async def get_by_account(
        self, account_id: int, limit: int = 50
    ) -> List[SandboxTransaction]:
        result = await self.db.execute(
            select(SandboxTransaction)
            .where(SandboxTransaction.account_id == account_id)
            .order_by(SandboxTransaction.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_deployment(
        self, deployment_id: int
    ) -> List[SandboxTransaction]:
        result = await self.db.execute(
            select(SandboxTransaction)
            .where(SandboxTransaction.deployment_id == deployment_id)
            .order_by(SandboxTransaction.created_at.desc())
        )
        return list(result.scalars().all())


class SandboxDeploymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, account_id: int, data: dict) -> SandboxDeployment:
        deployment = SandboxDeployment(account_id=account_id, **data)
        self.db.add(deployment)
        await self.db.commit()
        await self.db.refresh(deployment)
        return deployment

    async def get_by_id(self, deployment_id: int) -> Optional[SandboxDeployment]:
        result = await self.db.execute(
            select(SandboxDeployment).where(SandboxDeployment.id == deployment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_account(self, account_id: int) -> List[SandboxDeployment]:
        result = await self.db.execute(
            select(SandboxDeployment)
            .where(SandboxDeployment.account_id == account_id)
            .order_by(SandboxDeployment.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_deployments(self) -> List[SandboxDeployment]:
        result = await self.db.execute(
            select(SandboxDeployment).where(
                SandboxDeployment.status == DeploymentStatus.RUNNING
            )
        )
        return list(result.scalars().all())

    async def update(
        self, deployment: SandboxDeployment, data: dict
    ) -> SandboxDeployment:
        for key, value in data.items():
            if value is not None and hasattr(deployment, key):
                setattr(deployment, key, value)
        await self.db.commit()
        await self.db.refresh(deployment)
        return deployment

    async def delete(self, deployment: SandboxDeployment) -> bool:
        await self.db.delete(deployment)
        await self.db.commit()
        return True


class SandboxDailyValueRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, account_id: int, data: dict) -> SandboxDailyValue:
        daily_value = SandboxDailyValue(account_id=account_id, **data)
        self.db.add(daily_value)
        await self.db.commit()
        await self.db.refresh(daily_value)
        return daily_value

    async def get_by_account(
        self,
        account_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[SandboxDailyValue]:
        query = select(SandboxDailyValue).where(
            SandboxDailyValue.account_id == account_id
        )
        if start_date:
            query = query.where(SandboxDailyValue.date >= start_date)
        if end_date:
            query = query.where(SandboxDailyValue.date <= end_date)
        query = query.order_by(SandboxDailyValue.date)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_latest(self, account_id: int) -> Optional[SandboxDailyValue]:
        result = await self.db.execute(
            select(SandboxDailyValue)
            .where(SandboxDailyValue.account_id == account_id)
            .order_by(SandboxDailyValue.date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def upsert(self, account_id: int, date_val: date, data: dict) -> SandboxDailyValue:
        result = await self.db.execute(
            select(SandboxDailyValue).where(
                and_(
                    SandboxDailyValue.account_id == account_id,
                    SandboxDailyValue.date == date_val,
                )
            )
        )
        daily_value = result.scalar_one_or_none()
        if daily_value:
            for key, value in data.items():
                if hasattr(daily_value, key):
                    setattr(daily_value, key, value)
        else:
            daily_value = SandboxDailyValue(
                account_id=account_id, date=date_val, **data
            )
            self.db.add(daily_value)
        await self.db.commit()
        await self.db.refresh(daily_value)
        return daily_value
