import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '../test/utils';
import Login from './Login';

vi.mock('../api/auth', () => ({
  authApi: {
    login: vi.fn(),
  },
}));

vi.mock('../stores/authStore', () => ({
  useAuthStore: () => ({
    login: vi.fn(),
    isAuthenticated: false,
  }),
}));

describe('Login Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login form with title', () => {
    render(<Login />);
    expect(screen.getByText('EasyQuant')).toBeInTheDocument();
    expect(screen.getByText(/登录您的账户/i)).toBeInTheDocument();
  });

  it('renders email and password inputs', () => {
    render(<Login />);
    expect(screen.getByPlaceholderText(/邮箱/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/密码/i)).toBeInTheDocument();
  });

  it('renders submit button', () => {
    render(<Login />);
    const submitButton = screen.getByRole('button', { name: /登\s*录/i });
    expect(submitButton).toBeInTheDocument();
  });

  it('has link to register page', () => {
    render(<Login />);
    expect(screen.getByText(/注册/i)).toBeInTheDocument();
  });
});
