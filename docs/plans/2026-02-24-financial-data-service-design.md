# 财务数据服务设计文档

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

| 函数名 | 描述 | AKShare 接口 |
|--------|------|--------------|
| `get_balance_sheet()` | 资产负债表 | `stock_balance_sheet_by_report_em` |
| `get_income_statement()` | 利润表 | `stock_profit_sheet_by_report_em` |
| `get_cash_flow()` | 现金流量表 | `stock_cash_flow_sheet_by_report_em` |
| `get_financial_indicators()` | 财务指标 | `stock_financial_analysis_indicator` |
| `get_valuation()` | 估值指标 | `stock_a_lg_indicator` |
| `get_dividend()` | 分红数据 | `stock_history_dividend_detail` |
| `get_earnings_forecast()` | 业绩预告 | `stock_yjyg_em` |

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

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/data/stocks/{code}/balance-sheet` | GET | 获取资产负债表 |
| `/api/v1/data/stocks/{code}/income-statement` | GET | 获取利润表 |
| `/api/v1/data/stocks/{code}/cash-flow` | GET | 获取现金流量表 |
| `/api/v1/data/stocks/{code}/financial-indicators` | GET | 获取财务指标 |
| `/api/v1/data/stocks/{code}/valuation` | GET | 获取估值指标 |
| `/api/v1/data/stocks/{code}/dividend` | GET | 获取分红数据 |
| `/api/v1/data/stocks/{code}/earnings-forecast` | GET | 获取业绩预告 |

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

1. **扩展数据模型** - 在 `schemas/stock.py` 中添加财务数据模型
2. **实现数据获取** - 在 `data_service.py` 中添加 AKShare 调用和 Mock 数据
3. **添加 API 端点** - 在 `endpoints/data.py` 中添加 7 个新端点
4. **编写测试** - 添加单元测试和集成测试
5. **验证** - 运行测试，确保所有功能正常

---

## 参考资料

- [AKShare 官方文档](https://akshare.readthedocs.io/)
- [财务数据获取调研报告](../research/financial-data-sources.md)
