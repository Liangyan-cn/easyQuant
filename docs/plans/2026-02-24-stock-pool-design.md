# 股票池管理实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现股票池管理功能，支持系统预置池(沪深300/中证500)和用户自定义池

**Architecture:** 单表设计区分系统池和用户池，通过 Repository + Service + Endpoint 三层架构实现 CRUD 和权限控制

**Tech Stack:** Python, FastAPI, SQLAlchemy, Pydantic, AKShare

---

## 设计文档

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

## 9. 实施计划

---

### Task 1: 创建数据模型

**Files:**
- Create: `backend/app/models/stock_pool.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: 创建 stock_pool.py 模型文件**

```python
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base


class StockPoolType(str, Enum):
    SYSTEM = "system"
    USER = "user"


class StockPool(Base):
    __tablename__ = "stock_pools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    pool_type = Column(String(20), nullable=False, default=StockPoolType.USER.value)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("StockPoolItem", back_populates="pool", cascade="all, delete-orphan")
    owner = relationship("User", backref="stock_pools")


class StockPoolItem(Base):
    __tablename__ = "stock_pool_items"
    __table_args__ = (
        UniqueConstraint("pool_id", "stock_code", name="uix_pool_stock"),
    )

    id = Column(Integer, primary_key=True, index=True)
    pool_id = Column(Integer, ForeignKey("stock_pools.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(100), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)

    pool = relationship("StockPool", back_populates="items")
```

**Step 2: 更新 models/__init__.py 导出**

在 `__init__.py` 中添加:
```python
from app.models.stock_pool import StockPool, StockPoolItem, StockPoolType
```

并在 `__all__` 列表中添加: `"StockPool", "StockPoolItem", "StockPoolType"`

**Step 3: 验证语法**

Run: `cd backend && ./venv/bin/python -c "from app.models.stock_pool import *; print('OK')"`
Expected: OK

**Step 4: Commit**

```bash
git add backend/app/models/stock_pool.py backend/app/models/__init__.py
git commit -m "feat: add StockPool and StockPoolItem models"
```

---

### Task 2: 创建 Schema

**Files:**
- Create: `backend/app/schemas/stock_pool.py`

**Step 1: 创建 stock_pool.py Schema 文件**

```python
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StockPoolType(str, Enum):
    SYSTEM = "system"
    USER = "user"


class StockPoolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z0-9_]+$")
    description: Optional[str] = None


class StockPoolUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class StockPoolItemCreate(BaseModel):
    stock_code: str = Field(..., min_length=1, max_length=20)
    stock_name: Optional[str] = None


class ImportIndexRequest(BaseModel):
    index_code: str = Field(..., description="指数代码，如 000300")


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
    stock_count: int = 0
    created_at: datetime
    updated_at: datetime


class StockPoolDetailResponse(StockPoolResponse):
    items: List[StockPoolItemResponse] = []


class StockPoolListResponse(BaseModel):
    items: List[StockPoolResponse]
    total: int
    page: int
    size: int
```

**Step 2: 验证语法**

Run: `cd backend && ./venv/bin/python -c "from app.schemas.stock_pool import *; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add backend/app/schemas/stock_pool.py
git commit -m "feat: add StockPool schemas"
```

---

### Task 3: 创建 Repository

**Files:**
- Create: `backend/app/repositories/stock_pool_repo.py`

**Step 1: 创建 stock_pool_repo.py**

```python
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.stock_pool import StockPool, StockPoolItem, StockPoolType
from app.schemas.stock_pool import StockPoolCreate, StockPoolItemCreate, StockPoolUpdate


class StockPoolRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: StockPoolCreate, user_id: int) -> StockPool:
        pool = StockPool(
            name=data.name,
            code=data.code,
            description=data.description,
            pool_type=StockPoolType.USER.value,
            user_id=user_id,
        )
        self.db.add(pool)
        await self.db.commit()
        await self.db.refresh(pool)
        return pool

    async def create_system_pool(self, name: str, code: str, description: str) -> StockPool:
        pool = StockPool(
            name=name,
            code=code,
            description=description,
            pool_type=StockPoolType.SYSTEM.value,
            user_id=None,
        )
        self.db.add(pool)
        await self.db.commit()
        await self.db.refresh(pool)
        return pool

    async def get_by_id(self, pool_id: int) -> Optional[StockPool]:
        result = await self.db.execute(
            select(StockPool).options(selectinload(StockPool.items)).where(StockPool.id == pool_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[StockPool]:
        result = await self.db.execute(select(StockPool).where(StockPool.code == code))
        return result.scalar_one_or_none()

    async def get_list(
        self, user_id: int, page: int = 1, size: int = 20, pool_type: Optional[str] = None
    ) -> Tuple[List[StockPool], int]:
        base_query = select(StockPool).where(
            or_(StockPool.pool_type == StockPoolType.SYSTEM.value, StockPool.user_id == user_id)
        )
        if pool_type:
            base_query = base_query.where(StockPool.pool_type == pool_type)

        count_result = await self.db.execute(select(func.count()).select_from(base_query.subquery()))
        total = count_result.scalar() or 0

        result = await self.db.execute(
            base_query.order_by(StockPool.created_at.desc()).offset((page - 1) * size).limit(size)
        )
        pools = list(result.scalars().all())

        for pool in pools:
            item_count = await self.db.execute(
                select(func.count()).where(StockPoolItem.pool_id == pool.id)
            )
            pool.stock_count = item_count.scalar() or 0

        return pools, total

    async def update(self, pool_id: int, data: StockPoolUpdate) -> Optional[StockPool]:
        pool = await self.get_by_id(pool_id)
        if not pool:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(pool, key, value)
        pool.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(pool)
        return pool

    async def delete(self, pool_id: int) -> bool:
        pool = await self.get_by_id(pool_id)
        if not pool:
            return False
        await self.db.delete(pool)
        await self.db.commit()
        return True

    async def add_stock(self, pool_id: int, data: StockPoolItemCreate) -> StockPoolItem:
        item = StockPoolItem(
            pool_id=pool_id,
            stock_code=data.stock_code,
            stock_name=data.stock_name,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def add_stocks_bulk(self, pool_id: int, stocks: List[dict]) -> int:
        items = [
            StockPoolItem(pool_id=pool_id, stock_code=s["stock_code"], stock_name=s.get("stock_name"))
            for s in stocks
        ]
        self.db.add_all(items)
        await self.db.commit()
        return len(items)

    async def remove_stock(self, pool_id: int, stock_code: str) -> bool:
        result = await self.db.execute(
            select(StockPoolItem).where(
                StockPoolItem.pool_id == pool_id, StockPoolItem.stock_code == stock_code
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return False
        await self.db.delete(item)
        await self.db.commit()
        return True

    async def get_stock_item(self, pool_id: int, stock_code: str) -> Optional[StockPoolItem]:
        result = await self.db.execute(
            select(StockPoolItem).where(
                StockPoolItem.pool_id == pool_id, StockPoolItem.stock_code == stock_code
            )
        )
        return result.scalar_one_or_none()

    async def clear_stocks(self, pool_id: int) -> int:
        result = await self.db.execute(select(StockPoolItem).where(StockPoolItem.pool_id == pool_id))
        items = result.scalars().all()
        count = len(items)
        for item in items:
            await self.db.delete(item)
        await self.db.commit()
        return count
```

**Step 2: 验证语法**

Run: `cd backend && ./venv/bin/python -c "from app.repositories.stock_pool_repo import StockPoolRepository; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add backend/app/repositories/stock_pool_repo.py
git commit -m "feat: add StockPoolRepository"
```

---

### Task 4: 创建 Service

**Files:**
- Create: `backend/app/services/stock_pool_service.py`

**Step 1: 创建 stock_pool_service.py**

```python
import logging
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.models.stock_pool import StockPool, StockPoolType
from app.repositories.stock_pool_repo import StockPoolRepository
from app.schemas.stock_pool import (
    StockPoolCreate,
    StockPoolDetailResponse,
    StockPoolItemCreate,
    StockPoolItemResponse,
    StockPoolResponse,
    StockPoolUpdate,
)

logger = logging.getLogger(__name__)


class StockPoolService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = StockPoolRepository(db)

    async def create_pool(self, data: StockPoolCreate, user_id: int) -> StockPoolResponse:
        existing = await self.repo.get_by_code(data.code)
        if existing:
            raise ConflictException(f"Stock pool with code '{data.code}' already exists")
        pool = await self.repo.create(data, user_id)
        return self._to_response(pool)

    async def get_pool(self, pool_id: int, user_id: int) -> StockPoolDetailResponse:
        pool = await self.repo.get_by_id(pool_id)
        if not pool:
            raise NotFoundException("Stock pool not found")
        if not self._can_view(pool, user_id):
            raise ForbiddenException("Access denied")
        return self._to_detail_response(pool)

    async def get_pools(
        self, user_id: int, page: int = 1, size: int = 20, pool_type: Optional[str] = None
    ) -> Tuple[List[StockPoolResponse], int]:
        pools, total = await self.repo.get_list(user_id, page, size, pool_type)
        return [self._to_response(p) for p in pools], total

    async def update_pool(self, pool_id: int, data: StockPoolUpdate, user_id: int) -> StockPoolResponse:
        pool = await self.repo.get_by_id(pool_id)
        if not pool:
            raise NotFoundException("Stock pool not found")
        if not self._can_modify(pool, user_id):
            raise ForbiddenException("Cannot modify this stock pool")
        updated = await self.repo.update(pool_id, data)
        return self._to_response(updated)

    async def delete_pool(self, pool_id: int, user_id: int) -> bool:
        pool = await self.repo.get_by_id(pool_id)
        if not pool:
            raise NotFoundException("Stock pool not found")
        if not self._can_modify(pool, user_id):
            raise ForbiddenException("Cannot delete this stock pool")
        return await self.repo.delete(pool_id)

    async def add_stock(self, pool_id: int, data: StockPoolItemCreate, user_id: int) -> StockPoolItemResponse:
        pool = await self.repo.get_by_id(pool_id)
        if not pool:
            raise NotFoundException("Stock pool not found")
        if not self._can_modify(pool, user_id):
            raise ForbiddenException("Cannot modify this stock pool")
        existing = await self.repo.get_stock_item(pool_id, data.stock_code)
        if existing:
            raise ConflictException(f"Stock '{data.stock_code}' already in pool")
        item = await self.repo.add_stock(pool_id, data)
        return StockPoolItemResponse.model_validate(item)

    async def remove_stock(self, pool_id: int, stock_code: str, user_id: int) -> bool:
        pool = await self.repo.get_by_id(pool_id)
        if not pool:
            raise NotFoundException("Stock pool not found")
        if not self._can_modify(pool, user_id):
            raise ForbiddenException("Cannot modify this stock pool")
        return await self.repo.remove_stock(pool_id, stock_code)

    async def import_index(self, pool_id: int, index_code: str, user_id: int) -> int:
        pool = await self.repo.get_by_id(pool_id)
        if not pool:
            raise NotFoundException("Stock pool not found")
        if not self._can_modify(pool, user_id):
            raise ForbiddenException("Cannot modify this stock pool")

        stocks = self._fetch_index_stocks(index_code)
        if not stocks:
            raise NotFoundException(f"Index '{index_code}' not found or no stocks")

        await self.repo.clear_stocks(pool_id)
        count = await self.repo.add_stocks_bulk(pool_id, stocks)
        logger.info(f"Imported {count} stocks from index {index_code} to pool {pool_id}")
        return count

    def _fetch_index_stocks(self, index_code: str) -> List[dict]:
        try:
            import akshare as ak
            df = ak.index_stock_cons(symbol=index_code)
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    "stock_code": str(row.get("品种代码", row.get("constituent_code", ""))),
                    "stock_name": str(row.get("品种名称", row.get("constituent_name", ""))),
                })
            return stocks
        except ImportError:
            raise RuntimeError("AKShare not installed")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch index stocks: {e}")

    def _can_view(self, pool: StockPool, user_id: int) -> bool:
        return pool.pool_type == StockPoolType.SYSTEM.value or pool.user_id == user_id

    def _can_modify(self, pool: StockPool, user_id: int) -> bool:
        return pool.pool_type == StockPoolType.USER.value and pool.user_id == user_id

    def _to_response(self, pool: StockPool) -> StockPoolResponse:
        return StockPoolResponse(
            id=pool.id,
            name=pool.name,
            code=pool.code,
            pool_type=pool.pool_type,
            description=pool.description,
            stock_count=getattr(pool, "stock_count", len(pool.items) if pool.items else 0),
            created_at=pool.created_at,
            updated_at=pool.updated_at,
        )

    def _to_detail_response(self, pool: StockPool) -> StockPoolDetailResponse:
        return StockPoolDetailResponse(
            id=pool.id,
            name=pool.name,
            code=pool.code,
            pool_type=pool.pool_type,
            description=pool.description,
            stock_count=len(pool.items) if pool.items else 0,
            created_at=pool.created_at,
            updated_at=pool.updated_at,
            items=[StockPoolItemResponse.model_validate(item) for item in (pool.items or [])],
        )
```

**Step 2: 验证语法**

Run: `cd backend && ./venv/bin/python -c "from app.services.stock_pool_service import StockPoolService; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add backend/app/services/stock_pool_service.py
git commit -m "feat: add StockPoolService"
```

---

### Task 5: 创建 API 端点

**Files:**
- Create: `backend/app/api/v1/endpoints/stock_pool.py`
- Modify: `backend/app/api/v1/router.py`

**Step 1: 创建 stock_pool.py 端点文件**

```python
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.stock_pool import (
    ImportIndexRequest,
    StockPoolCreate,
    StockPoolDetailResponse,
    StockPoolItemCreate,
    StockPoolItemResponse,
    StockPoolListResponse,
    StockPoolResponse,
    StockPoolUpdate,
)
from app.services.stock_pool_service import StockPoolService

router = APIRouter(prefix="/stock-pools", tags=["stock-pools"])


@router.get("", response_model=StockPoolListResponse)
async def get_stock_pools(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    pool_type: Optional[str] = Query(None, description="Filter by pool type: system or user"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockPoolListResponse:
    service = StockPoolService(db)
    pools, total = await service.get_pools(current_user.id, page, size, pool_type)
    return StockPoolListResponse(items=pools, total=total, page=page, size=size)


@router.post("", response_model=StockPoolResponse)
async def create_stock_pool(
    data: StockPoolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockPoolResponse:
    service = StockPoolService(db)
    return await service.create_pool(data, current_user.id)


@router.get("/{pool_id}", response_model=StockPoolDetailResponse)
async def get_stock_pool(
    pool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockPoolDetailResponse:
    service = StockPoolService(db)
    return await service.get_pool(pool_id, current_user.id)


@router.put("/{pool_id}", response_model=StockPoolResponse)
async def update_stock_pool(
    pool_id: int,
    data: StockPoolUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockPoolResponse:
    service = StockPoolService(db)
    return await service.update_pool(pool_id, data, current_user.id)


@router.delete("/{pool_id}")
async def delete_stock_pool(
    pool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    service = StockPoolService(db)
    await service.delete_pool(pool_id, current_user.id)
    return {"message": "Stock pool deleted"}


@router.post("/{pool_id}/stocks", response_model=StockPoolItemResponse)
async def add_stock_to_pool(
    pool_id: int,
    data: StockPoolItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockPoolItemResponse:
    service = StockPoolService(db)
    return await service.add_stock(pool_id, data, current_user.id)


@router.delete("/{pool_id}/stocks/{stock_code}")
async def remove_stock_from_pool(
    pool_id: int,
    stock_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    service = StockPoolService(db)
    await service.remove_stock(pool_id, stock_code, current_user.id)
    return {"message": "Stock removed from pool"}


@router.post("/{pool_id}/import-index")
async def import_index_to_pool(
    pool_id: int,
    data: ImportIndexRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    service = StockPoolService(db)
    count = await service.import_index(pool_id, data.index_code, current_user.id)
    return {"message": f"Imported {count} stocks from index {data.index_code}"}
```

**Step 2: 更新 router.py 注册端点**

在 `backend/app/api/v1/router.py` 中添加:
```python
from app.api.v1.endpoints import stock_pool

api_router.include_router(stock_pool.router)
```

**Step 3: 验证语法**

Run: `cd backend && ./venv/bin/python -c "from app.api.v1.endpoints.stock_pool import router; print('OK')"`
Expected: OK

**Step 4: Commit**

```bash
git add backend/app/api/v1/endpoints/stock_pool.py backend/app/api/v1/router.py
git commit -m "feat: add stock pool API endpoints"
```

---

### Task 6: 创建系统池初始化脚本

**Files:**
- Create: `backend/app/services/stock_pool_init.py`
- Modify: `backend/app/main.py`

**Step 1: 创建初始化脚本**

```python
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock_pool import StockPoolType
from app.repositories.stock_pool_repo import StockPoolRepository

logger = logging.getLogger(__name__)

SYSTEM_POOLS = [
    {"code": "hs300", "name": "沪深300", "description": "沪深300指数成分股", "index_code": "000300"},
    {"code": "zz500", "name": "中证500", "description": "中证500指数成分股", "index_code": "000905"},
]


async def init_system_pools(db: AsyncSession) -> None:
    repo = StockPoolRepository(db)

    for pool_data in SYSTEM_POOLS:
        existing = await repo.get_by_code(pool_data["code"])
        if existing:
            logger.info(f"System pool '{pool_data['code']}' already exists, skipping")
            continue

        pool = await repo.create_system_pool(
            name=pool_data["name"],
            code=pool_data["code"],
            description=pool_data["description"],
        )
        logger.info(f"Created system pool: {pool_data['name']} (id={pool.id})")

        try:
            import akshare as ak
            df = ak.index_stock_cons(symbol=pool_data["index_code"])
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    "stock_code": str(row.get("品种代码", row.get("constituent_code", ""))),
                    "stock_name": str(row.get("品种名称", row.get("constituent_name", ""))),
                })
            if stocks:
                count = await repo.add_stocks_bulk(pool.id, stocks)
                logger.info(f"Imported {count} stocks to pool '{pool_data['code']}'")
        except ImportError:
            logger.warning("AKShare not installed, skipping stock import")
        except Exception as e:
            logger.error(f"Failed to import stocks for '{pool_data['code']}': {e}")
```

**Step 2: 在 main.py 中调用初始化**

在 `backend/app/main.py` 的 `lifespan` 函数中添加:
```python
from app.services.stock_pool_init import init_system_pools

# 在数据库初始化后调用
async with AsyncSessionLocal() as db:
    await init_system_pools(db)
```

**Step 3: 验证语法**

Run: `cd backend && ./venv/bin/python -c "from app.services.stock_pool_init import init_system_pools; print('OK')"`
Expected: OK

**Step 4: Commit**

```bash
git add backend/app/services/stock_pool_init.py backend/app/main.py
git commit -m "feat: add system pool initialization on startup"
```

---

### Task 7: 编写测试

**Files:**
- Create: `backend/tests/test_stock_pool.py`

**Step 1: 创建测试文件**

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestStockPoolCRUD:
    async def test_create_stock_pool(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/v1/stock-pools",
            json={"name": "测试池", "code": "test_pool", "description": "测试"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "测试池"
        assert data["code"] == "test_pool"
        assert data["pool_type"] == "user"

    async def test_get_stock_pools(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/v1/stock-pools", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_get_stock_pool_detail(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/api/v1/stock-pools",
            json={"name": "详情测试", "code": "detail_test"},
            headers=auth_headers,
        )
        pool_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/stock-pools/{pool_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pool_id
        assert "items" in data

    async def test_update_stock_pool(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/api/v1/stock-pools",
            json={"name": "更新测试", "code": "update_test"},
            headers=auth_headers,
        )
        pool_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/stock-pools/{pool_id}",
            json={"name": "更新后名称"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "更新后名称"

    async def test_delete_stock_pool(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/api/v1/stock-pools",
            json={"name": "删除测试", "code": "delete_test"},
            headers=auth_headers,
        )
        pool_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/stock-pools/{pool_id}", headers=auth_headers)
        assert response.status_code == 200


@pytest.mark.asyncio
class TestStockPoolItems:
    async def test_add_stock_to_pool(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/api/v1/stock-pools",
            json={"name": "股票测试", "code": "stock_test"},
            headers=auth_headers,
        )
        pool_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/stock-pools/{pool_id}/stocks",
            json={"stock_code": "600519", "stock_name": "贵州茅台"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["stock_code"] == "600519"

    async def test_remove_stock_from_pool(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/api/v1/stock-pools",
            json={"name": "移除测试", "code": "remove_test"},
            headers=auth_headers,
        )
        pool_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/stock-pools/{pool_id}/stocks",
            json={"stock_code": "600519"},
            headers=auth_headers,
        )

        response = await client.delete(
            f"/api/v1/stock-pools/{pool_id}/stocks/600519",
            headers=auth_headers,
        )
        assert response.status_code == 200


@pytest.mark.asyncio
class TestStockPoolPermissions:
    async def test_cannot_modify_system_pool(self, client: AsyncClient, auth_headers: dict):
        pools_resp = await client.get(
            "/api/v1/stock-pools?pool_type=system",
            headers=auth_headers,
        )
        if pools_resp.json()["total"] > 0:
            system_pool_id = pools_resp.json()["items"][0]["id"]
            response = await client.put(
                f"/api/v1/stock-pools/{system_pool_id}",
                json={"name": "尝试修改"},
                headers=auth_headers,
            )
            assert response.status_code == 403

    async def test_duplicate_code_rejected(self, client: AsyncClient, auth_headers: dict):
        await client.post(
            "/api/v1/stock-pools",
            json={"name": "重复测试1", "code": "dup_code"},
            headers=auth_headers,
        )
        response = await client.post(
            "/api/v1/stock-pools",
            json={"name": "重复测试2", "code": "dup_code"},
            headers=auth_headers,
        )
        assert response.status_code == 409
```

**Step 2: 运行测试**

Run: `cd backend && ./venv/bin/pytest tests/test_stock_pool.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add backend/tests/test_stock_pool.py
git commit -m "test: add stock pool tests"
```

---

### Task 8: 运行完整测试验证

**Step 1: 运行所有后端测试**

Run: `cd backend && ./venv/bin/pytest -v`
Expected: All tests PASS

**Step 2: 验证 API 文档**

Run: 访问 http://localhost:8000/docs 确认新端点显示正确

**Step 3: 最终 Commit**

```bash
git add -A
git commit -m "feat: complete stock pool management implementation"
```

---

## 参考资料

- [AKShare 指数成分股接口](https://akshare.readthedocs.io/zh_CN/latest/data/index/index.html#id4)
- [现有 Factor 模型参考](../backend/app/models/factor.py)
