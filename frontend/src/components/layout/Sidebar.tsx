/**
 * Sidebar Navigation Component
 */
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  ListTodo,
  BarChart3,
  Bell,
  Settings,
  FileText,
} from 'lucide-react';

const navigation = [
  { name: '概览', href: '/', icon: LayoutDashboard },
  { name: '任务管理', href: '/tasks', icon: ListTodo },
  { name: '数据分析', href: '/metrics', icon: BarChart3 },
  { name: '告警中心', href: '/alerts', icon: Bell },
  { name: '报表导出', href: '/reports', icon: FileText },
  { name: '系统设置', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r bg-card min-h-screen">
      <div className="p-6">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <span className="text-primary">GEO</span>
          <span>Monitor</span>
        </h1>
        <p className="text-xs text-muted-foreground mt-1">
          AI 模型品牌监控平台
        </p>
      </div>
      <nav className="px-3">
        <ul className="space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href || 
              (item.href !== '/' && pathname.startsWith(item.href));
            
            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
