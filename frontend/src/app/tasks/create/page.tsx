/**
 * Create Task Page
 * 创建监控任务页面
 */
'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  ArrowLeft, 
  Plus, 
  X, 
  Info, 
  Save,
  Play,
  Settings
} from 'lucide-react';

// 可用模型列表
const availableModels = [
  { id: 'gpt-4', name: 'GPT-4', provider: 'OpenAI', cost: '0.03/1K tokens' },
  { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', provider: 'OpenAI', cost: '0.002/1K tokens' },
  { id: 'claude-3-opus', name: 'Claude-3 Opus', provider: 'Anthropic', cost: '0.015/1K tokens' },
  { id: 'claude-3-sonnet', name: 'Claude-3 Sonnet', provider: 'Anthropic', cost: '0.003/1K tokens' },
];

// Cron表达式预设
const cronPresets = [
  { label: '每小时', value: '0 * * * *' },
  { label: '每6小时', value: '0 */6 * * *' },
  { label: '每天', value: '0 0 * * *' },
  { label: '每周', value: '0 0 * * 0' },
  { label: '自定义', value: 'custom' },
];

interface TaskFormData {
  name: string;
  description: string;
  schedule: string;
  customCron: string;
  isActive: boolean;
  selectedModels: string[];
  keywords: string[];
  targetBrand: string;
  positioningKeywords: string[];
}

export default function CreateTaskPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [newKeyword, setNewKeyword] = useState('');
  const [newPositioningKeyword, setNewPositioningKeyword] = useState('');
  
  const [formData, setFormData] = useState<TaskFormData>({
    name: '',
    description: '',
    schedule: '0 */6 * * *',
    customCron: '',
    isActive: true,
    selectedModels: [],
    keywords: [],
    targetBrand: '',
    positioningKeywords: [],
  });

  const handleInputChange = (field: keyof TaskFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const addKeyword = () => {
    if (newKeyword.trim() && !formData.keywords.includes(newKeyword.trim())) {
      handleInputChange('keywords', [...formData.keywords, newKeyword.trim()]);
      setNewKeyword('');
    }
  };

  const removeKeyword = (keyword: string) => {
    handleInputChange('keywords', formData.keywords.filter(k => k !== keyword));
  };

  const addPositioningKeyword = () => {
    if (newPositioningKeyword.trim() && !formData.positioningKeywords.includes(newPositioningKeyword.trim())) {
      handleInputChange('positioningKeywords', [...formData.positioningKeywords, newPositioningKeyword.trim()]);
      setNewPositioningKeyword('');
    }
  };

  const removePositioningKeyword = (keyword: string) => {
    handleInputChange('positioningKeywords', formData.positioningKeywords.filter(k => k !== keyword));
  };

  const toggleModel = (modelId: string) => {
    const isSelected = formData.selectedModels.includes(modelId);
    if (isSelected) {
      handleInputChange('selectedModels', formData.selectedModels.filter(id => id !== modelId));
    } else {
      handleInputChange('selectedModels', [...formData.selectedModels, modelId]);
    }
  };

  const handleSubmit = async (action: 'save' | 'save_and_run') => {
    setLoading(true);
    try {
      // TODO: 实现保存逻辑
      console.log('Saving task:', formData, action);
      
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 保存成功后跳转
      router.push('/dashboard?tab=tasks');
    } catch (error) {
      console.error('Failed to save task:', error);
    } finally {
      setLoading(false);
    }
  };

  const isFormValid = () => {
    return formData.name.trim() && 
           formData.selectedModels.length > 0 && 
           formData.keywords.length > 0;
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center space-x-4">
        <Button 
          variant="ghost" 
          size="sm"
          onClick={() => router.back()}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          返回
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">创建监控任务</h1>
          <p className="text-gray-600 mt-1">配置新的品牌监控任务</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 主要表单 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 基本信息 */}
          <Card>
            <CardHeader>
              <CardTitle>基本信息</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">任务名称 *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="输入任务名称"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">任务描述</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="描述此任务的目的和范围"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="targetBrand">目标品牌</Label>
                <Input
                  id="targetBrand"
                  value={formData.targetBrand}
                  onChange={(e) => handleInputChange('targetBrand', e.target.value)}
                  placeholder="输入要监控的品牌名称"
                />
              </div>
            </CardContent>
          </Card>

          {/* 调度设置 */}
          <Card>
            <CardHeader>
              <CardTitle>调度设置</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>执行频率</Label>
                <Select
                  value={formData.schedule}
                  onValueChange={(value) => handleInputChange('schedule', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {cronPresets.map((preset) => (
                      <SelectItem key={preset.value} value={preset.value}>
                        {preset.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {formData.schedule === 'custom' && (
                <div className="space-y-2">
                  <Label htmlFor="customCron">自定义Cron表达式</Label>
                  <Input
                    id="customCron"
                    value={formData.customCron}
                    onChange={(e) => handleInputChange('customCron', e.target.value)}
                    placeholder="0 */6 * * *"
                  />
                  <p className="text-xs text-gray-500">
                    格式: 分 时 日 月 周 (例如: 0 */6 * * * 表示每6小时执行一次)
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 模型选择 */}
          <Card>
            <CardHeader>
              <CardTitle>模型选择 *</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {availableModels.map((model) => (
                  <div
                    key={model.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-all ${
                      formData.selectedModels.includes(model.id)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => toggleModel(model.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{model.name}</h4>
                        <p className="text-sm text-gray-500">{model.provider}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-500">{model.cost}</p>
                        {formData.selectedModels.includes(model.id) && (
                          <Badge variant="default" className="mt-1">已选择</Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 关键词配置 */}
          <Card>
            <CardHeader>
              <CardTitle>关键词配置 *</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>监控关键词</Label>
                <div className="flex space-x-2">
                  <Input
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    placeholder="输入关键词"
                    onKeyPress={(e) => e.key === 'Enter' && addKeyword()}
                  />
                  <Button onClick={addKeyword} size="sm">
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {formData.keywords.map((keyword) => (
                    <Badge key={keyword} variant="secondary" className="flex items-center gap-1">
                      {keyword}
                      <X 
                        className="h-3 w-3 cursor-pointer" 
                        onClick={() => removeKeyword(keyword)}
                      />
                    </Badge>
                  ))}
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>定位关键词 (可选)</Label>
                <div className="flex space-x-2">
                  <Input
                    value={newPositioningKeyword}
                    onChange={(e) => setNewPositioningKeyword(e.target.value)}
                    placeholder="输入定位关键词"
                    onKeyPress={(e) => e.key === 'Enter' && addPositioningKeyword()}
                  />
                  <Button onClick={addPositioningKeyword} size="sm">
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {formData.positioningKeywords.map((keyword) => (
                    <Badge key={keyword} variant="outline" className="flex items-center gap-1">
                      {keyword}
                      <X 
                        className="h-3 w-3 cursor-pointer" 
                        onClick={() => removePositioningKeyword(keyword)}
                      />
                    </Badge>
                  ))}
                </div>
                <p className="text-xs text-gray-500">
                  定位关键词用于计算品牌在特定领域的表现
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 侧边栏 */}
        <div className="space-y-6">
          {/* 操作面板 */}
          <Card>
            <CardHeader>
              <CardTitle>操作</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button 
                onClick={() => handleSubmit('save_and_run')}
                disabled={!isFormValid() || loading}
                className="w-full"
              >
                <Play className="h-4 w-4 mr-2" />
                保存并立即运行
              </Button>
              
              <Button 
                variant="outline"
                onClick={() => handleSubmit('save')}
                disabled={!isFormValid() || loading}
                className="w-full"
              >
                <Save className="h-4 w-4 mr-2" />
                仅保存
              </Button>
              
              <Button 
                variant="ghost"
                onClick={() => router.back()}
                className="w-full"
              >
                取消
              </Button>
            </CardContent>
          </Card>

          {/* 帮助信息 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Info className="h-4 w-4 mr-2" />
                使用提示
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-gray-600">
              <div>
                <h4 className="font-medium text-gray-900">关键词选择</h4>
                <p>选择与您品牌相关的核心关键词，系统将监控这些词汇的声量表现。</p>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900">模型选择</h4>
                <p>不同模型有不同的成本和性能特点，建议根据预算和精度需求选择。</p>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900">执行频率</h4>
                <p>频率越高，数据越及时，但成本也会相应增加。</p>
              </div>
            </CardContent>
          </Card>

          {/* 预估成本 */}
          {formData.selectedModels.length > 0 && (
            <Alert>
              <Settings className="h-4 w-4" />
              <AlertDescription>
                <strong>预估成本:</strong> 根据选择的模型和执行频率，预计每月成本约为 $15-30
              </AlertDescription>
            </Alert>
          )}
        </div>
      </div>
    </div>
  );
}
