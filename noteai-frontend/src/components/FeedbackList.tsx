import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Button } from './ui/Button';

interface FeedbackImage {
  id: string;
  filename: string;
  url: string;
  size: number;
  type: string;
}

interface Feedback {
  id: string;
  type: string;
  title: string;
  content: string;
  category?: string;
  priority: string;
  status: string;
  rating?: number;
  admin_response?: string;
  images?: FeedbackImage[];
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  user?: {
    id: string;
    username: string;
    email: string;
  };
}

interface FeedbackListProps {
  feedbacks: Feedback[];
  onViewDetail: (feedback: Feedback) => void;
  onRespond?: (feedback: Feedback) => void;
  onEdit?: (feedback: Feedback) => void;
  onDelete?: (feedback: Feedback) => void;
  isAdmin?: boolean;
  loading?: boolean;
}

const FeedbackList: React.FC<FeedbackListProps> = ({
  feedbacks,
  onViewDetail,
  onRespond,
  onEdit,
  onDelete,
  isAdmin = false,
  loading = false
}) => {
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'bug': return '🐛';
      case 'feature': return '✨';
      case 'improvement': return '🔧';
      case 'general': return '💬';
      default: return '📝';
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'bug': return 'Bug报告';
      case 'feature': return '功能建议';
      case 'improvement': return '改进建议';
      case 'general': return '一般反馈';
      default: return '其他';
    }
  };

  const getCategoryIcon = (category?: string) => {
    switch (category) {
      case 'ui': return '🎨';
      case 'performance': return '⚡';
      case 'ai': return '🤖';
      case 'auth': return '🔐';
      default: return '📝';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'text-blue-600 bg-blue-50';
      case 'in_progress': return 'text-yellow-600 bg-yellow-50';
      case 'resolved': return 'text-green-600 bg-green-50';
      case 'closed': return 'text-gray-600 bg-gray-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'open': return '待处理';
      case 'in_progress': return '处理中';
      case 'resolved': return '已解决';
      case 'closed': return '已关闭';
      default: return status;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const StarDisplay: React.FC<{ rating?: number }> = ({ rating }) => {
    if (!rating) return null;
    
    return (
      <div className="flex items-center space-x-1">
        <span className="text-sm text-gray-600">评分:</span>
        <div className="flex">
          {[1, 2, 3, 4, 5].map((star) => (
            <span
              key={star}
              className={`text-sm ${star <= rating ? 'text-yellow-400' : 'text-gray-300'}`}
            >
              ⭐
            </span>
          ))}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-6">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-2/3"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (feedbacks.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="text-gray-400 text-6xl mb-4">📝</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">暂无反馈</h3>
          <p className="text-gray-600">还没有任何反馈记录</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {feedbacks.map((feedback) => (
        <Card key={feedback.id} className="hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                {/* 标题和类型 */}
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-lg">{getTypeIcon(feedback.type)}</span>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {feedback.title}
                  </h3>
                  <span className="text-sm text-gray-500">
                    {getTypeLabel(feedback.type)}
                  </span>
                </div>

                {/* 内容预览 */}
                <p className="text-gray-600 mb-3 line-clamp-2">
                  {feedback.content}
                </p>

                {/* 标签和信息 */}
                <div className="flex flex-wrap items-center gap-2 mb-3">
                  {/* 分类 */}
                  {feedback.category && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {getCategoryIcon(feedback.category)} {feedback.category}
                    </span>
                  )}

                  {/* 优先级 */}
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(feedback.priority)}`}>
                    {feedback.priority}
                  </span>

                  {/* 状态 */}
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(feedback.status)}`}>
                    {getStatusLabel(feedback.status)}
                  </span>

                  {/* 评分 */}
                  <StarDisplay rating={feedback.rating} />
                </div>

                {/* 用户信息（管理员视图） */}
                {isAdmin && feedback.user && (
                  <div className="text-sm text-gray-500 mb-2">
                    👤 {feedback.user.username} ({feedback.user.email})
                  </div>
                )}

                {/* 图片预览 */}
                {feedback.images && feedback.images.length > 0 && (
                  <div className="mb-3">
                    <div className="flex flex-wrap gap-2">
                      {feedback.images.slice(0, 3).map((image, index) => (
                        <div key={image.id} className="relative">
                          <img
                            src={`http://localhost:8000${image.url}`}
                            alt={image.filename}
                            className="w-16 h-16 object-cover rounded-lg border"
                            onError={(e) => {
                              // 如果图片加载失败，显示占位符
                              e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0yMCAyMEg0NFY0NEgyMFYyMFoiIHN0cm9rZT0iIzlDQTNBRiIgc3Ryb2tlLXdpZHRoPSIyIiBmaWxsPSJub25lIi8+CjxjaXJjbGUgY3g9IjI4IiBjeT0iMjgiIHI9IjMiIGZpbGw9IiM5Q0EzQUYiLz4KPHBhdGggZD0iTTIwIDM2TDI4IDI4TDM2IDM2TDQ0IDI4VjQ0SDIwVjM2WiIgZmlsbD0iIzlDQTNBRiIvPgo8L3N2Zz4K';
                            }}
                          />
                          {feedback.images && feedback.images.length > 3 && index === 2 && (
                            <div className="absolute inset-0 bg-black bg-opacity-50 rounded-lg flex items-center justify-center">
                              <span className="text-white text-xs font-medium">
                                +{feedback.images.length - 3}
                              </span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      📎 {feedback.images.length} 张图片
                    </p>
                  </div>
                )}

                {/* 管理员回复预览 */}
                {feedback.admin_response && (
                  <div className="bg-blue-50 border-l-4 border-blue-400 p-3 mb-3">
                    <p className="text-sm text-blue-800">
                      <strong>管理员回复:</strong> {feedback.admin_response.substring(0, 100)}
                      {feedback.admin_response.length > 100 && '...'}
                    </p>
                  </div>
                )}

                {/* 时间信息 */}
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>📅 创建: {formatDate(feedback.created_at)}</span>
                  {feedback.resolved_at && (
                    <span>✅ 解决: {formatDate(feedback.resolved_at)}</span>
                  )}
                </div>
              </div>

              {/* 操作按钮 */}
              <div className="flex flex-col space-y-2 ml-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onViewDetail(feedback)}
                >
                  查看详情
                </Button>

                {/* 用户编辑和删除按钮 */}
                {!isAdmin && feedback.status === 'open' && onEdit && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onEdit(feedback)}
                  >
                    ✏️ 编辑
                  </Button>
                )}

                {!isAdmin && feedback.status === 'open' && onDelete && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onDelete(feedback)}
                    className="text-red-600 hover:text-red-700 hover:border-red-300"
                  >
                    🗑️ 删除
                  </Button>
                )}

                {/* 管理员回复按钮 */}
                {isAdmin && onRespond && feedback.status !== 'resolved' && feedback.status !== 'closed' && (
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => onRespond(feedback)}
                  >
                    回复
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default FeedbackList;
