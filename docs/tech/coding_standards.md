# easyQuant 代码规范与 Git 工作流

**版本历史**:
- v1.0 | 2026-02-23 | @AI | 初始版本

---

## 1. 概述

本文档定义 easyQuant 项目的代码规范和 Git 工作流，确保团队代码风格一致、协作高效。

### 1.1 目标

- 统一代码风格，提高可读性
- 规范 Git 工作流，减少冲突
- 自动化代码质量检查

---

## 2. Python 代码规范

### 2.1 风格指南

遵循 [PEP 8](https://peps.python.org/pep-0008/) 风格指南，使用以下工具自动格式化：

| 工具 | 用途 | 配置文件 |
|------|------|----------|
| **Black** | 代码格式化 | `pyproject.toml` |
| **isort** | import 排序 | `pyproject.toml` |
| **Ruff** | 代码检查 | `pyproject.toml` |
| **mypy** | 类型检查 | `pyproject.toml` |

### 2.2 pyproject.toml 配置

```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
exclude = '''
/(
    \.git
    | \.venv
    | __pycache__
    | migrations
)/
'''

[tool.isort]
profile = "black"
line_length = 88
skip = [".venv", "migrations"]
known_first_party = ["app"]

[tool.ruff]
line-length = 88
target-version = "py311"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
]
exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "migrations",
]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
ignore_missing_imports = true
exclude = ["migrations", ".venv"]
```

### 2.3 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | snake_case | `factor_service.py` |
| 类 | PascalCase | `FactorService` |
| 函数 | snake_case | `calculate_factor()` |
| 变量 | snake_case | `factor_value` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| 私有成员 | _前缀 | `_internal_method()` |

### 2.4 类型注解

所有函数必须有类型注解：

```python
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class FactorCreate(BaseModel):
    name: str
    formula: str
    category: str

async def create_factor(
    factor_data: FactorCreate,
    user_id: int,
    created_at: Optional[datetime] = None,
) -> Factor:
    """创建因子"""
    ...
```

### 2.5 文档字符串

使用 Google 风格的 docstring：

```python
def calculate_ic(
    factor_values: pd.Series,
    returns: pd.Series,
    method: str = "spearman",
) -> float:
    """计算因子 IC 值

    Args:
        factor_values: 因子值序列
        returns: 收益率序列
        method: 相关系数计算方法，支持 "spearman" 或 "pearson"

    Returns:
        IC 值（-1 到 1 之间）

    Raises:
        ValueError: 当输入序列长度不一致时

    Example:
        >>> ic = calculate_ic(factor_values, returns)
        >>> print(f"IC: {ic:.4f}")
    """
    ...
```

---

## 3. TypeScript 代码规范

### 3.1 风格指南

使用 ESLint + Prettier 进行代码检查和格式化。

### 3.2 ESLint 配置

`.eslintrc.cjs`:

```javascript
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
    'plugin:prettier/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/explicit-function-return-type': 'warn',
    'no-console': ['warn', { allow: ['warn', 'error'] }],
  },
};
```

### 3.3 Prettier 配置

`.prettierrc`:

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false
}
```

### 3.4 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件（组件） | PascalCase | `FactorList.tsx` |
| 文件（工具） | camelCase | `apiClient.ts` |
| 组件 | PascalCase | `FactorCard` |
| 函数 | camelCase | `calculateReturn()` |
| 变量 | camelCase | `factorValue` |
| 常量 | UPPER_SNAKE_CASE | `API_BASE_URL` |
| 接口/类型 | PascalCase | `FactorResponse` |

### 3.5 组件结构

```typescript
import { useState, useEffect } from 'react';
import type { Factor } from '@/types';
import { factorApi } from '@/api';

interface FactorListProps {
  userId: number;
  onSelect?: (factor: Factor) => void;
}

export function FactorList({ userId, onSelect }: FactorListProps): JSX.Element {
  const [factors, setFactors] = useState<Factor[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFactors = async (): Promise<void> => {
      try {
        const data = await factorApi.list(userId);
        setFactors(data);
      } finally {
        setLoading(false);
      }
    };
    fetchFactors();
  }, [userId]);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="factor-list">
      {factors.map((factor) => (
        <FactorCard key={factor.id} factor={factor} onClick={() => onSelect?.(factor)} />
      ))}
    </div>
  );
}
```

---

## 4. Git 工作流

### 4.1 分支策略

采用 **Git Flow** 简化版：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Git 分支策略                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   main ─────●─────────────────●─────────────────●─────────────────●────▶   │
│              │                 ↑                 ↑                 ↑        │
│              │                 │                 │                 │        │
│   develop ───●───●───●───●────●───●───●───●────●───●───●───●────●────▶   │
│                  │       ↑        │       ↑        │       ↑                │
│                  │       │        │       │        │       │                │
│   feature/xxx ───●───●───┘        │       │        │       │                │
│                                   │       │        │       │                │
│   feature/yyy ────────────────────●───●───┘        │       │                │
│                                                    │       │                │
│   hotfix/zzz ──────────────────────────────────────●───────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| 分支 | 用途 | 命名规范 | 生命周期 |
|------|------|----------|----------|
| `main` | 生产环境代码 | - | 永久 |
| `develop` | 开发集成分支 | - | 永久 |
| `feature/*` | 新功能开发 | `feature/factor-crud` | 临时 |
| `bugfix/*` | Bug 修复 | `bugfix/login-error` | 临时 |
| `hotfix/*` | 紧急修复 | `hotfix/security-patch` | 临时 |
| `release/*` | 发布准备 | `release/v1.0.0` | 临时 |

### 4.2 分支命名规范

```
<type>/<issue-id>-<short-description>
```

示例：
- `feature/123-factor-crud`
- `bugfix/456-login-timeout`
- `hotfix/789-sql-injection`

### 4.3 Commit Message 规范

采用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(factor): add factor calculation` |
| `fix` | Bug 修复 | `fix(auth): fix token refresh issue` |
| `docs` | 文档更新 | `docs: update README` |
| `style` | 代码格式 | `style: format with black` |
| `refactor` | 重构 | `refactor(api): simplify error handling` |
| `perf` | 性能优化 | `perf(backtest): optimize loop` |
| `test` | 测试 | `test(factor): add unit tests` |
| `chore` | 构建/工具 | `chore: update dependencies` |
| `ci` | CI 配置 | `ci: add GitHub Actions` |

#### Scope 范围

| Scope | 说明 |
|-------|------|
| `auth` | 认证模块 |
| `factor` | 因子模块 |
| `strategy` | 策略模块 |
| `backtest` | 回测模块 |
| `trade` | 交易模块 |
| `api` | API 层 |
| `ui` | 前端 UI |
| `db` | 数据库 |

#### 示例

```
feat(factor): add IC calculation for factor evaluation

- Implement Spearman correlation for IC
- Add IC time series visualization
- Support multiple factor comparison

Closes #123
```

### 4.4 工作流程

#### 4.4.1 开发新功能

```bash
git checkout develop
git pull origin develop
git checkout -b feature/123-factor-crud

git add .
git commit -m "feat(factor): add factor CRUD API"

git push origin feature/123-factor-crud
```

#### 4.4.2 创建 Pull Request

1. 在 GitHub 上创建 PR
2. 填写 PR 模板
3. 指定 Reviewer
4. 等待 CI 通过
5. 获得 Approval 后合并

#### 4.4.3 合并策略

| 场景 | 合并方式 | 说明 |
|------|----------|------|
| feature → develop | Squash and merge | 压缩为单个 commit |
| develop → main | Merge commit | 保留完整历史 |
| hotfix → main | Merge commit | 保留完整历史 |

---

## 5. Pull Request 规范

### 5.1 PR 模板

创建 `.github/pull_request_template.md`：

```markdown
## 📝 Description

<!-- 简要描述这个 PR 做了什么 -->

## 🔗 Related Issues

<!-- 关联的 Issue，如 Closes #123 -->

## 📋 Type of Change

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Refactoring (no functional changes)
- [ ] 🧪 Test update

## 🧪 How Has This Been Tested?

<!-- 描述你是如何测试这些改动的 -->

- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## 📸 Screenshots (if applicable)

<!-- 如果有 UI 改动，请附上截图 -->

## ✅ Checklist

- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

### 5.2 Code Review 规范

#### Reviewer 职责

- 检查代码逻辑正确性
- 检查代码风格一致性
- 检查测试覆盖率
- 检查文档完整性
- 提供建设性反馈

#### Review 评论规范

| 前缀 | 含义 | 是否阻塞 |
|------|------|----------|
| `[blocking]` | 必须修改 | 是 |
| `[suggestion]` | 建议修改 | 否 |
| `[question]` | 疑问 | 否 |
| `[nit]` | 小问题 | 否 |
| `[praise]` | 表扬 | 否 |

---

## 6. Pre-commit Hooks

### 6.1 配置文件

创建 `.pre-commit-config.yaml`：

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.2.1
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic
          - types-redis

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.[jt]sx?$
        types: [file]
        additional_dependencies:
          - eslint@8.56.0
          - eslint-config-prettier@9.1.0
          - eslint-plugin-prettier@5.1.3
          - eslint-plugin-react-hooks@4.6.0
          - eslint-plugin-react-refresh@0.4.5
          - '@typescript-eslint/eslint-plugin@6.21.0'
          - '@typescript-eslint/parser@6.21.0'
          - prettier@3.2.5

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.14.1
    hooks:
      - id: commitizen
        stages: [commit-msg]
```

### 6.2 安装和使用

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
pre-commit run --all-files
```

---

## 7. 代码质量检查命令

### 7.1 后端

```bash
cd backend
source .venv/bin/activate

black .
isort .
ruff check . --fix
mypy .
pytest --cov=app --cov-report=html
```

### 7.2 前端

```bash
cd frontend

npm run lint
npm run lint:fix
npm run type-check
npm run test
npm run test:coverage
```

---

## 8. 目录结构规范

### 8.1 后端目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   ├── deps.py             # 依赖注入
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── factors.py
│   │       └── strategies.py
│   ├── core/                   # 核心模块
│   │   ├── __init__.py
│   │   ├── security.py         # 安全相关
│   │   └── exceptions.py       # 自定义异常
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── factor.py
│   │   └── strategy.py
│   ├── schemas/                # Pydantic Schema
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── factor.py
│   │   └── strategy.py
│   ├── services/               # 业务逻辑
│   │   ├── __init__.py
│   │   ├── factor_service.py
│   │   └── strategy_service.py
│   ├── repositories/           # 数据访问
│   │   ├── __init__.py
│   │   ├── factor_repo.py
│   │   └── strategy_repo.py
│   └── engine/                 # 回测引擎
│       ├── __init__.py
│       ├── backtest.py
│       └── events.py
├── tests/                      # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── migrations/                 # 数据库迁移
├── scripts/                    # 脚本
├── .env.example
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

### 8.2 前端目录结构

```
frontend/
├── src/
│   ├── main.tsx                # 应用入口
│   ├── App.tsx                 # 根组件
│   ├── api/                    # API 客户端
│   │   ├── index.ts
│   │   ├── client.ts
│   │   ├── auth.ts
│   │   └── factors.ts
│   ├── components/             # 通用组件
│   │   ├── ui/                 # 基础 UI 组件
│   │   └── common/             # 业务通用组件
│   ├── features/               # 功能模块
│   │   ├── auth/
│   │   ├── factors/
│   │   └── strategies/
│   ├── hooks/                  # 自定义 Hooks
│   ├── layouts/                # 布局组件
│   ├── pages/                  # 页面组件
│   ├── stores/                 # 状态管理
│   ├── types/                  # TypeScript 类型
│   ├── utils/                  # 工具函数
│   └── styles/                 # 全局样式
├── public/                     # 静态资源
├── tests/                      # 测试
├── .env.example
├── .eslintrc.cjs
├── .prettierrc
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## 9. 附录

### 9.1 常用命令速查

| 命令 | 说明 |
|------|------|
| `git checkout -b feature/xxx` | 创建功能分支 |
| `git commit -m "feat: xxx"` | 提交代码 |
| `git push origin feature/xxx` | 推送分支 |
| `git pull origin develop` | 拉取最新代码 |
| `git rebase develop` | 变基到 develop |
| `pre-commit run --all-files` | 运行所有检查 |

### 9.2 相关文档

- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
