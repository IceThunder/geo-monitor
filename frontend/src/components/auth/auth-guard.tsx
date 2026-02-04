'use client';

import React from 'react';
import { useAuth } from './auth-provider';
import { usePathname } from 'next/navigation';

interface AuthGuardProps {
  children: React.ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const { user, isLoading } = useAuth();
  const pathname = usePathname();

  // 公开页面列表（不需要认证）
  const publicPages = ['/auth/login', '/auth/register'];
  const isPublicPage = publicPages.includes(pathname);

  // 加载中显示加载页面
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">正在加载...</p>
        </div>
      </div>
    );
  }

  // 如果是公开页面或用户已认证，显示内容
  if (isPublicPage || user) {
    return <>{children}</>;
  }

  // 未认证用户访问受保护页面，显示空内容（路由会自动跳转）
  return null;
}
