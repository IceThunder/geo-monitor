/**
 * Settings Page
 * 设置页面 - 租户配置和用户偏好
 */
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Settings,
  Save,
  RefreshCw,
  Bell,
  Shield,
  Key,
  Link,
  AlertTriangle,
  CheckCircle,
  Loader2,
} from 'lucide-react';
import apiClient from '@/lib/api/client';

interface TenantConfig {
  openrouter_api_key_set: boolean;
  webhook_url: string | null;
  alert_threshold_accuracy: number;
  alert_threshold_sentiment: number;
}

interface UserProfile {
  id: string;
  email: string;
  name: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export default function SettingsPage() {
  const [config, setConfig] = useState<TenantConfig | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form state
  const [openrouterKey, setOpenrouterKey] = useState('');
  const [webhookUrl, setWebhookUrl] = useState('');
  const [thresholdAccuracy, setThresholdAccuracy] = useState(6);
  const [thresholdSentiment, setThresholdSentiment] = useState(0.5);
  const [userName, setUserName] = useState('');

  // Password change
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [configRes, profileRes] = await Promise.all([
        apiClient.get('/config'),
        apiClient.get('/auth/me'),
      ]);
      const configData = configRes.data;
      const profileData = profileRes.data;

      setConfig(configData);
      setProfile(profileData);
      setWebhookUrl(configData.webhook_url || '');
      setThresholdAccuracy(configData.alert_threshold_accuracy);
      setThresholdSentiment(configData.alert_threshold_sentiment);
      setUserName(profileData.name || '');
    } catch (err: any) {
      setError('加载设置失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSaveConfig = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const payload: Record<string, any> = {
        alert_threshold_accuracy: thresholdAccuracy,
        alert_threshold_sentiment: thresholdSentiment,
      };
      if (webhookUrl) payload.webhook_url = webhookUrl;
      if (openrouterKey) payload.openrouter_api_key = openrouterKey;

      await apiClient.put('/config', payload);

      // Update profile name if changed
      if (userName !== (profile?.name || '')) {
        await apiClient.put('/auth/me', { name: userName });
      }

      setOpenrouterKey('');
      setSuccess('设置已保存');
      await fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || '保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      setError('两次输入的新密码不一致');
      return;
    }
    if (newPassword.length < 8) {
      setError('新密码至少需要8个字符');
      return;
    }
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await apiClient.put('/auth/me/password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setSuccess('密码修改成功');
    } catch (err: any) {
      setError(err.response?.data?.detail || '密码修改失败');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-48 bg-gray-200 animate-pulse rounded" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-64 bg-gray-100 animate-pulse rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">系统设置</h1>
          <p className="text-gray-600 mt-1">配置系统参数和偏好设置</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" onClick={fetchData} disabled={saving}>
            <RefreshCw className="h-4 w-4 mr-2" />
            重置
          </Button>
          <Button onClick={handleSaveConfig} disabled={saving}>
            {saving ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            保存设置
          </Button>
        </div>
      </div>

      {/* 提示信息 */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
          <CheckCircle className="h-4 w-4 flex-shrink-0" />
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* API 配置 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Key className="h-5 w-5 mr-2" />
              API 配置
            </CardTitle>
            <CardDescription>配置 OpenRouter API 密钥和 Webhook</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="openrouter-key">OpenRouter API Key</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="openrouter-key"
                  type="password"
                  value={openrouterKey}
                  onChange={(e) => setOpenrouterKey(e.target.value)}
                  placeholder={config?.openrouter_api_key_set ? '••••••••（已配置）' : '输入 API Key'}
                />
                {config?.openrouter_api_key_set && (
                  <Badge variant="default" className="bg-green-600 flex-shrink-0">已配置</Badge>
                )}
              </div>
              <p className="text-xs text-gray-500">留空表示保持当前配置不变</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="webhook-url">Webhook URL</Label>
              <Input
                id="webhook-url"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                placeholder="https://your-webhook-url.com/notify"
              />
              <p className="text-xs text-gray-500">告警触发时会发送通知到此地址</p>
            </div>
          </CardContent>
        </Card>

        {/* 告警阈值 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Bell className="h-5 w-5 mr-2" />
              告警阈值
            </CardTitle>
            <CardDescription>设置触发告警的指标阈值</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="threshold-accuracy">
                准确率阈值（低于此值触发告警）
              </Label>
              <div className="flex items-center gap-3">
                <Input
                  id="threshold-accuracy"
                  type="number"
                  min={1}
                  max={10}
                  value={thresholdAccuracy}
                  onChange={(e) => setThresholdAccuracy(Number(e.target.value))}
                  className="w-24"
                />
                <span className="text-sm text-gray-500">/ 10 分</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="threshold-sentiment">
                情感分值阈值（低于此值触发告警）
              </Label>
              <div className="flex items-center gap-3">
                <Input
                  id="threshold-sentiment"
                  type="number"
                  min={-1}
                  max={1}
                  step={0.1}
                  value={thresholdSentiment}
                  onChange={(e) => setThresholdSentiment(Number(e.target.value))}
                  className="w-24"
                />
                <span className="text-sm text-gray-500">范围 -1.0 ~ 1.0</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 个人信息 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Settings className="h-5 w-5 mr-2" />
              个人信息
            </CardTitle>
            <CardDescription>修改您的个人资料</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>邮箱</Label>
              <Input value={profile?.email || ''} disabled />
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-name">用户名</Label>
              <Input
                id="user-name"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                placeholder="输入用户名"
              />
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">邮箱验证状态</span>
              {profile?.is_verified ? (
                <Badge variant="default" className="bg-green-600">已验证</Badge>
              ) : (
                <Badge variant="secondary">未验证</Badge>
              )}
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">注册时间</span>
              <span>{profile?.created_at ? new Date(profile.created_at).toLocaleDateString('zh-CN') : '-'}</span>
            </div>
          </CardContent>
        </Card>

        {/* 修改密码 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Shield className="h-5 w-5 mr-2" />
              修改密码
            </CardTitle>
            <CardDescription>更新您的登录密码</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="current-password">当前密码</Label>
              <Input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-password">新密码</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="至少8个字符"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">确认新密码</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>
            <Button
              variant="outline"
              onClick={handleChangePassword}
              disabled={saving || !currentPassword || !newPassword}
              className="w-full"
            >
              {saving ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Shield className="h-4 w-4 mr-2" />
              )}
              修改密码
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
