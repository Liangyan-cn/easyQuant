import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '../test/utils';
import Register from './Register';

vi.mock('../api/auth', () => ({
  authApi: {
    register: vi.fn(),
  },
}));

describe('Register Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders register form with title', () => {
    render(<Register />);
    expect(screen.getByText('EasyQuant')).toBeInTheDocument();
    expect(screen.getByText(/创建新账户/i)).toBeInTheDocument();
  });

  it('renders all input fields', () => {
    render(<Register />);
    expect(screen.getByPlaceholderText(/用户名/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/邮箱/i)).toBeInTheDocument();
  });

  it('renders submit button', () => {
    render(<Register />);
    const submitButton = screen.getByRole('button', { name: /注\s*册/i });
    expect(submitButton).toBeInTheDocument();
  });

  it('has link to login page', () => {
    render(<Register />);
    expect(screen.getByText(/登录/i)).toBeInTheDocument();
  });
});
