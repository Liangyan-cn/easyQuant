from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Date,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base


class SandboxStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    FEE = "fee"


class SandboxAccount(Base):
    __tablename__ = "sandbox_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    initial_capital = Column(Float, default=1000000.0)
    current_cash = Column(Float, default=1000000.0)
    total_value = Column(Float, default=1000000.0)
    status = Column(SQLEnum(SandboxStatus), default=SandboxStatus.ACTIVE)
    version = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    positions = relationship("SandboxPosition", back_populates="account", cascade="all, delete-orphan")
    transactions = relationship("SandboxTransaction", back_populates="account", cascade="all, delete-orphan")
    deployments = relationship("SandboxDeployment", back_populates="account", cascade="all, delete-orphan")
    daily_values = relationship("SandboxDailyValue", back_populates="account", cascade="all, delete-orphan")


class SandboxPosition(Base):
    __tablename__ = "sandbox_positions"
    __table_args__ = (
        UniqueConstraint("account_id", "stock_code", name="uq_sandbox_position_account_stock"),
    )

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("sandbox_accounts.id"), nullable=False)
    stock_code = Column(String(20), nullable=False)
    stock_name = Column(String(50), nullable=True)
    quantity = Column(Integer, default=0)
    avg_cost = Column(Float, default=0.0)
    current_price = Column(Float, default=0.0)
    market_value = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("SandboxAccount", back_populates="positions")


class SandboxTransaction(Base):
    __tablename__ = "sandbox_transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("sandbox_accounts.id"), nullable=False)
    deployment_id = Column(Integer, ForeignKey("sandbox_deployments.id"), nullable=True)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    stock_code = Column(String(20), nullable=True)
    stock_name = Column(String(50), nullable=True)
    quantity = Column(Integer, nullable=True)
    price = Column(Float, nullable=True)
    amount = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("SandboxAccount", back_populates="transactions")
    deployment = relationship("SandboxDeployment", back_populates="transactions")


class SandboxDeployment(Base):
    __tablename__ = "sandbox_deployments"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("sandbox_accounts.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    status = Column(SQLEnum(DeploymentStatus), default=DeploymentStatus.PENDING)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    stock_pool = Column(JSON, nullable=True)
    parameters = Column(JSON, nullable=True)
    allocation_ratio = Column(Float, default=1.0)
    last_run_date = Column(Date, nullable=True)
    last_run_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("SandboxAccount", back_populates="deployments")
    strategy = relationship("Strategy")
    transactions = relationship("SandboxTransaction", back_populates="deployment")


class SandboxDailyValue(Base):
    __tablename__ = "sandbox_daily_values"
    __table_args__ = (
        UniqueConstraint("account_id", "date", name="uq_sandbox_daily_value_account_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("sandbox_accounts.id"), nullable=False)
    date = Column(Date, nullable=False)
    total_value = Column(Float, nullable=False)
    cash = Column(Float, nullable=False)
    position_value = Column(Float, nullable=False)
    daily_return = Column(Float, nullable=True)
    cumulative_return = Column(Float, nullable=True)
    benchmark_return = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("SandboxAccount", back_populates="daily_values")
