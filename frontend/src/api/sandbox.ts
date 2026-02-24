import type { AxiosRequestConfig } from 'axios';
import { request } from './client';
import type {
  SandboxAccount,
  SandboxAccountCreate,
  SandboxAccountUpdate,
  SandboxAccountListParams,
  SandboxAccountListResponse,
  SandboxAccountDetail,
  SandboxDeployment,
  SandboxDeploymentCreate,
  DepositRequest,
  ResetAccountRequest,
} from '@/types/sandbox';

export const sandboxApi = {
  getAccountList(params?: SandboxAccountListParams, config?: AxiosRequestConfig) {
    return request.get<SandboxAccountListResponse>('/sandbox/accounts', { params, ...config });
  },

  getAccount(accountId: number, config?: AxiosRequestConfig) {
    return request.get<SandboxAccountDetail>(`/sandbox/accounts/${accountId}`, config);
  },

  createAccount(data: SandboxAccountCreate, config?: AxiosRequestConfig) {
    return request.post<SandboxAccount>('/sandbox/accounts', data, config);
  },

  updateAccount(accountId: number, data: SandboxAccountUpdate, config?: AxiosRequestConfig) {
    return request.put<SandboxAccount>(`/sandbox/accounts/${accountId}`, data, config);
  },

  deleteAccount(accountId: number, config?: AxiosRequestConfig) {
    return request.delete(`/sandbox/accounts/${accountId}`, config);
  },

  deposit(accountId: number, data: DepositRequest, config?: AxiosRequestConfig) {
    return request.post<SandboxAccount>(`/sandbox/accounts/${accountId}/deposit`, data, config);
  },

  resetAccount(accountId: number, data: ResetAccountRequest, config?: AxiosRequestConfig) {
    return request.post<SandboxAccount>(`/sandbox/accounts/${accountId}/reset`, data, config);
  },

  createDeployment(accountId: number, data: SandboxDeploymentCreate, config?: AxiosRequestConfig) {
    return request.post<SandboxDeployment>(`/sandbox/accounts/${accountId}/deployments`, data, config);
  },

  getDeployment(deploymentId: number, config?: AxiosRequestConfig) {
    return request.get<SandboxDeployment>(`/sandbox/deployments/${deploymentId}`, config);
  },

  runDeployment(deploymentId: number, runDate?: string, config?: AxiosRequestConfig) {
    return request.post<SandboxDeployment>(
      `/sandbox/deployments/${deploymentId}/run`,
      runDate ? { run_date: runDate } : {},
      config
    );
  },

  stopDeployment(deploymentId: number, config?: AxiosRequestConfig) {
    return request.post<SandboxDeployment>(`/sandbox/deployments/${deploymentId}/stop`, {}, config);
  },

  startDeployment(deploymentId: number, config?: AxiosRequestConfig) {
    return request.post<SandboxDeployment>(`/sandbox/deployments/${deploymentId}/start`, {}, config);
  },
};
