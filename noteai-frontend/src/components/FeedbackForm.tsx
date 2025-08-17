import React, { useState } from 'react';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card';

interface FeedbackFormProps {
  onSubmit: (feedback: FeedbackData) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

interface FeedbackData {
  type: string;
  title: string;
  content: string;
  category?: string;
  priority?: string;
  rating?: number;
  page_url?: string;
  browser_info?: any;
  device_info?: any;
  images?: File[];
}

const FeedbackForm: React.FC<FeedbackFormProps> = ({ onSubmit, onCancel, isSubmitting = false }) => {
  const [formData, setFormData] = useState<FeedbackData>({
    type: 'general',
    title: '',
    content: '',
    category: 'other',
    priority: 'medium',
    rating: undefined,
    page_url: window.location.href,
    images: []
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const feedbackTypes = [
    { value: 'bug', label: '🐛 Bug报告' },
    { value: 'feature', label: '✨ 功能建议' },
    { value: 'improvement', label: '🔧 改进建议' },
    { value: 'general', label: '💬 一般反馈' }
  ];

  const categories = [
    { value: 'ui', label: '🎨 界面设计' },
    { value: 'performance', label: '⚡ 性能问题' },
    { value: 'ai', label: '🤖 AI功能' },
    { value: 'auth', label: '🔐 登录认证' },
    { value: 'other', label: '📝 其他' }
  ];

  const priorities = [
    { value: 'low', label: '🟢 低' },
    { value: 'medium', label: '🟡 中' },
    { value: 'high', label: '🟠 高' },
    { value: 'critical', label: '🔴 紧急' }
  ];

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = '请输入反馈标题';
    }

    if (!formData.content.trim()) {
      newErrors.content = '请输入反馈内容';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      // 收集浏览器和设备信息
      const browserInfo = {
        userAgent: navigator.userAgent,
        language: navigator.language,
        platform: navigator.platform,
        cookieEnabled: navigator.cookieEnabled,
        onLine: navigator.onLine
      };

      const deviceInfo = {
        screenWidth: window.screen.width,
        screenHeight: window.screen.height,
        windowWidth: window.innerWidth,
        windowHeight: window.innerHeight,
        pixelRatio: window.devicePixelRatio
      };

      onSubmit({
        ...formData,
        browser_info: browserInfo,
        device_info: deviceInfo
      });
    }
  };

  const handleInputChange = (field: keyof FeedbackData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // 清除对应字段的错误
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validFiles = files.filter(file => {
      const isValidType = file.type.startsWith('image/');
      const isValidSize = file.size <= 5 * 1024 * 1024; // 5MB限制
      return isValidType && isValidSize;
    });

    if (validFiles.length !== files.length) {
      alert('只支持图片文件，且单个文件不能超过5MB');
    }

    setFormData(prev => ({
      ...prev,
      images: [...(prev.images || []), ...validFiles].slice(0, 5) // 最多5张图片
    }));
  };

  const removeImage = (index: number) => {
    setFormData(prev => ({
      ...prev,
      images: prev.images?.filter((_, i) => i !== index) || []
    }));
  };

  // 处理粘贴事件
  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    const imageFiles: File[] = [];

    for (let i = 0; i < items.length; i++) {
      const item = items[i];

      // 检查是否是图片
      if (item.type.startsWith('image/')) {
        const file = item.getAsFile();
        if (file) {
          // 生成一个有意义的文件名
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
          const extension = item.type.split('/')[1] || 'png';
          const newFile = new File([file], `pasted-image-${timestamp}.${extension}`, {
            type: item.type
          });
          imageFiles.push(newFile);
        }
      }
    }

    if (imageFiles.length > 0) {
      // 验证文件大小和数量
      const validFiles = imageFiles.filter(file => {
        const isValidSize = file.size <= 5 * 1024 * 1024; // 5MB限制
        return isValidSize;
      });

      if (validFiles.length !== imageFiles.length) {
        alert('部分图片超过5MB限制，已被过滤');
      }

      if (validFiles.length > 0) {
        setFormData(prev => {
          const currentImages = prev.images || [];
          const newImages = [...currentImages, ...validFiles].slice(0, 5); // 最多5张图片

          if (newImages.length < currentImages.length + validFiles.length) {
            alert('最多只能上传5张图片，超出部分已被忽略');
          }

          return {
            ...prev,
            images: newImages
          };
        });

        // 显示成功提示
        alert(`成功粘贴 ${validFiles.length} 张图片`);
      }
    }
  };

  // 处理拖拽上传
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const files = Array.from(e.dataTransfer.files);
    const imageFiles = files.filter(file => file.type.startsWith('image/'));

    if (imageFiles.length > 0) {
      const validFiles = imageFiles.filter(file => {
        const isValidSize = file.size <= 5 * 1024 * 1024; // 5MB限制
        return isValidSize;
      });

      if (validFiles.length !== imageFiles.length) {
        alert('部分图片超过5MB限制，已被过滤');
      }

      if (validFiles.length > 0) {
        setFormData(prev => ({
          ...prev,
          images: [...(prev.images || []), ...validFiles].slice(0, 5) // 最多5张图片
        }));

        alert(`成功添加 ${validFiles.length} 张图片`);
      }
    }
  };

  const StarRating: React.FC<{ rating: number | undefined; onChange: (rating: number) => void }> = ({ rating, onChange }) => {
    return (
      <div className="flex space-x-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => onChange(star)}
            className={`text-2xl transition-colors ${
              rating && star <= rating ? 'text-yellow-400' : 'text-gray-300 hover:text-yellow-200'
            }`}
          >
            ⭐
          </button>
        ))}
      </div>
    );
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>📝 提交反馈</CardTitle>
        <CardDescription>
          您的反馈对我们很重要，帮助我们改进产品体验
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6" onPaste={handlePaste}>
          {/* 反馈类型 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              反馈类型 *
            </label>
            <select
              value={formData.type}
              onChange={(e) => handleInputChange('type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {feedbackTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* 标题 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              标题 *
            </label>
            <Input
              value={formData.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              placeholder="简要描述您的反馈"
              error={errors.title}
            />
          </div>

          {/* 分类和优先级 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                分类
              </label>
              <select
                value={formData.category}
                onChange={(e) => handleInputChange('category', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {categories.map((category) => (
                  <option key={category.value} value={category.value}>
                    {category.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                优先级
              </label>
              <select
                value={formData.priority}
                onChange={(e) => handleInputChange('priority', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {priorities.map((priority) => (
                  <option key={priority.value} value={priority.value}>
                    {priority.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* 内容 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              详细描述 *
            </label>
            <textarea
              value={formData.content}
              onChange={(e) => handleInputChange('content', e.target.value)}
              placeholder="请详细描述您遇到的问题或建议..."
              rows={6}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.content ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.content && (
              <p className="mt-1 text-sm text-red-600">{errors.content}</p>
            )}
          </div>

          {/* 评分 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              整体评分（可选）
            </label>
            <StarRating
              rating={formData.rating}
              onChange={(rating) => handleInputChange('rating', rating)}
            />
          </div>

          {/* 图片上传 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              上传图片（可选，最多5张）
            </label>
            <div className="space-y-3">
              {/* 文件选择 */}
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageUpload}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />

              {/* 拖拽上传区域 */}
              <div
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors"
              >
                <div className="text-gray-500">
                  <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                    <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <p className="mt-2 text-sm">
                    <span className="font-medium text-blue-600">拖拽图片到此处</span> 或
                    <span className="font-medium text-green-600"> Ctrl+V 粘贴图片</span>
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    支持 JPG、PNG、GIF 格式，单个文件不超过 5MB
                  </p>
                </div>
              </div>

              {/* 图片预览 */}
              {formData.images && formData.images.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {formData.images.map((file, index) => (
                    <div key={index} className="relative">
                      <img
                        src={URL.createObjectURL(file)}
                        alt={`预览 ${index + 1}`}
                        className="w-full h-24 object-cover rounded-lg border"
                      />
                      <button
                        type="button"
                        onClick={() => removeImage(index)}
                        className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600"
                      >
                        ×
                      </button>
                      <div className="text-xs text-gray-500 mt-1 truncate">
                        {file.name}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="text-xs text-gray-500 space-y-1">
                <p>💡 <strong>上传方式：</strong></p>
                <p>• 点击上方按钮选择文件</p>
                <p>• 拖拽图片到虚线框内</p>
                <p>• 复制图片后按 Ctrl+V 粘贴</p>
                <p>• 支持 JPG、PNG、GIF 格式，单个文件不超过 5MB</p>
              </div>
            </div>
          </div>

          {/* 按钮 */}
          <div className="flex justify-end space-x-3">
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              取消
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? '提交中...' : '提交反馈'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default FeedbackForm;
