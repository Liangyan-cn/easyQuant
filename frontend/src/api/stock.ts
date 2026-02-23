import { request } from './client';
import type {
  StockListParams,
  StockListResponse,
  StockHistoryParams,
  StockHistoryResponse,
} from '@/types/stock';

export const stockApi = {
  getStockList(params?: StockListParams) {
    return request.get<StockListResponse>('/stocks', { params });
  },

  getStockHistory(code: string, params?: StockHistoryParams) {
    return request.get<StockHistoryResponse>(`/stocks/${code}/history`, { params });
  },
};
