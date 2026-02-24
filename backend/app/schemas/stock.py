from datetime import date as DateType
from typing import Optional

from pydantic import BaseModel, Field


class StockInfo(BaseModel):
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: str = Field(..., description="市场（SH/SZ）")
    industry: Optional[str] = Field(None, description="所属行业")


class StockListResponse(BaseModel):
    items: list[StockInfo]
    total: int
    page: int
    size: int


class OHLCVItem(BaseModel):
    date: DateType = Field(..., description="日期")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")
    amount: float = Field(..., description="成交额")


class StockHistoryResponse(BaseModel):
    code: str = Field(..., description="股票代码")
    period: str = Field(..., description="周期（daily/weekly/monthly）")
    items: list[OHLCVItem]


class BalanceSheetItem(BaseModel):
    date: DateType = Field(..., description="报告日期")
    total_assets: Optional[float] = Field(None, description="总资产")
    total_liabilities: Optional[float] = Field(None, description="总负债")
    total_equity: Optional[float] = Field(None, description="股东权益合计")
    current_assets: Optional[float] = Field(None, description="流动资产")
    non_current_assets: Optional[float] = Field(None, description="非流动资产")
    current_liabilities: Optional[float] = Field(None, description="流动负债")
    non_current_liabilities: Optional[float] = Field(None, description="非流动负债")
    cash_and_equivalents: Optional[float] = Field(None, description="货币资金")
    accounts_receivable: Optional[float] = Field(None, description="应收账款")
    inventory: Optional[float] = Field(None, description="存货")
    fixed_assets: Optional[float] = Field(None, description="固定资产")
    intangible_assets: Optional[float] = Field(None, description="无形资产")
    accounts_payable: Optional[float] = Field(None, description="应付账款")
    short_term_debt: Optional[float] = Field(None, description="短期借款")
    long_term_debt: Optional[float] = Field(None, description="长期借款")
    retained_earnings: Optional[float] = Field(None, description="未分配利润")


class BalanceSheetResponse(BaseModel):
    code: str = Field(..., description="股票代码")
    items: list[BalanceSheetItem]


class IncomeStatementItem(BaseModel):
    date: DateType = Field(..., description="报告日期")
    total_revenue: Optional[float] = Field(None, description="营业总收入")
    operating_revenue: Optional[float] = Field(None, description="营业收入")
    operating_cost: Optional[float] = Field(None, description="营业成本")
    gross_profit: Optional[float] = Field(None, description="毛利润")
    selling_expenses: Optional[float] = Field(None, description="销售费用")
    admin_expenses: Optional[float] = Field(None, description="管理费用")
    rd_expenses: Optional[float] = Field(None, description="研发费用")
    financial_expenses: Optional[float] = Field(None, description="财务费用")
    operating_profit: Optional[float] = Field(None, description="营业利润")
    total_profit: Optional[float] = Field(None, description="利润总额")
    income_tax: Optional[float] = Field(None, description="所得税费用")
    net_profit: Optional[float] = Field(None, description="净利润")
    net_profit_excluding_non_recurring: Optional[float] = Field(None, description="扣非净利润")
    eps: Optional[float] = Field(None, description="基本每股收益")
    diluted_eps: Optional[float] = Field(None, description="稀释每股收益")


class IncomeStatementResponse(BaseModel):
    code: str = Field(..., description="股票代码")
    items: list[IncomeStatementItem]


class CashFlowItem(BaseModel):
    date: DateType = Field(..., description="报告日期")
    operating_cash_flow: Optional[float] = Field(None, description="经营活动产生的现金流量净额")
    investing_cash_flow: Optional[float] = Field(None, description="投资活动产生的现金流量净额")
    financing_cash_flow: Optional[float] = Field(None, description="筹资活动产生的现金流量净额")
    net_cash_flow: Optional[float] = Field(None, description="现金及现金等价物净增加额")
    cash_received_from_sales: Optional[float] = Field(None, description="销售商品、提供劳务收到的现金")
    cash_paid_to_suppliers: Optional[float] = Field(None, description="购买商品、接受劳务支付的现金")
    cash_paid_to_employees: Optional[float] = Field(None, description="支付给职工的现金")
    cash_paid_for_taxes: Optional[float] = Field(None, description="支付的各项税费")
    cash_paid_for_investments: Optional[float] = Field(None, description="购建固定资产等支付的现金")
    cash_received_from_investments: Optional[float] = Field(None, description="处置固定资产等收回的现金")
    cash_received_from_borrowings: Optional[float] = Field(None, description="取得借款收到的现金")
    cash_paid_for_debt: Optional[float] = Field(None, description="偿还债务支付的现金")
    cash_paid_for_dividends: Optional[float] = Field(None, description="分配股利、利润支付的现金")
    free_cash_flow: Optional[float] = Field(None, description="自由现金流")


class CashFlowResponse(BaseModel):
    code: str = Field(..., description="股票代码")
    items: list[CashFlowItem]


class FinancialIndicatorItem(BaseModel):
    date: DateType = Field(..., description="报告日期")
    roe: Optional[float] = Field(None, description="净资产收益率")
    roa: Optional[float] = Field(None, description="总资产收益率")
    gross_margin: Optional[float] = Field(None, description="毛利率")
    net_margin: Optional[float] = Field(None, description="净利率")
    operating_margin: Optional[float] = Field(None, description="营业利润率")
    asset_turnover: Optional[float] = Field(None, description="总资产周转率")
    inventory_turnover: Optional[float] = Field(None, description="存货周转率")
    receivable_turnover: Optional[float] = Field(None, description="应收账款周转率")
    current_ratio: Optional[float] = Field(None, description="流动比率")
    quick_ratio: Optional[float] = Field(None, description="速动比率")
    debt_to_equity: Optional[float] = Field(None, description="资产负债率")
    interest_coverage: Optional[float] = Field(None, description="利息保障倍数")
    revenue_growth: Optional[float] = Field(None, description="营收同比增长率")
    profit_growth: Optional[float] = Field(None, description="净利润同比增长率")
    eps_growth: Optional[float] = Field(None, description="每股收益同比增长率")


class FinancialIndicatorResponse(BaseModel):
    code: str = Field(..., description="股票代码")
    items: list[FinancialIndicatorItem]


class ValuationItem(BaseModel):
    date: DateType = Field(..., description="日期")
    pe_ratio: Optional[float] = Field(None, description="市盈率(PE)")
    pe_ttm: Optional[float] = Field(None, description="市盈率(TTM)")
    pb_ratio: Optional[float] = Field(None, description="市净率(PB)")
    ps_ratio: Optional[float] = Field(None, description="市销率(PS)")
    ps_ttm: Optional[float] = Field(None, description="市销率(TTM)")
    pcf_ratio: Optional[float] = Field(None, description="市现率(PCF)")
    ev: Optional[float] = Field(None, description="企业价值(EV)")
    ev_to_ebitda: Optional[float] = Field(None, description="EV/EBITDA")
    market_cap: Optional[float] = Field(None, description="总市值")
    circulating_market_cap: Optional[float] = Field(None, description="流通市值")
    total_shares: Optional[float] = Field(None, description="总股本")
    circulating_shares: Optional[float] = Field(None, description="流通股本")


class ValuationResponse(BaseModel):
    code: str = Field(..., description="股票代码")
    items: list[ValuationItem]


class DividendItem(BaseModel):
    date: DateType = Field(..., description="分红日期")
    announcement_date: Optional[DateType] = Field(None, description="公告日期")
    ex_dividend_date: Optional[DateType] = Field(None, description="除权除息日")
    record_date: Optional[DateType] = Field(None, description="股权登记日")
    payment_date: Optional[DateType] = Field(None, description="派息日")
    dividend_per_share: Optional[float] = Field(None, description="每股股利")
    dividend_yield: Optional[float] = Field(None, description="股息率")
    bonus_shares_per_10: Optional[float] = Field(None, description="每10股送股数")
    transfer_shares_per_10: Optional[float] = Field(None, description="每10股转增股数")
    cash_per_10: Optional[float] = Field(None, description="每10股派息(元)")
    total_dividend: Optional[float] = Field(None, description="分红总额")


class DividendResponse(BaseModel):
    code: str = Field(..., description="股票代码")
    items: list[DividendItem]
