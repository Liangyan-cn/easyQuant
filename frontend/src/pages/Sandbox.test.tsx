import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../test/utils';
import Sandbox from './Sandbox';

vi.mock('../api/sandbox', () => ({
  sandboxApi: {
    getAccountList: vi.fn().mockResolvedValue({
      data: {
        items: [
          {
            id: 1,
            name: '测试账户1',
            description: '用于测试的沙盒账户',
            initial_capital: 1000000,
            current_cash: 800000,
            total_value: 1100000,
            status: 'active',
            created_at: '2024-01-01T00:00:00',
          },
          {
            id: 2,
            name: '测试账户2',
            description: '另一个测试账户',
            initial_capital: 500000,
            current_cash: 450000,
            total_value: 480000,
            status: 'paused',
            created_at: '2024-01-15T00:00:00',
          },
        ],
        total: 2,
      },
    }),
    createAccount: vi.fn(),
    updateAccount: vi.fn(),
    deleteAccount: vi.fn(),
  },
}));

describe('Sandbox Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page title', () => {
    render(<Sandbox />);
    expect(screen.getByText('沙盒账户')).toBeInTheDocument();
  });

  it('renders search input', () => {
    render(<Sandbox />);
    expect(screen.getByPlaceholderText('搜索账户名称或描述')).toBeInTheDocument();
  });

  it('renders create button', () => {
    render(<Sandbox />);
    expect(screen.getByText('新建账户')).toBeInTheDocument();
  });

  it('renders table with account data', async () => {
    render(<Sandbox />);
    await waitFor(() => {
      expect(screen.getByText('测试账户1')).toBeInTheDocument();
    });
    expect(screen.getByText('测试账户2')).toBeInTheDocument();
  });

  it('displays status tags correctly', async () => {
    render(<Sandbox />);
    await waitFor(() => {
      expect(screen.getByText('运行中')).toBeInTheDocument();
    });
    expect(screen.getByText('已暂停')).toBeInTheDocument();
  });

  it('formats currency values', async () => {
    render(<Sandbox />);
    await waitFor(() => {
      expect(screen.getByText('¥1,000,000.00')).toBeInTheDocument();
    });
  });

  it('displays return rate with color', async () => {
    render(<Sandbox />);
    await waitFor(() => {
      expect(screen.getByText('+10.00%')).toBeInTheDocument();
    });
    expect(screen.getByText('-4.00%')).toBeInTheDocument();
  });

  it('renders table columns', () => {
    render(<Sandbox />);
    expect(screen.getByRole('columnheader', { name: '账户名称' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '描述' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '初始资金' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '当前现金' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '总资产' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '收益率' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '状态' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '操作' })).toBeInTheDocument();
  });

  it('renders action buttons for each account', async () => {
    render(<Sandbox />);
    await waitFor(() => {
      const detailButtons = screen.getAllByText('详情');
      expect(detailButtons.length).toBe(2);
    });
    const editButtons = screen.getAllByText('编辑');
    expect(editButtons.length).toBe(2);
    const deleteButtons = screen.getAllByText('删除');
    expect(deleteButtons.length).toBe(2);
  });
});
