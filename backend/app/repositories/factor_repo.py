from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.factor import Factor, FactorCategory, FactorEvaluation, FactorValue
from app.schemas.factor import FactorCreate, FactorUpdate


class FactorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, factor_data: FactorCreate, user_id: Optional[int] = None) -> Factor:
        factor = Factor(
            name=factor_data.name,
            code=factor_data.code,
            category=factor_data.category,
            description=factor_data.description,
            formula=factor_data.formula,
            created_by=user_id,
        )
        self.db.add(factor)
        await self.db.commit()
        await self.db.refresh(factor)
        return factor

    async def get_by_id(self, factor_id: int) -> Optional[Factor]:
        result = await self.db.execute(select(Factor).where(Factor.id == factor_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Factor]:
        result = await self.db.execute(select(Factor).where(Factor.code == code))
        return result.scalar_one_or_none()

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        category: Optional[FactorCategory] = None,
        keyword: Optional[str] = None,
    ) -> Tuple[List[Factor], int]:
        query = select(Factor)
        count_query = select(func.count(Factor.id))

        if category:
            query = query.where(Factor.category == category)
            count_query = count_query.where(Factor.category == category)

        if keyword:
            keyword_filter = Factor.name.ilike(f"%{keyword}%") | Factor.code.ilike(f"%{keyword}%")
            query = query.where(keyword_filter)
            count_query = count_query.where(keyword_filter)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        query = query.order_by(Factor.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        factors = result.scalars().all()

        return list(factors), total

    async def update(self, factor_id: int, factor_data: FactorUpdate) -> Optional[Factor]:
        factor = await self.get_by_id(factor_id)
        if not factor:
            return None

        update_data = factor_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(factor, field, value)

        await self.db.commit()
        await self.db.refresh(factor)
        return factor

    async def delete(self, factor_id: int) -> bool:
        factor = await self.get_by_id(factor_id)
        if not factor:
            return False

        await self.db.delete(factor)
        await self.db.commit()
        return True

    async def get_category_stats(self) -> List[Tuple[FactorCategory, int]]:
        query = select(Factor.category, func.count(Factor.id)).group_by(Factor.category)
        result = await self.db.execute(query)
        return result.all()


class FactorValueRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create(self, factor_id: int, values: List[dict]) -> int:
        factor_values = [
            FactorValue(
                factor_id=factor_id,
                stock_code=v["stock_code"],
                date=v["date"],
                value=v["value"],
            )
            for v in values
        ]
        self.db.add_all(factor_values)
        await self.db.commit()
        return len(factor_values)

    async def replace_factor_values(self, factor_id: int, values: List[dict]) -> int:
        from sqlalchemy import delete
        delete_stmt = delete(FactorValue).where(FactorValue.factor_id == factor_id)
        await self.db.execute(delete_stmt)
        
        if not values:
            await self.db.commit()
            return 0
        
        factor_values = [
            FactorValue(
                factor_id=factor_id,
                stock_code=v["stock_code"],
                date=v["date"],
                value=v["value"],
            )
            for v in values
        ]
        self.db.add_all(factor_values)
        await self.db.commit()
        return len(factor_values)

    async def get_values(
        self,
        factor_id: int,
        stock_codes: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[FactorValue]:
        query = select(FactorValue).where(FactorValue.factor_id == factor_id)

        if stock_codes:
            query = query.where(FactorValue.stock_code.in_(stock_codes))
        if start_date:
            query = query.where(FactorValue.date >= start_date)
        if end_date:
            query = query.where(FactorValue.date <= end_date)

        query = query.order_by(FactorValue.date, FactorValue.stock_code)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_by_factor(self, factor_id: int) -> int:
        from sqlalchemy import delete
        stmt = delete(FactorValue).where(FactorValue.factor_id == factor_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount


class FactorEvaluationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, evaluation_data: dict) -> FactorEvaluation:
        evaluation = FactorEvaluation(**evaluation_data)
        self.db.add(evaluation)
        await self.db.commit()
        await self.db.refresh(evaluation)
        return evaluation

    async def get_by_factor(self, factor_id: int) -> List[FactorEvaluation]:
        query = select(FactorEvaluation).where(FactorEvaluation.factor_id == factor_id)
        query = query.order_by(FactorEvaluation.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_latest(self, factor_id: int) -> Optional[FactorEvaluation]:
        query = select(FactorEvaluation).where(FactorEvaluation.factor_id == factor_id)
        query = query.order_by(FactorEvaluation.created_at.desc()).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
