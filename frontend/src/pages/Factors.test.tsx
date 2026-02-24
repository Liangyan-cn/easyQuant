import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../test/utils';
import Factors from './Factors';

vi.mock('../api/factor', () => ({
  factorApi: {
    getFactorList: vi.fn().mockResolvedValue({
      data: {
        items: [
          {
            id: 1,
            name: '动量因子',
            code: 'momentum_20d',
            category: 'momentum',
            is_builtin: true,
            description: '20日动量因子',
          },
          {
            id: 2,
            name: '波动率因子',
            code: 'volatility_20d',
            category: 'volatility',
            is_builtin: false,
            description: '20日波动率',
          },
        ],
        total: 2,
      },
    }),
    createFactor: vi.fn(),
    updateFactor: vi.fn(),
    deleteFactor: vi.fn(),
    initBuiltinFactors: vi.fn(),
  },
}));

describe('Factors Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page title', () => {
    render(<Factors />);
    expect(screen.getByText('因子管理')).toBeInTheDocument();
  });

  it('renders search input', () => {
    render(<Factors />);
    expect(screen.getByPlaceholderText('搜索因子名称或代码')).toBeInTheDocument();
  });

  it('renders create button', () => {
    render(<Factors />);
    expect(screen.getByText('新建因子')).toBeInTheDocument();
  });

  it('renders init builtin button', () => {
    render(<Factors />);
    expect(screen.getByText('初始化内置因子')).toBeInTheDocument();
  });

  it('renders table with factor data', async () => {
    render(<Factors />);
    await waitFor(() => {
      expect(screen.getByText('动量因子')).toBeInTheDocument();
    });
    expect(screen.getByText('momentum_20d')).toBeInTheDocument();
  });

  it('displays builtin tag for builtin factors', async () => {
    render(<Factors />);
    await waitFor(() => {
      expect(screen.getByText('内置')).toBeInTheDocument();
    });
    expect(screen.getByText('自定义')).toBeInTheDocument();
  });

  it('renders table columns', () => {
    render(<Factors />);
    expect(screen.getByText('名称')).toBeInTheDocument();
    expect(screen.getByText('代码')).toBeInTheDocument();
    expect(screen.getByText('分类')).toBeInTheDocument();
    expect(screen.getByText('类型')).toBeInTheDocument();
    expect(screen.getByText('描述')).toBeInTheDocument();
    expect(screen.getByText('操作')).toBeInTheDocument();
  });

  it('renders detail button for each factor', async () => {
    render(<Factors />);
    await waitFor(() => {
      const detailButtons = screen.getAllByText('详情');
      expect(detailButtons.length).toBe(2);
    });
  });
});
