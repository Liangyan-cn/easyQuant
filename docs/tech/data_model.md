# easyQuant 数据架构设计

**版本历史**:
- v1.0 | 2026-02-23 | @AI | 初稿

---

## 0. 技术调研与选型评估

### 0.1 核心问题定义 (Problem Definition)

**本质问题**：如何设计一套统一、可扩展的数据模型，支撑因子管理、策略回测、沙盒验证、交易执行的全链路数据需求？

**现状不足**：
- 量化系统涉及多种数据类型（行情、因子、策略、交易），数据结构差异大
- 时序数据（行情、因子值）与业务数据（策略配置、订单）存储需求不同
- 回测与实盘需要统一的数据口径，避免数据不一致导致的策略失效

**关键技术挑战**：
1. **时序数据高效存储与查询**：行情数据量大，需要高性能时序查询
2. **数据一致性**：因子值、策略参数、交易记录需要事务保证
3. **数据血缘追踪**：回测结果需要关联到具体的因子版本和策略版本
4. **多租户隔离**：用户数据安全隔离

### 0.2 候选方案深度对比 (In-depth Comparison)

#### 方案 A：PostgreSQL + ClickHouse 混合存储

**学术/行业背景**：
- PostgreSQL 是金融行业最常用的关系型数据库，支持 ACID 事务
- ClickHouse 是 Yandex 开源的列式时序数据库，被广泛用于金融数据分析
- 混合存储模式在量化领域已成为主流（如 QuantConnect、聚宽）

**行业趋势**：
- 时序数据库市场快速增长，ClickHouse 已进入成熟期
- PostgreSQL 15+ 引入了更好的 JSON 支持和分区表性能

**适配点**：
- ✅ PostgreSQL 处理业务数据（策略、订单、用户），强一致性
- ✅ ClickHouse 处理时序数据（行情、因子值），高性能查询
- ✅ 成熟的生态系统，运维成本低
- ✅ 支持复杂 SQL 查询，便于数据分析

**致命弱点**：
- ⚠️ 需要维护两套数据库，增加运维复杂度
- ⚠️ 跨库 JOIN 需要应用层处理

**结论**：适合数据量大、查询性能要求高的场景

#### 方案 B：纯 PostgreSQL + TimescaleDB 扩展

**学术/行业背景**：
- TimescaleDB 是 PostgreSQL 的时序扩展，提供时序数据优化
- 单一数据库简化架构

**行业趋势**：
- TimescaleDB 在中小规模场景表现良好，但超大规模不如 ClickHouse

**适配点**：
- ✅ 单一数据库，架构简单
- ✅ 原生 SQL 支持，无需跨库查询
- ✅ 学习成本低

**致命弱点**：
- ❌ 时序查询性能不如 ClickHouse（10x 差距）
- ❌ 压缩率不如列式存储
- ❌ 大规模数据下性能下降明显

**结论**：适合数据量小、追求架构简单的场景

### 0.3 选型结论与演进路线 (Conclusion & Roadmap)

**本轮结论**：采用 **PostgreSQL + ClickHouse 混合存储**

**核心理由**：
- easyQuant 需要处理大量历史行情数据（10 年 A 股分钟线约 500GB）
- 回测场景需要高性能时序查询，ClickHouse 是最佳选择
- 业务数据（策略、订单）需要事务保证，PostgreSQL 是标准选择

**核心观点应用**：
- 时序数据（行情、因子值）存储在 ClickHouse
- 业务数据（用户、策略、订单）存储在 PostgreSQL
- 应用层通过 Repository 模式封装数据访问，屏蔽底层存储差异

**演进路线**：
- M1.0：PostgreSQL 单库启动（数据量小）
- M2.0：引入 ClickHouse 存储行情数据
- M3.0：完善数据血缘追踪
- M4.0：引入数据湖（可选）

---

## 1. 目标与非目标

### 1.1 目标

- 设计统一的数据模型，覆盖因子、策略、交易全链路
- 支持高效的时序数据查询（行情、因子值）
- 保证业务数据的事务一致性
- 支持数据版本管理和血缘追踪

### 1.2 非目标

- 实时流式数据处理（本阶段不涉及）
- 分布式事务（单机部署为主）
- 数据湖/数据仓库（后续里程碑）

---

## 2. 数据架构总览

### 2.1 数据分层架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Data Architecture                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Application Layer                            │   │
│  │                                                                     │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │   │
│  │   │   Factor    │  │  Strategy   │  │   Trading   │                │   │
│  │   │   Service   │  │   Service   │  │   Service   │                │   │
│  │   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │   │
│  │          │                │                │                        │   │
│  └──────────┴────────────────┴────────────────┴────────────────────────┘   │
│                              │                                              │
│  ┌───────────────────────────▼─────────────────────────────────────────┐   │
│  │                      Repository Layer                               │   │
│  │                                                                     │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │   │
│  │   │   Factor    │  │  Strategy   │  │    Trade    │                │   │
│  │   │    Repo     │  │    Repo     │  │    Repo     │                │   │
│  │   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │   │
│  │          │                │                │                        │   │
│  └──────────┴────────────────┴────────────────┴────────────────────────┘   │
│                              │                                              │
│  ┌───────────────────────────▼─────────────────────────────────────────┐   │
│  │                       Storage Layer                                 │   │
│  │                                                                     │   │
│  │   ┌─────────────────────────┐    ┌─────────────────────────┐       │   │
│  │   │      PostgreSQL         │    │      ClickHouse         │       │   │
│  │   │                         │    │                         │       │   │
│  │   │  • 用户数据 (users)     │    │  • 行情数据 (ohlcv)     │       │   │
│  │   │  • 因子定义 (factors)   │    │  • 因子值 (factor_values)│       │   │
│  │   │  • 策略配置 (strategies)│    │  • 回测快照 (snapshots) │       │   │
│  │   │  • 订单记录 (orders)    │    │                         │       │   │
│  │   │  • 持仓记录 (positions) │    │                         │       │   │
│  │   │  • 回测结果 (backtests) │    │                         │       │   │
│  │   │                         │    │                         │       │   │
│  │   └─────────────────────────┘    └─────────────────────────┘       │   │
│  │                                                                     │   │
│  │   ┌─────────────────────────┐                                      │   │
│  │   │         Redis           │                                      │   │
│  │   │                         │                                      │   │
│  │   │  • 会话缓存             │                                      │   │
│  │   │  • 实时行情缓存         │                                      │   │
│  │   │  • 任务队列             │                                      │   │
│  │   └─────────────────────────┘                                      │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Data Flow                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐                                                           │
│   │ Data Source │  (Tushare / AKShare / 券商 API)                           │
│   └──────┬──────┘                                                           │
│          │                                                                  │
│          ▼                                                                  │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                │
│   │    ETL     │ ───► │  ClickHouse │ ───► │   Factor    │                │
│   │  Pipeline   │      │   (OHLCV)   │      │  Compute    │                │
│   └─────────────┘      └─────────────┘      └──────┬──────┘                │
│                                                    │                        │
│                                                    ▼                        │
│                                             ┌─────────────┐                 │
│                                             │  ClickHouse │                 │
│                                             │(Factor Values)│                │
│                                             └──────┬──────┘                 │
│                                                    │                        │
│          ┌─────────────────────────────────────────┤                        │
│          │                                         │                        │
│          ▼                                         ▼                        │
│   ┌─────────────┐                           ┌─────────────┐                 │
│   │  Strategy   │                           │  Backtest   │                 │
│   │   Config    │ ─────────────────────────►│   Engine    │                 │
│   │ (PostgreSQL)│                           └──────┬──────┘                 │
│   └─────────────┘                                  │                        │
│                                                    ▼                        │
│                                             ┌─────────────┐                 │
│                                             │  Backtest   │                 │
│                                             │   Result    │                 │
│                                             │ (PostgreSQL)│                 │
│                                             └──────┬──────┘                 │
│                                                    │                        │
│                                                    ▼                        │
│                                             ┌─────────────┐                 │
│                                             │   Order     │                 │
│                                             │  Execution  │                 │
│                                             │ (PostgreSQL)│                 │
│                                             └─────────────┘                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 核心数据模型

### 3.1 领域模型概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Domain Model Overview                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐          │
│   │    User     │────────►│   Factor    │────────►│ FactorValue │          │
│   └─────────────┘  owns   └─────────────┘  has    └─────────────┘          │
│         │                       │                                           │
│         │ owns                  │ uses                                      │
│         ▼                       ▼                                           │
│   ┌─────────────┐         ┌─────────────┐                                  │
│   │  Strategy   │◄────────│  Backtest   │                                  │
│   └─────────────┘  runs   └─────────────┘                                  │
│         │                       │                                           │
│         │ generates             │ produces                                  │
│         ▼                       ▼                                           │
│   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐          │
│   │   Signal    │────────►│    Order    │────────►│    Fill     │          │
│   └─────────────┘ creates └─────────────┘ results └─────────────┘          │
│                                 │                                           │
│                                 │ updates                                   │
│                                 ▼                                           │
│                           ┌─────────────┐                                  │
│                           │  Position   │                                  │
│                           └─────────────┘                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Pydantic 数据模型定义

#### 3.2.1 基础模型

```python
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class BaseEntity(BaseModel):
    """基础实体模型"""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class TimestampMixin(BaseModel):
    """时间戳混入"""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

#### 3.2.2 用户模型

```python
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class User(BaseEntity):
    """用户模型"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password_hash: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True
```

#### 3.2.3 行情数据模型

```python
class MarketDataFrequency(str, Enum):
    TICK = "tick"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1M"

class OHLCV(BaseModel):
    """行情数据模型 (存储在 ClickHouse)"""
    symbol: str = Field(..., description="证券代码，如 000001.SZ")
    timestamp: datetime = Field(..., description="K线时间")
    frequency: MarketDataFrequency = Field(..., description="数据频率")
    open: Decimal = Field(..., ge=0, description="开盘价")
    high: Decimal = Field(..., ge=0, description="最高价")
    low: Decimal = Field(..., ge=0, description="最低价")
    close: Decimal = Field(..., ge=0, description="收盘价")
    volume: int = Field(..., ge=0, description="成交量")
    amount: Decimal = Field(default=Decimal("0"), ge=0, description="成交额")
    turnover: Optional[Decimal] = Field(None, ge=0, description="换手率")
    
    class Config:
        from_attributes = True

class StockInfo(BaseModel):
    """股票基础信息"""
    symbol: str = Field(..., description="证券代码")
    name: str = Field(..., description="证券名称")
    market: str = Field(..., description="市场，如 SH/SZ")
    industry: Optional[str] = Field(None, description="行业分类")
    list_date: Optional[datetime] = Field(None, description="上市日期")
    delist_date: Optional[datetime] = Field(None, description="退市日期")
    is_active: bool = True
```

#### 3.2.4 因子模型

```python
class FactorCategory(str, Enum):
    VALUE = "value"           # 价值因子
    GROWTH = "growth"         # 成长因子
    MOMENTUM = "momentum"     # 动量因子
    VOLATILITY = "volatility" # 波动率因子
    QUALITY = "quality"       # 质量因子
    SIZE = "size"             # 规模因子
    LIQUIDITY = "liquidity"   # 流动性因子
    TECHNICAL = "technical"   # 技术因子
    CUSTOM = "custom"         # 自定义因子

class FactorStatus(str, Enum):
    DRAFT = "draft"           # 草稿
    ACTIVE = "active"         # 激活
    DEPRECATED = "deprecated" # 已废弃

class Factor(BaseEntity):
    """因子定义模型 (存储在 PostgreSQL)"""
    user_id: UUID = Field(..., description="所属用户")
    name: str = Field(..., min_length=1, max_length=100, description="因子名称")
    code: str = Field(..., min_length=1, max_length=50, description="因子代码，唯一标识")
    category: FactorCategory = Field(..., description="因子分类")
    description: Optional[str] = Field(None, max_length=500, description="因子描述")
    formula: str = Field(..., description="因子计算公式/代码")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="因子参数")
    version: int = Field(default=1, ge=1, description="版本号")
    status: FactorStatus = Field(default=FactorStatus.DRAFT, description="因子状态")
    
    # 因子评估指标
    ic_mean: Optional[float] = Field(None, description="IC 均值")
    ic_ir: Optional[float] = Field(None, description="IC_IR")
    turnover: Optional[float] = Field(None, description="换手率")
    
    class Config:
        from_attributes = True

class FactorValue(BaseModel):
    """因子值模型 (存储在 ClickHouse)"""
    factor_id: UUID = Field(..., description="因子 ID")
    factor_code: str = Field(..., description="因子代码")
    symbol: str = Field(..., description="证券代码")
    timestamp: datetime = Field(..., description="计算时间")
    value: float = Field(..., description="因子值")
    rank: Optional[int] = Field(None, description="因子排名")
    percentile: Optional[float] = Field(None, ge=0, le=1, description="因子分位数")
    
    class Config:
        from_attributes = True
```

#### 3.2.5 策略模型

```python
class StrategyType(str, Enum):
    FACTOR_BASED = "factor_based"   # 因子策略
    RULE_BASED = "rule_based"       # 规则策略
    ML_BASED = "ml_based"           # 机器学习策略
    HYBRID = "hybrid"               # 混合策略

class StrategyStatus(str, Enum):
    DRAFT = "draft"
    BACKTESTING = "backtesting"
    SANDBOX = "sandbox"
    LIVE = "live"
    STOPPED = "stopped"

class Strategy(BaseEntity):
    """策略模型 (存储在 PostgreSQL)"""
    user_id: UUID = Field(..., description="所属用户")
    name: str = Field(..., min_length=1, max_length=100, description="策略名称")
    code: str = Field(..., min_length=1, max_length=50, description="策略代码")
    strategy_type: StrategyType = Field(..., description="策略类型")
    description: Optional[str] = Field(None, max_length=1000, description="策略描述")
    
    # 策略配置
    universe: List[str] = Field(default_factory=list, description="股票池")
    factors: List[UUID] = Field(default_factory=list, description="使用的因子 ID 列表")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    
    # 风控参数
    max_position_size: Decimal = Field(default=Decimal("0.1"), ge=0, le=1, description="单只股票最大仓位")
    max_drawdown: Decimal = Field(default=Decimal("0.2"), ge=0, le=1, description="最大回撤阈值")
    stop_loss: Optional[Decimal] = Field(None, ge=0, le=1, description="止损比例")
    take_profit: Optional[Decimal] = Field(None, ge=0, description="止盈比例")
    
    # 状态
    version: int = Field(default=1, ge=1, description="版本号")
    status: StrategyStatus = Field(default=StrategyStatus.DRAFT, description="策略状态")
    
    class Config:
        from_attributes = True
```

#### 3.2.6 回测模型

```python
class BacktestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Backtest(BaseEntity):
    """回测记录模型 (存储在 PostgreSQL)"""
    user_id: UUID = Field(..., description="所属用户")
    strategy_id: UUID = Field(..., description="策略 ID")
    strategy_version: int = Field(..., description="策略版本")
    
    # 回测配置
    start_date: datetime = Field(..., description="回测开始日期")
    end_date: datetime = Field(..., description="回测结束日期")
    initial_capital: Decimal = Field(default=Decimal("1000000"), gt=0, description="初始资金")
    benchmark: str = Field(default="000300.SH", description="基准指数")
    commission_rate: Decimal = Field(default=Decimal("0.0003"), ge=0, description="手续费率")
    slippage: Decimal = Field(default=Decimal("0.001"), ge=0, description="滑点")
    
    # 回测状态
    status: BacktestStatus = Field(default=BacktestStatus.PENDING, description="回测状态")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 回测结果 (完成后填充)
    total_return: Optional[Decimal] = Field(None, description="总收益率")
    annual_return: Optional[Decimal] = Field(None, description="年化收益率")
    max_drawdown: Optional[Decimal] = Field(None, description="最大回撤")
    sharpe_ratio: Optional[Decimal] = Field(None, description="夏普比率")
    sortino_ratio: Optional[Decimal] = Field(None, description="索提诺比率")
    calmar_ratio: Optional[Decimal] = Field(None, description="卡玛比率")
    win_rate: Optional[Decimal] = Field(None, description="胜率")
    profit_factor: Optional[Decimal] = Field(None, description="盈亏比")
    total_trades: Optional[int] = Field(None, description="总交易次数")
    
    class Config:
        from_attributes = True

class BacktestSnapshot(BaseModel):
    """回测快照模型 (存储在 ClickHouse)"""
    backtest_id: UUID = Field(..., description="回测 ID")
    timestamp: datetime = Field(..., description="快照时间")
    equity: Decimal = Field(..., description="权益")
    cash: Decimal = Field(..., description="现金")
    market_value: Decimal = Field(..., description="市值")
    daily_return: Decimal = Field(..., description="日收益率")
    cumulative_return: Decimal = Field(..., description="累计收益率")
    drawdown: Decimal = Field(..., description="回撤")
    
    class Config:
        from_attributes = True
```

#### 3.2.7 交易模型

```python
class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL_FILLED = "partial_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class Order(BaseEntity):
    """订单模型 (存储在 PostgreSQL)"""
    user_id: UUID = Field(..., description="所属用户")
    strategy_id: UUID = Field(..., description="策略 ID")
    backtest_id: Optional[UUID] = Field(None, description="回测 ID (回测订单)")
    
    # 订单信息
    symbol: str = Field(..., description="证券代码")
    order_type: OrderType = Field(..., description="订单类型")
    side: OrderSide = Field(..., description="买卖方向")
    quantity: int = Field(..., gt=0, description="委托数量")
    price: Optional[Decimal] = Field(None, ge=0, description="委托价格 (限价单)")
    
    # 成交信息
    filled_quantity: int = Field(default=0, ge=0, description="成交数量")
    filled_price: Optional[Decimal] = Field(None, ge=0, description="成交均价")
    commission: Decimal = Field(default=Decimal("0"), ge=0, description="手续费")
    slippage: Decimal = Field(default=Decimal("0"), ge=0, description="滑点成本")
    
    # 状态
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="订单状态")
    submitted_at: Optional[datetime] = Field(None, description="提交时间")
    filled_at: Optional[datetime] = Field(None, description="成交时间")
    cancelled_at: Optional[datetime] = Field(None, description="取消时间")
    reject_reason: Optional[str] = Field(None, description="拒绝原因")
    
    # 来源追踪
    signal_id: Optional[UUID] = Field(None, description="信号 ID")
    
    class Config:
        from_attributes = True

class Position(BaseEntity):
    """持仓模型 (存储在 PostgreSQL)"""
    user_id: UUID = Field(..., description="所属用户")
    strategy_id: UUID = Field(..., description="策略 ID")
    backtest_id: Optional[UUID] = Field(None, description="回测 ID (回测持仓)")
    
    # 持仓信息
    symbol: str = Field(..., description="证券代码")
    quantity: int = Field(..., ge=0, description="持仓数量")
    available_quantity: int = Field(..., ge=0, description="可用数量")
    cost_price: Decimal = Field(..., ge=0, description="成本价")
    current_price: Decimal = Field(..., ge=0, description="当前价")
    market_value: Decimal = Field(..., ge=0, description="市值")
    unrealized_pnl: Decimal = Field(default=Decimal("0"), description="浮动盈亏")
    realized_pnl: Decimal = Field(default=Decimal("0"), description="已实现盈亏")
    
    # 风控信息
    weight: Decimal = Field(default=Decimal("0"), ge=0, le=1, description="仓位权重")
    
    class Config:
        from_attributes = True

class Fill(BaseEntity):
    """成交记录模型 (存储在 PostgreSQL)"""
    order_id: UUID = Field(..., description="订单 ID")
    
    # 成交信息
    symbol: str = Field(..., description="证券代码")
    side: OrderSide = Field(..., description="买卖方向")
    quantity: int = Field(..., gt=0, description="成交数量")
    price: Decimal = Field(..., ge=0, description="成交价格")
    commission: Decimal = Field(default=Decimal("0"), ge=0, description="手续费")
    
    # 时间
    filled_at: datetime = Field(default_factory=datetime.now, description="成交时间")
    
    class Config:
        from_attributes = True
```

---

## 4. 数据库 Schema 设计

### 4.1 PostgreSQL Schema

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 股票基础信息表
CREATE TABLE stock_info (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    market VARCHAR(10) NOT NULL,
    industry VARCHAR(100),
    list_date DATE,
    delist_date DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 因子定义表
CREATE TABLE factors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    formula TEXT NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}',
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    ic_mean DECIMAL,
    ic_ir DECIMAL,
    turnover DECIMAL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, code, version)
);

-- 策略表
CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    strategy_type VARCHAR(50) NOT NULL,
    description TEXT,
    universe JSONB NOT NULL DEFAULT '[]',
    factors JSONB NOT NULL DEFAULT '[]',
    parameters JSONB NOT NULL DEFAULT '{}',
    max_position_size DECIMAL NOT NULL DEFAULT 0.1,
    max_drawdown DECIMAL NOT NULL DEFAULT 0.2,
    stop_loss DECIMAL,
    take_profit DECIMAL,
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, code, version)
);

-- 回测表
CREATE TABLE backtests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    strategy_id UUID NOT NULL REFERENCES strategies(id),
    strategy_version INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL NOT NULL DEFAULT 1000000,
    benchmark VARCHAR(20) NOT NULL DEFAULT '000300.SH',
    commission_rate DECIMAL NOT NULL DEFAULT 0.0003,
    slippage DECIMAL NOT NULL DEFAULT 0.001,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    total_return DECIMAL,
    annual_return DECIMAL,
    max_drawdown DECIMAL,
    sharpe_ratio DECIMAL,
    sortino_ratio DECIMAL,
    calmar_ratio DECIMAL,
    win_rate DECIMAL,
    profit_factor DECIMAL,
    total_trades INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 订单表
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    strategy_id UUID NOT NULL REFERENCES strategies(id),
    backtest_id UUID REFERENCES backtests(id),
    symbol VARCHAR(20) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL,
    filled_quantity INTEGER NOT NULL DEFAULT 0,
    filled_price DECIMAL,
    commission DECIMAL NOT NULL DEFAULT 0,
    slippage DECIMAL NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    submitted_at TIMESTAMP,
    filled_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    reject_reason TEXT,
    signal_id UUID,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 持仓表
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    strategy_id UUID NOT NULL REFERENCES strategies(id),
    backtest_id UUID REFERENCES backtests(id),
    symbol VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    available_quantity INTEGER NOT NULL DEFAULT 0,
    cost_price DECIMAL NOT NULL DEFAULT 0,
    current_price DECIMAL NOT NULL DEFAULT 0,
    market_value DECIMAL NOT NULL DEFAULT 0,
    unrealized_pnl DECIMAL NOT NULL DEFAULT 0,
    realized_pnl DECIMAL NOT NULL DEFAULT 0,
    weight DECIMAL NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(strategy_id, backtest_id, symbol)
);

-- 成交记录表
CREATE TABLE fills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL NOT NULL,
    commission DECIMAL NOT NULL DEFAULT 0,
    filled_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_factors_user_id ON factors(user_id);
CREATE INDEX idx_factors_code ON factors(code);
CREATE INDEX idx_strategies_user_id ON strategies(user_id);
CREATE INDEX idx_strategies_code ON strategies(code);
CREATE INDEX idx_backtests_user_id ON backtests(user_id);
CREATE INDEX idx_backtests_strategy_id ON backtests(strategy_id);
CREATE INDEX idx_backtests_status ON backtests(status);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_strategy_id ON orders(strategy_id);
CREATE INDEX idx_orders_backtest_id ON orders(backtest_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_positions_user_id ON positions(user_id);
CREATE INDEX idx_positions_strategy_id ON positions(strategy_id);
CREATE INDEX idx_fills_order_id ON fills(order_id);
```

### 4.2 ClickHouse Schema

```sql
-- 行情数据表 (按日期分区)
CREATE TABLE ohlcv (
    symbol String,
    timestamp DateTime,
    frequency String,
    open Decimal(18, 4),
    high Decimal(18, 4),
    low Decimal(18, 4),
    close Decimal(18, 4),
    volume UInt64,
    amount Decimal(18, 4),
    turnover Nullable(Decimal(18, 6))
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp, frequency)
SETTINGS index_granularity = 8192;

-- 因子值表 (按日期分区)
CREATE TABLE factor_values (
    factor_id UUID,
    factor_code String,
    symbol String,
    timestamp DateTime,
    value Float64,
    rank Nullable(UInt32),
    percentile Nullable(Float64)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (factor_code, timestamp, symbol)
SETTINGS index_granularity = 8192;

-- 回测快照表 (按回测 ID 分区)
CREATE TABLE backtest_snapshots (
    backtest_id UUID,
    timestamp DateTime,
    equity Decimal(18, 4),
    cash Decimal(18, 4),
    market_value Decimal(18, 4),
    daily_return Decimal(18, 6),
    cumulative_return Decimal(18, 6),
    drawdown Decimal(18, 6)
) ENGINE = MergeTree()
PARTITION BY backtest_id
ORDER BY (backtest_id, timestamp)
SETTINGS index_granularity = 8192;
```

---

## 5. 数据访问层设计

### 5.1 Repository 模式

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from uuid import UUID

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """仓储基类"""
    
    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        pass

class FactorRepository(BaseRepository[Factor]):
    """因子仓储"""
    
    async def get_by_code(self, user_id: UUID, code: str) -> Optional[Factor]:
        pass
    
    async def get_by_user(self, user_id: UUID) -> List[Factor]:
        pass
    
    async def get_latest_version(self, user_id: UUID, code: str) -> Optional[Factor]:
        pass

class StrategyRepository(BaseRepository[Strategy]):
    """策略仓储"""
    
    async def get_by_code(self, user_id: UUID, code: str) -> Optional[Strategy]:
        pass
    
    async def get_by_user(self, user_id: UUID) -> List[Strategy]:
        pass
    
    async def get_by_status(self, user_id: UUID, status: StrategyStatus) -> List[Strategy]:
        pass

class MarketDataRepository(ABC):
    """行情数据仓储 (ClickHouse)"""
    
    @abstractmethod
    async def get_ohlcv(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        frequency: MarketDataFrequency
    ) -> List[OHLCV]:
        pass
    
    @abstractmethod
    async def get_latest_price(self, symbols: List[str]) -> Dict[str, Decimal]:
        pass
    
    @abstractmethod
    async def bulk_insert_ohlcv(self, data: List[OHLCV]) -> int:
        pass

class FactorValueRepository(ABC):
    """因子值仓储 (ClickHouse)"""
    
    @abstractmethod
    async def get_factor_values(
        self,
        factor_code: str,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> List[FactorValue]:
        pass
    
    @abstractmethod
    async def bulk_insert_factor_values(self, data: List[FactorValue]) -> int:
        pass
```

---

## 6. 性能预估与容量规划

### 6.1 数据量预估

| 数据类型 | 预估数量 | 单条大小 | 总大小 |
|----------|----------|----------|--------|
| 日线行情 (10年 A股) | 5000股 × 2500天 = 1250万条 | 100B | ~1.2GB |
| 分钟线行情 (10年 A股) | 5000股 × 240分钟 × 2500天 = 30亿条 | 100B | ~280GB |
| 因子值 (100因子) | 100 × 5000股 × 2500天 = 12.5亿条 | 50B | ~60GB |
| 策略配置 | ~10000条 | 2KB | ~20MB |
| 回测记录 | ~100000条 | 1KB | ~100MB |
| 订单记录 | ~1000万条 | 500B | ~5GB |

### 6.2 性能指标

| 操作 | 目标延迟 | 预期 QPS |
|------|----------|----------|
| 单股日线查询 (10年) | < 100ms | 100 |
| 多股日线查询 (100股 × 1年) | < 500ms | 50 |
| 因子值查询 (1因子 × 100股 × 1年) | < 200ms | 100 |
| 策略 CRUD | < 50ms | 100 |
| 回测结果查询 | < 100ms | 50 |

### 6.3 存储规划

- **PostgreSQL**: 50GB (业务数据 + 索引)
- **ClickHouse**: 500GB (时序数据，启用压缩后约 100GB)
- **Redis**: 2GB (缓存)

---

## 7. 数据安全与合规

### 7.1 数据隔离

- 所有业务表包含 `user_id` 字段，实现多租户数据隔离
- Repository 层强制校验 `user_id`，防止越权访问

### 7.2 敏感数据处理

- 用户密码使用 bcrypt 加密存储
- API Key 使用 AES 加密存储
- 日志中脱敏处理交易金额、持仓数量

### 7.3 数据备份

- PostgreSQL: 每日全量备份 + 实时 WAL 归档
- ClickHouse: 每周全量备份 + 增量备份
- 备份保留 30 天

---

## 8. 里程碑对齐

| 里程碑 | 数据架构重点 |
|--------|--------------|
| **M0** | 数据模型设计、Schema 定义 |
| **M1.0 MVP** | PostgreSQL 单库实现、基础 CRUD |
| **M2.0 沙盒** | 引入 ClickHouse、因子值存储、回测快照 |
| **M3.0 交易** | 订单/持仓实时同步、数据一致性保证 |
| **M4.0 智能化** | 数据血缘追踪、数据质量监控 |
