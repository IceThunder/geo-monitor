/**
 * Users Page
 * 用户管理页面
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Users, Plus, Trash2, AlertCircle, Mail, Clock, Shield } from 'lucide-react';
import apiClient, { handleApiError } from '@/lib/api/client';

interface User {
  user_id: string;
  email: string;
  name: string;
  role: string;
  is_primary: boolean;
  joined_at: string;
  permissions: string[];
}

interface Invitation {
  id: string;
  email: string;
  role: string;
  invited_at: string;
  expires_at: string;
}

export default function UsersPage() {
  const [members, setMembers] = useState<User[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Invite dialog state
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [inviting, setInviting] = useState(false);

  // Remove member dialog state
  const [removeDialogOpen, setRemoveDialogOpen] = useState(false);
  const [userToRemove, setUserToRemove] = useState<User | null>(null);
  const [removing, setRemoving] = useState(false);

  // Cancel invitation dialog state
  const [cancelInviteDialogOpen, setCancelInviteDialogOpen] = useState(false);
  const [invitationToCancel, setInvitationToCancel] = useState<Invitation | null>(null);
  const [canceling, setCanceling] = useState(false);

  // Fetch members and invitations
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [membersRes, invitationsRes] = await Promise.all([
        apiClient.get('/users/tenant/members'),
        apiClient.get('/users/tenant/invitations'),
      ]);

      setMembers(membersRes.data);
      setInvitations(invitationsRes.data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Invite user
  const handleInviteUser = async () => {
    if (!inviteEmail.trim()) {
      return;
    }

    try {
      setInviting(true);
      await apiClient.post('/users/tenant/invite', {
        email: inviteEmail,
        role: inviteRole,
      });

      setInviteDialogOpen(false);
      setInviteEmail('');
      setInviteRole('member');
      fetchData();
    } catch (err) {
      alert(handleApiError(err));
    } finally {
      setInviting(false);
    }
  };

  // Update member role
  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      await apiClient.put(`/users/tenant/member/${userId}/role`, null, {
        params: { new_role: newRole },
      });
      fetchData();
    } catch (err) {
      alert(handleApiError(err));
    }
  };

  // Remove member
  const handleRemoveMember = async () => {
    if (!userToRemove) return;

    try {
      setRemoving(true);
      await apiClient.delete(`/users/tenant/member/${userToRemove.user_id}`);

      setRemoveDialogOpen(false);
      setUserToRemove(null);
      fetchData();
    } catch (err) {
      alert(handleApiError(err));
    } finally {
      setRemoving(false);
    }
  };

  // Cancel invitation
  const handleCancelInvitation = async () => {
    if (!invitationToCancel) return;

    try {
      setCanceling(true);
      await apiClient.delete(`/users/tenant/invitation/${invitationToCancel.id}`);

      setCancelInviteDialogOpen(false);
      setInvitationToCancel(null);
      fetchData();
    } catch (err) {
      alert(handleApiError(err));
    } finally {
      setCanceling(false);
    }
  };

  // Calculate stats
  const totalUsers = members.length;
  const activeUsers = members.filter((m) => m.role !== 'viewer').length;
  const admins = members.filter((m) => m.role === 'admin' || m.role === 'owner').length;
  const pendingInvitations = invitations.length;

  // Get role badge variant
  const getRoleBadgeVariant = (role: string) => {
    if (role === 'owner' || role === 'admin') return 'default';
    return 'secondary';
  };

  // Get role display name
  const getRoleDisplayName = (role: string) => {
    const roleMap: Record<string, string> = {
      owner: '所有者',
      admin: '管理员',
      member: '成员',
      viewer: '查看者',
    };
    return roleMap[role] || role;
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">用户管理</h1>
          <p className="text-gray-600 mt-1">管理系统用户和权限设置</p>
        </div>
        <Button onClick={() => setInviteDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          邀请用户
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* 用户统计 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">总用户数</p>
                {loading ? (
                  <Skeleton className="h-8 w-16 mt-1" />
                ) : (
                  <p className="text-2xl font-bold text-gray-900">{totalUsers}</p>
                )}
              </div>
              <Users className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">活跃用户</p>
                {loading ? (
                  <Skeleton className="h-8 w-16 mt-1" />
                ) : (
                  <p className="text-2xl font-bold text-gray-900">{activeUsers}</p>
                )}
              </div>
              <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
                <div className="h-4 w-4 bg-green-500 rounded-full"></div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">管理员</p>
                {loading ? (
                  <Skeleton className="h-8 w-16 mt-1" />
                ) : (
                  <p className="text-2xl font-bold text-gray-900">{admins}</p>
                )}
              </div>
              <div className="h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center">
                <Shield className="h-4 w-4 text-purple-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">待审核</p>
                {loading ? (
                  <Skeleton className="h-8 w-16 mt-1" />
                ) : (
                  <p className="text-2xl font-bold text-gray-900">{pendingInvitations}</p>
                )}
              </div>
              <div className="h-8 w-8 bg-orange-100 rounded-full flex items-center justify-center">
                <Clock className="h-4 w-4 text-orange-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 用户列表 */}
      <Card>
        <CardHeader>
          <CardTitle>用户列表</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <Skeleton className="h-10 w-10 rounded-full" />
                    <div className="space-y-2">
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-3 w-48" />
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Skeleton className="h-6 w-16" />
                    <Skeleton className="h-9 w-20" />
                  </div>
                </div>
              ))}
            </div>
          ) : members.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Users className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>暂无用户</p>
            </div>
          ) : (
            <div className="space-y-4">
              {members.map((user) => (
                <div key={user.user_id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-center space-x-4">
                    <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 font-semibold">
                        {user.name ? user.name[0].toUpperCase() : user.email[0].toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium">{user.name || '未设置姓名'}</p>
                      <p className="text-sm text-gray-500">{user.email}</p>
                      {user.is_primary && (
                        <Badge variant="default" className="mt-1 text-xs">主账户</Badge>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Badge variant={getRoleBadgeVariant(user.role)}>
                      {getRoleDisplayName(user.role)}
                    </Badge>

                    {user.role !== 'owner' && (
                      <>
                        <Select
                          value={user.role}
                          onValueChange={(value) => handleRoleChange(user.user_id, value)}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="admin">管理员</SelectItem>
                            <SelectItem value="member">成员</SelectItem>
                            <SelectItem value="viewer">查看者</SelectItem>
                          </SelectContent>
                        </Select>

                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setUserToRemove(user);
                            setRemoveDialogOpen(true);
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 待处理邀请 */}
      {!loading && invitations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              待处理邀请
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {invitations.map((invitation) => (
                <div
                  key={invitation.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg bg-amber-50"
                >
                  <div className="flex items-center space-x-4">
                    <div className="h-10 w-10 bg-amber-100 rounded-full flex items-center justify-center">
                      <Mail className="h-5 w-5 text-amber-600" />
                    </div>
                    <div>
                      <p className="font-medium">{invitation.email}</p>
                      <p className="text-sm text-gray-500">
                        邀请时间: {new Date(invitation.invited_at).toLocaleDateString('zh-CN')}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Badge variant="secondary">{getRoleDisplayName(invitation.role)}</Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setInvitationToCancel(invitation);
                        setCancelInviteDialogOpen(true);
                      }}
                    >
                      取消邀请
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Invite User Dialog */}
      <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>邀请用户</DialogTitle>
            <DialogDescription>
              输入用户邮箱并选择角色，系统将发送邀请邮件
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="email">邮箱地址</Label>
              <Input
                id="email"
                type="email"
                placeholder="user@example.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role">用户角色</Label>
              <Select value={inviteRole} onValueChange={setInviteRole}>
                <SelectTrigger id="role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">管理员</SelectItem>
                  <SelectItem value="member">成员</SelectItem>
                  <SelectItem value="viewer">查看者</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setInviteDialogOpen(false)}
              disabled={inviting}
            >
              取消
            </Button>
            <Button onClick={handleInviteUser} disabled={inviting || !inviteEmail.trim()}>
              {inviting ? '发送中...' : '发送邀请'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Remove Member Confirmation Dialog */}
      <Dialog open={removeDialogOpen} onOpenChange={setRemoveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认移除用户</DialogTitle>
            <DialogDescription>
              确定要移除用户 <strong>{userToRemove?.email}</strong> 吗？此操作无法撤销。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRemoveDialogOpen(false)}
              disabled={removing}
            >
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={handleRemoveMember}
              disabled={removing}
            >
              {removing ? '移除中...' : '确认移除'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Cancel Invitation Confirmation Dialog */}
      <Dialog open={cancelInviteDialogOpen} onOpenChange={setCancelInviteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>取消邀请</DialogTitle>
            <DialogDescription>
              确定要取消发送给 <strong>{invitationToCancel?.email}</strong> 的邀请吗？
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCancelInviteDialogOpen(false)}
              disabled={canceling}
            >
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={handleCancelInvitation}
              disabled={canceling}
            >
              {canceling ? '取消中...' : '确认取消'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
