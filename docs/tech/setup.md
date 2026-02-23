# easyQuant 开发环境搭建指南

**版本历史**:
- v1.0 | 2026-02-23 | @AI | 初始版本

---

## 1. 概述

本文档提供 easyQuant 项目的开发环境搭建指南，帮助新开发者在 **30 分钟内** 完成环境配置并运行项目。

### 1.1 目标读者

- 新加入项目的开发者
- 需要在新机器上配置环境的团队成员

### 1.2 预计时间

| 步骤 | 预计时间 |
|------|----------|
| 系统依赖安装 | 10 分钟 |
| 项目克隆与配置 | 5 分钟 |
| 数据库初始化 | 5 分钟 |
| 验证运行 | 5 分钟 |
| **总计** | **25 分钟** |

---

## 2. 系统要求

### 2.1 硬件要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2 核 | 4 核+ |
| 内存 | 8 GB | 16 GB+ |
| 磁盘 | 20 GB | 50 GB+ (SSD) |

### 2.2 软件要求

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| **Python** | 3.11+ | 后端运行时 |
| **Node.js** | 18+ | 前端运行时 |
| **PostgreSQL** | 15+ | 主数据库 |
| **Redis** | 7+ | 缓存和消息队列 |
| **Git** | 2.30+ | 版本控制 |
| **Docker** | 24+ | 容器化部署（可选） |

### 2.3 操作系统支持

| 操作系统 | 支持状态 | 说明 |
|----------|----------|------|
| macOS 13+ | ✅ 完全支持 | 推荐开发环境 |
| Ubuntu 22.04+ | ✅ 完全支持 | 推荐生产环境 |
| Windows 11 + WSL2 | ✅ 支持 | 需要 WSL2 |
| Windows 11 原生 | ⚠️ 部分支持 | 可能有兼容性问题 |

---

## 3. 环境安装

### 3.1 macOS 安装指南

#### 3.1.1 安装 Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 3.1.2 安装系统依赖

```bash
brew install python@3.11 node@18 postgresql@15 redis git
brew services start postgresql@15
brew services start redis
```

#### 3.1.3 验证安装

```bash
python3 --version    # Python 3.11.x
node --version       # v18.x.x
psql --version       # psql (PostgreSQL) 15.x
redis-cli --version  # redis-cli 7.x.x
git --version        # git version 2.x.x
```

---

### 3.2 Ubuntu/Debian 安装指南

#### 3.2.1 更新系统

```bash
sudo apt update && sudo apt upgrade -y
```

#### 3.2.2 安装 Python 3.11

```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install python3.11 python3.11-venv python3.11-dev -y
```

#### 3.2.3 安装 Node.js 18

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

#### 3.2.4 安装 PostgreSQL 15

```bash
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
sudo apt install postgresql-15 postgresql-contrib-15 -y
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 3.2.5 安装 Redis

```bash
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### 3.2.6 验证安装

```bash
python3.11 --version
node --version
psql --version
redis-cli --version
```

---

### 3.3 Windows (WSL2) 安装指南

#### 3.3.1 安装 WSL2

```powershell
wsl --install -d Ubuntu-22.04
```

#### 3.3.2 进入 WSL2 环境

```powershell
wsl
```

#### 3.3.3 按照 Ubuntu 指南安装

进入 WSL2 后，按照 [3.2 Ubuntu/Debian 安装指南](#32-ubuntudebian-安装指南) 进行安装。

---

## 4. 项目配置

### 4.1 克隆项目

```bash
git clone https://github.com/your-org/easyQuant.git
cd easyQuant
```

### 4.2 后端配置

#### 4.2.1 创建虚拟环境

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
```

#### 4.2.2 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

#### 4.2.3 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# 数据库配置
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/easyquant
REDIS_URL=redis://localhost:6379/0

# JWT 配置
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
APP_ENV=development
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

# 日志配置
LOG_LEVEL=DEBUG
```

### 4.3 前端配置

#### 4.3.1 安装依赖

```bash
cd frontend
npm install
```

#### 4.3.2 配置环境变量

```bash
cp .env.example .env.local
```

编辑 `.env.local` 文件：

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=easyQuant
```

---

## 5. 数据库初始化

### 5.1 创建数据库

#### macOS

```bash
createdb easyquant
```

#### Ubuntu/Linux

```bash
sudo -u postgres createdb easyquant
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
```

### 5.2 运行数据库迁移

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

### 5.3 初始化种子数据（可选）

```bash
python scripts/seed_data.py
```

---

## 6. 运行项目

### 6.1 启动后端服务

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 http://localhost:8000 启动。

API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 6.2 启动前端服务

```bash
cd frontend
npm run dev
```

前端服务将在 http://localhost:5173 启动。

### 6.3 使用 Docker Compose（可选）

如果你更喜欢使用 Docker，可以一键启动所有服务：

```bash
docker-compose up -d
```

服务端口：
- 前端: http://localhost:3000
- 后端: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

---

## 7. 开发工具配置

### 7.1 VS Code 推荐配置

#### 7.1.1 推荐扩展

创建 `.vscode/extensions.json`：

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "ms-python.isort",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-azuretools.vscode-docker",
    "eamodio.gitlens",
    "usernamehw.errorlens"
  ]
}
```

#### 7.1.2 工作区设置

创建 `.vscode/settings.json`：

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/bin/python",
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "editor.rulers": [88, 120],
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true
}
```

### 7.2 PyCharm 配置

1. 打开项目：`File > Open > 选择 easyQuant 目录`
2. 配置 Python 解释器：`Settings > Project > Python Interpreter > Add > Existing Environment > 选择 .venv/bin/python`
3. 启用 Black 格式化：`Settings > Tools > Black > Enable`
4. 配置数据库：`Database > + > PostgreSQL > 填写连接信息`

---

## 8. 常见问题排查

### 8.1 Python 版本问题

**问题**: `python3` 命令指向错误版本

**解决方案**:

```bash
# macOS
brew link python@3.11 --force

# Ubuntu
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
sudo update-alternatives --config python3
```

### 8.2 PostgreSQL 连接问题

**问题**: `psql: error: connection refused`

**解决方案**:

```bash
# 检查服务状态
# macOS
brew services list | grep postgresql

# Ubuntu
sudo systemctl status postgresql

# 启动服务
# macOS
brew services start postgresql@15

# Ubuntu
sudo systemctl start postgresql
```

### 8.3 端口占用问题

**问题**: `Address already in use`

**解决方案**:

```bash
# 查找占用端口的进程
lsof -i :8000

# 终止进程
kill -9 <PID>
```

### 8.4 依赖安装失败

**问题**: `pip install` 失败

**解决方案**:

```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 8.5 Node.js 依赖问题

**问题**: `npm install` 失败

**解决方案**:

```bash
# 清除缓存
npm cache clean --force

# 删除 node_modules 重新安装
rm -rf node_modules package-lock.json
npm install

# 使用国内镜像
npm config set registry https://registry.npmmirror.com
npm install
```

### 8.6 数据库迁移失败

**问题**: `alembic upgrade head` 失败

**解决方案**:

```bash
# 检查数据库连接
psql -U postgres -d easyquant -c "SELECT 1;"

# 重置迁移（开发环境）
alembic downgrade base
alembic upgrade head

# 查看迁移历史
alembic history
```

---

## 9. 验证清单

完成环境搭建后，请验证以下项目：

- [ ] Python 版本 >= 3.11
- [ ] Node.js 版本 >= 18
- [ ] PostgreSQL 服务运行中
- [ ] Redis 服务运行中
- [ ] 后端服务启动成功 (http://localhost:8000/docs)
- [ ] 前端服务启动成功 (http://localhost:5173)
- [ ] 数据库迁移成功
- [ ] API 接口可访问

---

## 10. 下一步

环境搭建完成后，建议阅读以下文档：

1. [代码规范与 Git 工作流](./coding_standards.md) - 了解代码风格和提交规范
2. [技术架构设计](./architecture.md) - 了解系统架构
3. [API 设计规范](./api_spec.md) - 了解 API 接口规范
4. [数据模型设计](./data_model.md) - 了解数据库设计

---

## 11. 获取帮助

如果遇到问题，可以通过以下方式获取帮助：

1. 查看项目 Wiki
2. 在 GitHub Issues 中搜索或提问
3. 联系团队成员
