from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base


class StockPoolType(str, Enum):
    SYSTEM = "system"
    USER = "user"


class StockPool(Base):
    __tablename__ = "stock_pools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    pool_type = Column(String(20), nullable=False, default=StockPoolType.USER.value)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("StockPoolItem", back_populates="pool", cascade="all, delete-orphan")
    owner = relationship("User", backref="stock_pools")


class StockPoolItem(Base):
    __tablename__ = "stock_pool_items"
    __table_args__ = (
        UniqueConstraint("pool_id", "stock_code", name="uix_pool_stock"),
    )

    id = Column(Integer, primary_key=True, index=True)
    pool_id = Column(Integer, ForeignKey("stock_pools.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(100), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)

    pool = relationship("StockPool", back_populates="items")
