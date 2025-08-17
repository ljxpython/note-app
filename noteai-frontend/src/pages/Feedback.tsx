import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import FeedbackForm from '../components/FeedbackForm';
import FeedbackList from '../components/FeedbackList';
import FeedbackEditModal from '../components/FeedbackEditModal';
import { useAuth } from '../contexts/AuthContext';

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

const FeedbackPage: React.FC = () => {
  const { user } = useAuth();
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [selectedFeedback, setSelectedFeedback] = useState<Feedback | null>(null);
  const [editingFeedback, setEditingFeedback] = useState<Feedback | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // 获取我的反馈列表
  const fetchMyFeedback = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/v1/feedback/my', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setFeedbacks(data.data.feedback || []);
      } else {
        console.error('获取反馈列表失败');
      }
    } catch (error) {
      console.error('获取反馈列表错误:', error);
    } finally {
      setLoading(false);
    }
  };

  // 提交反馈
  const handleSubmitFeedback = async (feedbackData: FeedbackData) => {
    try {
      setSubmitting(true);
      const token = localStorage.getItem('access_token');

      // 如果有图片，使用FormData
      if (feedbackData.images && feedbackData.images.length > 0) {
        const formData = new FormData();

        // 添加文本字段
        formData.append('type', feedbackData.type);
        formData.append('title', feedbackData.title);
        formData.append('content', feedbackData.content);
        if (feedbackData.category) formData.append('category', feedbackData.category);
        if (feedbackData.priority) formData.append('priority', feedbackData.priority);
        if (feedbackData.rating) formData.append('rating', feedbackData.rating.toString());
        if (feedbackData.page_url) formData.append('page_url', feedbackData.page_url);
        if (feedbackData.browser_info) formData.append('browser_info', JSON.stringify(feedbackData.browser_info));
        if (feedbackData.device_info) formData.append('device_info', JSON.stringify(feedbackData.device_info));

        // 添加图片文件
        feedbackData.images.forEach((file, index) => {
          formData.append(`images`, file);
        });

        const response = await fetch('http://localhost:8000/api/v1/feedback', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
            // 不设置Content-Type，让浏览器自动设置multipart/form-data
          },
          body: formData
        });

        if (response.ok) {
          const data = await response.json();
          console.log('反馈提交成功:', data);
          setShowForm(false);
          fetchMyFeedback();
          alert('反馈提交成功！感谢您的宝贵意见。');
        } else {
          const errorData = await response.json();
          console.error('反馈提交失败:', errorData);
          alert('反馈提交失败，请稍后重试。');
        }
      } else {
        // 没有图片，使用JSON
        const response = await fetch('http://localhost:8000/api/v1/feedback', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(feedbackData)
        });

        if (response.ok) {
          const data = await response.json();
          console.log('反馈提交成功:', data);
          setShowForm(false);
          fetchMyFeedback(); // 刷新列表

          // 显示成功消息
          alert('反馈提交成功！感谢您的宝贵意见。');
        } else {
          const errorData = await response.json();
          console.error('反馈提交失败:', errorData);
          alert('反馈提交失败，请稍后重试。');
        }
      }
    } catch (error) {
      console.error('反馈提交错误:', error);
      alert('反馈提交失败，请检查网络连接。');
    } finally {
      setSubmitting(false);
    }
  };

  // 查看反馈详情
  const handleViewDetail = async (feedback: Feedback) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/feedback/${feedback.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedFeedback(data.data);
      } else {
        console.error('获取反馈详情失败');
      }
    } catch (error) {
      console.error('获取反馈详情错误:', error);
    }
  };

  // 编辑反馈
  const handleEditFeedback = (feedback: Feedback) => {
    setEditingFeedback(feedback);
  };

  // 保存编辑
  const handleSaveEdit = async (feedbackId: string, updatedData: any) => {
    try {
      setIsEditing(true);
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/feedback/${feedbackId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updatedData)
      });

      if (response.ok) {
        const data = await response.json();
        console.log('反馈更新成功:', data);
        setEditingFeedback(null);
        fetchMyFeedback(); // 刷新列表
        alert('反馈更新成功！');
      } else {
        const errorData = await response.json();
        console.error('反馈更新失败:', errorData);
        alert('反馈更新失败，请稍后重试。');
      }
    } catch (error) {
      console.error('反馈更新错误:', error);
      alert('反馈更新失败，请检查网络连接。');
    } finally {
      setIsEditing(false);
    }
  };

  // 删除反馈
  const handleDeleteFeedback = async (feedback: Feedback) => {
    if (!window.confirm(`确定要删除反馈"${feedback.title}"吗？此操作不可撤销。`)) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/feedback/${feedback.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('反馈删除成功:', data);
        fetchMyFeedback(); // 刷新列表
        alert('反馈删除成功！');
      } else {
        const errorData = await response.json();
        console.error('反馈删除失败:', errorData);
        alert('反馈删除失败，请稍后重试。');
      }
    } catch (error) {
      console.error('反馈删除错误:', error);
      alert('反馈删除失败，请检查网络连接。');
    }
  };

  useEffect(() => {
    fetchMyFeedback();
  }, []);

  // 反馈详情模态框
  const FeedbackDetailModal: React.FC<{ feedback: Feedback; onClose: () => void }> = ({ feedback, onClose }) => {
    const formatDate = (dateString: string) => {
      return new Date(dateString).toLocaleString('zh-CN');
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="flex items-center space-x-2">
                  <span>{feedback.type === 'bug' ? '🐛' : feedback.type === 'feature' ? '✨' : feedback.type === 'improvement' ? '🔧' : '💬'}</span>
                  <span>{feedback.title}</span>
                </CardTitle>
                <div className="flex items-center space-x-2 mt-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    feedback.status === 'open' ? 'bg-blue-100 text-blue-800' :
                    feedback.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                    feedback.status === 'resolved' ? 'bg-green-100 text-green-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {feedback.status === 'open' ? '待处理' :
                     feedback.status === 'in_progress' ? '处理中' :
                     feedback.status === 'resolved' ? '已解决' : '已关闭'}
                  </span>
                  <span className="text-sm text-gray-500">
                    优先级: {feedback.priority}
                  </span>
                  {feedback.rating && (
                    <span className="text-sm text-gray-500">
                      评分: {'⭐'.repeat(feedback.rating)}
                    </span>
                  )}
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={onClose}>
                ✕
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">反馈内容</h4>
              <p className="text-gray-700 whitespace-pre-wrap">{feedback.content}</p>
            </div>

            {/* 图片展示 */}
            {feedback.images && feedback.images.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">相关图片</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {feedback.images.map((image) => (
                    <div key={image.id} className="relative group">
                      <img
                        src={`http://localhost:8000${image.url}`}
                        alt={image.filename}
                        className="w-full h-32 object-cover rounded-lg border cursor-pointer hover:opacity-80 transition-opacity"
                        onClick={() => window.open(`http://localhost:8000${image.url}`, '_blank')}
                        onError={(e) => {
                          // 如果图片加载失败，显示占位符
                          e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTI4IiBoZWlnaHQ9IjEyOCIgdmlld0JveD0iMCAwIDEyOCAxMjgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMjgiIGhlaWdodD0iMTI4IiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0zMiAzMkg5NlY5NkgzMlYzMloiIHN0cm9rZT0iIzlDQTNBRiIgc3Ryb2tlLXdpZHRoPSIyIiBmaWxsPSJub25lIi8+CjxjaXJjbGUgY3g9IjQ4IiBjeT0iNDgiIHI9IjYiIGZpbGw9IiM5Q0EzQUYiLz4KPHBhdGggZD0iTTMyIDcyTDQ4IDU2TDY0IDcyTDk2IDQwVjk2SDMyVjcyWiIgZmlsbD0iIzlDQTNBRiIvPgo8L3N2Zz4K';
                        }}
                      />
                      <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs p-2 rounded-b-lg opacity-0 group-hover:opacity-100 transition-opacity">
                        <p className="truncate">{image.filename}</p>
                        <p>{(image.size / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  💡 点击图片可在新窗口中查看大图
                </p>
              </div>
            )}

            {feedback.admin_response && (
              <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
                <h4 className="font-medium text-blue-900 mb-2">管理员回复</h4>
                <p className="text-blue-800 whitespace-pre-wrap">{feedback.admin_response}</p>
              </div>
            )}

            <div className="border-t pt-4">
              <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                <div>
                  <strong>创建时间:</strong> {formatDate(feedback.created_at)}
                </div>
                <div>
                  <strong>更新时间:</strong> {formatDate(feedback.updated_at)}
                </div>
                {feedback.resolved_at && (
                  <div className="col-span-2">
                    <strong>解决时间:</strong> {formatDate(feedback.resolved_at)}
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* 页面标题 */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">用户反馈</h1>
            <p className="text-gray-600 mt-2">提交问题报告、功能建议或一般反馈</p>
          </div>
          <Button onClick={() => setShowForm(true)}>
            📝 提交反馈
          </Button>
        </div>

        {/* 反馈表单 */}
        {showForm && (
          <div className="mb-8">
            <FeedbackForm
              onSubmit={handleSubmitFeedback}
              onCancel={() => setShowForm(false)}
              isSubmitting={submitting}
            />
          </div>
        )}

        {/* 反馈统计 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-blue-600">
                {feedbacks.length}
              </div>
              <div className="text-sm text-gray-600">总反馈数</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {feedbacks.filter(f => f.status === 'open').length}
              </div>
              <div className="text-sm text-gray-600">待处理</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-orange-600">
                {feedbacks.filter(f => f.status === 'in_progress').length}
              </div>
              <div className="text-sm text-gray-600">处理中</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-green-600">
                {feedbacks.filter(f => f.status === 'resolved').length}
              </div>
              <div className="text-sm text-gray-600">已解决</div>
            </CardContent>
          </Card>
        </div>

        {/* 反馈列表 */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">我的反馈</h2>
          <FeedbackList
            feedbacks={feedbacks}
            onViewDetail={handleViewDetail}
            onEdit={handleEditFeedback}
            onDelete={handleDeleteFeedback}
            loading={loading}
          />
        </div>

        {/* 反馈详情模态框 */}
        {selectedFeedback && (
          <FeedbackDetailModal
            feedback={selectedFeedback}
            onClose={() => setSelectedFeedback(null)}
          />
        )}

        {/* 反馈编辑模态框 */}
        {editingFeedback && (
          <FeedbackEditModal
            feedback={editingFeedback}
            onSave={handleSaveEdit}
            onCancel={() => setEditingFeedback(null)}
            isSubmitting={isEditing}
          />
        )}
      </div>
    </div>
  );
};

export default FeedbackPage;
