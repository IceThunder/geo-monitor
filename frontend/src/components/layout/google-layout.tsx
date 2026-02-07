'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/components/auth/auth-provider';
import { NotificationProvider, NotificationCenter, useNotifications } from '@/components/notifications/notification-provider';
import { cn } from '@/lib/utils';
import { taskApi, SearchResult } from '@/lib/api/tasks';
import {
  BarChart3,
  Settings,
  Search,
  Menu,
  X,
  Home,
  Activity,
  FileText,
  Users,
  ChevronDown,
  Plus,
  Filter,
  MoreVertical,
  HelpCircle,
  User,
  LogOut,
  Sun,
  Moon,
  Globe,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

interface GoogleLayoutProps {
  children: React.ReactNode;
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
  active?: boolean;
}

const navigation: NavItem[] = [
  { name: '概览', href: '/dashboard', icon: Home },
  { name: '任务管理', href: '/tasks', icon: Activity },
  { name: '分析报告', href: '/analytics', icon: BarChart3 },
  { name: '用户管理', href: '/users', icon: Users },
  { name: '设置', href: '/settings', icon: Settings },
];

// Derive WebSocket URL from the API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_URL = API_URL.replace('http', 'ws') + '/api/ws';

export function GoogleLayout({ children }: GoogleLayoutProps) {
  const pathname = usePathname();
  const { user } = useAuth();

  // Auth pages and unauthenticated users don't need the notification system
  const isAuthPage = pathname.startsWith('/auth');
  if (isAuthPage || !user) {
    return <>{children}</>;
  }

  return (
    <NotificationProvider wsUrl={WS_URL}>
      <GoogleLayoutContent>{children}</GoogleLayoutContent>
    </NotificationProvider>
  );
}

/**
 * Inner layout component that lives inside NotificationProvider,
 * so it can use the useNotifications() hook for WebSocket auto-connect.
 */
function GoogleLayoutContent({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [isDark, setIsDark] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { connect, disconnect } = useNotifications();

  // Auto-connect WebSocket when the user is authenticated
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token && user) {
      connect(token);
    }
    return () => disconnect();
  }, [user, connect, disconnect]);

  // Close search dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setSearchOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close search on route change
  useEffect(() => {
    setSearchOpen(false);
    setSearchQuery('');
  }, [pathname]);

  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!value.trim()) {
      setSearchResults(null);
      setSearchOpen(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      try {
        setSearchLoading(true);
        const results = await taskApi.searchGlobal(value.trim());
        setSearchResults(results);
        setSearchOpen(true);
      } catch {
        setSearchResults(null);
      } finally {
        setSearchLoading(false);
      }
    }, 300);
  }, []);

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setSearchOpen(false);
      setSearchQuery('');
    }
  };

  // 获取当前页面标题
  const getCurrentPageTitle = () => {
    const currentNav = navigation.find(item => pathname.startsWith(item.href));
    return currentNav?.name || 'GEO Monitor';
  };

  // 获取面包屑导航
  const getBreadcrumbs = () => {
    const segments = pathname.split('/').filter(Boolean);
    const breadcrumbs = [{ name: '首页', href: '/' }];

    let currentPath = '';
    segments.forEach(segment => {
      currentPath += `/${segment}`;
      const navItem = navigation.find(item => item.href === currentPath);
      if (navItem) {
        breadcrumbs.push({ name: navItem.name, href: currentPath });
      }
    });

    return breadcrumbs;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-50 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between px-4 py-3">
          {/* 左侧：Logo 和菜单 */}
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden"
            >
              <Menu className="h-5 w-5" />
            </Button>

            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-8 h-8 bg-blue-600 rounded-lg">
                <Globe className="h-5 w-5 text-white" />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                  GEO Monitor
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  地理位置监控系统
                </p>
              </div>
            </div>
          </div>

          {/* 中间：搜索栏 */}
          <div className="hidden md:flex flex-1 max-w-lg mx-8" ref={searchRef}>
            <div className="relative w-full">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder="搜索任务、关键词..."
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                onFocus={() => { if (searchResults) setSearchOpen(true); }}
                onKeyDown={handleSearchKeyDown}
                className="pl-10 pr-4 py-2 w-full bg-gray-100 dark:bg-gray-700 border-0 focus:bg-white dark:focus:bg-gray-600"
              />

              {/* Search dropdown */}
              {searchOpen && searchResults && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
                  {searchResults.tasks.length === 0 && searchResults.keywords.length === 0 ? (
                    <div className="p-4 text-center text-sm text-gray-500">
                      未找到匹配结果
                    </div>
                  ) : (
                    <>
                      {searchResults.tasks.length > 0 && (
                        <div>
                          <div className="px-3 py-2 text-xs font-semibold text-gray-500 bg-gray-50 dark:bg-gray-900">
                            任务
                          </div>
                          {searchResults.tasks.map((t) => (
                            <Link
                              key={t.id}
                              href={`/tasks/${t.id}`}
                              className="flex items-center px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                              onClick={() => setSearchOpen(false)}
                            >
                              <Activity className="h-4 w-4 text-blue-500 mr-3 flex-shrink-0" />
                              <div className="min-w-0">
                                <p className="text-sm font-medium truncate">{t.name}</p>
                                {t.description && (
                                  <p className="text-xs text-gray-500 truncate">{t.description}</p>
                                )}
                              </div>
                            </Link>
                          ))}
                        </div>
                      )}
                      {searchResults.keywords.length > 0 && (
                        <div>
                          <div className="px-3 py-2 text-xs font-semibold text-gray-500 bg-gray-50 dark:bg-gray-900">
                            关键词
                          </div>
                          {searchResults.keywords.map((kw, i) => (
                            <Link
                              key={`${kw.task_id}-${kw.keyword}-${i}`}
                              href={`/tasks/${kw.task_id}`}
                              className="flex items-center px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                              onClick={() => setSearchOpen(false)}
                            >
                              <Search className="h-4 w-4 text-green-500 mr-3 flex-shrink-0" />
                              <div className="min-w-0">
                                <p className="text-sm font-medium truncate">{kw.keyword}</p>
                                <p className="text-xs text-gray-500 truncate">任务: {kw.task_name}</p>
                              </div>
                            </Link>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* 右侧：操作按钮 */}
          <div className="flex items-center space-x-2">
            {/* 快速创建 */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="hidden sm:flex">
                  <Plus className="h-4 w-4 mr-2" />
                  创建
                  <ChevronDown className="h-4 w-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem>
                  <Activity className="h-4 w-4 mr-2" />
                  新建监控任务
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <FileText className="h-4 w-4 mr-2" />
                  创建报告
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Users className="h-4 w-4 mr-2" />
                  邀请用户
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* 通知中心 */}
            <NotificationCenter />

            {/* 主题切换 */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsDark(!isDark)}
            >
              {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </Button>

            {/* 用户菜单 */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                  <Avatar className="h-8 w-8">
                    <AvatarImage alt={user?.name} />
                    <AvatarFallback className="bg-blue-600 text-white">
                      {user?.name?.[0] || '?'}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <div className="flex items-center justify-start gap-2 p-2">
                  <div className="flex flex-col space-y-1 leading-none">
                    <p className="font-medium">{user?.name}</p>
                    <p className="w-[200px] truncate text-sm text-muted-foreground">
                      {user?.email}
                    </p>
                  </div>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <User className="mr-2 h-4 w-4" />
                  个人资料
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="mr-2 h-4 w-4" />
                  设置
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <HelpCircle className="mr-2 h-4 w-4" />
                  帮助
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  退出登录
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* 侧边栏 */}
        <aside className={cn(
          "fixed inset-y-0 left-0 z-40 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:inset-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}>
          <div className="flex flex-col h-full pt-16 lg:pt-0">
            {/* 导航菜单 */}
            <nav className="flex-1 px-4 py-4 space-y-1">
              {navigation.map((item) => {
                const isActive = pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors",
                      isActive
                        ? "bg-blue-50 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300"
                        : "text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                    )}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <item.icon
                      className={cn(
                        "mr-3 h-5 w-5 flex-shrink-0",
                        isActive
                          ? "text-blue-700 dark:text-blue-300"
                          : "text-gray-400 group-hover:text-gray-500"
                      )}
                    />
                    {item.name}
                    {item.badge && (
                      <Badge className="ml-auto bg-red-500 text-white">
                        {item.badge}
                      </Badge>
                    )}
                  </Link>
                );
              })}
            </nav>

            {/* 底部信息 */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
              <div className="text-xs text-gray-500 dark:text-gray-400">
                <p>版本 v1.0.0</p>
                <p>&copy; 2026 GEO Monitor</p>
              </div>
            </div>
          </div>
        </aside>

        {/* 遮罩层 */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-30 bg-gray-600 opacity-75 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* 主内容区域 */}
        <main className="flex-1 lg:ml-0">
          {/* 页面头部 */}
          <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
            <div className="px-6 py-4">
              {/* 面包屑导航 */}
              <nav className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400 mb-2">
                {getBreadcrumbs().map((crumb, index) => (
                  <React.Fragment key={crumb.href}>
                    {index > 0 && <span>/</span>}
                    <Link
                      href={crumb.href}
                      className="hover:text-gray-700 dark:hover:text-gray-300"
                    >
                      {crumb.name}
                    </Link>
                  </React.Fragment>
                ))}
              </nav>

              {/* 页面标题 */}
              <div className="flex items-center justify-between">
                <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {getCurrentPageTitle()}
                </h1>

                <div className="flex items-center space-x-2">
                  <Button variant="outline" size="sm">
                    <Filter className="h-4 w-4 mr-2" />
                    筛选
                  </Button>
                  <Button variant="outline" size="sm">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* 页面内容 */}
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
