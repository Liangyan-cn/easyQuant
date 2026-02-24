#!/usr/bin/env python3
"""
批量计算因子值脚本

用途：为所有支持的因子预计算最近一年的数据
特点：
  - 自动跳过已有数据的因子
  - 自动跳过需要财务数据的因子
  - 显示详细的计算进度

使用方法：
  cd backend
  PYTHONPATH=. ./venv/bin/python app/scripts/batch_calculate_factors.py

支持的因子：
  - momentum_20d: 20日动量因子
  - momentum_60d: 60日动量因子
  - volatility_20d: 20日波动率
  - turnover_rate: 换手率
  - log_market_cap: 市值对数

暂不支持的因子（需要财务数据）：
  - ep_ratio: 市盈率倒数
  - bp_ratio: 市净率倒数
  - roe: 净资产收益率
  - revenue_growth: 营收增长率
"""
import asyncio
from datetime import date, timedelta

from sqlalchemy import select, func
from app.core.database import async_session_maker
from app.models.factor import Factor, FactorValue
from app.services.factor_calculator import FactorCalculator
from app.schemas.factor import FactorCalculateRequest


CALCULABLE_FACTOR_CODES = [
    "momentum_20d",
    "momentum_60d",
    "volatility_20d",
    "turnover_rate",
    "log_market_cap",
]


async def get_factor_value_count(db, factor_id: int, start_date: date, end_date: date) -> int:
    result = await db.execute(
        select(func.count(FactorValue.id)).where(
            FactorValue.factor_id == factor_id,
            FactorValue.date >= start_date,
            FactorValue.date <= end_date,
        )
    )
    return result.scalar() or 0


async def main():
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    print(f"批量计算因子值: {start_date} ~ {end_date}")
    print("=" * 60)

    calculated_count = 0
    skipped_count = 0
    failed_count = 0

    async with async_session_maker() as db:
        result = await db.execute(select(Factor))
        factors = result.scalars().all()

        for factor in factors:
            print(f"\n[{factor.id}] {factor.name} ({factor.code})")

            if factor.code not in CALCULABLE_FACTOR_CODES:
                print(f"  ⏭️  跳过: 暂不支持计算 (需要财务数据)")
                skipped_count += 1
                continue

            existing_count = await get_factor_value_count(db, factor.id, start_date, end_date)

            if existing_count > 0:
                print(f"  ✅ 已有数据: {existing_count:,} 条")
                continue

            print(f"  🔄 开始计算...")
            try:
                calculator = FactorCalculator(db)
                request = FactorCalculateRequest(
                    factor_id=factor.id,
                    start_date=start_date,
                    end_date=end_date,
                )
                calc_result = await calculator.calculate_factor(request)
                print(f"  ✅ 计算完成: {calc_result.calculated_count:,} 条数据")
                calculated_count += 1
            except Exception as e:
                print(f"  ❌ 计算失败: {e}")
                failed_count += 1

    print("\n" + "=" * 60)
    print(f"批量计算完成!")
    print(f"  - 新计算: {calculated_count} 个因子")
    print(f"  - 跳过: {skipped_count} 个因子 (不支持)")
    print(f"  - 失败: {failed_count} 个因子")


if __name__ == "__main__":
    asyncio.run(main())
