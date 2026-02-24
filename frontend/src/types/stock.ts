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
