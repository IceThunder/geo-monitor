/**
 * 认证相关的工具函数和类型定义
 */

import apiClient from '@/lib/api/client';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  is_verified: boolean;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  plan_type: string;
  status: string;
  role: string;
  is_primary: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  tenants: Tenant[];
}

export interface RegisterResponse {
  message: string;
  user_id: string;
  tenant_id: string;
}

/**
 * 获取存储的访问token
 */
export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

/**
 * 获取存储的刷新token
 */
export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('refresh_token');
}

/**
 * 获取当前用户信息
 */
export function getCurrentUser(): User | null {
  if (typeof window === 'undefined') return null;
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
}

/**
 * 获取当前租户信息
 */
export function getCurrentTenant(): Tenant | null {
  if (typeof window === 'undefined') return null;
  const tenantStr = localStorage.getItem('current_tenant');
  return tenantStr ? JSON.parse(tenantStr) : null;
}

/**
 * 检查用户是否已登录
 */
export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

/**
 * 清除认证信息
 */
export function clearAuth(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  localStorage.removeItem('current_tenant');
}

/**
 * 创建带认证头的fetch请求
 */
export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getAccessToken();
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // 如果token过期，尝试刷新
  if (response.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      // 重新发送请求
      const newHeaders: Record<string, string> = {
        ...headers,
        'Authorization': `Bearer ${getAccessToken()}`,
      };
      return fetch(url, {
        ...options,
        headers: newHeaders,
      });
    } else {
      // 刷新失败，清除认证信息并跳转到登录页
      clearAuth();
      window.location.href = '/auth/login';
    }
  }

  return response;
}

/**
 * 刷新访问token
 */
export async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const response = await apiClient.post('/auth/refresh', {
      refresh_token: refreshToken,
    });

    if (response.data) {
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      return true;
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
  }

  return false;
}

/**
 * 登出用户
 */
export async function logout(): Promise<void> {
  const refreshToken = getRefreshToken();

  if (refreshToken) {
    try {
      await apiClient.post('/auth/logout', {
        refresh_token: refreshToken,
      });
    } catch (error) {
      console.error('Logout request failed:', error);
    }
  }

  clearAuth();
  window.location.href = '/auth/login';
}
