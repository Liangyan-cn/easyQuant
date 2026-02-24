import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../test/utils';
import Strategies from './Strategies';

vi.mock('../api/strategy', () => ({
  strategyApi: {
    getStrategyList: vi.fn().mockResolvedValue({
      data: {
        items: [
          {
            id: 1,
            name: '均线交叉策略',
            code: 'ma_cross',
            strategy_type: 'trend',
            status: 'active',
            is_builtin: true,
            description: '基于均线交叉的趋势策略',
          },
          {
            id: 2,
            name: '动量策略',
            code: 'momentum',
            strategy_type: 'momentum',
            status: 'draft',
            is_builtin: false,
            description: '基于动量因子的策略',
          },
        ],
        total: 2,
      },
    }),
    createStrategy: vi.fn(),
    updateStrategy: vi.fn(),
    deleteStrategy: vi.fn(),
    cloneStrategy: vi.fn(),
  },
}));

describe('Strategies Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page title', () => {
    render(<Strategies />);
    expect(screen.getByText('策略管理')).toBeInTheDocument();
  });

  it('renders search input', () => {
    render(<Strategies />);
    expect(screen.getByPlaceholderText('搜索策略名称或代码')).toBeInTheDocument();
  });

  it('renders create button', () => {
    render(<Strategies />);
    expect(screen.getByText('新建策略')).toBeInTheDocument();
  });

  it('renders table with strategy data', async () => {
    render(<Strategies />);
    await waitFor(() => {
      expect(screen.getByText('均线交叉策略')).toBeInTheDocument();
    });
    expect(screen.getByText('ma_cross')).toBeInTheDocument();
  });

  it('displays status tags correctly', async () => {
    render(<Strategies />);
    await waitFor(() => {
      expect(screen.getByText('运行中')).toBeInTheDocument();
    });
    expect(screen.getByText('草稿')).toBeInTheDocument();
  });

  it('displays builtin tag for builtin strategies', async () => {
    render(<Strategies />);
    await waitFor(() => {
      expect(screen.getByText('内置')).toBeInTheDocument();
    });
    expect(screen.getByText('自定义')).toBeInTheDocument();
  });

  it('renders table columns', () => {
    render(<Strategies />);
    expect(screen.getByRole('columnheader', { name: '名称' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '代码' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '类型' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '状态' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '来源' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '描述' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '操作' })).toBeInTheDocument();
  });

  it('renders action buttons for each strategy', async () => {
    render(<Strategies />);
    await waitFor(() => {
      const detailButtons = screen.getAllByText('详情');
      expect(detailButtons.length).toBe(2);
    });
    const copyButtons = screen.getAllByText('复制');
    expect(copyButtons.length).toBe(2);
  });
});
