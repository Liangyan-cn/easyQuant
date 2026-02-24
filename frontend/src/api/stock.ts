import type { AxiosRequestConfig } from 'axios';
import { request } from './client';
import type {
  StockListParams,
  StockListResponse,
  StockHistoryParams,
  StockHistoryResponse,
} from '@/types/stock';

export const stockApi = {
  getStockList(params?: StockListParams, config?: AxiosRequestConfig) {
    return request.get<StockListResponse>('/data/stocks', { params, ...config });
  },

  getStockHistory(code: string, params?: StockHistoryParams, config?: AxiosRequestConfig) {
    return request.get<StockHistoryResponse>(`/data/stocks/${code}/history`, { params, ...config });
  },
};
