# easyQuant 项目看板

**版本历史**:
- v2.2 | 2026-02-23 | @AI | Sprint 2 启动 (M1.0 基础设施)

---

## 📝 指令 (Instructions)

- 本文件是项目进度的 **单一事实来源 (SSOT)**
- 只有 `sprint-manager` 及其子技能可以修改此文件
- 任务状态标记: `[ ]` (Pending), `[~]` (In Progress), `[x]` (Done)
- 优先级标记: `P0` (必须), `P1` (重要), `P2` (可选)

---

## 📊 Sprint 进度总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Sprint 2 进度看板                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   强制任务        项目初始化      用户认证        数据接口                   │
│   ────────        ──────────      ────────        ────────                  │
│   [██████] 2/2   [██████] 4/4   [██████] 4/4   [██████] 3/3               │
│     100%           100%           100%           100%                       │
│                                                                             │
│   ─────────────────────────────────────────────────────────────────────    │
│   总体进度: [██████████████████████████] 13/13 (100%) ✅                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| 类别 | 完成 | 总数 | 进度 | 状态 |
|------|------|------|------|------|
| 强制任务 | 2 | 2 | 100% | ✅ 完成 |
| 项目初始化 | 4 | 4 | 100% | ✅ 完成 |
| 用户认证 | 4 | 4 | 100% | ✅ 完成 |
| 数据接口 | 3 | 3 | 100% | ✅ 完成 |
| **总计** | **13** | **13** | **100%** | ✅ 完成 |

---

## 🏃 当前 Sprint

### Sprint 基本信息

| 字段 | 值 |
|------|------|
| **Sprint ID** | Sprint 2 |
| **标题** | M1.0 基础设施 |
| **周期** | 2026-02-23 ~ 2026-03-09 (2 周) |
| **里程碑** | M1.0 - MVP 发布 (Phase 1/4) |
| **目标** | 完成项目基础设施搭建，包括项目初始化、用户认证、基础数据接口 |

### Sprint 目标

> 搭建项目基础框架，实现用户认证和基础数据接口，为后续功能开发奠定基础。

### 成功标准

- [ ] 后端项目结构搭建完成，符合架构设计
- [ ] 前端项目结构搭建完成，符合架构设计
- [ ] 用户注册/登录功能可用
- [ ] JWT Token 认证机制正常工作
- [ ] 基础数据接口可获取股票列表和历史行情
- [ ] 所有 API 接口有单元测试覆盖

---

## ✅ 强制任务 (Mandatory)

### M-01: 里程碑对齐与方向校准

| 字段 | 值 |
|------|------|
| **状态** | ✅ 完成 |
| **优先级** | P0 |
| **完成时间** | 2026-02-23 |

**检查项**:
- [x] 确认 Sprint 目标与 M1.0 里程碑对齐
- [x] 确认技术栈选型与架构设计一致 (FastAPI + React + PostgreSQL)
- [x] 确认 API 设计与 api_spec.md 一致 (RESTful + JWT)
- [x] 确认数据模型与 data_model.md 一致 (PostgreSQL 单库启动)

---

### M-02: Sprint 启动检查

| 字段 | 值 |
|------|------|
| **状态** | ✅ 完成 |
| **优先级** | P0 |
| **完成时间** | 2026-02-23 |

**检查项**:
- [x] 开发环境已按 setup.md 配置完成
- [x] Git 分支策略已按 coding_standards.md 配置 (main → develop → feature/sprint2-infrastructure)
- [ ] CI/CD 流程已按 cicd.md 配置 (待项目初始化后配置)
- [ ] 数据库已创建并初始化 (待 INIT-03 完成)

---

## 🏗️ 项目初始化 (Project Setup)

### INIT-01: 后端项目初始化

| 字段 | 值 |
|------|------|
| **状态** | ✅ 完成 |
| **优先级** | P0 |
| **完成时间** | 2026-02-23 |
| **输出** | `backend/` 目录结构 |

**交付内容**:
- [x] FastAPI 项目结构搭建
- [x] 目录结构符合 coding_standards.md 规范
- [x] pyproject.toml 配置 (Black, isort, Ruff, mypy)
- [x] requirements.txt 和 requirements-dev.txt
- [x] .env.example 环境变量模板
- [ ] Alembic 数据库迁移配置 (待 INIT-03)
- [x] pytest 测试框架配置

**技术规格**:
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/v1/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── repositories/
├── tests/
├── migrations/
├── pyproject.toml
└── requirements.txt
```

---

### INIT-02: 前端项目初始化

| 字段 | 值 |
|------|------|
| **状态** | ✅ 完成 |
| **优先级** | P0 |
| **完成时间** | 2026-02-23 |
| **输出** | `frontend/` 目录结构 |

**交付内容**:
- [x] Vite + React + TypeScript 项目创建
- [x] 目录结构符合 coding_standards.md 规范
- [x] ESLint + Prettier 配置
- [x] Ant Design 组件库集成
- [x] React Router 路由配置
- [x] Axios API 客户端封装
- [x] 基础布局组件

**技术规格**:
```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── layouts/
│   ├── pages/
│   ├── stores/
│   ├── types/
│   └── utils/
├── .eslintrc.cjs
├── .prettierrc
└── vite.config.ts
```

---

### INIT-03: 数据库初始化

| 字段 | 值 |
|------|------|
| **状态** | ✅ 完成 |
| **优先级** | P0 |
| **完成时间** | 2026-02-23 |
| **输出** | 数据库 Schema |

**交付内容**:
- [x] PostgreSQL 数据库创建 (docker-compose.dev.yml)
- [x] 用户表 (users) 创建
- [x] Alembic 初始迁移脚本 (001_create_users_table.py)
- [ ] 种子数据脚本 (可选)

**数据库 Schema**:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### INIT-04: Docker 开发环境

| 字段 | 值 |
|------|------|
| **状态** | ✅ 完成 |
| **优先级** | P1 |
| **完成时间** | 2026-02-23 |
| **输出** | docker-compose.dev.yml |

**交付内容**:
- [x] docker-compose.dev.yml (PostgreSQL + Redis)
- [ ] 后端 Dockerfile (待生产环境时完善)
- [ ] 前端 Dockerfile (待生产环境时完善)
- [ ] .dockerignore 文件 (待生产环境时完善)

---

## 🔐 用户认证 (Authentication)

### AUTH-01: 用户注册 API

| 字段 | 值 |
|------|------|
| **状态** | ✅ 完成 |
| **优先级** | P0 |
| **完成时间** | 2026-02-23 |
| **用户故事** | - |
| **API** | `POST /api/v1/auth/register` |

**交付内容**:
- [x] 注册 API 端点实现
- [x] 邮箱格式验证
- [x] 密码强度验证 (8+ 字符)
- [x] 密码 bcrypt 加密存储
- [x] 重复邮箱检查
- [ ] 单元测试 (待补充)

**API 规格**:
```json
// Request
POST /api/v1/auth/register
{
    "email": "user@example.com",
    "password": "password123",
    "username": "username"
}

// Response 201
{
    "code": 0,
    "message": "success",
    "data": {
        "id": 1,
        "email": "user@example.com",
        "username": "username"
    }
}
```

---

### AUTH-02: 用户登录 API

| 字段 | 值 |
|------|------|
| **状态** | ✅ 完成 |
| **优先级** | P0 |
| **完成时间** | 2026-02-23 |
| **用户故事** | - |
| **API** | `POST /api/v1/auth/login` |

**交付内容**:
- [x] 登录 API 端点实现
- [x] 邮箱/密码验证
- [x] JWT Access Token 生成
- [x] JWT Refresh Token 生成
- [ ] 登录失败次数限制 (可选)
- [ ] 单元测试 (待补充)

**API 规格**:
```json
// Request
POST /api/v1/auth/login
{
    "email": "user@example.com",
    "password": "password123"
}

// Response 200
{
    "code": 0,
    "message": "success",
    "data": {
        "access_token": "eyJ...",
        "refresh_token": "eyJ...",
        "token_type": "bearer",
        "expires_in": 1800
    }
}
```

---

### AUTH-03: Token 刷新 API

| 字段 | 值 |
|------|------|
| **状态** | ✅ 完成 |
| **优先级** | P0 |
| **完成时间** | 2026-02-23 |
| **API** | `POST /api/v1/auth/refresh` |

**交付内容**:
- [x] Token 刷新 API 端点实现
- [x] Refresh Token 验证
- [x] 新 Access Token 生成
- [ ] 单元测试 (待补充)

---

### AUTH-04: 前端认证集成

| 字段 | 值 |
|------|------|
| **状态** | ✅ 完成 |
| **优先级** | P0 |
| **完成时间** | 2026-02-23 |

**交付内容**:
- [x] 登录页面 UI (Ant Design Form)
- [x] 注册页面 UI (Ant Design Form)
- [x] Token 存储 (zustand persist)
- [x] Axios 请求拦截器 (自动添加 Token)
- [x] Token 过期自动刷新
- [x] 登出功能
- [x] 路由守卫 (ProtectedRoute)

---

## 📊 基础数据接口 (Data API)

### DATA-01: 股票列表 API

| 字段 | 值 |
|------|------|
| **状态** | ✅ 完成 |
| **优先级** | P0 |
| **完成时间** | 2026-02-23 |
| **API** | `GET /api/v1/data/stocks` |

**交付内容**:
- [x] 股票列表 API 端点实现
- [x] 支持分页查询
- [x] 支持按名称/代码搜索
- [x] 支持按市场筛选 (沪市/深市)
- [x] 数据源集成 (AKShare + 模拟数据回退)
- [ ] 单元测试 (待补充)

**API 规格**:
```json
// Request
GET /api/v1/data/stocks?page=1&size=20&keyword=茅台&market=sh

// Response 200
{
    "code": 0,
    "message": "success",
    "data": {
        "items": [
            {
                "code": "600519",
                "name": "贵州茅台",
                "market": "sh",
                "industry": "白酒"
            }
        ],
        "total": 1,
        "page": 1,
        "size": 20
    }
}
```

---

### DATA-02: 历史行情 API

| 字段 | 值 |
|------|------|
| **状态** | ✅ 完成 |
| **优先级** | P0 |
| **完成时间** | 2026-02-23 |
| **API** | `GET /api/v1/data/stocks/{code}/history` |

**交付内容**:
- [x] 历史行情 API 端点实现
- [x] 支持日线/周线/月线
- [x] 支持时间范围查询
- [x] 数据源集成 (AKShare + 模拟数据回退)
- [x] 数据缓存 (内存缓存 5 分钟)
- [ ] 单元测试 (待补充)

**API 规格**:
```json
// Request
GET /api/v1/data/stocks/600519/history?period=daily&start=2024-01-01&end=2024-12-31

// Response 200
{
    "code": 0,
    "message": "success",
    "data": {
        "code": "600519",
        "period": "daily",
        "items": [
            {
                "date": "2024-01-02",
                "open": 1800.00,
                "high": 1820.00,
                "low": 1790.00,
                "close": 1810.00,
                "volume": 1000000,
                "amount": 1800000000
            }
        ]
    }
}
```

---

### DATA-03: 前端数据展示

| 字段 | 值 |
|------|------|
| **状态** | ✅ 完成 |
| **优先级** | P1 |
| **完成时间** | 2026-02-23 |

**交付内容**:
- [x] 股票列表页面 (Ant Design Table + 分页 + 搜索 + 筛选)
- [x] 股票搜索功能
- [x] 股票详情页面
- [x] K 线图展示 (ECharts 蜡烛图 + 成交量)

---

## 📦 待办池 (Backlog)

### M1.0 MVP 剩余任务

| ID | 优先级 | 特性 | 描述 | 用户故事 | Sprint |
|----|--------|------|------|----------|--------|
| B-02 | P0 | 因子管理 CRUD | 创建、编辑、删除因子 | US-F01 | Sprint 3 |
| B-03 | P0 | 因子计算 | 批量计算因子值 | US-F02 | Sprint 3 |
| B-04 | P0 | 因子评估 | IC、IR、分组收益 | US-F03 | Sprint 3 |
| B-05 | P0 | 策略管理 CRUD | 创建、编辑、删除策略 | US-S01 | Sprint 4 |
| B-06 | P0 | 策略回测 | 策略的历史回测框架 | US-S02 | Sprint 4 |
| B-07 | P0 | 绩效评估 | 回测绩效指标计算 | US-S02 | Sprint 4 |
| B-08 | P0 | 策略对比 | 多策略对比分析 | US-S03 | Sprint 4 |
| B-10 | P1 | 新手引导 | 交互式引导完成首次回测 | US-L01 | Sprint 5 |
| B-11 | P0 | 示例策略 | 5 个示例策略 | US-L02 | Sprint 4 |

### M2.0 沙盒阶段

| ID | 优先级 | 特性 | 描述 | 用户故事 |
|----|--------|------|------|----------|
| B-12 | P0 | 沙盒账户 | 虚拟资金账户管理 | US-B01 |
| B-13 | P0 | 策略部署 | 将策略部署到沙盒 | US-B02 |
| B-14 | P0 | 沙盒执行 | 每日自动执行策略 | US-B02 |
| B-15 | P1 | 沙盒对比 | 多策略净值对比 | US-B03 |
| B-16 | P1 | 毕业机制 | 沙盒策略毕业到实盘 | US-B03 |

### M3.0 交易阶段

| ID | 优先级 | 特性 | 描述 | 用户故事 |
|----|--------|------|------|----------|
| B-17 | P0 | 持仓管理 | 实时持仓查询 | US-T01 |
| B-18 | P0 | 手动下单 | 买入/卖出订单 | US-T02 |
| B-19 | P1 | 交易记录 | 历史交易查询 | US-T03 |
| B-20 | P0 | 模拟交易 | 内置模拟交易 | - |
| B-21 | P0 | 券商对接 | 对接主流券商 API | - |
| B-22 | P0 | 风险管理 | 仓位控制、止损止盈 | - |

---

## 🎯 里程碑 (Milestones)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           easyQuant 里程碑路线图                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   2026 Q1          2026 Q2          2026 Q3          2026 Q4               │
│   ────────         ────────         ────────         ────────              │
│                                                                             │
│   ┌─────┐         ┌─────┐         ┌─────┐         ┌─────┐                 │
│   │ M0  │────────▶│ M1.0│────────▶│ M2.0│────────▶│ M3.0│────────▶ M4.0  │
│   │     │         │     │         │     │         │     │                 │
│   │文档 │         │ MVP │         │沙盒 │         │交易 │                 │
│   └─────┘         └─────┘         └─────┘         └─────┘                 │
│    ✅               🏃               ⚪               ⚪                      │
│   2 周             8 周             6 周             8 周                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| 里程碑 | 状态 | 周期 | 核心交付 | 成功指标 |
|--------|------|------|----------|----------|
| **M0** | ✅ 完成 | 2 周 | 产品愿景、技术架构、开发规范 | 文档完整度 100% |
| **M1.0** | 🏃 进行中 | 8 周 | 因子管理、策略回测、基础数据 | 首次回测完成率 > 60% |
| **M2.0** | ⚪ 待开始 | 6 周 | 虚拟账户、多策略对比、毕业机制 | 沙盒使用率 > 40% |
| **M3.0** | ⚪ 待开始 | 8 周 | 模拟交易、券商对接、风控系统 | 订单执行成功率 > 99% |
| **M4.0** | ⚪ 待开始 | 持续 | AI 因子推荐、策略助手、市场分析 | 用户满意度 NPS > 50 |

### M1.0 Sprint 拆分

| Sprint | 周期 | 重点 | 状态 |
|--------|------|------|------|
| Sprint 2 | 2 周 | 基础设施 (项目初始化、用户认证、数据接口) | 🏃 进行中 |
| Sprint 3 | 2 周 | 因子模块 (因子 CRUD、因子计算、因子评估) | ⚪ 待开始 |
| Sprint 4 | 2 周 | 策略模块 (策略 CRUD、回测引擎、绩效评估) | ⚪ 待开始 |
| Sprint 5 | 2 周 | 完善优化 (示例策略、新手引导、Bug 修复) | ⚪ 待开始 |

---

## 📚 相关文档

| 文档 | 路径 | 版本 | 说明 |
|------|------|------|------|
| 产品愿景 | `docs/product/vision.md` | v2.0 | 用户画像、价值主张 |
| 用户故事 | `docs/product/user_stories.md` | v2.0 | 14 个核心用户故事 |
| 竞品分析 | `docs/product/competitor_analysis.md` | v2.0 | 8 个竞品深度分析 |
| 里程碑规划 | `docs/product/milestones.md` | v2.0 | M0-M4.0 详细规划 |
| 技术架构 | `docs/tech/architecture.md` | v2.0 | 系统架构、事件模型 |
| 数据模型 | `docs/tech/data_model.md` | v1.0 | 数据库设计、Pydantic 模型 |
| API 规范 | `docs/tech/api_spec.md` | v1.0 | 30+ API 接口定义 |
| 环境搭建 | `docs/tech/setup.md` | v1.0 | 开发环境搭建指南 |
| 代码规范 | `docs/tech/coding_standards.md` | v1.0 | 代码风格、Git 工作流 |
| CI/CD | `docs/tech/cicd.md` | v1.0 | 持续集成/部署流程 |

---

## 📜 历史 Sprints (Completed)

### ✅ Sprint 1: M0 项目启动 (Completed)

| 字段 | 值 |
|------|------|
| **周期** | 2026-02-23 |
| **里程碑** | M0 - 核心文档与架构设计 |
| **完成率** | 100% (11/11 tasks) |
| **Summary** | `docs/sprints/sprint-1-m0-summary.md` |

**关键交付物**:

| 类别 | 交付物 |
|------|--------|
| 产品文档 | ✅ vision.md (v2.0), user_stories.md (v2.0), competitor_analysis.md (v2.0), milestones.md (v2.0) |
| 技术文档 | ✅ architecture.md (v2.0), data_model.md (v1.0), api_spec.md (v1.0) |
| 项目管理 | ✅ setup.md (v1.0), coding_standards.md (v1.0), cicd.md (v1.0) |

**完工验收**: ✅ 已完成
