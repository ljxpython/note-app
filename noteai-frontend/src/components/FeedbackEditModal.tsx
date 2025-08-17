import React, { useState } from 'react';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';

interface Feedback {
  id: string;
  type: string;
  title: string;
  content: string;
  category?: string;
  priority: string;
  status: string;
  rating?: number;
}

interface FeedbackEditModalProps {
  feedback: Feedback;
  onSave: (feedbackId: string, updatedData: any) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

const FeedbackEditModal: React.FC<FeedbackEditModalProps> = ({
  feedback,
  onSave,
  onCancel,
  isSubmitting = false
}) => {
  const [formData, setFormData] = useState({
    title: feedback.title,
    content: feedback.content,
    category: feedback.category || 'other',
    priority: feedback.priority,
    rating: feedback.rating
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

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
      onSave(feedback.id, formData);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // 清除对应字段的错误
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <CardTitle>✏️ 编辑反馈</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
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

            {/* 提示信息 */}
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
              <div className="flex">
                <div className="ml-3">
                  <p className="text-sm text-yellow-700">
                    <strong>注意：</strong> 只能编辑待处理状态的反馈。编辑后需要重新等待管理员处理。
                  </p>
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
                {isSubmitting ? '保存中...' : '保存修改'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default FeedbackEditModal;
