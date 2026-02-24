import type { AxiosRequestConfig } from 'axios';
import { request } from './client';
import type {
  Strategy,
  StrategyCreate,
  StrategyUpdate,
  StrategyListParams,
  StrategyListResponse,
  Backtest,
  BacktestCreate,
  BacktestDetail,
} from '@/types/strategy';

export const strategyApi = {
  getStrategyList(params?: StrategyListParams, config?: AxiosRequestConfig) {
    return request.get<StrategyListResponse>('/strategies/', { params, ...config });
  },

  getStrategy(id: number, config?: AxiosRequestConfig) {
    return request.get<Strategy>(`/strategies/${id}`, config);
  },

  createStrategy(data: StrategyCreate, config?: AxiosRequestConfig) {
    return request.post<Strategy>('/strategies/', data, config);
  },

  updateStrategy(id: number, data: StrategyUpdate, config?: AxiosRequestConfig) {
    return request.put<Strategy>(`/strategies/${id}`, data, config);
  },

  deleteStrategy(id: number, config?: AxiosRequestConfig) {
    return request.delete(`/strategies/${id}`, config);
  },

  cloneStrategy(id: number, config?: AxiosRequestConfig) {
    return request.post<Strategy>(`/strategies/${id}/clone`, {}, config);
  },

  getStrategyBacktests(strategyId: number, limit?: number, config?: AxiosRequestConfig) {
    return request.get<{ items: Backtest[]; total: number }>(`/strategies/${strategyId}/backtests`, {
      params: { limit },
      ...config,
    });
  },

  createBacktest(data: BacktestCreate, config?: AxiosRequestConfig) {
    return request.post<Backtest>('/strategies/backtests', data, config);
  },

  getBacktest(backtestId: number, config?: AxiosRequestConfig) {
    return request.get<BacktestDetail>(`/strategies/backtests/${backtestId}`, config);
  },

  deleteBacktest(backtestId: number, config?: AxiosRequestConfig) {
    return request.delete(`/strategies/backtests/${backtestId}`, config);
  },

  getBacktestOrders(backtestId: number, page?: number, size?: number, config?: AxiosRequestConfig) {
    return request.get(`/strategies/backtests/${backtestId}/orders`, {
      params: { page, size },
      ...config,
    });
  },

  getBacktestPositions(backtestId: number, config?: AxiosRequestConfig) {
    return request.get(`/strategies/backtests/${backtestId}/positions`, config);
  },

  runBacktest(backtestId: number, config?: AxiosRequestConfig) {
    return request.post<{
      status: string;
      backtest_id: number;
      result?: {
        total_return?: number;
        annual_return?: number;
        max_drawdown?: number;
        sharpe_ratio?: number;
        total_trades?: number;
      };
    }>(`/strategies/backtests/${backtestId}/run`, {}, config);
  },
};
