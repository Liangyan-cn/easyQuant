import logging
from datetime import date
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.factor import Factor, FactorCategory
from app.repositories.factor_repo import FactorEvaluationRepository, FactorRepository, FactorValueRepository
from app.schemas.factor import (
    FactorCategoryStats,
    FactorCreate,
    FactorListResponse,
    FactorResponse,
    FactorUpdate,
)

logger = logging.getLogger(__name__)


class FactorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.factor_repo = FactorRepository(db)
        self.value_repo = FactorValueRepository(db)
        self.eval_repo = FactorEvaluationRepository(db)

    async def create_factor(self, factor_data: FactorCreate, user_id: Optional[int] = None) -> FactorResponse:
        logger.info(f"Creating factor: {factor_data.code}")
        existing = await self.factor_repo.get_by_code(factor_data.code)
        if existing:
            logger.warning(f"Factor code already exists: {factor_data.code}")
            raise ConflictException(detail=f"Factor with code '{factor_data.code}' already exists")

        factor = await self.factor_repo.create(factor_data, user_id)
        logger.info(f"Factor created: id={factor.id}, code={factor.code}")
        return FactorResponse.model_validate(factor)

    async def get_factor(self, factor_id: int) -> FactorResponse:
        factor = await self.factor_repo.get_by_id(factor_id)
        if not factor:
            raise NotFoundException(detail=f"Factor with id {factor_id} not found")
        return FactorResponse.model_validate(factor)

    async def get_factor_by_code(self, code: str) -> FactorResponse:
        factor = await self.factor_repo.get_by_code(code)
        if not factor:
            raise NotFoundException(detail=f"Factor with code '{code}' not found")
        return FactorResponse.model_validate(factor)

    async def list_factors(
        self,
        page: int = 1,
        size: int = 20,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> FactorListResponse:
        category_enum = None
        if category:
            try:
                category_enum = FactorCategory(category)
            except ValueError:
                pass

        factors, total = await self.factor_repo.get_list(page, size, category_enum, keyword, user_id)
        return FactorListResponse(
            items=[FactorResponse.model_validate(f) for f in factors],
            total=total,
            page=page,
            size=size,
        )

    async def update_factor(self, factor_id: int, factor_data: FactorUpdate) -> FactorResponse:
        logger.info(f"Updating factor: id={factor_id}")
        factor = await self.factor_repo.get_by_id(factor_id)
        if not factor:
            raise NotFoundException(detail=f"Factor with id {factor_id} not found")

        if factor.is_builtin:
            raise ConflictException(detail="Cannot modify built-in factor")

        if factor_data.code and factor_data.code != factor.code:
            existing = await self.factor_repo.get_by_code(factor_data.code)
            if existing:
                raise ConflictException(detail=f"Factor with code '{factor_data.code}' already exists")

        updated = await self.factor_repo.update(factor_id, factor_data)
        logger.info(f"Factor updated: id={factor_id}")
        return FactorResponse.model_validate(updated)

    async def delete_factor(self, factor_id: int) -> bool:
        logger.info(f"Deleting factor: id={factor_id}")
        factor = await self.factor_repo.get_by_id(factor_id)
        if not factor:
            raise NotFoundException(detail=f"Factor with id {factor_id} not found")

        if factor.is_builtin:
            raise ConflictException(detail="Cannot delete built-in factor")

        result = await self.factor_repo.delete(factor_id)
        logger.info(f"Factor deleted: id={factor_id}")
        return result

    async def get_category_stats(self) -> List[FactorCategoryStats]:
        stats = await self.factor_repo.get_category_stats()
        return [FactorCategoryStats(category=cat, count=count) for cat, count in stats]

    async def init_builtin_factors(self) -> int:
        builtin_factors = [
            {
                "name": "动量因子 (20日)",
                "code": "momentum_20d",
                "category": FactorCategory.MOMENTUM,
                "description": "过去20个交易日的收益率",
                "formula": "(close - close.shift(20)) / close.shift(20)",
                "is_builtin": 1,
            },
            {
                "name": "动量因子 (60日)",
                "code": "momentum_60d",
                "category": FactorCategory.MOMENTUM,
                "description": "过去60个交易日的收益率",
                "formula": "(close - close.shift(60)) / close.shift(60)",
                "is_builtin": 1,
            },
            {
                "name": "市盈率倒数",
                "code": "ep_ratio",
                "category": FactorCategory.VALUE,
                "description": "市盈率的倒数 (E/P)",
                "formula": "1 / pe_ratio",
                "is_builtin": 1,
            },
            {
                "name": "市净率倒数",
                "code": "bp_ratio",
                "category": FactorCategory.VALUE,
                "description": "市净率的倒数 (B/P)",
                "formula": "1 / pb_ratio",
                "is_builtin": 1,
            },
            {
                "name": "ROE",
                "code": "roe",
                "category": FactorCategory.QUALITY,
                "description": "净资产收益率",
                "formula": "net_profit / equity",
                "is_builtin": 1,
            },
            {
                "name": "营收增长率",
                "code": "revenue_growth",
                "category": FactorCategory.GROWTH,
                "description": "营业收入同比增长率",
                "formula": "(revenue - revenue.shift(252)) / revenue.shift(252)",
                "is_builtin": 1,
            },
            {
                "name": "波动率 (20日)",
                "code": "volatility_20d",
                "category": FactorCategory.VOLATILITY,
                "description": "过去20个交易日收益率的标准差",
                "formula": "returns.rolling(20).std()",
                "is_builtin": 1,
            },
            {
                "name": "换手率",
                "code": "turnover_rate",
                "category": FactorCategory.LIQUIDITY,
                "description": "日均换手率",
                "formula": "volume / float_shares",
                "is_builtin": 1,
            },
            {
                "name": "市值对数",
                "code": "log_market_cap",
                "category": FactorCategory.SIZE,
                "description": "总市值的自然对数",
                "formula": "log(market_cap)",
                "is_builtin": 1,
            },
        ]

        count = 0
        for factor_data in builtin_factors:
            existing = await self.factor_repo.get_by_code(factor_data["code"])
            if not existing:
                factor = Factor(**factor_data)
                self.db.add(factor)
                count += 1

        if count > 0:
            await self.db.commit()
            logger.info(f"Initialized {count} built-in factors")

        return count


async def init_builtin_factors(db: AsyncSession):
    service = FactorService(db)
    await service.init_builtin_factors()
