# 财务数据服务实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 扩展 data_service.py 以支持 A 股财务数据获取（资产负债表、利润表、现金流量表、财务指标、估值指标、分红数据）

**Architecture:** 在现有 data_service.py 中新增财务数据获取函数，复用现有的内存缓存模式和 Mock 数据降级机制

**Tech Stack:** Python, FastAPI, AKShare, Pydantic

---

## 设计文档

**日期**: 2026-02-24  
**Sprint**: Sprint 11  
**状态**: 已批准

---

## 1. 概述

### 1.1 背景

easyQuant 量化投资平台需要获取 A 股财务数据以支持：
- **因子计算**: 计算基本面因子如 PE、PB、ROE 等
- **策略分析**: 策略中的财务筛选条件
- **独立展示**: 前端展示股票财务报表数据

### 1.2 设计决策

基于调研报告 (`docs/research/financial-data-sources.md`) 的推荐，采用：
- **数据源**: AKShare (免费、无 API 限制、数据全面)
- **实现方案**: 扩展现有 `data_service.py` (方案 A)
- **缓存策略**: 内存缓存 (与现有模式一致)

---

## 2. 架构设计

### 2.1 模块结构

```
backend/app/
├── services/
│   └── data_service.py          # 扩展：新增财务数据函数
├── schemas/
│   └── stock.py                 # 扩展：新增财务数据模型
└── api/v1/endpoints/
    └── data.py                  # 扩展：新增财务数据端点
```

### 2.2 函数清单

| 函数名                       | 描述       | AKShare 接口                         |
| ---------------------------- | ---------- | ------------------------------------ |
| `get_balance_sheet()`        | 资产负债表 | `stock_balance_sheet_by_report_em`   |
| `get_income_statement()`     | 利润表     | `stock_profit_sheet_by_report_em`    |
| `get_cash_flow()`            | 现金流量表 | `stock_cash_flow_sheet_by_report_em` |
| `get_financial_indicators()` | 财务指标   | `stock_financial_analysis_indicator` |
| `get_valuation()`            | 估值指标   | `stock_a_lg_indicator`               |
| `get_dividend()`             | 分红数据   | `stock_history_dividend_detail`      |
| `get_earnings_forecast()`    | 业绩预告   | `stock_yjyg_em`                      |

---

## 3. 数据模型

### 3.1 资产负债表 (BalanceSheetItem)

```python
class BalanceSheetItem(BaseModel):
    report_date: date          # 报告期
    total_assets: float        # 总资产
    total_liabilities: float   # 总负债
    total_equity: float        # 股东权益
    current_assets: float      # 流动资产
    current_liabilities: float # 流动负债
    cash: float                # 货币资金
    inventory: float           # 存货
    accounts_receivable: float # 应收账款
```

### 3.2 利润表 (IncomeStatementItem)

```python
class IncomeStatementItem(BaseModel):
    report_date: date
    revenue: float             # 营业收入
    operating_profit: float    # 营业利润
    net_profit: float          # 净利润
    gross_profit: float        # 毛利润
    operating_cost: float      # 营业成本
```

### 3.3 现金流量表 (CashFlowItem)

```python
class CashFlowItem(BaseModel):
    report_date: date
    operating_cash_flow: float  # 经营活动现金流
    investing_cash_flow: float  # 投资活动现金流
    financing_cash_flow: float  # 筹资活动现金流
    net_cash_flow: float        # 现金净增加额
```

### 3.4 财务指标 (FinancialIndicators)

```python
class FinancialIndicators(BaseModel):
    report_date: date
    roe: float                  # 净资产收益率
    roa: float                  # 总资产收益率
    gross_margin: float         # 毛利率
    net_margin: float           # 净利率
    debt_ratio: float           # 资产负债率
    current_ratio: float        # 流动比率
```

### 3.5 估值指标 (ValuationData)

```python
class ValuationData(BaseModel):
    date: date
    pe_ttm: float               # 市盈率(TTM)
    pb: float                   # 市净率
    ps_ttm: float               # 市销率(TTM)
    pcf: float                  # 市现率
    market_cap: float           # 总市值
```

### 3.6 分红数据 (DividendItem)

```python
class DividendItem(BaseModel):
    announce_date: date         # 公告日期
    ex_date: Optional[date]     # 除权除息日
    dividend_per_share: float   # 每股股利
    dividend_yield: float       # 股息率
```

---

## 4. API 设计

### 4.1 端点列表

| 端点                                              | 方法 | 描述           |
| ------------------------------------------------- | ---- | -------------- |
| `/api/v1/data/stocks/{code}/balance-sheet`        | GET  | 获取资产负债表 |
| `/api/v1/data/stocks/{code}/income-statement`     | GET  | 获取利润表     |
| `/api/v1/data/stocks/{code}/cash-flow`            | GET  | 获取现金流量表 |
| `/api/v1/data/stocks/{code}/financial-indicators` | GET  | 获取财务指标   |
| `/api/v1/data/stocks/{code}/valuation`            | GET  | 获取估值指标   |
| `/api/v1/data/stocks/{code}/dividend`             | GET  | 获取分红数据   |
| `/api/v1/data/stocks/{code}/earnings-forecast`    | GET  | 获取业绩预告   |

### 4.2 请求参数

所有端点支持以下可选参数：
- `limit`: 返回记录数量限制 (默认 8，即最近 8 个季度)

---

## 5. 缓存策略

### 5.1 缓存变量

```python
_balance_sheet_cache: dict[str, tuple[datetime, BalanceSheetResponse]] = {}
_income_cache: dict[str, tuple[datetime, IncomeStatementResponse]] = {}
_cash_flow_cache: dict[str, tuple[datetime, CashFlowResponse]] = {}
_indicators_cache: dict[str, tuple[datetime, FinancialIndicatorsResponse]] = {}
_valuation_cache: dict[str, tuple[datetime, ValuationResponse]] = {}
_dividend_cache: dict[str, tuple[datetime, DividendResponse]] = {}
```

### 5.2 缓存 TTL

```python
FINANCIAL_CACHE_TTL_SECONDS = 3600  # 1小时 (财务数据更新频率低)
```

---

## 6. 错误处理

与现有 `data_service.py` 模式一致：

1. **AKShare 未安装** → 返回 Mock 数据
2. **数据解析错误** → 返回 Mock 数据
3. **网络错误** → 返回 Mock 数据

所有错误记录到日志，不向用户暴露内部错误。

---

## 7. 测试计划

### 7.1 单元测试

- 测试每个财务数据获取函数
- 测试缓存机制
- 测试 Mock 数据降级

### 7.2 集成测试

- 测试 API 端点响应
- 测试数据格式正确性

---

## 8. 实施计划

---

### Task 1: 扩展数据模型 - 添加财务数据 Schema

**Files:**
- Modify: `backend/app/schemas/stock.py`

**Step 1: 添加财务数据模型到 stock.py**

在 `StockHistoryResponse` 之后添加以下模型：

```python
class BalanceSheetItem(BaseModel):
    report_date: DateType = Field(..., description="报告期")
    total_assets: Optional[float] = Field(None, description="总资产")
    total_liabilities: Optional[float] = Field(None, description="总负债")
    total_equity: Optional[float] = Field(None, description="股东权益")
    current_assets: Optional[float] = Field(None, description="流动资产")
    current_liabilities: Optional[float] = Field(None, description="流动负债")
    cash: Optional[float] = Field(None, description="货币资金")
    inventory: Optional[float] = Field(None, description="存货")
    accounts_receivable: Optional[float] = Field(None, description="应收账款")


class BalanceSheetResponse(BaseModel):
    code: str = Field(..., description="股票代码")
    items: list[BalanceSheetItem]


class IncomeStatementItem(BaseModel):
    report_date: DateType = Field(..., description="报告期")
    revenue: Optional[float] = Field(None, description="营业收入")
    operating_profit: Optional[float] = Field(None, description="营业利润")
    net_profit: Optional[float] = Field(None, description="净利润")
    gross_profit: Optional[float] = Field(None, description="毛利润")
    operating_cost: Optional[float] = Field(None, description="营业成本")


class IncomeStatementResponse(BaseModel):
    code: str = Field(..., description="股票代码")
    items: list[IncomeStatementItem]


class CashFlowItem(BaseModel):
    report_date: DateType = Field(..., description="报告期")
    operating_cash_flow: Optional[float] = Field(None, description="经营活动现金流")
    investing_cash_flow: Optional[float] = Field(None, description="投资活动现金流")
    financing_cash_flow: Optional[float] = Field(None, description="筹资活动现金流")
    net_cash_flow: Optional[float] = Field(None, description="现金净增加额")


class CashFlowResponse(BaseModel):
    code: str = Field(..., description="股票代码")
    items: list[CashFlowItem]


class FinancialIndicatorItem(BaseModel):
    report_date: DateType = Field(..., description="报告期")
    roe: Optional[float] = Field(None, description="净资产收益率")
    roa: Optional[float] = Field(None, description="总资产收益率")
    gross_margin: Optional[float] = Field(None, description="毛利率")
    net_margin: Optional[float] = Field(None, description="净利率")
    debt_ratio: Optional[float] = Field(None, description="资产负债率")
    current_ratio: Optional[float] = Field(None, description="流动比率")


class FinancialIndicatorResponse(BaseModel):
    code: str = Field(..., description="股票代码")
    items: list[FinancialIndicatorItem]


class ValuationItem(BaseModel):
    date: DateType = Field(..., description="日期")
    pe_ttm: Optional[float] = Field(None, description="市盈率(TTM)")
    pb: Optional[float] = Field(None, description="市净率")
    ps_ttm: Optional[float] = Field(None, description="市销率(TTM)")
    market_cap: Optional[float] = Field(None, description="总市值(亿)")


class ValuationResponse(BaseModel):
    code: str = Field(..., description="股票代码")
    items: list[ValuationItem]


class DividendItem(BaseModel):
    report_date: DateType = Field(..., description="报告期")
    dividend_per_share: Optional[float] = Field(None, description="每股股利")
    ex_date: Optional[DateType] = Field(None, description="除权除息日")


class DividendResponse(BaseModel):
    code: str = Field(..., description="股票代码")
    items: list[DividendItem]
```

**Step 2: 验证语法**

Run: `cd backend && ./venv/bin/python -c "from app.schemas.stock import *; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add backend/app/schemas/stock.py
git commit -m "feat: add financial data schemas"
```

---

### Task 2: 实现财务数据获取函数 - Mock 数据

**Files:**
- Modify: `backend/app/services/data_service.py`

**Step 1: 添加财务数据缓存变量和 TTL**

在现有缓存变量之后添加：

```python
_balance_sheet_cache: dict[str, tuple[datetime, "BalanceSheetResponse"]] = {}
_income_cache: dict[str, tuple[datetime, "IncomeStatementResponse"]] = {}
_cash_flow_cache: dict[str, tuple[datetime, "CashFlowResponse"]] = {}
_indicators_cache: dict[str, tuple[datetime, "FinancialIndicatorResponse"]] = {}
_valuation_cache: dict[str, tuple[datetime, "ValuationResponse"]] = {}
_dividend_cache: dict[str, tuple[datetime, "DividendResponse"]] = {}

FINANCIAL_CACHE_TTL_SECONDS = 3600
```

**Step 2: 添加 Mock 数据生成函数**

```python
def _get_mock_balance_sheet(code: str, limit: int = 8) -> list["BalanceSheetItem"]:
    from app.schemas.stock import BalanceSheetItem
    items = []
    base_date = date.today()
    for i in range(limit):
        quarter_offset = i * 90
        report_date = base_date - timedelta(days=quarter_offset)
        report_date = report_date.replace(day=1)
        items.append(BalanceSheetItem(
            report_date=report_date,
            total_assets=random.uniform(1e10, 1e12),
            total_liabilities=random.uniform(1e9, 5e11),
            total_equity=random.uniform(1e9, 5e11),
            current_assets=random.uniform(1e9, 1e11),
            current_liabilities=random.uniform(1e9, 1e11),
            cash=random.uniform(1e8, 1e10),
            inventory=random.uniform(1e8, 1e10),
            accounts_receivable=random.uniform(1e8, 1e10),
        ))
    return items


def _get_mock_income_statement(code: str, limit: int = 8) -> list["IncomeStatementItem"]:
    from app.schemas.stock import IncomeStatementItem
    items = []
    base_date = date.today()
    for i in range(limit):
        quarter_offset = i * 90
        report_date = base_date - timedelta(days=quarter_offset)
        report_date = report_date.replace(day=1)
        revenue = random.uniform(1e9, 1e11)
        items.append(IncomeStatementItem(
            report_date=report_date,
            revenue=revenue,
            operating_profit=revenue * random.uniform(0.1, 0.3),
            net_profit=revenue * random.uniform(0.05, 0.2),
            gross_profit=revenue * random.uniform(0.2, 0.5),
            operating_cost=revenue * random.uniform(0.5, 0.8),
        ))
    return items


def _get_mock_cash_flow(code: str, limit: int = 8) -> list["CashFlowItem"]:
    from app.schemas.stock import CashFlowItem
    items = []
    base_date = date.today()
    for i in range(limit):
        quarter_offset = i * 90
        report_date = base_date - timedelta(days=quarter_offset)
        report_date = report_date.replace(day=1)
        items.append(CashFlowItem(
            report_date=report_date,
            operating_cash_flow=random.uniform(-1e9, 1e10),
            investing_cash_flow=random.uniform(-1e10, 1e9),
            financing_cash_flow=random.uniform(-1e10, 1e10),
            net_cash_flow=random.uniform(-1e9, 1e9),
        ))
    return items


def _get_mock_financial_indicators(code: str, limit: int = 8) -> list["FinancialIndicatorItem"]:
    from app.schemas.stock import FinancialIndicatorItem
    items = []
    base_date = date.today()
    for i in range(limit):
        quarter_offset = i * 90
        report_date = base_date - timedelta(days=quarter_offset)
        report_date = report_date.replace(day=1)
        items.append(FinancialIndicatorItem(
            report_date=report_date,
            roe=random.uniform(5, 30),
            roa=random.uniform(2, 15),
            gross_margin=random.uniform(20, 60),
            net_margin=random.uniform(5, 25),
            debt_ratio=random.uniform(20, 70),
            current_ratio=random.uniform(1, 3),
        ))
    return items


def _get_mock_valuation(code: str, limit: int = 30) -> list["ValuationItem"]:
    from app.schemas.stock import ValuationItem
    items = []
    base_date = date.today()
    for i in range(limit):
        items.append(ValuationItem(
            date=base_date - timedelta(days=i),
            pe_ttm=random.uniform(10, 50),
            pb=random.uniform(1, 10),
            ps_ttm=random.uniform(1, 20),
            market_cap=random.uniform(100, 10000),
        ))
    return items


def _get_mock_dividend(code: str, limit: int = 10) -> list["DividendItem"]:
    from app.schemas.stock import DividendItem
    items = []
    base_date = date.today()
    for i in range(limit):
        year_offset = i * 365
        report_date = base_date - timedelta(days=year_offset)
        items.append(DividendItem(
            report_date=report_date,
            dividend_per_share=random.uniform(0.1, 2.0),
            ex_date=report_date + timedelta(days=30),
        ))
    return items
```

**Step 3: 验证语法**

Run: `cd backend && ./venv/bin/python -c "from app.services.data_service import *; print('OK')"`
Expected: OK

**Step 4: Commit**

```bash
git add backend/app/services/data_service.py
git commit -m "feat: add mock data generators for financial data"
```

---

### Task 3: 实现财务数据获取函数 - AKShare 集成

**Files:**
- Modify: `backend/app/services/data_service.py`

**Step 1: 添加 AKShare 数据获取函数**

```python
def _fetch_balance_sheet_from_akshare(code: str, limit: int = 8) -> list["BalanceSheetItem"]:
    from app.schemas.stock import BalanceSheetItem
    try:
        import akshare as ak
        symbol = f"SH{code}" if code.startswith("6") else f"SZ{code}"
        df = ak.stock_balance_sheet_by_report_em(symbol=symbol)
        items = []
        for _, row in df.head(limit).iterrows():
            try:
                report_date = datetime.strptime(str(row.get("REPORT_DATE", ""))[:10], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            items.append(BalanceSheetItem(
                report_date=report_date,
                total_assets=row.get("TOTAL_ASSETS"),
                total_liabilities=row.get("TOTAL_LIABILITIES"),
                total_equity=row.get("TOTAL_EQUITY"),
                current_assets=row.get("TOTAL_CURRENT_ASSETS"),
                current_liabilities=row.get("TOTAL_CURRENT_LIAB"),
                cash=row.get("MONETARYFUNDS"),
                inventory=row.get("INVENTORY"),
                accounts_receivable=row.get("ACCOUNTS_RECE"),
            ))
        logger.info(f"Fetched {len(items)} balance sheet records for {code}")
        return items if items else _get_mock_balance_sheet(code, limit)
    except ImportError:
        logger.warning("AKShare not installed, using mock data")
        return _get_mock_balance_sheet(code, limit)
    except Exception as e:
        logger.error(f"Error fetching balance sheet for {code}: {e}")
        return _get_mock_balance_sheet(code, limit)


def _fetch_income_from_akshare(code: str, limit: int = 8) -> list["IncomeStatementItem"]:
    from app.schemas.stock import IncomeStatementItem
    try:
        import akshare as ak
        symbol = f"SH{code}" if code.startswith("6") else f"SZ{code}"
        df = ak.stock_profit_sheet_by_report_em(symbol=symbol)
        items = []
        for _, row in df.head(limit).iterrows():
            try:
                report_date = datetime.strptime(str(row.get("REPORT_DATE", ""))[:10], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            revenue = row.get("TOTAL_OPERATE_INCOME")
            cost = row.get("TOTAL_OPERATE_COST")
            items.append(IncomeStatementItem(
                report_date=report_date,
                revenue=revenue,
                operating_profit=row.get("OPERATE_PROFIT"),
                net_profit=row.get("NETPROFIT"),
                gross_profit=(revenue - cost) if revenue and cost else None,
                operating_cost=cost,
            ))
        logger.info(f"Fetched {len(items)} income records for {code}")
        return items if items else _get_mock_income_statement(code, limit)
    except ImportError:
        logger.warning("AKShare not installed, using mock data")
        return _get_mock_income_statement(code, limit)
    except Exception as e:
        logger.error(f"Error fetching income for {code}: {e}")
        return _get_mock_income_statement(code, limit)


def _fetch_cash_flow_from_akshare(code: str, limit: int = 8) -> list["CashFlowItem"]:
    from app.schemas.stock import CashFlowItem
    try:
        import akshare as ak
        symbol = f"SH{code}" if code.startswith("6") else f"SZ{code}"
        df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
        items = []
        for _, row in df.head(limit).iterrows():
            try:
                report_date = datetime.strptime(str(row.get("REPORT_DATE", ""))[:10], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            items.append(CashFlowItem(
                report_date=report_date,
                operating_cash_flow=row.get("NETCASH_OPERATE"),
                investing_cash_flow=row.get("NETCASH_INVEST"),
                financing_cash_flow=row.get("NETCASH_FINANCE"),
                net_cash_flow=row.get("CCE_ADD"),
            ))
        logger.info(f"Fetched {len(items)} cash flow records for {code}")
        return items if items else _get_mock_cash_flow(code, limit)
    except ImportError:
        logger.warning("AKShare not installed, using mock data")
        return _get_mock_cash_flow(code, limit)
    except Exception as e:
        logger.error(f"Error fetching cash flow for {code}: {e}")
        return _get_mock_cash_flow(code, limit)


def _fetch_indicators_from_akshare(code: str, limit: int = 8) -> list["FinancialIndicatorItem"]:
    from app.schemas.stock import FinancialIndicatorItem
    try:
        import akshare as ak
        df = ak.stock_financial_analysis_indicator(symbol=code)
        items = []
        for _, row in df.head(limit).iterrows():
            try:
                report_date = datetime.strptime(str(row.get("日期", ""))[:10], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            items.append(FinancialIndicatorItem(
                report_date=report_date,
                roe=row.get("净资产收益率"),
                roa=row.get("总资产报酬率"),
                gross_margin=row.get("销售毛利率"),
                net_margin=row.get("销售净利率"),
                debt_ratio=row.get("资产负债率"),
                current_ratio=row.get("流动比率"),
            ))
        logger.info(f"Fetched {len(items)} indicator records for {code}")
        return items if items else _get_mock_financial_indicators(code, limit)
    except ImportError:
        logger.warning("AKShare not installed, using mock data")
        return _get_mock_financial_indicators(code, limit)
    except Exception as e:
        logger.error(f"Error fetching indicators for {code}: {e}")
        return _get_mock_financial_indicators(code, limit)


def _fetch_valuation_from_akshare(code: str, limit: int = 30) -> list["ValuationItem"]:
    from app.schemas.stock import ValuationItem
    try:
        import akshare as ak
        symbol = f"sh{code}" if code.startswith("6") else f"sz{code}"
        df = ak.stock_a_lg_indicator(symbol=symbol)
        items = []
        for _, row in df.tail(limit).iloc[::-1].iterrows():
            try:
                trade_date = datetime.strptime(str(row.get("trade_date", "")), "%Y%m%d").date()
            except (ValueError, TypeError):
                continue
            items.append(ValuationItem(
                date=trade_date,
                pe_ttm=row.get("pe_ttm"),
                pb=row.get("pb"),
                ps_ttm=row.get("ps_ttm"),
                market_cap=row.get("total_mv"),
            ))
        logger.info(f"Fetched {len(items)} valuation records for {code}")
        return items if items else _get_mock_valuation(code, limit)
    except ImportError:
        logger.warning("AKShare not installed, using mock data")
        return _get_mock_valuation(code, limit)
    except Exception as e:
        logger.error(f"Error fetching valuation for {code}: {e}")
        return _get_mock_valuation(code, limit)


def _fetch_dividend_from_akshare(code: str, limit: int = 10) -> list["DividendItem"]:
    from app.schemas.stock import DividendItem
    try:
        import akshare as ak
        symbol = f"sh{code}" if code.startswith("6") else f"sz{code}"
        df = ak.stock_history_dividend_detail(symbol=symbol, indicator="分红")
        items = []
        for _, row in df.head(limit).iterrows():
            try:
                report_date = datetime.strptime(str(row.get("公告日期", ""))[:10], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            ex_date = None
            try:
                ex_date = datetime.strptime(str(row.get("除权除息日", ""))[:10], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass
            items.append(DividendItem(
                report_date=report_date,
                dividend_per_share=row.get("派息(税前)(元)"),
                ex_date=ex_date,
            ))
        logger.info(f"Fetched {len(items)} dividend records for {code}")
        return items if items else _get_mock_dividend(code, limit)
    except ImportError:
        logger.warning("AKShare not installed, using mock data")
        return _get_mock_dividend(code, limit)
    except Exception as e:
        logger.error(f"Error fetching dividend for {code}: {e}")
        return _get_mock_dividend(code, limit)
```

**Step 2: 验证语法**

Run: `cd backend && ./venv/bin/python -c "from app.services.data_service import *; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add backend/app/services/data_service.py
git commit -m "feat: add AKShare integration for financial data"
```

---

### Task 4: 实现公开 API 函数

**Files:**
- Modify: `backend/app/services/data_service.py`

**Step 1: 添加带缓存的公开函数**

```python
def _is_financial_cache_valid(cache_time: Optional[datetime]) -> bool:
    if cache_time is None:
        return False
    return (datetime.now() - cache_time).total_seconds() < FINANCIAL_CACHE_TTL_SECONDS


def get_balance_sheet(code: str, limit: int = 8) -> "BalanceSheetResponse":
    from app.schemas.stock import BalanceSheetResponse
    cache_key = f"{code}_{limit}"
    if cache_key in _balance_sheet_cache:
        cache_time, cached = _balance_sheet_cache[cache_key]
        if _is_financial_cache_valid(cache_time):
            return cached
    items = _fetch_balance_sheet_from_akshare(code, limit)
    response = BalanceSheetResponse(code=code, items=items)
    _balance_sheet_cache[cache_key] = (datetime.now(), response)
    return response


def get_income_statement(code: str, limit: int = 8) -> "IncomeStatementResponse":
    from app.schemas.stock import IncomeStatementResponse
    cache_key = f"{code}_{limit}"
    if cache_key in _income_cache:
        cache_time, cached = _income_cache[cache_key]
        if _is_financial_cache_valid(cache_time):
            return cached
    items = _fetch_income_from_akshare(code, limit)
    response = IncomeStatementResponse(code=code, items=items)
    _income_cache[cache_key] = (datetime.now(), response)
    return response


def get_cash_flow(code: str, limit: int = 8) -> "CashFlowResponse":
    from app.schemas.stock import CashFlowResponse
    cache_key = f"{code}_{limit}"
    if cache_key in _cash_flow_cache:
        cache_time, cached = _cash_flow_cache[cache_key]
        if _is_financial_cache_valid(cache_time):
            return cached
    items = _fetch_cash_flow_from_akshare(code, limit)
    response = CashFlowResponse(code=code, items=items)
    _cash_flow_cache[cache_key] = (datetime.now(), response)
    return response


def get_financial_indicators(code: str, limit: int = 8) -> "FinancialIndicatorResponse":
    from app.schemas.stock import FinancialIndicatorResponse
    cache_key = f"{code}_{limit}"
    if cache_key in _indicators_cache:
        cache_time, cached = _indicators_cache[cache_key]
        if _is_financial_cache_valid(cache_time):
            return cached
    items = _fetch_indicators_from_akshare(code, limit)
    response = FinancialIndicatorResponse(code=code, items=items)
    _indicators_cache[cache_key] = (datetime.now(), response)
    return response


def get_valuation(code: str, limit: int = 30) -> "ValuationResponse":
    from app.schemas.stock import ValuationResponse
    cache_key = f"{code}_{limit}"
    if cache_key in _valuation_cache:
        cache_time, cached = _valuation_cache[cache_key]
        if _is_financial_cache_valid(cache_time):
            return cached
    items = _fetch_valuation_from_akshare(code, limit)
    response = ValuationResponse(code=code, items=items)
    _valuation_cache[cache_key] = (datetime.now(), response)
    return response


def get_dividend(code: str, limit: int = 10) -> "DividendResponse":
    from app.schemas.stock import DividendResponse
    cache_key = f"{code}_{limit}"
    if cache_key in _dividend_cache:
        cache_time, cached = _dividend_cache[cache_key]
        if _is_financial_cache_valid(cache_time):
            return cached
    items = _fetch_dividend_from_akshare(code, limit)
    response = DividendResponse(code=code, items=items)
    _dividend_cache[cache_key] = (datetime.now(), response)
    return response
```

**Step 2: 验证语法**

Run: `cd backend && ./venv/bin/python -c "from app.services.data_service import get_balance_sheet, get_income_statement, get_cash_flow, get_financial_indicators, get_valuation, get_dividend; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add backend/app/services/data_service.py
git commit -m "feat: add public API functions for financial data with caching"
```

---

### Task 5: 添加 API 端点

**Files:**
- Modify: `backend/app/api/v1/endpoints/data.py`

**Step 1: 添加导入和端点**

在文件顶部添加导入：

```python
from app.schemas.stock import (
    StockHistoryResponse,
    StockListResponse,
    BalanceSheetResponse,
    IncomeStatementResponse,
    CashFlowResponse,
    FinancialIndicatorResponse,
    ValuationResponse,
    DividendResponse,
)
from app.services.data_service import (
    get_stock_history,
    get_stock_list,
    get_balance_sheet,
    get_income_statement,
    get_cash_flow,
    get_financial_indicators,
    get_valuation,
    get_dividend,
)
```

在文件末尾添加端点：

```python
@router.get("/stocks/{code}/balance-sheet", response_model=BalanceSheetResponse)
async def stock_balance_sheet(
    code: str,
    limit: int = Query(8, ge=1, le=20, description="返回记录数量"),
) -> BalanceSheetResponse:
    return get_balance_sheet(code=code, limit=limit)


@router.get("/stocks/{code}/income-statement", response_model=IncomeStatementResponse)
async def stock_income_statement(
    code: str,
    limit: int = Query(8, ge=1, le=20, description="返回记录数量"),
) -> IncomeStatementResponse:
    return get_income_statement(code=code, limit=limit)


@router.get("/stocks/{code}/cash-flow", response_model=CashFlowResponse)
async def stock_cash_flow(
    code: str,
    limit: int = Query(8, ge=1, le=20, description="返回记录数量"),
) -> CashFlowResponse:
    return get_cash_flow(code=code, limit=limit)


@router.get("/stocks/{code}/financial-indicators", response_model=FinancialIndicatorResponse)
async def stock_financial_indicators(
    code: str,
    limit: int = Query(8, ge=1, le=20, description="返回记录数量"),
) -> FinancialIndicatorResponse:
    return get_financial_indicators(code=code, limit=limit)


@router.get("/stocks/{code}/valuation", response_model=ValuationResponse)
async def stock_valuation(
    code: str,
    limit: int = Query(30, ge=1, le=100, description="返回记录数量"),
) -> ValuationResponse:
    return get_valuation(code=code, limit=limit)


@router.get("/stocks/{code}/dividend", response_model=DividendResponse)
async def stock_dividend(
    code: str,
    limit: int = Query(10, ge=1, le=50, description="返回记录数量"),
) -> DividendResponse:
    return get_dividend(code=code, limit=limit)
```

**Step 2: 验证语法**

Run: `cd backend && ./venv/bin/python -c "from app.api.v1.endpoints.data import router; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add backend/app/api/v1/endpoints/data.py
git commit -m "feat: add API endpoints for financial data"
```

---

### Task 6: 编写测试

**Files:**
- Modify: `backend/tests/test_data.py`

**Step 1: 添加财务数据测试类**

```python
class TestBalanceSheet:
    async def test_get_balance_sheet(self, client: AsyncClient):
        response = await client.get("/api/v1/data/stocks/600519/balance-sheet")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "600519"
        assert "items" in data
        assert isinstance(data["items"], list)

    async def test_get_balance_sheet_with_limit(self, client: AsyncClient):
        response = await client.get("/api/v1/data/stocks/600519/balance-sheet?limit=4")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 4


class TestIncomeStatement:
    async def test_get_income_statement(self, client: AsyncClient):
        response = await client.get("/api/v1/data/stocks/600519/income-statement")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "600519"
        assert "items" in data

    async def test_income_statement_fields(self, client: AsyncClient):
        response = await client.get("/api/v1/data/stocks/600519/income-statement")
        assert response.status_code == 200
        data = response.json()
        if data["items"]:
            item = data["items"][0]
            assert "report_date" in item
            assert "revenue" in item
            assert "net_profit" in item


class TestCashFlow:
    async def test_get_cash_flow(self, client: AsyncClient):
        response = await client.get("/api/v1/data/stocks/600519/cash-flow")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "600519"
        assert "items" in data


class TestFinancialIndicators:
    async def test_get_financial_indicators(self, client: AsyncClient):
        response = await client.get("/api/v1/data/stocks/600519/financial-indicators")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "600519"
        assert "items" in data

    async def test_financial_indicators_fields(self, client: AsyncClient):
        response = await client.get("/api/v1/data/stocks/600519/financial-indicators")
        assert response.status_code == 200
        data = response.json()
        if data["items"]:
            item = data["items"][0]
            assert "roe" in item
            assert "gross_margin" in item


class TestValuation:
    async def test_get_valuation(self, client: AsyncClient):
        response = await client.get("/api/v1/data/stocks/600519/valuation")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "600519"
        assert "items" in data

    async def test_valuation_fields(self, client: AsyncClient):
        response = await client.get("/api/v1/data/stocks/600519/valuation")
        assert response.status_code == 200
        data = response.json()
        if data["items"]:
            item = data["items"][0]
            assert "pe_ttm" in item
            assert "pb" in item


class TestDividend:
    async def test_get_dividend(self, client: AsyncClient):
        response = await client.get("/api/v1/data/stocks/600519/dividend")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "600519"
        assert "items" in data
```

**Step 2: 运行测试**

Run: `cd backend && ./venv/bin/pytest tests/test_data.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add backend/tests/test_data.py
git commit -m "test: add tests for financial data endpoints"
```

---

### Task 7: 运行完整测试验证

**Step 1: 运行所有后端测试**

Run: `cd backend && ./venv/bin/pytest -v`
Expected: All tests PASS

**Step 2: 验证 API 文档**

Run: 访问 http://localhost:8000/docs 确认新端点显示正确

**Step 3: 最终 Commit**

```bash
git add -A
git commit -m "feat: complete financial data service implementation"
```

---

## 参考资料

- [AKShare 官方文档](https://akshare.readthedocs.io/)
- [财务数据获取调研报告](../research/financial-data-sources.md)
