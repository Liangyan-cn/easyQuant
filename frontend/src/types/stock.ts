export interface StockInfo {
  code: string;
  name: string;
  market: 'SH' | 'SZ';
  industry?: string;
  listDate?: string;
  totalShares?: number;
  circulatingShares?: number;
  latestPrice?: number;
  change?: number;
  changePercent?: number;
  volume?: number;
  amount?: number;
}

export interface OHLCVItem {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount?: number;
}

export interface StockListParams {
  page?: number;
  size?: number;
  keyword?: string;
  market?: 'SH' | 'SZ' | '';
  pool_code?: string;
}

export interface StockListResponse {
  items: StockInfo[];
  total: number;
  page: number;
  size: number;
}

export interface StockHistoryParams {
  period?: 'daily' | 'weekly' | 'monthly';
  start?: string;
  end?: string;
}

export interface StockHistoryResponse {
  code: string;
  period: 'daily' | 'weekly' | 'monthly';
  items: OHLCVItem[];
}

export interface FinancialIndicatorItem {
  date: string;
  eps: number | null;
  bps: number | null;
  roe: number | null;
  roa: number | null;
  gross_profit_margin: number | null;
  net_profit_margin: number | null;
  debt_ratio: number | null;
  current_ratio: number | null;
  quick_ratio: number | null;
  revenue_growth: number | null;
  profit_growth: number | null;
}

export interface FinancialIndicatorResponse {
  code: string;
  items: FinancialIndicatorItem[];
}

export interface ValuationItem {
  date: string;
  pe: number | null;
  pe_ttm: number | null;
  pb: number | null;
  ps: number | null;
  ps_ttm: number | null;
  dv_ratio: number | null;
  dv_ttm: number | null;
  total_mv: number | null;
  circ_mv: number | null;
}

export interface ValuationResponse {
  code: string;
  items: ValuationItem[];
}
