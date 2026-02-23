# easyQuant CI/CD 流程设计

**版本历史**:
- v1.0 | 2026-02-23 | @AI | 初始版本

---

## 1. 概述

本文档定义 easyQuant 项目的持续集成（CI）和持续部署（CD）流程，确保代码质量和自动化部署。

### 1.1 目标

- 自动化代码质量检查
- 自动化测试执行
- 自动化构建和部署
- 快速反馈和问题发现

### 1.2 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| CI/CD 平台 | GitHub Actions | 与 GitHub 深度集成 |
| 容器化 | Docker | 统一运行环境 |
| 容器编排 | Docker Compose | 本地开发和测试 |
| 镜像仓库 | GitHub Container Registry | 镜像存储 |

---

## 2. CI/CD 流程总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CI/CD 流程图                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│   │  Push   │───▶│  Lint   │───▶│  Test   │───▶│  Build  │                 │
│   │         │    │         │    │         │    │         │                 │
│   └─────────┘    └─────────┘    └─────────┘    └─────────┘                 │
│        │              │              │              │                       │
│        │              ▼              ▼              ▼                       │
│        │         ┌─────────┐   ┌─────────┐   ┌─────────┐                   │
│        │         │ Black   │   │  Unit   │   │ Docker  │                   │
│        │         │ Ruff    │   │  Tests  │   │  Image  │                   │
│        │         │ ESLint  │   │         │   │         │                   │
│        │         │ mypy    │   │  Integ  │   │         │                   │
│        │         └─────────┘   │  Tests  │   └─────────┘                   │
│        │                       └─────────┘         │                       │
│        │                                           │                       │
│        ▼                                           ▼                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                         Deploy Pipeline                              │ │
│   │  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐          │ │
│   │  │ develop │───▶│ Staging │───▶│  main   │───▶│  Prod   │          │ │
│   │  │  merge  │    │  Deploy │    │  merge  │    │  Deploy │          │ │
│   │  └─────────┘    └─────────┘    └─────────┘    └─────────┘          │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. GitHub Actions 配置

### 3.1 CI 工作流

创建 `.github/workflows/ci.yml`：

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "18"

jobs:
  lint-backend:
    name: Lint Backend
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('backend/requirements*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run Black
        run: black --check .

      - name: Run isort
        run: isort --check-only .

      - name: Run Ruff
        run: ruff check .

      - name: Run mypy
        run: mypy .

  lint-frontend:
    name: Lint Frontend
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run ESLint
        run: npm run lint

      - name: Run TypeScript check
        run: npm run type-check

  test-backend:
    name: Test Backend
    runs-on: ubuntu-latest
    needs: lint-backend
    defaults:
      run:
        working-directory: backend

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: easyquant_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('backend/requirements*.txt') }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/easyquant_test
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET_KEY: test-secret-key
        run: |
          pytest --cov=app --cov-report=xml --cov-report=html -v

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./backend/coverage.xml
          flags: backend
          fail_ci_if_error: false

  test-frontend:
    name: Test Frontend
    runs-on: ubuntu-latest
    needs: lint-frontend
    defaults:
      run:
        working-directory: frontend

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm run test:coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./frontend/coverage/lcov.info
          flags: frontend
          fail_ci_if_error: false

  build:
    name: Build Docker Images
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]
    if: github.event_name == 'push'

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/backend:${{ github.sha }}
            ghcr.io/${{ github.repository }}/backend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/frontend:${{ github.sha }}
            ghcr.io/${{ github.repository }}/frontend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### 3.2 CD 工作流

创建 `.github/workflows/deploy.yml`：

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

env:
  PYTHON_VERSION: "3.11"

jobs:
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop' || github.event.inputs.environment == 'staging'
    environment:
      name: staging
      url: https://staging.easyquant.io

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Staging
        run: |
          echo "Deploying to staging environment..."
          # Add deployment commands here

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.event.inputs.environment == 'production'
    environment:
      name: production
      url: https://easyquant.io

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Production
        run: |
          echo "Deploying to production environment..."
          # Add deployment commands here
```

---

## 4. Docker 配置

### 4.1 后端 Dockerfile

创建 `backend/Dockerfile`：

```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.2 前端 Dockerfile

创建 `frontend/Dockerfile`：

```dockerfile
FROM node:18-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 4.3 前端 Nginx 配置

创建 `frontend/nginx.conf`：

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
}
```

### 4.4 Docker Compose

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/easyquant
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-dev-secret-key}
      - APP_ENV=development
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend

  db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=easyquant
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

### 4.5 开发环境 Docker Compose

创建 `docker-compose.dev.yml`：

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=easyquant
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

---

## 5. 环境管理

### 5.1 环境分类

| 环境 | 用途 | 分支 | URL |
|------|------|------|-----|
| **development** | 本地开发 | feature/* | localhost |
| **staging** | 测试验证 | develop | staging.easyquant.io |
| **production** | 生产环境 | main | easyquant.io |

### 5.2 环境变量管理

#### GitHub Secrets 配置

| Secret | 环境 | 说明 |
|--------|------|------|
| `DATABASE_URL` | staging/production | 数据库连接字符串 |
| `REDIS_URL` | staging/production | Redis 连接字符串 |
| `JWT_SECRET_KEY` | staging/production | JWT 密钥 |
| `DEPLOY_KEY` | staging/production | 部署密钥 |

#### 环境变量文件

```
.env.example      # 模板文件（提交到 Git）
.env              # 本地开发（不提交）
.env.staging      # Staging 环境
.env.production   # 生产环境
```

---

## 6. 部署策略

### 6.1 蓝绿部署

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           蓝绿部署流程                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Load Balancer                                                             │
│        │                                                                    │
│        ▼                                                                    │
│   ┌─────────┐                                                              │
│   │ Router  │                                                              │
│   └────┬────┘                                                              │
│        │                                                                    │
│   ┌────┴────┐                                                              │
│   │         │                                                              │
│   ▼         ▼                                                              │
│ ┌─────┐   ┌─────┐                                                          │
│ │Blue │   │Green│                                                          │
│ │ v1  │   │ v2  │  ◄── 新版本部署到 Green                                  │
│ │ ✓   │   │     │                                                          │
│ └─────┘   └─────┘                                                          │
│                                                                             │
│   步骤：                                                                    │
│   1. 部署新版本到 Green                                                     │
│   2. 测试 Green 环境                                                        │
│   3. 切换流量到 Green                                                       │
│   4. 保留 Blue 用于回滚                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 滚动更新

```yaml
# Kubernetes 滚动更新配置示例
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

---

## 7. 监控和告警

### 7.1 健康检查

后端健康检查端点：

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
    }

@app.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database not ready")
```

### 7.2 CI/CD 通知

创建 `.github/workflows/notify.yml`：

```yaml
name: Notify

on:
  workflow_run:
    workflows: ["CI", "Deploy"]
    types: [completed]

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Send notification
        if: ${{ github.event.workflow_run.conclusion == 'failure' }}
        run: |
          echo "Workflow ${{ github.event.workflow_run.name }} failed!"
          # Add Slack/Email notification here
```

---

## 8. 安全最佳实践

### 8.1 密钥管理

- 使用 GitHub Secrets 存储敏感信息
- 定期轮换密钥
- 不在日志中打印敏感信息

### 8.2 镜像安全

```yaml
# 在 CI 中添加镜像扫描
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'ghcr.io/${{ github.repository }}/backend:${{ github.sha }}'
    format: 'sarif'
    output: 'trivy-results.sarif'
```

### 8.3 依赖安全

```yaml
# 定期检查依赖漏洞
- name: Check for vulnerabilities
  run: |
    pip install safety
    safety check -r requirements.txt
```

---

## 9. 常用命令

### 9.1 本地开发

```bash
docker-compose -f docker-compose.dev.yml up -d

cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

cd frontend && npm run dev
```

### 9.2 构建镜像

```bash
docker build -t easyquant-backend ./backend
docker build -t easyquant-frontend ./frontend
```

### 9.3 运行测试

```bash
cd backend && pytest -v --cov=app
cd frontend && npm run test
```

---

## 10. 附录

### 10.1 CI/CD 指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| CI 构建时间 | < 10 分钟 | 从 Push 到完成 |
| 测试覆盖率 | > 80% | 代码覆盖率 |
| 部署频率 | 每日 | 持续部署 |
| 部署成功率 | > 99% | 部署成功率 |
| MTTR | < 30 分钟 | 平均恢复时间 |

### 10.2 相关文档

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Docker 文档](https://docs.docker.com/)
- [Kubernetes 文档](https://kubernetes.io/docs/)
