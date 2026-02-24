from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base


class StrategyType(str, Enum):
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    TREND_FOLLOWING = "trend_following"
    FACTOR_BASED = "factor_based"
    CUSTOM = "custom"


class StrategyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class BacktestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    strategy_type = Column(SQLEnum(StrategyType), nullable=False, default=StrategyType.CUSTOM)
    status = Column(SQLEnum(StrategyStatus), nullable=False, default=StrategyStatus.DRAFT)
    description = Column(Text, nullable=True)
    logic = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=True)
    is_builtin = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    backtests = relationship("Backtest", back_populates="strategy", cascade="all, delete-orphan")
    creator = relationship("User", backref="strategies")


class Backtest(Base):
    __tablename__ = "backtests"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=True)
    status = Column(SQLEnum(BacktestStatus), nullable=False, default=BacktestStatus.PENDING)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False, default=1000000.0)
    commission_rate = Column(Float, nullable=False, default=0.0003)
    slippage = Column(Float, nullable=False, default=0.001)
    benchmark = Column(String(20), nullable=True, default="000300")
    stock_pool = Column(JSON, nullable=True)
    parameters = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    strategy = relationship("Strategy", back_populates="backtests")
    result = relationship("BacktestResult", back_populates="backtest", uselist=False, cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="backtest", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="backtest", cascade="all, delete-orphan")


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    total_return = Column(Float, nullable=True)
    annual_return = Column(Float, nullable=True)
    benchmark_return = Column(Float, nullable=True)
    alpha = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)
    
    win_rate = Column(Float, nullable=True)
    profit_loss_ratio = Column(Float, nullable=True)
    total_trades = Column(Integer, nullable=True)
    avg_holding_days = Column(Float, nullable=True)
    
    equity_curve = Column(JSON, nullable=True)
    daily_returns = Column(JSON, nullable=True)
    monthly_returns = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    backtest = relationship("Backtest", back_populates="result")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    side = Column(SQLEnum(OrderSide), nullable=False)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    filled_price = Column(Float, nullable=True)
    filled_quantity = Column(Integer, nullable=True)
    commission = Column(Float, nullable=True)
    slippage_cost = Column(Float, nullable=True)
    order_time = Column(DateTime, nullable=False)
    filled_time = Column(DateTime, nullable=True)
    signal_reason = Column(String(200), nullable=True)

    backtest = relationship("Backtest", back_populates="orders")


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    avg_cost = Column(Float, nullable=False, default=0.0)
    market_value = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, nullable=True)
    realized_pnl = Column(Float, nullable=True, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    backtest = relationship("Backtest", back_populates="positions")
