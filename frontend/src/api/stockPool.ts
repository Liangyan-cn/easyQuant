import type { AxiosRequestConfig } from 'axios';
import { request } from './client';
import type {
  StockPool,
  StockPoolDetail,
  StockPoolListResponse,
  StockPoolListParams,
  StockPoolCreate,
  StockPoolUpdate,
  StockPoolItemCreate,
  StockPoolItem,
} from '@/types/stockPool';

export const stockPoolApi = {
  getPoolList(params?: StockPoolListParams, config?: AxiosRequestConfig) {
    return request.get<StockPoolListResponse>('/stock-pools', { params, ...config });
  },

  getPool(id: number, config?: AxiosRequestConfig) {
    return request.get<StockPoolDetail>(`/stock-pools/${id}`, config);
  },

  createPool(data: StockPoolCreate, config?: AxiosRequestConfig) {
    return request.post<StockPool>('/stock-pools', data, config);
  },

  updatePool(id: number, data: StockPoolUpdate, config?: AxiosRequestConfig) {
    return request.put<StockPool>(`/stock-pools/${id}`, data, config);
  },

  deletePool(id: number, config?: AxiosRequestConfig) {
    return request.delete(`/stock-pools/${id}`, config);
  },

  addStock(poolId: number, data: StockPoolItemCreate, config?: AxiosRequestConfig) {
    return request.post<StockPoolItem>(`/stock-pools/${poolId}/stocks`, data, config);
  },

  removeStock(poolId: number, stockCode: string, config?: AxiosRequestConfig) {
    return request.delete(`/stock-pools/${poolId}/stocks/${stockCode}`, config);
  },
};
