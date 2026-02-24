# A股财务数据获取方案调研报告

**调研日期**: 2026-02-24  
**Sprint**: Sprint 10  
**任务**: TASK-5 财务数据获取调研

---

## 1. 调研背景

easyQuant 量化投资平台需要获取 A 股财务数据（财报、估值、分红等）以支持因子计算和策略分析。本报告对主流数据源进行调研，评估其适用性。

---

## 2. 数据源对比

### 2.1 免费/开源数据源

| 数据源 | 费用 | 财务数据覆盖 | API 限制 | 数据来源 | 推荐指数 |
|--------|------|--------------|----------|----------|----------|
| **AKShare** | 完全免费 | ⭐⭐⭐⭐⭐ 全面 | 无限制 | 东方财富、巨潮 | ⭐⭐⭐⭐⭐ |
| **Tushare Pro** | 积分制 | ⭐⭐⭐⭐⭐ 全面 | 需积分 | 自建数据库 | ⭐⭐⭐⭐ |
| **Baostock** | 完全免费 | ⭐⭐⭐ 基础 | 无限制 | 证券公司 | ⭐⭐⭐ |

### 2.2 付费数据源

| 数据源 | 费用 | 财务数据覆盖 | 适用场景 | 推荐指数 |
|--------|------|--------------|----------|----------|
| **Wind 万得** | 年费数万元 | ⭐⭐⭐⭐⭐ 最全 | 机构/专业 | ⭐⭐⭐⭐⭐ |
| **同花顺 iFind** | 年费数万元 | ⭐⭐⭐⭐⭐ 全面 | 机构/专业 | ⭐⭐⭐⭐ |
| **东方财富 Choice** | 年费数千元 | ⭐⭐⭐⭐ 较全 | 中小机构 | ⭐⭐⭐⭐ |

---

## 3. 详细分析

### 3.1 AKShare (推荐首选)

**官网**: https://akshare.readthedocs.io/

**优势**:
- 完全免费开源，无 API 限制
- 数据来源权威（东方财富、巨潮网）
- 财务数据接口丰富：
  - `stock_balance_sheet_by_report_em` - 资产负债表
  - `stock_profit_sheet_by_report_em` - 利润表
  - `stock_cash_flow_sheet_by_report_em` - 现金流量表
  - `stock_financial_analysis_indicator` - 财务指标
  - `stock_dupont_analysis` - 杜邦分析
- 更新频繁，社区活跃

**劣势**:
- 数据源依赖第三方网站，可能有延迟
- API 接口变更较频繁，需关注版本更新

**代码示例**:
```python
import akshare as ak

# 获取资产负债表
balance_df = ak.stock_balance_sheet_by_report_em(symbol="SH600519")

# 获取利润表
profit_df = ak.stock_profit_sheet_by_report_em(symbol="SH600519")

# 获取财务指标
indicator_df = ak.stock_financial_analysis_indicator(symbol="600519")
```

### 3.2 Tushare Pro

**官网**: https://tushare.pro/

**优势**:
- 数据全面（股票、基金、期货、宏观）
- 自建数据库，数据质量高
- 社区支持完善

**劣势**:
- 积分制限制：
  - 基础数据免费
  - 财务数据需 120+ 积分
  - 高频数据需 2000+ 积分
- 积分获取方式：注册、邀请、捐赠

**代码示例**:
```python
import tushare as ts

ts.set_token('your_token')
pro = ts.pro_api()

# 获取利润表
income_df = pro.income(ts_code='600519.SH')

# 获取资产负债表
balance_df = pro.balancesheet(ts_code='600519.SH')

# 获取现金流量表
cashflow_df = pro.cashflow(ts_code='600519.SH')
```

### 3.3 Baostock

**官网**: http://baostock.com/

**优势**:
- 完全免费，无限制
- 数据来源稳定（证券公司）
- 支持历史数据回溯

**劣势**:
- 财务数据相对较少
- 界面和文档较简陋
- 更新频率较低

**代码示例**:
```python
import baostock as bs

bs.login()

# 获取季频财务数据
rs = bs.query_profit_data(code="sh.600519", year=2024, quarter=3)
print(rs.get_data())

bs.logout()
```

### 3.4 Wind 万得 (专业级)

**优势**:
- 数据最全面、最权威
- 实时数据支持
- 专业级数据质量

**劣势**:
- 费用高昂（年费数万元）
- 需要安装客户端
- 适合机构用户

---

## 4. 财务数据覆盖对比

| 数据类型 | AKShare | Tushare | Baostock | Wind |
|----------|---------|---------|----------|------|
| 资产负债表 | ✅ | ✅ | ✅ | ✅ |
| 利润表 | ✅ | ✅ | ✅ | ✅ |
| 现金流量表 | ✅ | ✅ | ✅ | ✅ |
| 财务指标 | ✅ | ✅ | ⚠️ 部分 | ✅ |
| 杜邦分析 | ✅ | ✅ | ❌ | ✅ |
| 估值指标 | ✅ | ✅ | ⚠️ 部分 | ✅ |
| 分红数据 | ✅ | ✅ | ✅ | ✅ |
| 股东信息 | ✅ | ✅ | ⚠️ 部分 | ✅ |
| 业绩预告 | ✅ | ✅ | ❌ | ✅ |
| 业绩快报 | ✅ | ✅ | ❌ | ✅ |

---

## 5. 推荐方案

### 5.1 短期方案 (推荐)

**主数据源**: AKShare  
**备用数据源**: Tushare Pro (免费积分范围)

**理由**:
1. AKShare 完全免费，无 API 限制
2. 财务数据覆盖全面，满足因子计算需求
3. 数据来源权威（东方财富、巨潮网）
4. 社区活跃，问题响应快

**实施步骤**:
1. 安装 AKShare: `pip install akshare`
2. 封装财务数据获取服务
3. 实现数据缓存机制（避免频繁请求）
4. 定期更新财报数据（季报发布后）

### 5.2 长期方案

如果项目发展到专业级需求，可考虑：
1. **Tushare Pro 付费积分** - 获取更高频率数据
2. **东方财富 Choice** - 性价比较高的付费方案
3. **Wind 万得** - 机构级专业需求

---

## 6. 技术实现建议

### 6.1 数据服务架构

```
┌─────────────────────────────────────────────┐
│           Financial Data Service            │
├─────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────────┐ │
│  │ AKShare │  │ Tushare │  │  Baostock   │ │
│  │ Adapter │  │ Adapter │  │   Adapter   │ │
│  └────┬────┘  └────┬────┘  └──────┬──────┘ │
│       └────────────┼───────────────┘        │
│                    ▼                        │
│           ┌───────────────┐                 │
│           │  Data Cache   │                 │
│           │   (Redis)     │                 │
│           └───────────────┘                 │
└─────────────────────────────────────────────┘
```

### 6.2 核心接口设计

```python
class FinancialDataService:
    async def get_balance_sheet(self, stock_code: str, period: str) -> dict:
        """获取资产负债表"""
        pass
    
    async def get_income_statement(self, stock_code: str, period: str) -> dict:
        """获取利润表"""
        pass
    
    async def get_cash_flow(self, stock_code: str, period: str) -> dict:
        """获取现金流量表"""
        pass
    
    async def get_financial_indicators(self, stock_code: str) -> dict:
        """获取财务指标"""
        pass
    
    async def get_valuation(self, stock_code: str) -> dict:
        """获取估值指标 (PE, PB, PS, PCF)"""
        pass
```

---

## 7. 结论

**推荐方案**: 使用 **AKShare** 作为主数据源

| 评估维度 | 评分 | 说明 |
|----------|------|------|
| 成本 | ⭐⭐⭐⭐⭐ | 完全免费 |
| 数据覆盖 | ⭐⭐⭐⭐⭐ | 财务数据全面 |
| 易用性 | ⭐⭐⭐⭐ | API 简洁，文档完善 |
| 稳定性 | ⭐⭐⭐⭐ | 社区活跃，更新频繁 |
| 扩展性 | ⭐⭐⭐⭐ | 可与 Tushare 互补 |

**下一步行动**:
1. 在 backend 中添加 AKShare 依赖
2. 实现 FinancialDataService 服务
3. 集成到因子计算模块
4. 添加数据缓存机制

---

## 参考资料

- [AKShare 官方文档](https://akshare.readthedocs.io/)
- [Tushare Pro 官方文档](https://tushare.pro/document/2)
- [Baostock 官方文档](http://baostock.com/baostock/index.php)
- [开源金融数据比较 - 雪球](https://xueqiu.com/3892199197/158561215)
