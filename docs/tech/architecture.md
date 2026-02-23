# easyQuant 技术架构设计

**版本历史**:
- v1.0 | 2026-02-23 | @AI | 初稿

---

## 0. 技术调研与选型评估

### 0.1 核心问题定义 (Problem Definition)

**本质问题**：如何为个人投资者构建一个低门槛、可扩展、可信赖的量化投资平台？

**现状不足**：
- 现有开源方案（Zipline、Backtrader）功能强但学习曲线陡峭，不适合新手
- 国内平台（聚宽、米筐）依赖云端，数据与策略不可控
- 简单脚本方案无法支撑因子管理、沙盒验证、交易执行的完整链路

**关键技术挑战**：
1. **回测与实盘一致性**：避免 Lookahead Bias，确保回测结果可信
2. **模块解耦**：因子、策略、执行层独立演进
3. **数据一致性**：统一数据口径，支持多数据源
4. **低延迟响应**：沙盒与实盘场景下的实时性要求

### 0.2 候选方案深度对比 (In-depth Comparison)

#### 方案 A：事件驱动架构 (Event-Driven Architecture)

**学术/行业背景**：
- QuantConnect LEAN 引擎采用事件驱动设计，支持回测与实盘无缝切换
- QuantStart 系列文章详细阐述了 Event-Driven Backtester 的设计原理
- 核心事件类型：MarketEvent → SignalEvent → OrderEvent → FillEvent

**行业趋势**：
- Gartner 将 Event-Driven Model 列为战略技术趋势
- 事件驱动架构在金融交易系统中已成熟（上升期 → 成熟期）

**适配点**：
- ✅ 回测与实盘代码复用率高（仅需替换 DataHandler 和 ExecutionHandler）
- ✅ 天然避免 Lookahead Bias（数据以事件形式"滴灌"）
- ✅ 支持复杂订单类型（限价单、市价单、MOO/MOC）
- ✅ 便于扩展风控、滑点、手续费模型

**致命弱点**：
- ⚠️ 实现复杂度高，需要严格的测试覆盖
- ⚠️ 相比向量化回测，执行速度较慢

**结论**：适合需要高保真回测与实盘一致性的场景

#### 方案 B：向量化回测 (Vectorized Backtesting)

**学术/行业背景**：
- 基于 Pandas/NumPy 的批量计算，Zipline 早期版本采用此模式
- 适合快速验证策略逻辑

**行业趋势**：
- 仍广泛用于研究阶段，但生产环境逐渐被事件驱动取代

**适配点**：
- ✅ 实现简单，开发速度快
- ✅ 计算效率高（向量化操作）

**致命弱点**：
- ❌ 回测与实盘代码无法复用
- ❌ 容易引入 Lookahead Bias
- ❌ 难以模拟真实交易成本与滑点

**结论**：适合快速原型验证，不适合生产环境

### 0.3 选型结论与演进路线 (Conclusion & Roadmap)

**本轮结论**：采用 **事件驱动架构 (Event-Driven Architecture)**

**核心理由**：
- easyQuant 的核心价值是"沙盒优先、可信验证"，事件驱动架构天然支持回测与实盘一致性
- 个人投资者对执行速度要求不高（非高频交易），可接受事件驱动的性能开销

**核心观点应用**：
- 所有策略逻辑必须基于事件接口开发，禁止直接访问未来数据
- DataHandler 必须实现统一接口，支持历史数据与实时数据源切换
- 交易成本模型作为独立组件，便于后续扩展

**演进路线**：
- M1.0：基础事件驱动框架 + 简单回测
- M2.0：沙盒系统 + 多策略并行
- M3.0：实盘执行 + 券商 API 对接
- M4.0：性能优化（热点路径向量化加速）

---

## 1. 目标与非目标

### 1.1 目标

- 构建可扩展的事件驱动量化交易平台
- 支持因子管理、策略回测、沙盒验证、交易执行全链路
- 回测与实盘代码复用率 > 90%
- 为个人投资者提供低门槛的量化工具

### 1.2 非目标

- 高频交易（微秒级延迟）
- 机构级风控与合规系统
- 多资产类别（本阶段仅支持 A 股）

---

## 2. 系统架构与数据流

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              easyQuant Platform                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Web UI    │    │   CLI Tool  │    │   REST API  │    │  WebSocket  │  │
│  │  (React)    │    │  (Python)   │    │  (FastAPI)  │    │  (实时推送)  │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                  │                  │                  │         │
│         └──────────────────┴────────┬─────────┴──────────────────┘         │
│                                     │                                       │
│  ┌──────────────────────────────────▼──────────────────────────────────┐   │
│  │                        API Gateway / BFF                            │   │
│  │                   (认证、限流、路由、协议转换)                         │   │
│  └──────────────────────────────────┬──────────────────────────────────┘   │
│                                     │                                       │
├─────────────────────────────────────┼───────────────────────────────────────┤
│                              Core Services                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │    Factor    │  │   Strategy   │  │   Sandbox    │  │   Trading    │    │
│  │   Service    │  │   Service    │  │   Service    │  │   Service    │    │
│  │              │  │              │  │              │  │              │    │
│  │ • 因子 CRUD  │  │ • 策略 CRUD  │  │ • 虚拟账户   │  │ • 订单管理   │    │
│  │ • 因子计算   │  │ • 回测引擎   │  │ • 多策略实测 │  │ • 持仓管理   │    │
│  │ • 因子评估   │  │ • 绩效评估   │  │ • 对比分析   │  │ • 风险控制   │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │            │
│         └─────────────────┴────────┬────────┴─────────────────┘            │
│                                    │                                        │
│  ┌─────────────────────────────────▼─────────────────────────────────────┐ │
│  │                         Event Bus (事件总线)                          │ │
│  │                                                                       │ │
│  │   MarketEvent ──► SignalEvent ──► OrderEvent ──► FillEvent           │ │
│  │                                                                       │ │
│  │   实现: Redis Streams / RabbitMQ / 内存队列 (根据部署规模选择)         │ │
│  └─────────────────────────────────┬─────────────────────────────────────┘ │
│                                    │                                        │
├────────────────────────────────────┼────────────────────────────────────────┤
│                              Engine Layer                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │    Data      │  │   Strategy   │  │  Portfolio   │  │  Execution   │    │
│  │   Handler    │  │   Engine     │  │   Manager    │  │   Handler    │    │
│  │              │  │              │  │              │  │              │    │
│  │ • 数据获取   │  │ • 信号生成   │  │ • 仓位管理   │  │ • 订单执行   │    │
│  │ • 数据清洗   │  │ • 策略调度   │  │ • 风险计算   │  │ • 成交模拟   │    │
│  │ • 事件发布   │  │ • 参数优化   │  │ • 资金分配   │  │ • 滑点模型   │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │            │
├─────────┴─────────────────┴─────────────────┴─────────────────┴────────────┤
│                              Data Layer                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Market     │  │   Factor     │  │   Strategy   │  │    Trade     │    │
│  │    Data      │  │    Store     │  │    Store     │  │    Store     │    │
│  │              │  │              │  │              │  │              │    │
│  │ • 行情数据   │  │ • 因子定义   │  │ • 策略配置   │  │ • 订单记录   │    │
│  │ • 财务数据   │  │ • 因子值     │  │ • 回测结果   │  │ • 持仓快照   │    │
│  │ • 基础信息   │  │ • 评估指标   │  │ • 绩效指标   │  │ • 交易流水   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                             │
│  存储选型: PostgreSQL (主库) + Redis (缓存) + ClickHouse (时序数据)         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心模块划分

| 层级       | 模块              | 职责               | 技术选型                        |
| ---------- | ----------------- | ------------------ | ------------------------------- |
| **表现层** | Web UI            | 可视化操作界面     | React + TypeScript + Ant Design |
|            | CLI Tool          | 命令行工具         | Python + Click                  |
|            | REST API          | HTTP 接口          | FastAPI                         |
|            | WebSocket         | 实时推送           | FastAPI WebSocket               |
| **网关层** | API Gateway       | 认证、限流、路由   | FastAPI Middleware              |
| **服务层** | Factor Service    | 因子管理与计算     | Python                          |
|            | Strategy Service  | 策略管理与回测     | Python                          |
|            | Sandbox Service   | 沙盒验证           | Python                          |
|            | Trading Service   | 交易执行           | Python                          |
| **引擎层** | Data Handler      | 数据获取与事件发布 | Python + Pandas                 |
|            | Strategy Engine   | 信号生成与策略调度 | Python                          |
|            | Portfolio Manager | 仓位与风险管理     | Python                          |
|            | Execution Handler | 订单执行与成交模拟 | Python                          |
| **数据层** | Market Data       | 行情与基础数据     | PostgreSQL + ClickHouse         |
|            | Factor Store      | 因子存储           | PostgreSQL                      |
|            | Strategy Store    | 策略与回测结果     | PostgreSQL                      |
|            | Trade Store       | 交易记录           | PostgreSQL                      |

### 2.3 事件驱动数据流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Event-Driven Data Flow                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐                                                           │
│   │ Data Source │  (历史数据 / 实时行情)                                     │
│   └──────┬──────┘                                                           │
│          │                                                                  │
│          ▼                                                                  │
│   ┌─────────────┐      ┌─────────────┐                                      │
│   │    Data     │ ───► │   Market    │  (每个 Bar/Tick 生成一个事件)         │
│   │   Handler   │      │   Event     │                                      │
│   └─────────────┘      └──────┬──────┘                                      │
│                               │                                             │
│                               ▼                                             │
│                        ┌─────────────┐                                      │
│                        │   Event     │  (FIFO 队列)                          │
│                        │   Queue     │                                      │
│                        └──────┬──────┘                                      │
│                               │                                             │
│          ┌────────────────────┼────────────────────┐                        │
│          │                    │                    │                        │
│          ▼                    ▼                    ▼                        │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                 │
│   │  Strategy   │      │  Portfolio  │      │  Execution  │                 │
│   │   Engine    │      │   Manager   │      │   Handler   │                 │
│   └──────┬──────┘      └──────┬──────┘      └──────┬──────┘                 │
│          │                    │                    │                        │
│          ▼                    ▼                    ▼                        │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                 │
│   │   Signal    │      │   Order     │      │    Fill     │                 │
│   │   Event     │ ───► │   Event     │ ───► │   Event     │                 │
│   └─────────────┘      └─────────────┘      └─────────────┘                 │
│                                                                             │
│   事件类型说明:                                                              │
│   • MarketEvent  - 新的市场数据到达 (Bar/Tick)                               │
│   • SignalEvent  - 策略产生交易信号 (BUY/SELL/HOLD)                          │
│   • OrderEvent   - 组合管理器生成订单 (MARKET/LIMIT)                         │
│   • FillEvent    - 订单成交确认 (含手续费、滑点)                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 回测与实盘切换

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Backtest vs Live Trading                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────┐    ┌─────────────────────────────┐        │
│   │        Backtest Mode        │    │      Live Trading Mode      │        │
│   ├─────────────────────────────┤    ├─────────────────────────────┤        │
│   │                             │    │                             │        │
│   │  HistoricalDataHandler      │    │  LiveDataHandler            │        │
│   │  • 读取本地/数据库历史数据   │    │  • 连接实时行情源            │        │
│   │  • 按时间顺序滴灌事件        │    │  • 订阅 Tick/Bar 推送        │        │
│   │                             │    │                             │        │
│   │  SimulatedExecutionHandler  │    │  BrokerExecutionHandler     │        │
│   │  • 模拟成交                 │    │  • 连接券商 API              │        │
│   │  • 滑点/手续费模型          │    │  • 真实订单提交              │        │
│   │                             │    │                             │        │
│   └──────────────┬──────────────┘    └──────────────┬──────────────┘        │
│                  │                                  │                       │
│                  └──────────────┬───────────────────┘                       │
│                                 │                                           │
│                                 ▼                                           │
│                  ┌─────────────────────────────┐                            │
│                  │      Shared Components      │                            │
│                  │                             │                            │
│                  │  • Strategy Engine          │  ◄── 策略代码 100% 复用    │
│                  │  • Portfolio Manager        │  ◄── 仓位逻辑 100% 复用    │
│                  │  • Risk Controller          │  ◄── 风控逻辑 100% 复用    │
│                  │  • Event Queue              │  ◄── 事件机制 100% 复用    │
│                  │                             │                            │
│                  └─────────────────────────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 核心设计

### 3.1 事件类型定义 (Pydantic Models)

```python
from enum import Enum
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

class EventType(str, Enum):
    MARKET = "MARKET"
    SIGNAL = "SIGNAL"
    ORDER = "ORDER"
    FILL = "FILL"

class SignalDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    EXIT = "EXIT"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class BaseEvent(BaseModel):
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)

class MarketEvent(BaseEvent):
    event_type: EventType = EventType.MARKET
    symbol: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    bar_time: datetime

class SignalEvent(BaseEvent):
    event_type: EventType = EventType.SIGNAL
    symbol: str
    direction: SignalDirection
    strength: float = Field(ge=0.0, le=1.0, default=1.0)
    strategy_id: str

class OrderEvent(BaseEvent):
    event_type: EventType = EventType.ORDER
    symbol: str
    order_type: OrderType
    side: OrderSide
    quantity: int
    limit_price: Optional[Decimal] = None
    strategy_id: str

class FillEvent(BaseEvent):
    event_type: EventType = EventType.FILL
    symbol: str
    side: OrderSide
    quantity: int
    fill_price: Decimal
    commission: Decimal
    slippage: Decimal
    order_id: str
```

### 3.2 核心接口定义

```python
from abc import ABC, abstractmethod
from typing import Generator, Optional
from queue import Queue

class DataHandler(ABC):
    """数据处理器抽象基类"""
    
    @abstractmethod
    def get_latest_bar(self, symbol: str) -> Optional[MarketEvent]:
        """获取最新的 Bar 数据"""
        pass
    
    @abstractmethod
    def get_latest_bars(self, symbol: str, n: int = 1) -> list[MarketEvent]:
        """获取最近 N 个 Bar 数据"""
        pass
    
    @abstractmethod
    def update_bars(self) -> None:
        """更新 Bar 数据并发布 MarketEvent"""
        pass
    
    @property
    @abstractmethod
    def continue_backtest(self) -> bool:
        """是否继续回测"""
        pass

class Strategy(ABC):
    """策略抽象基类"""
    
    @abstractmethod
    def calculate_signals(self, event: MarketEvent) -> Optional[SignalEvent]:
        """根据市场事件计算交易信号"""
        pass

class Portfolio(ABC):
    """组合管理器抽象基类"""
    
    @abstractmethod
    def update_signal(self, event: SignalEvent) -> Optional[OrderEvent]:
        """根据信号生成订单"""
        pass
    
    @abstractmethod
    def update_fill(self, event: FillEvent) -> None:
        """更新持仓与资金"""
        pass
    
    @abstractmethod
    def update_timeindex(self, event: MarketEvent) -> None:
        """更新时间索引与净值"""
        pass

class ExecutionHandler(ABC):
    """执行处理器抽象基类"""
    
    @abstractmethod
    def execute_order(self, event: OrderEvent) -> Optional[FillEvent]:
        """执行订单"""
        pass
```

### 3.3 事件循环核心逻辑

```python
from queue import Queue, Empty
import time

class Backtest:
    """回测引擎"""
    
    def __init__(
        self,
        data_handler: DataHandler,
        strategy: Strategy,
        portfolio: Portfolio,
        execution_handler: ExecutionHandler,
        heartbeat: float = 0.0  # 回测模式下无需等待
    ):
        self.data_handler = data_handler
        self.strategy = strategy
        self.portfolio = portfolio
        self.execution_handler = execution_handler
        self.heartbeat = heartbeat
        self.events: Queue = Queue()
    
    def run(self) -> None:
        """运行回测"""
        while True:
            # 更新 Bar 数据
            if self.data_handler.continue_backtest:
                self.data_handler.update_bars()
            else:
                break
            
            # 处理事件队列
            while True:
                try:
                    event = self.events.get(block=False)
                except Empty:
                    break
                
                if event.event_type == EventType.MARKET:
                    # 策略计算信号
                    signal = self.strategy.calculate_signals(event)
                    if signal:
                        self.events.put(signal)
                    # 更新组合时间索引
                    self.portfolio.update_timeindex(event)
                
                elif event.event_type == EventType.SIGNAL:
                    # 组合生成订单
                    order = self.portfolio.update_signal(event)
                    if order:
                        self.events.put(order)
                
                elif event.event_type == EventType.ORDER:
                    # 执行订单
                    fill = self.execution_handler.execute_order(event)
                    if fill:
                        self.events.put(fill)
                
                elif event.event_type == EventType.FILL:
                    # 更新持仓
                    self.portfolio.update_fill(event)
            
            # 心跳等待（实盘模式下使用）
            if self.heartbeat > 0:
                time.sleep(self.heartbeat)
```

### 3.4 错误处理与重试策略

| 场景           | 策略            | 实现                            |
| -------------- | --------------- | ------------------------------- |
| 数据源连接失败 | 指数退避重试    | 最多 5 次，间隔 1s/2s/4s/8s/16s |
| 订单执行超时   | 超时取消 + 告警 | 30s 超时，发送通知              |
| 行情数据缺失   | 跳过 + 日志记录 | 记录缺失时间点，继续回测        |
| 策略异常       | 熔断 + 告警     | 连续 3 次异常暂停策略           |

---

## 3.5 性能预估与容量规划

### 性能指标预估

| 指标         | 目标值         | 测量方法       |
| ------------ | -------------- | -------------- |
| 回测速度     | > 10,000 Bar/s | 单策略日线回测 |
| API 延迟     | < 200ms        | P95 响应时间   |
| 实时行情延迟 | < 500ms        | 从数据源到策略 |
| 并发策略数   | > 10           | 沙盒多策略并行 |

### 资源消耗预估

- **内存**: 单策略回测 ~500MB，沙盒 10 策略 ~2GB
- **CPU**: 回测为 CPU 密集型，建议 4 核以上
- **存储**: 10 年 A 股日线数据 ~5GB，分钟线 ~500GB

### 容量规划

- **预期 QPS**: 日常 10 QPS，峰值 100 QPS
- **扩展策略**: 无状态服务，支持水平扩展
- **瓶颈分析**: 回测引擎为计算瓶颈，可通过多进程并行优化

---

## 4. 技术栈选型

### 4.1 后端技术栈

| 类别         | 选型           | 理由                                  |
| ------------ | -------------- | ------------------------------------- |
| **语言**     | Python 3.11+   | 量化生态成熟（Pandas、NumPy、TA-Lib） |
| **Web 框架** | FastAPI        | 异步支持、自动文档、类型安全          |
| **ORM**      | SQLAlchemy 2.0 | 成熟稳定、支持异步                    |
| **任务队列** | Celery + Redis | 异步任务、定时任务                    |
| **消息队列** | Redis Streams  | 轻量级事件总线，后期可升级 RabbitMQ   |

### 4.2 前端技术栈

| 类别         | 选型                  | 理由                 |
| ------------ | --------------------- | -------------------- |
| **框架**     | React 18              | 生态成熟、组件丰富   |
| **语言**     | TypeScript            | 类型安全、IDE 支持好 |
| **UI 库**    | Ant Design            | 企业级组件、图表支持 |
| **图表**     | ECharts / TradingView | 专业金融图表         |
| **状态管理** | Zustand               | 轻量、简单           |

### 4.3 数据存储

| 类别         | 选型          | 理由                          |
| ------------ | ------------- | ----------------------------- |
| **主数据库** | PostgreSQL 15 | 事务支持、JSON 支持、成熟稳定 |
| **时序数据** | ClickHouse    | 高性能时序查询、列式存储      |
| **缓存**     | Redis 7       | 高性能、支持 Streams          |
| **文件存储** | MinIO / 本地  | 回测结果、报告存储            |

### 4.4 基础设施

| 类别       | 选型                    | 理由               |
| ---------- | ----------------------- | ------------------ |
| **容器化** | Docker + Docker Compose | 本地开发与部署一致 |
| **CI/CD**  | GitHub Actions          | 免费、集成好       |
| **监控**   | Prometheus + Grafana    | 开源、功能完整     |
| **日志**   | Loki                    | 与 Grafana 集成    |

---

## 5. 安全与合规

### 5.1 密钥管理

- 敏感配置使用环境变量或 `.env` 文件
- 生产环境使用 Vault 或云服务密钥管理
- API Key 加密存储，禁止明文日志

### 5.2 日志脱敏

- 用户密码、API Key 禁止记录
- 交易金额、持仓数量脱敏处理
- 日志分级：DEBUG/INFO/WARNING/ERROR

### 5.3 数据安全

- 数据库连接使用 SSL
- 用户数据隔离（多租户）
- 定期备份与恢复演练

---

## 6. 可观测性

### 6.1 日志

- 结构化日志（JSON 格式）
- 请求 ID 链路追踪
- 关键操作审计日志

### 6.2 指标

- 系统指标：CPU、内存、磁盘
- 业务指标：回测次数、策略数量、交易量
- 性能指标：API 延迟、回测速度

### 6.3 告警

- 系统异常告警（服务不可用）
- 业务异常告警（策略熔断）
- 资源告警（磁盘空间不足）

---

## 7. 测试策略

### 7.1 测试分层

| 层级     | 覆盖率目标 | 工具                    |
| -------- | ---------- | ----------------------- |
| 单元测试 | > 80%      | pytest                  |
| 集成测试 | > 60%      | pytest + testcontainers |
| E2E 测试 | 核心流程   | Playwright              |

### 7.2 回测验证

- Golden Dataset：使用已知结果的历史数据验证回测引擎
- 边界测试：空数据、极端行情、停牌处理
- 一致性测试：回测与实盘逻辑一致性

---

## 8. 里程碑对齐

| 里程碑          | 架构重点                               |
| --------------- | -------------------------------------- |
| **M0**          | 架构设计、技术选型、核心接口定义       |
| **M1.0 MVP**    | 事件驱动框架、因子/策略 CRUD、基础回测 |
| **M2.0 沙盒**   | 多策略并行、虚拟账户、对比分析         |
| **M3.0 交易**   | 券商 API 对接、实盘执行、风控          |
| **M4.0 智能化** | AI 因子推荐、策略助手、性能优化        |
