import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../test/utils';
import Stocks from './Stocks';

vi.mock('../api/stock', () => ({
  stockApi: {
    getStockList: vi.fn().mockResolvedValue({
      data: {
        items: [
          {
            code: '000001',
            name: '平安银行',
            market: 'SZ',
            industry: '银行',
            latestPrice: 10.5,
            changePercent: 1.25,
            volume: 50000000,
            amount: 525000000,
          },
          {
            code: '600000',
            name: '浦发银行',
            market: 'SH',
            industry: '银行',
            latestPrice: 8.2,
            changePercent: -0.5,
            volume: 30000000,
            amount: 246000000,
          },
        ],
        total: 2,
      },
    }),
  },
}));

describe('Stocks Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page title', () => {
    render(<Stocks />);
    expect(screen.getByText('股票列表')).toBeInTheDocument();
  });

  it('renders search input', () => {
    render(<Stocks />);
    expect(screen.getByPlaceholderText('搜索股票名称或代码')).toBeInTheDocument();
  });

  it('renders market filter', () => {
    render(<Stocks />);
    expect(screen.getByText('全部市场')).toBeInTheDocument();
  });

  it('renders table with stock data', async () => {
    render(<Stocks />);
    await waitFor(() => {
      expect(screen.getByText('平安银行')).toBeInTheDocument();
    });
    expect(screen.getByText('000001')).toBeInTheDocument();
  });

  it('displays market labels correctly', async () => {
    render(<Stocks />);
    await waitFor(() => {
      expect(screen.getByText('深市')).toBeInTheDocument();
    });
    expect(screen.getByText('沪市')).toBeInTheDocument();
  });

  it('formats price change with colors', async () => {
    render(<Stocks />);
    await waitFor(() => {
      expect(screen.getByText('+1.25%')).toBeInTheDocument();
    });
    expect(screen.getByText('-0.50%')).toBeInTheDocument();
  });

  it('renders table columns', () => {
    render(<Stocks />);
    expect(screen.getByRole('columnheader', { name: '代码' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '名称' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '市场' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '行业' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '最新价' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '涨跌幅' })).toBeInTheDocument();
  });
});
