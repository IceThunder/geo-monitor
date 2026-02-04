'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';

interface User {
  id: string;
  email: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  // 检查认证状态
  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const userData = localStorage.getItem('user_data');
      
      if (!token || !userData) {
        setIsLoading(false);
        return;
      }

      // 简单验证：检查token是否存在和用户数据是否有效
      try {
        const user = JSON.parse(userData);
        if (user && user.id && user.email) {
          setUser(user);
        } else {
          // 用户数据无效，清除本地存储
          localStorage.removeItem('access_token');
          localStorage.removeItem('user_data');
        }
      } catch (parseError) {
        // 解析用户数据失败，清除本地存储
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
      }
    } catch (error) {
      console.error('认证检查失败:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_data');
    } finally {
      setIsLoading(false);
    }
  };

  // 登录函数
  const login = async (email: string, password: string) => {
    try {
      const response = await fetch('http://127.0.0.1:8001/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '登录失败');
      }

      const data = await response.json();
      
      // 保存token和用户信息
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user_data', JSON.stringify(data.user));
      
      setUser(data.user);
      
      // 跳转到仪表板
      router.push('/dashboard');
    } catch (error) {
      console.error('登录失败:', error);
      throw error;
    }
  };

  // 登出函数
  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    setUser(null);
    router.push('/auth/login');
  };

  // 初始化时检查认证状态
  useEffect(() => {
    checkAuthStatus();
  }, []);

  // 路由保护逻辑
  useEffect(() => {
    if (!isLoading) {
      const isAuthPage = pathname.startsWith('/auth');
      const isAuthenticated = !!user;

      if (!isAuthenticated && !isAuthPage) {
        // 未认证且不在认证页面，跳转到登录页
        router.push('/auth/login');
      } else if (isAuthenticated && isAuthPage) {
        // 已认证但在认证页面，跳转到仪表板
        router.push('/dashboard');
      }
    }
  }, [user, isLoading, pathname, router]);

  const value: AuthContextType = {
    user,
    isLoading,
    login,
    logout,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
