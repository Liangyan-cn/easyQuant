import type { AxiosRequestConfig } from 'axios';
import { request } from './client';
import type {
  StockListParams,
  StockListResponse,
  StockHistoryParams,
  StockHistoryResponse,
  FinancialIndicatorResponse,
  ValuationResponse,
} from '@/types/stock';

export const stockApi = {
  getStockList(params?: StockListParams, config?: AxiosRequestConfig) {
    return request.get<StockListResponse>('/data/stocks', { params, ...config });
  },

  getStockHistory(code: string, params?: StockHistoryParams, config?: AxiosRequestConfig) {
    return request.get<StockHistoryResponse>(`/data/stocks/${code}/history`, { params, ...config });
  },

  getFinancialIndicators(code: string, limit = 8, config?: AxiosRequestConfig) {
    return request.get<FinancialIndicatorResponse>(`/data/stocks/${code}/financial-indicators`, { params: { limit }, ...config });
  },

  getValuation(code: string, limit = 30, config?: AxiosRequestConfig) {
    return request.get<ValuationResponse>(`/data/stocks/${code}/valuation`, { params: { limit }, ...config });
  },
};
