export type StrategyType = 'momentum' | 'mean_reversion' | 'trend_following' | 'factor_based' | 'custom';
export type StrategyStatus = 'draft' | 'active' | 'archived';
export type BacktestStatus = 'pending' | 'running' | 'completed' | 'failed';

export const STRATEGY_TYPE_LABELS: Record<StrategyType, string> = {
  momentum: '动量策略',
  mean_reversion: '均值回归',
  trend_following: '趋势跟踪',
  factor_based: '因子策略',
  custom: '自定义',
};

export const STRATEGY_STATUS_LABELS: Record<StrategyStatus, string> = {
  draft: '草稿',
  active: '运行中',
  archived: '已归档',
};

export const BACKTEST_STATUS_LABELS: Record<BacktestStatus, string> = {
  pending: '等待中',
  running: '运行中',
  completed: '已完成',
  failed: '失败',
};

export interface Strategy {
  id: number;
  name: string;
  code: string;
  strategy_type: StrategyType;
  status: StrategyStatus;
  description?: string;
  logic?: string;
  parameters?: Record<string, unknown>;
  is_builtin: boolean;
  created_by?: number;
  created_at: string;
  updated_at: string;
}

export interface StrategyCreate {
  name: string;
  code: string;
  strategy_type: StrategyType;
  description?: string;
  logic?: string;
  parameters?: Record<string, unknown>;
}

export interface StrategyUpdate {
  name?: string;
  code?: string;
  strategy_type?: StrategyType;
  status?: StrategyStatus;
  description?: string;
  logic?: string;
  parameters?: Record<string, unknown>;
}

export interface StrategyListParams {
  page?: number;
  size?: number;
  strategy_type?: StrategyType;
  status?: StrategyStatus;
  keyword?: string;
}

export interface StrategyListResponse {
  items: Strategy[];
  total: number;
  page: number;
  size: number;
}

export interface Backtest {
  id: number;
  strategy_id: number;
  name?: string;
  status: BacktestStatus;
  start_date: string;
  end_date: string;
  initial_capital: number;
  commission_rate: number;
  slippage: number;
  benchmark?: string;
  stock_pool?: string[];
  parameters?: Record<string, unknown>;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface BacktestCreate {
  strategy_id: number;
  name?: string;
  start_date: string;
  end_date: string;
  initial_capital?: number;
  commission_rate?: number;
  slippage?: number;
  benchmark?: string;
  stock_pool?: string[];
  parameters?: Record<string, unknown>;
}

export interface BacktestResult {
  id: number;
  backtest_id: number;
  total_return?: number;
  annual_return?: number;
  benchmark_return?: number;
  alpha?: number;
  beta?: number;
  sharpe_ratio?: number;
  sortino_ratio?: number;
  max_drawdown?: number;
  volatility?: number;
  win_rate?: number;
  profit_loss_ratio?: number;
  total_trades?: number;
  avg_holding_days?: number;
  created_at: string;
}

export interface EquityCurvePoint {
  date: string;
  equity: number;
  benchmark?: number;
}

export interface BacktestDetail {
  backtest: Backtest;
  result?: BacktestResult;
  equity_curve?: EquityCurvePoint[];
}

export interface Order {
  id: number;
  backtest_id: number;
  stock_code: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  filled_price?: number;
  filled_quantity?: number;
  commission?: number;
  order_time: string;
  filled_time?: string;
  signal_reason?: string;
}
