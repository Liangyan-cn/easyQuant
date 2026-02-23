# 技术架构设计

**版本历史**:
*   v1.0 | 2026-02-23 | @user | 初稿

## 0. 技术调研与选型评估

### 0.1 核心问题定义 (Problem Definition)
* **本质问题**: 如何为个人投资者提供从研究、回测、沙盒到交易执行的端到端量化能力，并保持低门槛与可扩展性？
* **现状不足**: 传统研究型平台与开源回测框架往往缺乏完整交易闭环或新手友好性，难以支撑从学习到实盘的连续体验。

### 0.2 候选方案深度对比 (In-depth Comparison)
#### 方案 A：模块化插件式架构
* **学术/行业背景**: LEAN 强调组件可插拔与模块化设计，便于扩展数据源、交易执行与结果输出。[QuantConnect LEAN](https://github.com/QuantConnect/Lean)
* **行业趋势**: 从单体走向模块化与可插拔组件，支持多数据源、多券商与多运行模式。
* **适配点**:
  - 适合多阶段演进（M1 回测、M2 沙盒、M3 交易执行）
  - 可按需引入新模块（指标体系、风控、监控）
* **致命弱点**:
  - 初期设计成本高，接口定义复杂
  - 需要严格的版本治理与模块边界
* **结论**: 适合作为长期架构基础，但需控制早期复杂度。

#### 方案 B：轻量单体架构
* **学术/行业背景**: 事件驱动回测框架强调简单、易用与快速迭代。[Zipline](https://github.com/quantopian/zipline)
* **行业趋势**: 小团队早期倾向单体快速验证。
* **适配点**:
  - 开发成本低、迭代快
  - 便于快速试错验证
* **致命弱点**:
  - 扩展性差，难以支持多数据源与交易执行
  - 无法支撑端到端闭环
* **结论**: 适合原型阶段，但不满足 M2/M3 的扩展诉求。

### 0.4 选型结论与演进路线 (Conclusion & Roadmap)
* **本轮结论 (Current Milestone)**: 选择模块化插件式架构
* **核心理由**: 兼容长期扩展与端到端闭环需求
* **核心观点应用 (Application)**:
    * 采用分层模块边界与可替换接口，避免核心链路被单一实现锁定
* **演进路线**: M1 先落地核心模块接口，M2/M3 逐步补齐沙盒与交易执行模块

## 1. 目标与非目标
* 目标：
  - 定义端到端量化平台的核心模块边界
  - 建立数据流与关键接口的统一规范
* 非目标：
  - 不在 M0 定义具体算法策略实现细节
  - 不在 M0 完成券商实盘对接

## 2. 架构与数据流
* 模块边界：
```
数据层 -> 研究层 -> 回测层 -> 沙盒层 -> 交易执行层 -> 监控与复盘
```
* 调用链路：
```mermaid
graph LR
    A[数据接入] --> B[因子研究]
    B --> C[策略开发]
    C --> D[回测引擎]
    D --> E[沙盒实测]
    E --> F[交易执行]
    F --> G[监控与复盘]
```

## 3. 核心设计
* **数据结构 (Spec Definition)**:
```python
from pydantic import BaseModel
from typing import Dict, List, Optional

class FactorSpec(BaseModel):
    id: str
    name: str
    description: Optional[str]
    parameters: Dict[str, float]

class StrategySpec(BaseModel):
    id: str
    name: str
    factor_ids: List[str]
    parameters: Dict[str, float]

class BacktestRequest(BaseModel):
    strategy_id: str
    start_date: str
    end_date: str
    capital: float
    benchmark: Optional[str]

class TradeSignal(BaseModel):
    symbol: str
    action: str
    quantity: float

class PortfolioSnapshot(BaseModel):
    timestamp: str
    positions: Dict[str, float]
    cash: float
```
* **接口定义**:
  - `DataProvider.get_bars(symbol, start, end)`
  - `BacktestEngine.run(request)`
  - `ExecutionGateway.submit(signal)`
* 关键算法/流程：
  1. 数据接入与清洗  
  2. 因子计算与策略生成  
  3. 回测与绩效评估  
  4. 沙盒实测与风控校验  
  5. 实盘执行与交易复盘  
* 错误处理与重试策略：
  - 数据源超时：指数退避重试 3 次
  - 交易执行失败：降级为模拟执行并记录告警

## 3.5 性能预估与容量规划 (Performance Estimation)

### 性能指标预估
| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 延迟 (Latency) | < 300ms | P95 响应时间 |
| 吞吐 (Throughput) | > 50 QPS | 并发请求数 |
| 准确率 (Accuracy) | > 90% | Golden Dataset 评测 |
| 召回率 (Recall) | > 85% | Golden Dataset 评测 |

### 资源消耗预估
* **内存**: 2GB
* **GPU**: 不需要
* **存储**: 数据缓存 10GB

### 成本估算
* **API 调用成本**: 以数据源供应商计价为准
* **计算成本**: CPU 实例为主
* **存储成本**: 低频数据为主

### 容量规划
* **预期 QPS**: 日常 5 QPS，峰值 50 QPS
* **扩展策略**: 无状态服务可水平扩展
* **瓶颈分析**: 数据读取与回测计算为主要瓶颈

## 4. 安全与合规
* 密钥管理：使用环境变量与密钥管理服务
* 日志脱敏：交易与用户信息脱敏

## 5. 可观测性
* 日志：记录核心链路与异常
* 指标：QPS、延迟、错误率
* Trace：关键调用链路追踪

## 6. 测试与验证
* 单元测试：核心模块接口
* 集成测试：回测与沙盒链路

## 7. 迁移与发布（如需要）
* 兼容性：保持接口向后兼容
* 发布步骤：灰度发布与回滚策略
