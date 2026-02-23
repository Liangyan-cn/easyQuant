# easyQuant 项目看板

## 📝 指令 (Instructions)
- 本文件是项目进度的 **单一事实来源 (SSOT)**。
- 只有 `sprint-manager` 及其子技能可以修改此文件。
- 任务状态标记: `[ ]` (Pending), `[~]` (In Progress), `[x]` (Done).

## 🏃 当前 Sprint

**Sprint ID**: Sprint 1
**标题**: M0 项目启动
**周期**: 2025-02-23 ~ 2025-03-08
**目标**: 完善项目核心文档，明确产品方向和技术架构
**里程碑**: M0 - 核心文档与架构设计

### 强制任务

- [x] 里程碑对齐与方向校准 (Milestone Alignment & Direction Check)
    - ✅ 愿景一致性: backlog.md 和 milestones.md 愿景一致
    - ✅ M0 目标对齐: Sprint 目标与 M0 里程碑匹配
    - ✅ 任务完整性: M0 所有任务已分解到 kanban.md
    - ✅ 输出路径: 所有文档输出路径已定义
- [x] Sprint 启动检查 (Sprint Initialization Checklist)
    - ✅ 目录结构: docs/tech, docs/product, docs/reports, docs/sprints 已创建
    - ✅ Git 状态: 工作区干净，已提交到 main 分支
    - ✅ 技能就绪: 5 个 Agent Skills 已配置
    - ✅ 工具就绪: init_workspace, analyze_docs, generate_index 可用

### 产品文档

- [x] **产品愿景文档** (Priority: P0)
    - 目标用户画像（个人投资者细分）
    - 核心价值主张
    - 差异化竞争优势
    - 输出: `docs/product/vision.md`

- [x] **核心用户故事** (Priority: P0)
    - 因子研究员场景
    - 策略开发者场景
    - 交易执行者场景
    - 输出: `docs/product/user_stories.md`

- [x] **竞品分析报告** (Priority: P1)
    - 国内量化平台对比（聚宽、米筐、优矿）
    - 海外平台参考（QuantConnect、Zipline）
    - 差异化定位
    - 输出: `docs/product/competitor_analysis.md`

### 技术文档

- [x] **技术架构设计** (Priority: P0)
    - 系统整体架构图
    - 核心模块划分
    - 技术栈选型（前端/后端/数据库/消息队列）
    - 输出: `docs/tech/architecture.md`

- [x] **数据架构设计** (Priority: P0)
    - 数据模型设计（因子、策略、交易）
    - 数据流设计
    - 数据存储方案
    - 输出: `docs/tech/data_model.md`

- [ ] **API 设计规范** (Priority: P1)
    - RESTful API 设计原则
    - 接口版本管理
    - 错误码规范
    - 输出: `docs/tech/api_spec.md`

### 项目管理

- [ ] **开发环境搭建指南** (Priority: P1)
    - 输出: `docs/tech/setup.md`

- [ ] **代码规范与 Git 工作流** (Priority: P1)
    - 输出: `docs/tech/coding_standards.md`

- [ ] **CI/CD 流程设计** (Priority: P2)
    - 输出: `docs/tech/cicd.md`

## 📦 待办池 (Backlog)

### M1.0 MVP 阶段

| 优先级 | 特性 | 描述 |
|--------|------|------|
| P0 | 用户认证 | 注册、登录、会话管理 |
| P0 | 因子管理 CRUD | 创建、编辑、删除因子 |
| P0 | 因子回测 | 因子的历史回测能力 |
| P0 | 策略管理 CRUD | 创建、编辑、删除策略 |
| P0 | 策略回测 | 策略的历史回测框架 |
| P0 | 绩效评估 | 回测绩效指标计算 |
| P0 | 基础数据接口 | 股票、基金历史数据 |

## 🎯 里程碑 (Milestones)

| 里程碑 | 状态 | 描述 |
|--------|------|------|
| **M0** | 🏃 进行中 | 核心文档与架构设计 |
| **M1.0** | ⚪ 待开始 | MVP 核心基础功能 |
| **M2.0** | ⚪ 待开始 | 沙盒系统 |
| **M3.0** | ⚪ 待开始 | 交易执行 |
| **M4.0** | ⚪ 待开始 | 智能化升级 |

## 📜 历史 Sprints (Completed)
<!-- Completed sprints will be archived here -->
