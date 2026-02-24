# Sprint 6 Summary: M2.0 沙盒系统

## 🎯 Goal & Status
- **Goal**: 实现虚拟账户和多策略对比功能，让用户能在沙盒中验证策略有效性
- **Status**: ✅ Completed
- **里程碑**: M2.0 - 沙盒系统
- **启动日期**: 2026-02-24
- **完成日期**: 2026-02-24

## 🎬 User Story Demo Scenarios

### 场景 1: 创建沙盒账户
- **Input**: 用户在沙盒页面点击"新建账户"，输入名称和初始资金 100 万
- **Output**: 系统创建虚拟账户，显示账户详情页面

### 场景 2: 部署策略到沙盒
- **Input**: 用户选择"均线交叉策略"，设置运行周期和资金比例
- **Output**: 策略部署成功，状态为"待运行"

### 场景 3: 执行策略
- **Input**: 用户点击"运行"按钮
- **Output**: 系统获取真实行情，生成交易信号，执行模拟交易，更新持仓和净值

### 场景 4: 多策略对比
- **Input**: 用户选择多个部署进行对比
- **Output**: 显示各策略的收益率、夏普比率、最大回撤等指标对比

## 📋 Task Detail Archive

### TASK-1: 沙盒账户数据模型与 API (P0) ✅

**说明**: 实现沙盒账户的数据库模型和 CRUD API

**交付产物**:
| 产物 | 路径 | 说明 |
|------|------|------|
| 数据模型 | `backend/app/models/sandbox.py` | SandboxAccount, SandboxPosition, SandboxTransaction, SandboxDeployment, SandboxDailyValue |
| Schema | `backend/app/schemas/sandbox.py` | Pydantic 请求/响应模型 |
| Repository | `backend/app/repositories/sandbox_repo.py` | 数据访问层 |
| Service | `backend/app/services/sandbox_service.py` | 业务逻辑层 |
| API | `backend/app/api/v1/endpoints/sandbox.py` | 11 个 REST API 端点 |

---

### TASK-2: 沙盒执行引擎 (P0) ✅

**说明**: 实现沙盒策略执行引擎，支持策略部署、每日执行和模拟撮合

**交付产物**:
| 产物 | 路径 | 说明 |
|------|------|------|
| 执行引擎 | `backend/app/services/sandbox_engine.py` | SandboxExecutionEngine 类 |
| 策略接口扩展 | `backend/app/services/backtest_engine.py` | 添加 generate_signal_from_prices 方法 |

**核心功能**:
- 获取真实行情数据
- 生成交易信号
- 执行模拟撮合（买入/卖出）
- 更新持仓和净值
- 记录每日净值历史

---

### TASK-3: 多策略对比服务 (P0) ✅

**说明**: 实现多策略绩效对比分析功能

**交付产物**:
| 产物 | 路径 | 说明 |
|------|------|------|
| 对比服务 | `backend/app/services/sandbox_service.py` | compare_strategies 方法 |

**计算指标**:
- total_return: 总收益率
- annual_return: 年化收益率
- max_drawdown: 最大回撤
- sharpe_ratio: 夏普比率
- volatility: 波动率
- win_rate: 胜率
- total_trades: 总交易次数

---

### TASK-4: 沙盒前端页面 (P0) ✅

**说明**: 实现沙盒管理的前端页面

**交付产物**:
| 产物 | 路径 | 说明 |
|------|------|------|
| 类型定义 | `frontend/src/types/sandbox.ts` | TypeScript 接口 |
| API 客户端 | `frontend/src/api/sandbox.ts` | API 调用方法 |
| 账户列表页 | `frontend/src/pages/Sandbox.tsx` | 账户列表、搜索、新建 |
| 账户详情页 | `frontend/src/pages/SandboxDetail.tsx` | 持仓、交易、部署管理 |

---

### TASK-5: 测试与文档 (P1) ✅

**说明**: 编写单元测试、集成测试，更新 API 文档

**交付产物**:
| 产物 | 路径 | 说明 |
|------|------|------|
| 测试用例 | `backend/tests/test_sandbox.py` | 15 个 API 测试用例 |
| API 文档 | `docs/api-reference.md` | 沙盒 API 文档 |

**测试结果**:
- 核心测试: 50 passed ✅
- 前端构建: 成功 ✅

## 🐛 Critical Bugs & Retrospective

### 修复的问题
1. **TypeScript InputNumber 类型错误**: parser 函数返回类型不匹配，修复为使用泛型 `InputNumber<number>`

### 技术决策
1. **沙盒执行引擎架构**: 复用回测引擎的策略类，通过 `generate_signal_from_prices` 方法生成信号
2. **数据模型设计**: 使用独立的 SandboxPosition/SandboxTransaction 表，与回测数据隔离
3. **绩效指标计算**: 在服务层实现，支持灵活的对比分析

## 📊 Metrics

| 指标 | 数值 |
|------|------|
| 新增后端文件 | 5 |
| 新增前端文件 | 4 |
| 新增 API 端点 | 11 |
| 新增测试用例 | 15 |
| 核心测试通过率 | 100% |
