# easyQuant 项目看板

## 🏃 当前 Sprint

**Sprint ID**: Sprint 12
**标题**: 易用性问题修复 (基于人工评估)
**状态**: 🔄 进行中
**里程碑**: M2.0 - 沙盒系统 (用户体验)
**目标**: 修复人工评估发现的 15 个易用性问题，提升小白用户体验
**启动日期**: 2026-02-24
**问题来源**: `docs/ux/usability-issues.md`

### 强制任务
- [x] 里程碑对齐与方向校准
- [x] Sprint 启动检查
- [x] 功能梳理与易用性评估 (TASK-0)

### 任务列表

#### TASK-0: 功能梳理与易用性评估 (P0) ✅

**说明**: 逐一梳理系统各模块功能，评估小白用户使用体验，识别易用性问题

**依赖**: 无

**子任务**:
- [x] 首页功能梳理
- [x] 因子模块梳理
- [x] 策略模块梳理
- [x] 回测模块梳理
- [x] 沙盒模块梳理
- [x] 数据模块梳理
- [x] 汇总易用性问题清单

**交付产物**: 
- `docs/ux/feature-review.md` - 功能梳理文档
- `docs/ux/usability-issues.md` - 易用性问题清单 (15 个问题)

#### TASK-1: 阻塞问题修复 (P0) ✅

**说明**: 修复 5 个阻塞级别问题，确保核心功能可用

**依赖**: TASK-0

**子任务**:
- [x] H1: 首页卡片添加点击跳转
- [x] D2: 股票池详情股票列表添加跳转到股票详情
- [x] D3: 股票池详情添加股票搜索功能
- [x] G1: 移除 /settings 菜单入口
- [x] G2: 移除 /profile 菜单入口

**交付产物**:
- `frontend/src/pages/Home.tsx` - 首页卡片点击跳转
- `frontend/src/components/StockPoolTab.tsx` - 股票池搜索和跳转
- `frontend/src/layouts/MainLayout.tsx` - 移除未实现菜单

#### TASK-2: 首页重构 (P0) ✅

**说明**: 重新设计首页，仅展示已支持的功能入口

**依赖**: TASK-1

**子任务**:
- [x] 明确首页设计原则 (仅展示可用功能)
- [x] 重新设计功能卡片 (5个功能模块)
- [x] 移除或标记未实现功能 ("即将上线"标签)
- [x] 添加快速入口导航 (4步引导)

**交付产物**:
- `frontend/src/pages/Home.tsx` - 重构首页，添加快速开始引导

#### TASK-3: 内置因子/策略说明 (P1) ✅

**说明**: 为内置因子和策略添加详细说明，解决用户困惑

**依赖**: 无

**子任务**:
- [x] F1: 优化"初始化内置因子"按钮提示 (Tooltip + 空状态引导)
- [x] F2: 为因子分析添加结果解读指南 (IC/IR 说明)
- [x] S1: 简化策略状态设计 (移除状态筛选器)
- [x] S2: 为内置策略添加详细描述 (策略类型说明)

**交付产物**:
- `frontend/src/pages/Factors.tsx` - 因子列表空状态引导
- `frontend/src/pages/FactorDetail.tsx` - 因子分析结果解读
- `frontend/src/pages/Strategies.tsx` - 策略列表空状态引导
- `frontend/src/pages/StrategyDetail.tsx` - 策略类型说明

#### TASK-4: 数据模块优化 (P1) ✅

**说明**: 优化股票池和股票列表的交互体验

**依赖**: TASK-1

**子任务**:
- [x] D1: 调整 Tab 顺序 (股票池 → 股票列表)
- [ ] D4: 改造股票选择组件 (延期)
- [ ] D5: 股票列表添加股票池筛选器 (延期)

**交付产物**:
- `frontend/src/pages/Stocks.tsx` - Tab 顺序调整，重命名为"数据中心"

---

### ⏸️ Sprint 11: 股票池管理与数据缓存 (暂停)

**状态**: ⏸️ 暂停 (因 AKShare 限流无法完成缓存预加载测试)
**里程碑**: M2.0 - 沙盒系统 (数据服务增强)
**目标**: 实现股票池管理功能，建立数据缓存机制
**启动日期**: 2026-02-24

**已完成任务**:
- ✅ TASK-1: 股票池管理 (P0) - 后端 API 完成，前端待开发
- ✅ TASK-2: 数据缓存方案 (P1) - 核心功能完成，预加载因限流暂停

**待恢复条件**: AKShare 限流解除后继续预加载测试

**交付产物**:
- `backend/app/models/stock_pool.py` - StockPool, StockPoolItem 数据模型
- `backend/app/services/cache_service.py` - CacheService (Parquet 持久化)
- `backend/app/scripts/cache_loader.py` - 预加载脚本
- `backend/tests/test_stock_pool.py` - 9 个测试
- `backend/tests/test_cache.py` - 4 个测试

---

## �� Backlog

### M2.0 沙盒系统增强

| 特性         | 描述               | 优先级 |
| ------------ | ------------------ | ------ |
| 定时执行     | 每日自动执行策略   | P0     |
| 策略组合     | 多策略组合管理     | P1     |
| 净值曲线图表 | 可视化净值走势     | P1     |
| 毕业机制     | 策略达标后推荐实盘 | P2     |

### 功能完整性修复

| 描述                | 模块     | 优先级 | 状态     |
| ------------------- | -------- | ------ | -------- |
| 修改密码功能        | 用户系统 | P2     | 待处理   |
| 部署删除前端入口    | 沙盒系统 | P1     | 待处理   |
| 账户出金功能        | 沙盒系统 | P2     | 待处理   |
| 策略参数界面编辑    | 策略系统 | P1     | 待处理   |
| 策略状态转换 API    | 策略系统 | P2     | 待处理   |
| 回测取消功能        | 回测系统 | P1     | 待处理   |
| 因子值单条更新/删除 | 因子系统 | P2     | 待处理   |
| 因子评估历史展示    | 因子系统 | P2     | 待处理   |
| 用户资源权限验证    | 全局安全 | P0     | ✅ 已完成 |

### 数据服务增强

| 描述             | 模块     | 优先级 | 状态     |
| ---------------- | -------- | ------ | -------- |
| 财务数据获取调研 | 数据服务 | P1     | ✅ 已完成 |

### 技术债务 (Tech Debt)

| 描述                   | 优先级 | 来源            | 状态     |
| ---------------------- | ------ | --------------- | -------- |
| Redis 缓存替换内存缓存 | P2     | Sprint 2.1 评估 | 待处理   |
| API Rate Limiting      | P2     | Sprint 2.1 评估 | 待处理   |
| Token 存储优化         | P2     | Sprint 2.1 评估 | 待处理   |
| 环境变量验证           | P2     | Sprint 2.1 评估 | 待处理   |
| 新手引导功能           | P2     | Sprint 5 延期   | 待处理   |
| 沙盒测试环境配置       | P1     | Sprint 6        | ✅ 已修复 |

---

## 🎯 里程碑 (Milestones)

| 里程碑 | 状态     | 核心交付                         | 成功指标             |
| ------ | -------- | -------------------------------- | -------------------- |
| M0     | ✅ 完成   | 产品愿景、技术架构、开发规范     | 文档完整度 100%      |
| M1.0   | ✅ 完成   | 因子管理、策略回测、基础数据     | 首次回测完成率 > 60% |
| M2.0   | 🔄 进行中 | 沙盒系统 - 虚拟账户、多策略对比  | 沙盒使用率 > 40%     |
| M3.0   | ⚪ 待开始 | 交易执行 - 模拟交易、券商对接    | 订单执行成功率 > 99% |
| M4.0   | ⚪ 待开始 | 智能升级 - AI 因子推荐、策略助手 | 用户满意度 NPS > 50  |

---

## 📜 历史 Sprints

### ✅ Sprint 10: 功能完整性修复与财务数据调研 (已完成)
**里程碑**: M2.0 - 沙盒系统 (功能完善)
**目标**: 修复 Backlog 中的功能缺失项，调研财务数据获取方案，提升产品完整度
**执行日期**: 2026-02-24
**总结文档**: `docs/sprints/sprint-10-summary.md`

**关键交付物**:
- ✅ 安全加固: 用户资源权限验证 (Factor/Strategy/Sandbox API)
- ✅ 调研报告: 财务数据获取方案 (推荐 AKShare)

**测试统计**: 180 个后端测试通过 (100%)

**完工验收**: ✅ 已完成 (3/3 任务, 100%)

---

### ✅ Sprint 9: 测试覆盖与 CI/CD 建设 (已完成)
**里程碑**: M2.0 - 沙盒系统 (质量保障)
**目标**: 提升测试覆盖率，建立 CI/CD 流程，确保代码质量标准化
**执行日期**: 2026-02-24
**总结文档**: `docs/sprints/sprint-9-summary.md`

**关键交付物**:
- ✅ 后端测试: 180 tests (sandbox_engine, factor_calculator, backtest_engine)
- ✅ 前端单元测试: 46 tests (Home, Stocks, Factors, Strategies, Sandbox)
- ✅ E2E 测试: 62 tests (factors, strategies, sandbox, user-journey)
- ✅ CI/CD: GitHub Actions 工作流 + PR 模板

**测试统计**: 288 个测试用例 (后端 66% 覆盖率, E2E 95% 通过率)

**完工验收**: ✅ 已完成 (5/5 任务, 100%)

---

### ✅ Sprint 8: M2.0 功能完整性修复 (已完成)
**里程碑**: M2.0 - 沙盒系统
**目标**: 修复功能缺失和逻辑不完整的问题，确保核心功能闭环
**执行日期**: 2026-02-24
**总结文档**: `docs/sprints/sprint-8-summary.md`

**关键交付物**:
- ✅ 用户登出: 后端 API + 前端用户菜单
- ✅ 沙盒部署: 恢复运行 API + 状态管理
- ✅ 策略复制: 克隆 API + 前端复制按钮
- ✅ 回测增强: 删除/重跑按钮 + 权益曲线图表
- ✅ 因子分析: 计算+评估合并 + 批量计算脚本

**代码提交**: 7 个 commits, 114 个文件, 17,817 行新增代码

**完工验收**: ✅ 已完成 (4/4 任务, 100%)

---

### ✅ Sprint 7: M2.0 沙盒代码质量优化 (已完成)
**里程碑**: M2.0 - 沙盒系统
**目标**: 修复代码审查发现的问题，提升代码质量和安全性
**执行日期**: 2026-02-24
**总结文档**: `docs/sprints/sprint-7-summary.md`

**关键交付物**:
- ✅ 数据验证: 除零保护、日期范围验证
- ✅ 并发控制: 乐观锁机制 (version 字段 + update_with_lock)
- ✅ 配置化: TradingConfig 类 (佣金率、印花税率、无风险利率)
- ✅ 数据库索引: SandboxDailyValue、SandboxPosition 唯一索引
- ✅ 代码质量: 类型注解、常量提取、日志优化

**完工验收**: ✅ 已完成 (5/5 任务, 100%)

---

### ✅ Sprint 6: M2.0 沙盒系统 (已完成)
**里程碑**: M2.0 - 沙盒系统 (Phase 1/2)
**目标**: 实现虚拟账户和多策略对比功能
**执行日期**: 2026-02-24
**总结文档**: `docs/sprints/sprint-6-summary.md`

**关键交付物**:
- ✅ 数据模型: SandboxAccount, SandboxPosition, SandboxTransaction, SandboxDeployment, SandboxDailyValue
- ✅ 执行引擎: SandboxExecutionEngine (信号生成、模拟撮合、净值计算)
- ✅ 多策略对比: 7 项绩效指标计算 (收益率、夏普比率、最大回撤等)
- ✅ 前端页面: 沙盒账户列表、详情、策略部署
- ✅ API 端点: 11 个沙盒相关 API
- ✅ 测试: 50 个核心测试通过

**完工验收**: ✅ 已完成 (5/5 任务, 100%)

---

### ✅ Sprint 5: MVP 完善与发布准备 (已完成)
**里程碑**: M1.0 - MVP 发布 (Phase 4/4)
**目标**: 完善 MVP 功能，修复已知问题，准备发布
**执行日期**: 2026-02-24
**总结文档**: `docs/sprints/sprint-5-summary.md`

**关键交付物**:
- ✅ Bug 修复: TypeScript 编译错误修复
- ✅ 回测集成: 回测执行 API + 前端回测配置/结果展示
- ✅ 因子功能: 因子计算和评估功能已集成
- ✅ API 文档: `docs/api-reference.md`
- ✅ 测试: 50 个后端测试全部通过

**完工验收**: ✅ 已完成 (6/6 任务, 100%)

---

### ✅ Sprint 4: 策略模块 (已完成)
**里程碑**: M1.0 - MVP 发布 (Phase 3/4)
**目标**: 实现策略的完整生命周期管理，包括 CRUD、回测引擎和绩效评估
**执行日期**: 2026-02-23
**总结文档**: `docs/sprints/sprint-4-summary.md`

**关键交付物**:
- ✅ 后端: Strategy/Backtest/BacktestResult 数据模型 + CRUD API + 回测引擎 + 绩效评估
- ✅ 前端: 策略列表页面 + 策略详情页面
- ✅ 内置策略: 5 个示例策略 (双均线、动量、均值回归、布林带、RSI)
- ✅ 测试: 15 个策略 API 测试用例

**完工验收**: ✅ 已完成 (7/7 任务, 100%)

---

### ✅ Sprint 3: 因子模块 (已完成)
**里程碑**: M1.0 - MVP 发布 (Phase 2/4)
**目标**: 实现因子的完整生命周期管理
**执行日期**: 2026-02-23
**总结文档**: `docs/sprints/sprint-3-summary.md`

**关键交付物**:
- ✅ 后端: Factor 数据模型 + CRUD API + 计算引擎 + 评估服务
- ✅ 前端: 因子列表页面 + 因子详情页面 (含图表)
- ✅ 测试: 12 个因子 API 测试用例
- ✅ 技术债务修复: Pydantic ConfigDict 迁移、passlib crypt 废弃警告

**完工验收**: ✅ 已完成 (7/7 任务, 100%)

---

### ✅ Sprint 2.1: 质量加固 (已完成)
**里程碑**: M1.0 - MVP 发布 (Phase 1.5/4)
**目标**: 建立完整的自动化测试体系
**执行日期**: 2026-02-23
**总结文档**: `docs/sprints/sprint-2.1-summary.md`

**完工验收**: ✅ 已完成 (12/12 任务, 100%)

---

### ✅ Sprint 2: M1.0 基础设施 (已完成)
**里程碑**: M1.0 - MVP 发布 (Phase 1/4)
**目标**: 完成项目基础设施搭建
**执行日期**: 2026-02-23
**总结文档**: `docs/sprints/sprint-2-summary.md`

**完工验收**: ✅ 已完成 (13/13 任务, 100%)

---

### ✅ Sprint 1: M0 项目启动 (已完成)
**里程碑**: M0 - 核心文档与架构设计
**目标**: 完善项目核心文档
**执行日期**: 2026-02-23
**总结文档**: `docs/sprints/sprint-1-m0-summary.md`

**完工验收**: ✅ 已完成 (11/11 任务, 100%)

---

## 📚 核心文档索引

> ⚠️ **Sprint 结束检查**: 每次 Sprint 结束时，需检查以下核心文档是否需要更新。如有过时内容，应在下一 Sprint 中补充文档更新任务。

### 产品文档

| 文档       | 路径                                  | 说明               |
| ---------- | ------------------------------------- | ------------------ |
| 产品愿景   | `docs/product/vision.md`              | 产品定位与核心价值 |
| 用户故事   | `docs/product/user_stories.md`        | 用户需求与场景     |
| 里程碑规划 | `docs/product/milestones.md`          | 版本规划与交付节点 |
| 产品待办   | `docs/product/backlog.md`             | 功能待办列表       |
| 竞品分析   | `docs/product/competitor_analysis.md` | 竞品调研与分析     |

### 技术文档

| 文档       | 路径                            | 说明                 |
| ---------- | ------------------------------- | -------------------- |
| 技术架构   | `docs/tech/architecture.md`     | 系统架构设计         |
| 数据模型   | `docs/tech/data_model.md`       | 数据库设计与模型定义 |
| API 参考   | `docs/api-reference.md`         | API 接口文档         |
| 代码规范   | `docs/tech/coding_standards.md` | 编码规范与最佳实践   |
| CI/CD 文档 | `docs/tech/cicd.md`             | 持续集成与部署流程   |
| 环境配置   | `docs/tech/setup.md`            | 开发环境配置指南     |      | 文档 | 路径 |
| ---------- | ------------------------------  |
| 产品愿景   | `docs/product/vision.md`        |
| 用户故事   | `docs/product/user_stories.md`  |
| 里程碑规划 | `docs/product/milestones.md`    |
| 技术架构   | `docs/tech/architecture.md`     |
| API 参考   | `docs/api-reference.md`         |
| 数据模型   | `docs/tech/data_model.md`       |                      | 文档 | 路径 |
| ---------- | ------------------------------  |
| 产品愿景   | `docs/product/vision.md`        |
| 用户故事   | `docs/product/user_stories.md`  |
| 里程碑规划 | `docs/product/milestones.md`    |
| 技术架构   | `docs/tech/architecture.md`     |
| API 参考   | `docs/api-reference.md`         |
| 数据模型   | `docs/tech/data_model.md`       |                      | 文档 | 路径 |
| ---------- | ------------------------------  |
| 产品愿景   | `docs/product/vision.md`        |
| 用户故事   | `docs/product/user_stories.md`  |
| 里程碑规划 | `docs/product/milestones.md`    |
| 技术架构   | `docs/tech/architecture.md`     |
| API 参考   | `docs/api-reference.md`         |
| 数据模型   | `docs/tech/data_model.md`       |                      | 文档 | 路径 |
| ---------- | ------------------------------  |
| 产品愿景   | `docs/product/vision.md`        |
| 用户故事   | `docs/product/user_stories.md`  |
| 里程碑规划 | `docs/product/milestones.md`    |
| 技术架构   | `docs/tech/architecture.md`     |
| API 参考   | `docs/api-reference.md`         |
| 数据模型   | `docs/tech/data_model.md`       |                      | 文档 | 路径 |
| ---------- | ------------------------------  |
| 产品愿景   | `docs/product/vision.md`        |
| 用户故事   | `docs/product/user_stories.md`  |
| 里程碑规划 | `docs/product/milestones.md`    |
| 技术架构   | `docs/tech/architecture.md`     |
| API 参考   | `docs/api-reference.md`         |
| 数据模型   | `docs/tech/data_model.md`       |                      | 文档 | 路径 |
| ---------- | ------------------------------  |
| 产品愿景   | `docs/product/vision.md`        |
| 用户故事   | `docs/product/user_stories.md`  |
| 里程碑规划 | `docs/product/milestones.md`    |
| 技术架构   | `docs/tech/architecture.md`     |
| API 参考   | `docs/api-reference.md`         |
| 数据模型   | `docs/tech/data_model.md`       || 文档       | 路径                           |
| ---------- | ------------------------------ |
| 产品愿景   | `docs/product/vision.md`       |
| 用户故事   | `docs/product/user_stories.md` |
| 里程碑规划 | `docs/product/milestones.md`   |
| 技术架构   | `docs/tech/architecture.md`    |
| API 参考   | `docs/api-reference.md`        |
| 数据模型   | `docs/tech/data_model.md`      |