/**
 * Settings Page
 * 设置页面
 */
'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Settings, Save, RefreshCw, Bell, Shield, Database } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">系统设置</h1>
          <p className="text-gray-600 mt-1">配置系统参数和偏好设置</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            重置
          </Button>
          <Button>
            <Save className="h-4 w-4 mr-2" />
            保存设置
          </Button>
        </div>
      </div>

      {/* 设置分类 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 通知设置 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Bell className="h-5 w-5 mr-2" />
              通知设置
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">邮件通知</p>
                <p className="text-sm text-gray-500">接收系统邮件通知</p>
              </div>
              <Badge variant="default">已启用</Badge>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">实时告警</p>
                <p className="text-sm text-gray-500">重要事件实时推送</p>
              </div>
              <Badge variant="default">已启用</Badge>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">周报推送</p>
                <p className="text-sm text-gray-500">每周数据报告</p>
              </div>
              <Badge variant="secondary">已禁用</Badge>
            </div>
          </CardContent>
        </Card>

        {/* 安全设置 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Shield className="h-5 w-5 mr-2" />
              安全设置
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">双因素认证</p>
                <p className="text-sm text-gray-500">增强账户安全性</p>
              </div>
              <Badge variant="default">已启用</Badge>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">登录日志</p>
                <p className="text-sm text-gray-500">记录登录活动</p>
              </div>
              <Badge variant="default">已启用</Badge>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">会话超时</p>
                <p className="text-sm text-gray-500">30分钟无操作自动登出</p>
              </div>
              <Badge variant="default">已启用</Badge>
            </div>
          </CardContent>
        </Card>

        {/* 数据设置 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Database className="h-5 w-5 mr-2" />
              数据设置
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">数据备份</p>
                <p className="text-sm text-gray-500">每日自动备份</p>
              </div>
              <Badge variant="default">已启用</Badge>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">数据保留</p>
                <p className="text-sm text-gray-500">保留90天历史数据</p>
              </div>
              <Badge variant="default">90天</Badge>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">API限制</p>
                <p className="text-sm text-gray-500">每小时1000次请求</p>
              </div>
              <Badge variant="secondary">1000/h</Badge>
            </div>
          </CardContent>
        </Card>

        {/* 系统信息 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Settings className="h-5 w-5 mr-2" />
              系统信息
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">系统版本</span>
              <Badge variant="outline">v1.0.0</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">最后更新</span>
              <span className="text-sm">2026-02-01</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">运行时间</span>
              <span className="text-sm">15天 8小时</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">数据库状态</span>
              <Badge variant="default" className="bg-green-600">正常</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
