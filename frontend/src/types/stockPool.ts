export type StockPoolType = 'system' | 'user';

export interface StockPoolItem {
  stock_code: string;
  stock_name: string | null;
  added_at: string;
}

export interface StockPool {
  id: number;
  name: string;
  code: string;
  pool_type: StockPoolType;
  description: string | null;
  stock_count: number;
  created_at: string;
  updated_at: string;
}

export interface StockPoolDetail extends StockPool {
  items: StockPoolItem[];
}

export interface StockPoolListResponse {
  items: StockPool[];
  total: number;
  page: number;
  size: number;
}

export interface StockPoolListParams {
  page?: number;
  size?: number;
  pool_type?: StockPoolType;
}

export interface StockPoolCreate {
  name: string;
  code: string;
  description?: string;
}

export interface StockPoolUpdate {
  name?: string;
  description?: string;
}

export interface StockPoolItemCreate {
  stock_code: string;
  stock_name?: string;
}

export const POOL_TYPE_LABELS: Record<StockPoolType, string> = {
  system: '系统',
  user: '用户',
};
