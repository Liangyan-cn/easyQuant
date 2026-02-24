# 股票池管理设计文档

**日期**: 2026-02-24  
**Sprint**: Sprint 11  
**状态**: 已批准

---

## 1. 概述

### 1.1 背景

easyQuant 量化投资平台需要股票池管理功能，用于：
- 管理用户关注的股票集合
- 为回测和策略执行提供股票范围
- 支持数据缓存的范围界定

### 1.2 设计决策

- **数据模型**: 单表设计，通过 `pool_type` 区分系统池和用户池
- **权限模型**: 系统池全局可见，用户池仅创建者可见
- **嵌套支持**: 不支持，每个池独立
- **预置池**: 沪深300、中证500

---

## 2. 数据模型

### 2.1 StockPool 表

```sql
CREATE TABLE stock_pools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    pool_type VARCHAR(20) NOT NULL DEFAULT 'user',
    user_id INTEGER REFERENCES users(id),
    description TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_stock_pools_name ON stock_pools(name);
CREATE INDEX ix_stock_pools_code ON stock_pools(code);
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, auto | 主键 |
| name | String(100) | NOT NULL, INDEX | 股票池名称 |
| code | String(50) | UNIQUE, NOT NULL | 股票池代码 |
| pool_type | String(20) | NOT NULL | system/user |
| user_id | Integer | FK, NULL | 创建者ID |
| description | Text | NULL | 描述 |
| created_at | DateTime | NOT NULL | 创建时间 |
| updated_at | DateTime | NOT NULL | 更新时间 |

### 2.2 StockPoolItem 表

```sql
CREATE TABLE stock_pool_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pool_id INTEGER NOT NULL REFERENCES stock_pools(id) ON DELETE CASCADE,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100),
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pool_id, stock_code)
);

CREATE INDEX ix_stock_pool_items_pool_id ON stock_pool_items(pool_id);
CREATE INDEX ix_stock_pool_items_stock_code ON stock_pool_items(stock_code);
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, auto | 主键 |
| pool_id | Integer | FK, NOT NULL | 所属股票池 |
| stock_code | String(20) | NOT NULL, INDEX | 股票代码 |
| stock_name | String(100) | NULL | 股票名称 |
| added_at | DateTime | NOT NULL | 添加时间 |

---

## 3. API 设计

### 3.1 端点列表

| 端点 | 方法 | 描述 | 权限 |
|------|------|------|------|
| `/api/v1/stock-pools` | GET | 获取股票池列表 | 系统池 + 自己的用户池 |
| `/api/v1/stock-pools` | POST | 创建股票池 | 登录用户 |
| `/api/v1/stock-pools/{id}` | GET | 获取股票池详情 | 系统池或自己的 |
| `/api/v1/stock-pools/{id}` | PUT | 更新股票池 | 仅自己的用户池 |
| `/api/v1/stock-pools/{id}` | DELETE | 删除股票池 | 仅自己的用户池 |
| `/api/v1/stock-pools/{id}/stocks` | POST | 添加股票 | 仅自己的用户池 |
| `/api/v1/stock-pools/{id}/stocks/{code}` | DELETE | 删除股票 | 仅自己的用户池 |
| `/api/v1/stock-pools/{id}/import-index` | POST | 从指数导入 | 仅自己的用户池 |

### 3.2 请求/响应示例

#### 创建股票池

```http
POST /api/v1/stock-pools
Content-Type: application/json

{
    "name": "我的自选股",
    "code": "my_watchlist",
    "description": "个人关注的股票"
}
```

#### 获取股票池列表

```http
GET /api/v1/stock-pools?page=1&size=20
```

```json
{
    "items": [
        {
            "id": 1,
            "name": "沪深300",
            "code": "hs300",
            "pool_type": "system",
            "description": "沪深300指数成分股",
            "stock_count": 300,
            "created_at": "2026-02-24T00:00:00",
            "updated_at": "2026-02-24T00:00:00"
        }
    ],
    "total": 3,
    "page": 1,
    "size": 20
}
```

#### 添加股票到池

```http
POST /api/v1/stock-pools/1/stocks
Content-Type: application/json

{
    "stock_code": "600519",
    "stock_name": "贵州茅台"
}
```

#### 从指数导入

```http
POST /api/v1/stock-pools/1/import-index
Content-Type: application/json

{
    "index_code": "000300"
}
```

---

## 4. Schema 设计

### 4.1 枚举类型

```python
class StockPoolType(str, Enum):
    SYSTEM = "system"
    USER = "user"
```

### 4.2 请求 Schema

```python
class StockPoolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50, pattern="^[a-z0-9_]+$")
    description: Optional[str] = None

class StockPoolUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

class StockPoolItemCreate(BaseModel):
    stock_code: str = Field(..., min_length=1, max_length=20)
    stock_name: Optional[str] = None

class ImportIndexRequest(BaseModel):
    index_code: str = Field(..., description="指数代码，如 000300")
```

### 4.3 响应 Schema

```python
class StockPoolItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    stock_code: str
    stock_name: Optional[str]
    added_at: datetime

class StockPoolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str
    pool_type: StockPoolType
    description: Optional[str]
    stock_count: int
    created_at: datetime
    updated_at: datetime

class StockPoolDetailResponse(StockPoolResponse):
    items: List[StockPoolItemResponse]

class StockPoolListResponse(BaseModel):
    items: List[StockPoolResponse]
    total: int
    page: int
    size: int
```

---

## 5. 权限逻辑

### 5.1 可见性规则

```python
def get_visible_pools_query(user_id: int):
    """获取用户可见的股票池查询条件"""
    return or_(
        StockPool.pool_type == StockPoolType.SYSTEM,
        StockPool.user_id == user_id
    )
```

### 5.2 修改权限

```python
def can_modify_pool(pool: StockPool, user_id: int) -> bool:
    """检查用户是否可以修改股票池"""
    return pool.pool_type == StockPoolType.USER and pool.user_id == user_id
```

---

## 6. 系统预置股票池

### 6.1 预置池列表

| 代码 | 名称 | 指数代码 | AKShare 接口 |
|------|------|----------|--------------|
| `hs300` | 沪深300 | 000300 | `ak.index_stock_cons("000300")` |
| `zz500` | 中证500 | 000905 | `ak.index_stock_cons("000905")` |

### 6.2 初始化逻辑

```python
async def init_system_pools(db: AsyncSession):
    """初始化系统预置股票池"""
    system_pools = [
        {"code": "hs300", "name": "沪深300", "description": "沪深300指数成分股"},
        {"code": "zz500", "name": "中证500", "description": "中证500指数成分股"},
    ]
    
    for pool_data in system_pools:
        existing = await repo.get_by_code(pool_data["code"])
        if not existing:
            pool = await repo.create_system_pool(pool_data)
            await import_index_stocks(pool.id, pool_data["code"])
```

---

## 7. 错误处理

| 场景 | HTTP 状态码 | 错误码 | 错误信息 |
|------|-------------|--------|----------|
| 股票池不存在 | 404 | POOL_NOT_FOUND | Stock pool not found |
| 无权限修改系统池 | 403 | CANNOT_MODIFY_SYSTEM | Cannot modify system pool |
| 无权限访问他人池 | 403 | ACCESS_DENIED | Access denied |
| 股票池代码重复 | 409 | CODE_EXISTS | Stock pool code already exists |
| 股票已在池中 | 409 | STOCK_EXISTS | Stock already in pool |

---

## 8. 文件结构

```
backend/app/
├── models/
│   └── stock_pool.py          # 数据模型
├── schemas/
│   └── stock_pool.py          # Pydantic Schema
├── repositories/
│   └── stock_pool_repo.py     # 数据访问层
├── services/
│   └── stock_pool_service.py  # 业务逻辑层
└── api/v1/endpoints/
    └── stock_pool.py          # API 端点
```

---

## 参考资料

- [AKShare 指数成分股接口](https://akshare.readthedocs.io/zh_CN/latest/data/index/index.html#id4)
- [现有 Factor 模型参考](../backend/app/models/factor.py)
