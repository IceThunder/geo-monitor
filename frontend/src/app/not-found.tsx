/**
 * Not Found Page
 * 404错误页面
 */
'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Home, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-gray-300">404</h1>
          <h2 className="text-2xl font-semibold text-gray-900 mt-4">页面未找到</h2>
          <p className="text-gray-600 mt-2">
            抱歉，您访问的页面不存在或已被移动。
          </p>
        </div>
        
        <div className="space-y-4">
          <Link href="/" className="block">
            <Button className="w-full">
              <Home className="h-4 w-4 mr-2" />
              返回首页
            </Button>
          </Link>
          
          <Link href="/dashboard" className="block">
            <Button variant="outline" className="w-full">
              <ArrowLeft className="h-4 w-4 mr-2" />
              返回仪表板
            </Button>
          </Link>
        </div>
        
        <div className="mt-8 text-sm text-gray-500">
          <p>如果您认为这是一个错误，请联系系统管理员。</p>
        </div>
      </div>
    </div>
  );
}
