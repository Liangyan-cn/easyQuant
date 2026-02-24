# easyQuant

**让个人投资者拥有专业级的量化投资能力**

easyQuant 是一个面向个人投资者的**一站式量化投资管理平台**，帮助用户管理因子、设计策略、沙盒验证和执行交易。

## 🎯 愿景

降低量化投资门槛，让不懂编程的用户也能使用专业的量化工具。

## ✨ 核心功能

| 模块 | 描述 | 状态 |
|------|------|------|
| **因子管理** | 构建、测试和优化投资因子 | ✅ 已完成 |
| **策略管理** | 设计、回测和部署量化策略 | ✅ 已完成 |
| **沙盒测试** | 安全环境中多策略实测评估 | ✅ 已完成 |
| **交易管理** | 执行交易、监控持仓和风险 | 🚧 规划中 |

## 🗺️ 里程碑

- **M1.0 MVP** - 核心基础功能（因子/策略管理、回测、绩效评估）
- **M2.0 沙盒系统** - 虚拟资金账户、多策略实测、对比分析
- **M3.0 交易执行** - 模拟交易、持仓管理、券商 API 对接
- **M4.0 智能化升级** - AI 因子推荐、策略助手、市场分析

详见 [milestones.md](docs/product/milestones.md)

## 📁 项目结构

```
easyQuant/
├── docs/                    # 文档目录
│   └── product/             # 产品文档
│       ├── backlog.md       # 产品待办事项
│       └── milestones.md    # 里程碑规划
├── scripts/                 # 工具脚本
│   ├── init_workspace.py    # 工作区初始化
│   ├── analyze_docs.py      # 文档分析
│   └── generate_index.py    # 索引生成
├── skills/                  # Agent 技能
│   ├── skill-creator/       # 技能创建器
│   ├── spec-generator/      # PRD 生成器
│   ├── sprint-manager/      # Sprint 管理器
│   ├── task-executor/       # 任务执行器
│   └── tech-design-generator/ # 技术设计生成器
├── kanban.md                # 项目看板 (SSOT)
├── LICENSE                  # MIT 许可证
└── README.md                # 项目说明
```

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Git

### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等

# 初始化数据库
./venv/bin/alembic upgrade head

# 启动开发服务器
./venv/bin/uvicorn app.main:app --reload --port 8000
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:3000 即可使用系统。

### 文档工具

```bash
# 分析文档状态
python scripts/analyze_docs.py

# 生成文档报告
python scripts/analyze_docs.py --report

# 生成文档索引
python scripts/generate_index.py
```

## 🔧 运维脚本

### 批量计算因子值

当需要为所有因子预计算最近一年的数据时，可以使用批量计算脚本：

```bash
cd backend

# 执行批量计算（已有数据的因子会自动跳过）
PYTHONPATH=. ./venv/bin/python app/scripts/batch_calculate_factors.py
```

**输出示例：**
```
批量计算因子值: 2025-02-24 ~ 2026-02-24
============================================================

[1] 动量因子 (20日) (momentum_20d)
  ✅ 已有数据: 110,207 条

[2] 动量因子 (60日) (momentum_60d)
  🔄 开始计算...
  ✅ 计算完成: 90,276 条数据

[5] ROE (roe)
  ⏭️  跳过: 暂不支持计算 (需要财务数据)

============================================================
批量计算完成!
```

**支持计算的因子类型：**
- 动量因子 (momentum_20d, momentum_60d)
- 波动率 (volatility_20d)
- 换手率 (turnover_rate)
- 市值对数 (log_market_cap)

**暂不支持的因子（需要财务数据）：**
- 市盈率倒数 (ep_ratio)
- 市净率倒数 (bp_ratio)
- ROE (roe)
- 营收增长率 (revenue_growth)

### 数据缓存管理

预加载股票历史数据到本地缓存，减少 API 调用：

```bash
cd backend

# 查看缓存状态
PYTHONPATH=. ./venv/bin/python app/scripts/cache_loader.py status

# 查看可用股票池
PYTHONPATH=. ./venv/bin/python app/scripts/cache_loader.py list

# 预加载整个股票池
PYTHONPATH=. ./venv/bin/python app/scripts/cache_loader.py preload              # 默认 hs300
PYTHONPATH=. ./venv/bin/python app/scripts/cache_loader.py preload --pool zz500 # 中证500

# 预加载单只股票
PYTHONPATH=. ./venv/bin/python app/scripts/cache_loader.py preload --stock 000001

# 增量更新
PYTHONPATH=. ./venv/bin/python app/scripts/cache_loader.py update --pool hs300
```

## 🛠️ Agent Skills

本项目集成了一套 Agent 技能，用于辅助项目管理和开发：

| 技能 | 用途 |
|------|------|
| `sprint-manager` | Sprint 生命周期管理（启动/健康检查/结束） |
| `spec-generator` | 生成标准化 PRD 文档 |
| `tech-design-generator` | 生成技术设计文档 |
| `task-executor` | 任务拆解和执行指导 |
| `skill-creator` | 创建新的 Agent 技能 |

## 📋 项目管理

- **看板**: [kanban.md](kanban.md) - 项目进度的单一事实来源 (SSOT)
- **待办**: [backlog.md](docs/product/backlog.md) - 产品待办事项池
- **里程碑**: [milestones.md](docs/product/milestones.md) - 长期规划

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat`: 新功能
- `fix`: 修复 Bug
- `docs`: 文档变更
- `refactor`: 代码重构
- `test`: 测试用例
- `chore`: 构建/工具变更

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件
