export type FactorCategory =
  | 'momentum'
  | 'value'
  | 'quality'
  | 'growth'
  | 'volatility'
  | 'liquidity'
  | 'size'
  | 'technical'
  | 'custom';

export interface Factor {
  id: number;
  name: string;
  code: string;
  category: FactorCategory;
  description: string | null;
  formula: string | null;
  is_builtin: boolean;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface FactorListResponse {
  items: Factor[];
  total: number;
  page: number;
  size: number;
}

export interface FactorListParams {
  page?: number;
  size?: number;
  category?: FactorCategory;
  keyword?: string;
}

export interface FactorCreate {
  name: string;
  code: string;
  category: FactorCategory;
  description?: string;
  formula?: string;
}

export interface FactorUpdate {
  name?: string;
  code?: string;
  category?: FactorCategory;
  description?: string;
  formula?: string;
}

export interface FactorCalculateRequest {
  factor_id: number;
  stock_codes?: string[];
  start_date: string;
  end_date: string;
}

export interface FactorCalculateResponse {
  factor_id: number;
  total_stocks: number;
  total_dates: number;
  calculated_count: number;
  status: string;
}

export interface FactorEvaluationRequest {
  factor_id: number;
  start_date: string;
  end_date: string;
  benchmark?: string;
}

export interface GroupReturnItem {
  group: number;
  return_value: number;
  stock_count: number;
}

export interface FactorEvaluation {
  id: number;
  factor_id: number;
  start_date: string;
  end_date: string;
  ic_mean: number | null;
  ic_std: number | null;
  ir: number | null;
  ic_positive_ratio: number | null;
  turnover: number | null;
  created_at: string;
}

export interface FactorEvaluationDetail {
  evaluation: FactorEvaluation;
  ic_series: Array<{ date: string; ic: number }>;
  group_returns: GroupReturnItem[];
}

export interface FactorCategoryStats {
  category: FactorCategory;
  count: number;
}

export const FACTOR_CATEGORY_LABELS: Record<FactorCategory, string> = {
  momentum: '动量',
  value: '估值',
  quality: '质量',
  growth: '成长',
  volatility: '波动',
  liquidity: '流动性',
  size: '规模',
  technical: '技术',
  custom: '自定义',
};

export interface FactorAnalyzeRequest {
  factor_id: number;
  start_date: string;
  end_date: string;
  stock_codes?: string[];
  force_recalculate?: boolean;
}

export interface FactorAnalyzeResponse {
  factor_id: number;
  calculated_count: number;
  evaluation: FactorEvaluation;
  ic_series: Array<{ date: string; ic: number }>;
  group_returns: GroupReturnItem[];
}
