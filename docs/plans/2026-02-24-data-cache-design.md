# 数据缓存方案设计

**日期**: 2026-02-24
**Sprint**: Sprint 11
**任务**: TASK-2 数据缓存方案

## 1. 概述

### 1.1 目标

实现股票池内数据的持久化缓存机制，减少对外部 API (AKShare) 的重复调用，提升整体系统性能。

### 1.2 设计原则

- **历史数据不变**: 已过去的日期数据不会变化，适合长期缓存
- **预加载 + 按需加载**: 系统股票池预加载，其他股票按需缓存
- **文件持久化**: 使用 Parquet 格式存储，重启后快速恢复

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        数据缓存架构                              │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  API 层      │────▶│  CacheService    │────▶│  Parquet 文件    │
│  data.py     │     │  (内存+持久化)   │     │  (本地存储)      │
└──────────────┘     └──────────────────┘     └──────────────────┘
                              │                        ▲
                              │ 缓存未命中             │ 预加载/增量更新
                              ▼                        │
                     ┌──────────────────┐     ┌──────────────────┐
                     │  AKShare         │     │  预加载脚本      │
                     │  (外部数据源)    │     │  cache_loader.py │
                     └──────────────────┘     └──────────────────┘
```

### 2.2 缓存层次

| 层次 | 存储 | 特点 |
|------|------|------|
| L1 内存缓存 | Python dict | 最快访问，进程生命周期 |
| L2 文件缓存 | Parquet 文件 | 持久化，重启后可恢复 |
| L3 外部数据源 | AKShare API | 最慢，按需获取 |

## 3. 缓存策略

### 3.1 预加载策略

| 策略 | 范围 | 触发方式 |
|------|------|----------|
| 预加载 | 沪深300 + 中证500 (~800只) | 脚本手动执行 |
| 按需加载 | 其他股票 | 首次访问时加载并缓存 |
| 增量更新 | 已缓存股票 | 脚本手动执行（每日收盘后） |

### 3.2 数据访问流程

```
API 请求 → CacheService.get()
  → L1 内存缓存命中? 
    → 是: 返回数据
    → 否: L2 Parquet 文件存在?
      → 是: 加载到 L1 并返回
      → 否: 调用 AKShare → 缓存到 L1 → 返回
```

### 3.3 预加载流程

```
脚本执行 → 读取系统股票池 (hs300, zz500)
  → 遍历成分股 → 批量调用 AKShare
  → 合并数据 → 写入 Parquet 文件
  → 更新 metadata.json
```

## 4. 文件结构

### 4.1 缓存目录

```
backend/app/data/cache/
├── ohlcv.parquet           # 所有股票的历史行情数据
├── balance_sheet.parquet   # 资产负债表
├── income.parquet          # 利润表
├── cash_flow.parquet       # 现金流量表
├── indicators.parquet      # 财务指标
├── valuation.parquet       # 估值指标
├── dividend.parquet        # 分红数据
└── metadata.json           # 缓存元数据
```

### 4.2 Parquet 文件结构

**ohlcv.parquet 列定义**:

| 列名 | 类型 | 说明 |
|------|------|------|
| stock_code | string | 股票代码 |
| date | date | 交易日期 |
| open | float | 开盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| close | float | 收盘价 |
| volume | int64 | 成交量 |
| amount | float | 成交额 |
| change_percent | float | 涨跌幅 |

### 4.3 元数据结构

**metadata.json**:

```json
{
  "version": "1.0",
  "last_update": "2026-02-24T15:30:00",
  "ohlcv": {
    "stock_count": 800,
    "record_count": 400000,
    "date_range": ["2024-02-24", "2026-02-24"],
    "file_size_mb": 45.2,
    "last_update": "2026-02-24T15:30:00"
  },
  "balance_sheet": {
    "stock_count": 800,
    "record_count": 3200,
    "last_update": "2026-02-24T15:30:00"
  },
  "preloaded_pools": ["hs300", "zz500"],
  "on_demand_stocks": ["688001", "688002"]
}
```

## 5. 核心组件

### 5.1 CacheService

**文件**: `backend/app/services/cache_service.py`

**职责**:
- 管理内存缓存 (L1)
- 读写 Parquet 文件 (L2)
- 缓存命中/未命中处理
- 按需加载逻辑

**核心方法**:

```python
class CacheService:
    def get_ohlcv(self, stock_code: str, start_date: date, end_date: date) -> pd.DataFrame
    def get_financial(self, stock_code: str, data_type: str) -> pd.DataFrame
    def save_to_cache(self, data_type: str, df: pd.DataFrame) -> None
    def load_from_file(self, data_type: str) -> pd.DataFrame
    def get_cache_stats(self) -> CacheStats
```

### 5.2 CacheLoader

**文件**: `backend/app/scripts/cache_loader.py`

**职责**:
- 预加载系统股票池数据
- 增量更新已缓存数据
- 生成缓存元数据

**命令行接口**:

```bash
# 预加载系统股票池
python -m app.scripts.cache_loader preload

# 增量更新（获取最新数据）
python -m app.scripts.cache_loader update

# 查看缓存状态
python -m app.scripts.cache_loader status
```

### 5.3 Cache API

**文件**: `backend/app/api/v1/endpoints/cache.py`

**端点**:

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/cache/status` | GET | 查看缓存状态 |
| `/api/v1/cache/stats` | GET | 缓存统计信息 |

## 6. 数据模型

### 6.1 CacheStats Schema

```python
class CacheStats(BaseModel):
    total_stocks: int
    cached_stocks: int
    memory_usage_mb: float
    file_size_mb: float
    last_update: datetime
    hit_rate: float
    
class CacheStatus(BaseModel):
    ohlcv: CacheDataStatus
    balance_sheet: CacheDataStatus
    income: CacheDataStatus
    cash_flow: CacheDataStatus
    indicators: CacheDataStatus
    valuation: CacheDataStatus
    dividend: CacheDataStatus
    
class CacheDataStatus(BaseModel):
    stock_count: int
    record_count: int
    date_range: Optional[tuple[str, str]]
    file_size_mb: float
    last_update: datetime
```

## 7. 与现有系统集成

### 7.1 修改 data_service.py

将现有的内存缓存替换为 CacheService 调用：

```python
# 修改前
async def get_stock_history(...):
    if _is_cache_valid(stock_code):
        return _history_cache[stock_code]
    # 调用 AKShare...

# 修改后
async def get_stock_history(...):
    cache = CacheService()
    return cache.get_ohlcv(stock_code, start_date, end_date)
```

### 7.2 启动时行为

应用启动时：
1. 检查 Parquet 文件是否存在
2. 如果存在，加载元数据
3. 不自动预加载（由脚本手动触发）

## 8. 性能预估

### 8.1 存储大小

| 数据类型 | 记录数 | 预估大小 |
|----------|--------|----------|
| OHLCV (2年) | 800股 × 500天 = 400,000 | ~45 MB |
| 财务数据 | 800股 × 8季度 = 6,400 | ~5 MB |
| **总计** | | **~50 MB** |

### 8.2 性能对比

| 场景 | 无缓存 | 有缓存 | 提升 |
|------|--------|--------|------|
| 单股票历史行情 | ~2s | ~10ms | 200x |
| 批量获取 100 股票 | ~200s | ~1s | 200x |
| 应用启动 | - | ~2s (加载元数据) | - |

## 9. 交付产物

| 文件 | 说明 |
|------|------|
| `backend/app/services/cache_service.py` | 缓存服务核心逻辑 |
| `backend/app/scripts/cache_loader.py` | 预加载/更新脚本 |
| `backend/app/api/v1/endpoints/cache.py` | 缓存状态 API |
| `backend/app/schemas/cache.py` | 缓存相关 Schema |
| `backend/tests/test_cache.py` | 缓存测试用例 |

## 10. 实现计划

| 任务 | 优先级 | 依赖 |
|------|--------|------|
| 1. 创建 CacheService 基础结构 | P0 | 无 |
| 2. 实现 Parquet 读写 | P0 | 任务1 |
| 3. 实现预加载脚本 | P0 | 任务2 |
| 4. 集成到 data_service | P0 | 任务2 |
| 5. 实现缓存状态 API | P1 | 任务1 |
| 6. 编写测试用例 | P1 | 任务1-4 |
