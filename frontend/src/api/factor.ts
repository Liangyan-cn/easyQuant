import type { AxiosRequestConfig } from 'axios';
import { request } from './client';
import type {
  Factor,
  FactorAnalyzeRequest,
  FactorAnalyzeResponse,
  FactorCalculateRequest,
  FactorCalculateResponse,
  FactorCategoryStats,
  FactorCreate,
  FactorEvaluationDetail,
  FactorEvaluationRequest,
  FactorEvaluation,
  FactorListParams,
  FactorListResponse,
  FactorUpdate,
} from '@/types/factor';

export const factorApi = {
  getFactorList(params?: FactorListParams, config?: AxiosRequestConfig) {
    return request.get<FactorListResponse>('/factors', { params, ...config });
  },

  getFactor(id: number, config?: AxiosRequestConfig) {
    return request.get<Factor>(`/factors/${id}`, config);
  },

  createFactor(data: FactorCreate, config?: AxiosRequestConfig) {
    return request.post<Factor>('/factors', data, config);
  },

  updateFactor(id: number, data: FactorUpdate, config?: AxiosRequestConfig) {
    return request.put<Factor>(`/factors/${id}`, data, config);
  },

  deleteFactor(id: number, config?: AxiosRequestConfig) {
    return request.delete(`/factors/${id}`, config);
  },

  getCategoryStats(config?: AxiosRequestConfig) {
    return request.get<FactorCategoryStats[]>('/factors/categories', config);
  },

  initBuiltinFactors(config?: AxiosRequestConfig) {
    return request.post<{ message: string; count: number }>('/factors/init-builtin', {}, config);
  },

  calculateFactor(data: FactorCalculateRequest, config?: AxiosRequestConfig) {
    return request.post<FactorCalculateResponse>('/factors/calculate', data, config);
  },

  evaluateFactor(data: FactorEvaluationRequest, config?: AxiosRequestConfig) {
    return request.post<FactorEvaluationDetail>('/factors/evaluate', data, config);
  },

  getFactorEvaluations(factorId: number, config?: AxiosRequestConfig) {
    return request.get<FactorEvaluation[]>(`/factors/${factorId}/evaluations`, config);
  },

  analyzeFactor(data: FactorAnalyzeRequest, config?: AxiosRequestConfig) {
    return request.post<FactorAnalyzeResponse>('/factors/analyze', data, config);
  },

  getLatestEvaluation(factorId: number, config?: AxiosRequestConfig) {
    return request.get<FactorEvaluation | null>(`/factors/${factorId}/latest-evaluation`, config);
  },
};
