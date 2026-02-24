import { describe, it, expect } from 'vitest';
import { render, screen } from '../test/utils';
import Home from './Home';

describe('Home Component', () => {
  it('renders welcome title', () => {
    render(<Home />);
    expect(screen.getByText('欢迎使用 EasyQuant')).toBeInTheDocument();
  });

  it('renders platform description', () => {
    render(<Home />);
    expect(screen.getByText(/一站式量化交易平台/)).toBeInTheDocument();
  });

  it('renders strategy backtest card', () => {
    render(<Home />);
    expect(screen.getByText('策略回测')).toBeInTheDocument();
    expect(screen.getByText(/基于历史数据验证您的交易策略/)).toBeInTheDocument();
  });

  it('renders real-time market card', () => {
    render(<Home />);
    expect(screen.getByText('实时行情')).toBeInTheDocument();
    expect(screen.getByText(/接入多市场实时数据/)).toBeInTheDocument();
  });

  it('renders auto trading card', () => {
    render(<Home />);
    expect(screen.getByText('自动交易')).toBeInTheDocument();
    expect(screen.getByText(/策略自动执行/)).toBeInTheDocument();
  });

  it('renders three feature cards', () => {
    render(<Home />);
    const cards = screen.getAllByRole('img', { hidden: true });
    expect(cards.length).toBeGreaterThanOrEqual(3);
  });
});
