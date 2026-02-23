# easyQuant API 设计规范

**版本历史**:
- v1.0 | 2026-02-23 | @AI | 初稿

---

## 0. 设计原则

### 0.1 核心原则

| 原则 | 说明 |
|------|------|
| **RESTful** | 遵循 REST 架构风格，资源导向设计 |
| **一致性** | 统一的命名、响应格式、错误处理 |
| **版本化** | 支持 API 版本管理，平滑升级 |
| **安全性** | JWT 认证、HTTPS、输入校验 |
| **可观测** | 请求追踪、日志记录、性能监控 |

### 0.2 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| **框架** | FastAPI | 异步支持、自动文档、类型安全 |
| **序列化** | Pydantic v2 | 高性能、类型校验 |
| **认证** | JWT (PyJWT) | 无状态、可扩展 |
| **文档** | OpenAPI 3.0 | 自动生成、Swagger UI |

---

## 1. URL 设计规范

### 1.1 基础结构

```
https://{host}/api/{version}/{resource}/{id}/{sub-resource}
```

**示例**:
```
GET  https://api.easyquant.com/api/v1/factors
GET  https://api.easyquant.com/api/v1/factors/123
GET  https://api.easyquant.com/api/v1/strategies/456/backtests
POST https://api.easyquant.com/api/v1/strategies/456/backtests
```

### 1.2 命名规范

| 规则 | 示例 | 说明 |
|------|------|------|
| 资源名使用复数 | `/factors`, `/strategies` | 表示资源集合 |
| 使用 kebab-case | `/factor-values`, `/backtest-results` | URL 友好 |
| 避免动词 | ❌ `/getFactors` ✅ `/factors` | 用 HTTP 方法表示动作 |
| 层级不超过 3 层 | `/strategies/{id}/backtests` | 保持简洁 |

### 1.3 HTTP 方法语义

| 方法 | 语义 | 幂等性 | 示例 |
|------|------|--------|------|
| `GET` | 查询资源 | ✅ | `GET /factors` |
| `POST` | 创建资源 | ❌ | `POST /factors` |
| `PUT` | 全量更新 | ✅ | `PUT /factors/123` |
| `PATCH` | 部分更新 | ✅ | `PATCH /factors/123` |
| `DELETE` | 删除资源 | ✅ | `DELETE /factors/123` |

---

## 2. 版本管理

### 2.1 版本策略

采用 **URL 路径版本** 方式：

```
/api/v1/factors
/api/v2/factors
```

**版本演进规则**:
- **Major (v1 → v2)**: 不兼容变更（删除字段、修改语义）
- **Minor**: 兼容变更（新增字段、新增接口），无需升版本号
- **Deprecation**: 旧版本保留至少 6 个月，通过 Header 提示

### 2.2 版本兼容性

```python
from fastapi import Header, HTTPException

async def check_api_version(
    x_api_version: str = Header(default="v1", alias="X-API-Version")
):
    supported_versions = ["v1", "v2"]
    if x_api_version not in supported_versions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported API version: {x_api_version}"
        )
    return x_api_version
```

### 2.3 废弃通知

响应 Header 中添加废弃警告：

```
Deprecation: true
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Link: </api/v2/factors>; rel="successor-version"
```

---

## 3. 请求规范

### 3.1 请求 Header

| Header | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `Authorization` | ✅ | JWT Token | `Bearer eyJhbGciOiJIUzI1NiIs...` |
| `Content-Type` | ✅ | 请求体格式 | `application/json` |
| `Accept` | ❌ | 期望响应格式 | `application/json` |
| `X-Request-ID` | ❌ | 请求追踪 ID | `req-abc123` |
| `X-API-Version` | ❌ | API 版本 | `v1` |

### 3.2 查询参数

#### 分页

```
GET /factors?page=1&page_size=20
GET /factors?offset=0&limit=20
```

**分页参数**:
| 参数 | 类型 | 默认值 | 最大值 | 说明 |
|------|------|--------|--------|------|
| `page` | int | 1 | - | 页码（从 1 开始） |
| `page_size` | int | 20 | 100 | 每页数量 |
| `offset` | int | 0 | - | 偏移量 |
| `limit` | int | 20 | 100 | 限制数量 |

#### 排序

```
GET /factors?sort=created_at&order=desc
GET /factors?sort=-created_at,name
```

**排序参数**:
| 参数 | 说明 | 示例 |
|------|------|------|
| `sort` | 排序字段 | `created_at`, `-created_at` (降序) |
| `order` | 排序方向 | `asc`, `desc` |

#### 过滤

```
GET /factors?category=momentum&status=active
GET /factors?created_at_gte=2024-01-01&created_at_lte=2024-12-31
```

**过滤操作符**:
| 后缀 | 操作 | 示例 |
|------|------|------|
| (无) | 等于 | `status=active` |
| `_ne` | 不等于 | `status_ne=draft` |
| `_gt` | 大于 | `ic_mean_gt=0.05` |
| `_gte` | 大于等于 | `created_at_gte=2024-01-01` |
| `_lt` | 小于 | `ic_mean_lt=0.1` |
| `_lte` | 小于等于 | `created_at_lte=2024-12-31` |
| `_in` | 包含 | `category_in=momentum,value` |
| `_like` | 模糊匹配 | `name_like=动量` |

#### 字段选择

```
GET /factors?fields=id,name,category
GET /factors?exclude=formula,parameters
```

### 3.3 请求体规范

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID

class FactorCreateRequest(BaseModel):
    """创建因子请求"""
    name: str = Field(..., min_length=1, max_length=100, description="因子名称")
    code: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-z][a-z0-9_]*$', description="因子代码")
    category: str = Field(..., description="因子分类")
    description: Optional[str] = Field(None, max_length=500, description="因子描述")
    formula: str = Field(..., description="因子计算公式")
    parameters: dict = Field(default_factory=dict, description="因子参数")

class FactorUpdateRequest(BaseModel):
    """更新因子请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    formula: Optional[str] = None
    parameters: Optional[dict] = None
    status: Optional[str] = None

class BacktestCreateRequest(BaseModel):
    """创建回测请求"""
    strategy_id: UUID = Field(..., description="策略 ID")
    start_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="开始日期")
    end_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="结束日期")
    initial_capital: float = Field(default=1000000, gt=0, description="初始资金")
    benchmark: str = Field(default="000300.SH", description="基准指数")
    commission_rate: float = Field(default=0.0003, ge=0, le=0.01, description="手续费率")
    slippage: float = Field(default=0.001, ge=0, le=0.1, description="滑点")
```

---

## 4. 响应规范

### 4.1 统一响应格式

```python
from pydantic import BaseModel
from typing import TypeVar, Generic, Optional, List
from datetime import datetime

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """统一响应格式"""
    success: bool = True
    code: int = 0
    message: str = "OK"
    data: Optional[T] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None

class PaginatedData(BaseModel, Generic[T]):
    """分页数据"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

class PaginatedResponse(APIResponse[PaginatedData[T]], Generic[T]):
    """分页响应"""
    pass
```

### 4.2 成功响应示例

#### 单个资源

```json
{
  "success": true,
  "code": 0,
  "message": "OK",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "动量因子",
    "code": "momentum_20d",
    "category": "momentum",
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req-abc123"
}
```

#### 列表资源

```json
{
  "success": true,
  "code": 0,
  "message": "OK",
  "data": {
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "动量因子",
        "code": "momentum_20d"
      },
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "价值因子",
        "code": "pe_ratio"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req-abc123"
}
```

#### 创建成功

```json
{
  "success": true,
  "code": 0,
  "message": "Created",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req-abc123"
}
```

### 4.3 HTTP 状态码

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| `200` | OK | 查询、更新成功 |
| `201` | Created | 创建成功 |
| `204` | No Content | 删除成功 |
| `400` | Bad Request | 请求参数错误 |
| `401` | Unauthorized | 未认证 |
| `403` | Forbidden | 无权限 |
| `404` | Not Found | 资源不存在 |
| `409` | Conflict | 资源冲突（如重复创建） |
| `422` | Unprocessable Entity | 业务校验失败 |
| `429` | Too Many Requests | 请求频率超限 |
| `500` | Internal Server Error | 服务器内部错误 |
| `503` | Service Unavailable | 服务不可用 |

---

## 5. 错误码规范

### 5.1 错误码结构

```
XXYYYY

XX   - 模块代码 (00-99)
YYYY - 错误序号 (0000-9999)
```

### 5.2 模块代码分配

| 模块代码 | 模块名称 | 说明 |
|----------|----------|------|
| `00` | 通用 | 通用错误 |
| `10` | 认证 | 认证授权相关 |
| `20` | 用户 | 用户管理 |
| `30` | 因子 | 因子管理 |
| `40` | 策略 | 策略管理 |
| `50` | 回测 | 回测服务 |
| `60` | 交易 | 交易执行 |
| `70` | 数据 | 数据服务 |

### 5.3 错误码定义

```python
from enum import IntEnum

class ErrorCode(IntEnum):
    # 通用错误 (00xxxx)
    SUCCESS = 0
    UNKNOWN_ERROR = 1
    INVALID_PARAMETER = 2
    RESOURCE_NOT_FOUND = 3
    RESOURCE_ALREADY_EXISTS = 4
    OPERATION_NOT_ALLOWED = 5
    RATE_LIMIT_EXCEEDED = 6
    SERVICE_UNAVAILABLE = 7
    
    # 认证错误 (10xxxx)
    AUTH_TOKEN_MISSING = 100001
    AUTH_TOKEN_INVALID = 100002
    AUTH_TOKEN_EXPIRED = 100003
    AUTH_PERMISSION_DENIED = 100004
    AUTH_USER_DISABLED = 100005
    
    # 用户错误 (20xxxx)
    USER_NOT_FOUND = 200001
    USER_ALREADY_EXISTS = 200002
    USER_PASSWORD_INCORRECT = 200003
    USER_EMAIL_INVALID = 200004
    
    # 因子错误 (30xxxx)
    FACTOR_NOT_FOUND = 300001
    FACTOR_CODE_EXISTS = 300002
    FACTOR_FORMULA_INVALID = 300003
    FACTOR_COMPUTE_FAILED = 300004
    FACTOR_STATUS_INVALID = 300005
    
    # 策略错误 (40xxxx)
    STRATEGY_NOT_FOUND = 400001
    STRATEGY_CODE_EXISTS = 400002
    STRATEGY_CONFIG_INVALID = 400003
    STRATEGY_STATUS_INVALID = 400004
    STRATEGY_FACTOR_NOT_FOUND = 400005
    
    # 回测错误 (50xxxx)
    BACKTEST_NOT_FOUND = 500001
    BACKTEST_ALREADY_RUNNING = 500002
    BACKTEST_DATE_INVALID = 500003
    BACKTEST_DATA_INSUFFICIENT = 500004
    BACKTEST_FAILED = 500005
    
    # 交易错误 (60xxxx)
    ORDER_NOT_FOUND = 600001
    ORDER_QUANTITY_INVALID = 600002
    ORDER_PRICE_INVALID = 600003
    ORDER_INSUFFICIENT_FUNDS = 600004
    ORDER_POSITION_NOT_FOUND = 600005
    ORDER_ALREADY_FILLED = 600006
    
    # 数据错误 (70xxxx)
    DATA_NOT_FOUND = 700001
    DATA_SOURCE_UNAVAILABLE = 700002
    DATA_FORMAT_INVALID = 700003
    DATA_RANGE_INVALID = 700004
```

### 5.4 错误响应格式

```python
class ErrorDetail(BaseModel):
    """错误详情"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None

class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    code: int
    message: str
    errors: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None
```

**错误响应示例**:

```json
{
  "success": false,
  "code": 300002,
  "message": "Factor code already exists",
  "errors": [
    {
      "field": "code",
      "message": "Factor with code 'momentum_20d' already exists",
      "code": "DUPLICATE_CODE"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req-abc123"
}
```

**参数校验错误**:

```json
{
  "success": false,
  "code": 2,
  "message": "Invalid parameters",
  "errors": [
    {
      "field": "name",
      "message": "String should have at least 1 character",
      "code": "string_too_short"
    },
    {
      "field": "start_date",
      "message": "String should match pattern '^\\d{4}-\\d{2}-\\d{2}$'",
      "code": "string_pattern_mismatch"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req-abc123"
}
```

---

## 6. 认证与授权

### 6.1 JWT 认证

```python
from datetime import datetime, timedelta
from typing import Optional
import jwt
from pydantic import BaseModel

class TokenPayload(BaseModel):
    """Token 载荷"""
    sub: str  # user_id
    exp: datetime
    iat: datetime
    jti: str  # token_id
    role: str

class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int  # 秒
    refresh_token: Optional[str] = None

def create_access_token(
    user_id: str,
    role: str,
    expires_delta: timedelta = timedelta(hours=24)
) -> str:
    payload = TokenPayload(
        sub=user_id,
        exp=datetime.utcnow() + expires_delta,
        iat=datetime.utcnow(),
        jti=str(uuid4()),
        role=role
    )
    return jwt.encode(payload.dict(), SECRET_KEY, algorithm="HS256")
```

### 6.2 认证流程

```
POST /api/v1/auth/login
{
  "username": "user@example.com",
  "password": "password123"
}

Response:
{
  "success": true,
  "code": 0,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

### 6.3 权限控制

```python
from enum import Enum
from functools import wraps

class Permission(str, Enum):
    FACTOR_READ = "factor:read"
    FACTOR_WRITE = "factor:write"
    STRATEGY_READ = "strategy:read"
    STRATEGY_WRITE = "strategy:write"
    BACKTEST_RUN = "backtest:run"
    TRADE_EXECUTE = "trade:execute"
    ADMIN = "admin:*"

ROLE_PERMISSIONS = {
    "guest": [Permission.FACTOR_READ, Permission.STRATEGY_READ],
    "user": [
        Permission.FACTOR_READ, Permission.FACTOR_WRITE,
        Permission.STRATEGY_READ, Permission.STRATEGY_WRITE,
        Permission.BACKTEST_RUN
    ],
    "admin": [Permission.ADMIN]
}

def require_permission(permission: Permission):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=None, **kwargs):
            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=403,
                    detail="Permission denied"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

---

## 7. API 端点定义

### 7.1 认证模块

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/v1/auth/register` | 用户注册 |
| `POST` | `/api/v1/auth/login` | 用户登录 |
| `POST` | `/api/v1/auth/logout` | 用户登出 |
| `POST` | `/api/v1/auth/refresh` | 刷新 Token |
| `POST` | `/api/v1/auth/password/reset` | 重置密码 |
| `GET` | `/api/v1/auth/me` | 获取当前用户信息 |

### 7.2 因子模块

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/v1/factors` | 获取因子列表 |
| `POST` | `/api/v1/factors` | 创建因子 |
| `GET` | `/api/v1/factors/{id}` | 获取因子详情 |
| `PUT` | `/api/v1/factors/{id}` | 更新因子 |
| `DELETE` | `/api/v1/factors/{id}` | 删除因子 |
| `POST` | `/api/v1/factors/{id}/compute` | 计算因子值 |
| `GET` | `/api/v1/factors/{id}/values` | 获取因子值 |
| `GET` | `/api/v1/factors/{id}/evaluation` | 获取因子评估 |

### 7.3 策略模块

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/v1/strategies` | 获取策略列表 |
| `POST` | `/api/v1/strategies` | 创建策略 |
| `GET` | `/api/v1/strategies/{id}` | 获取策略详情 |
| `PUT` | `/api/v1/strategies/{id}` | 更新策略 |
| `DELETE` | `/api/v1/strategies/{id}` | 删除策略 |
| `POST` | `/api/v1/strategies/{id}/clone` | 克隆策略 |
| `GET` | `/api/v1/strategies/{id}/backtests` | 获取策略回测列表 |

### 7.4 回测模块

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/v1/backtests` | 获取回测列表 |
| `POST` | `/api/v1/backtests` | 创建回测 |
| `GET` | `/api/v1/backtests/{id}` | 获取回测详情 |
| `DELETE` | `/api/v1/backtests/{id}` | 删除回测 |
| `POST` | `/api/v1/backtests/{id}/cancel` | 取消回测 |
| `GET` | `/api/v1/backtests/{id}/results` | 获取回测结果 |
| `GET` | `/api/v1/backtests/{id}/trades` | 获取回测交易记录 |
| `GET` | `/api/v1/backtests/{id}/positions` | 获取回测持仓记录 |
| `GET` | `/api/v1/backtests/{id}/equity-curve` | 获取权益曲线 |

### 7.5 交易模块

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/v1/orders` | 获取订单列表 |
| `POST` | `/api/v1/orders` | 创建订单 |
| `GET` | `/api/v1/orders/{id}` | 获取订单详情 |
| `DELETE` | `/api/v1/orders/{id}` | 取消订单 |
| `GET` | `/api/v1/positions` | 获取持仓列表 |
| `GET` | `/api/v1/positions/{symbol}` | 获取单个持仓 |
| `GET` | `/api/v1/account` | 获取账户信息 |

### 7.6 数据模块

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/v1/market-data/stocks` | 获取股票列表 |
| `GET` | `/api/v1/market-data/stocks/{symbol}` | 获取股票信息 |
| `GET` | `/api/v1/market-data/ohlcv` | 获取 K 线数据 |
| `GET` | `/api/v1/market-data/quotes` | 获取实时行情 |

---

## 8. 限流与熔断

### 8.1 限流策略

```python
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# 全局限流
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # 默认: 100 请求/分钟
    pass

# 端点级限流
@router.post("/backtests")
@limiter.limit("10/minute")  # 回测创建: 10 次/分钟
async def create_backtest(request: Request, ...):
    pass

@router.get("/market-data/ohlcv")
@limiter.limit("60/minute")  # 行情查询: 60 次/分钟
async def get_ohlcv(request: Request, ...):
    pass
```

### 8.2 限流响应

```json
{
  "success": false,
  "code": 6,
  "message": "Rate limit exceeded",
  "errors": [
    {
      "message": "Too many requests. Limit: 10/minute. Retry after 30 seconds."
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req-abc123"
}
```

**响应 Header**:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705315830
Retry-After: 30
```

---

## 9. 性能预估

### 9.1 性能指标

| 端点类型 | 目标延迟 (P95) | 预期 QPS |
|----------|----------------|----------|
| 认证 | < 100ms | 50 |
| 因子 CRUD | < 50ms | 100 |
| 策略 CRUD | < 50ms | 100 |
| 回测创建 | < 200ms | 10 |
| 行情查询 | < 100ms | 100 |
| 因子值查询 | < 200ms | 50 |

### 9.2 容量规划

- **并发连接**: 1000
- **请求队列**: 10000
- **超时时间**: 30s
- **最大请求体**: 10MB

---

## 10. 里程碑对齐

| 里程碑 | API 重点 |
|--------|----------|
| **M0** | API 规范定义、错误码设计 |
| **M1.0 MVP** | 认证、因子、策略、回测基础 API |
| **M2.0 沙盒** | 沙盒 API、多策略对比 API |
| **M3.0 交易** | 订单、持仓、账户 API |
| **M4.0 智能化** | AI 推荐 API、WebSocket 实时推送 |
