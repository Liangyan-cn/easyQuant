export type SandboxStatus = 'active' | 'paused' | 'stopped';
export type DeploymentStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed';
export type TransactionType = 'deposit' | 'withdraw' | 'buy' | 'sell' | 'dividend' | 'fee';

export const SANDBOX_STATUS_LABELS: Record<SandboxStatus, string> = {
  active: '运行中',
  paused: '已暂停',
  stopped: '已停止',
};

export const DEPLOYMENT_STATUS_LABELS: Record<DeploymentStatus, string> = {
  pending: '待运行',
  running: '运行中',
  paused: '已暂停',
  completed: '已完成',
  failed: '失败',
};

export const TRANSACTION_TYPE_LABELS: Record<TransactionType, string> = {
  deposit: '入金',
  withdraw: '出金',
  buy: '买入',
  sell: '卖出',
  dividend: '分红',
  fee: '手续费',
};

export interface SandboxAccount {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  initial_capital: number;
  current_cash: number;
  total_value: number;
  status: SandboxStatus;
  created_at: string;
  updated_at: string;
}

export interface SandboxAccountCreate {
  name: string;
  description?: string;
  initial_capital?: number;
}

export interface SandboxAccountUpdate {
  name?: string;
  description?: string;
  status?: SandboxStatus;
}

export interface SandboxAccountListParams {
  page?: number;
  size?: number;
}

export interface SandboxAccountListResponse {
  items: SandboxAccount[];
  total: number;
  page: number;
  size: number;
}

export interface SandboxPosition {
  id: number;
  account_id: number;
  stock_code: string;
  stock_name?: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  realized_pnl: number;
  updated_at: string;
}

export interface SandboxTransaction {
  id: number;
  account_id: number;
  deployment_id?: number;
  transaction_type: TransactionType;
  stock_code?: string;
  stock_name?: string;
  quantity?: number;
  price?: number;
  amount: number;
  commission: number;
  description?: string;
  created_at: string;
}

export interface SandboxDeployment {
  id: number;
  account_id: number;
  strategy_id: number;
  name: string;
  status: DeploymentStatus;
  start_date: string;
  end_date?: string;
  stock_pool?: string[];
  parameters?: Record<string, unknown>;
  allocation_ratio: number;
  last_run_date?: string;
  last_run_result?: Record<string, unknown>;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface SandboxDeploymentCreate {
  strategy_id: number;
  name: string;
  start_date: string;
  end_date?: string;
  stock_pool?: string[];
  parameters?: Record<string, unknown>;
  allocation_ratio?: number;
}

export interface SandboxDailyValue {
  id: number;
  account_id: number;
  date: string;
  total_value: number;
  cash: number;
  position_value: number;
  daily_return?: number;
  cumulative_return?: number;
  benchmark_return?: number;
}

export interface SandboxAccountDetail {
  account: SandboxAccount;
  positions: SandboxPosition[];
  recent_transactions: SandboxTransaction[];
  deployments: SandboxDeployment[];
  daily_values: SandboxDailyValue[];
}

export interface DepositRequest {
  amount: number;
  description?: string;
}

export interface ResetAccountRequest {
  initial_capital?: number;
}
