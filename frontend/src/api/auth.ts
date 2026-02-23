import { request } from './client';
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '@/types/auth';

export const authApi = {
  login(email: string, password: string) {
    return request.post<TokenResponse>('/auth/login', { email, password } as LoginRequest);
  },

  register(email: string, password: string, username: string) {
    return request.post<User>('/auth/register', { email, password, username } as RegisterRequest);
  },

  refreshToken() {
    const refreshToken = localStorage.getItem('refreshToken');
    return request.post<TokenResponse>('/auth/refresh', { refreshToken });
  },

  getCurrentUser() {
    return request.get<User>('/auth/me');
  },
};
