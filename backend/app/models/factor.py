from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base


class FactorCategory(str, Enum):
    MOMENTUM = "momentum"
    VALUE = "value"
    QUALITY = "quality"
    GROWTH = "growth"
    VOLATILITY = "volatility"
    LIQUIDITY = "liquidity"
    SIZE = "size"
    TECHNICAL = "technical"
    CUSTOM = "custom"


class Factor(Base):
    __tablename__ = "factors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    category = Column(SQLEnum(FactorCategory), nullable=False, default=FactorCategory.CUSTOM)
    description = Column(Text, nullable=True)
    formula = Column(Text, nullable=True)
    is_builtin = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    values = relationship("FactorValue", back_populates="factor", cascade="all, delete-orphan")
    creator = relationship("User", backref="factors")


class FactorValue(Base):
    __tablename__ = "factor_values"
    __table_args__ = (
        UniqueConstraint("factor_id", "stock_code", "date", name="uix_factor_stock_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    factor_id = Column(Integer, ForeignKey("factors.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    factor = relationship("Factor", back_populates="values")


class FactorEvaluation(Base):
    __tablename__ = "factor_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    factor_id = Column(Integer, ForeignKey("factors.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    ic_mean = Column(Float, nullable=True)
    ic_std = Column(Float, nullable=True)
    ir = Column(Float, nullable=True)
    ic_positive_ratio = Column(Float, nullable=True)
    turnover = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    factor = relationship("Factor", backref="evaluations")
