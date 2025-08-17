import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  Sparkles, 
  TrendingUp, 
  Clock,
  Plus,
  Star,
  Tag,
  BarChart3,
  Calendar,
  Zap
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useAuth } from '../contexts/AuthContext';
import { aiAPI, noteAPI } from '../services/api';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalNotes: 0,
    aiUsageToday: 0,
    aiUsageMonth: 0,
    favoriteNotes: 0,
    recentNotes: [] as any[],
    aiQuota: null as any,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // 并行加载数据
      const [notesResponse, quotaResponse] = await Promise.all([
        noteAPI.getNotes({ limit: 5 }),
        aiAPI.getQuota(),
      ]);

      if (notesResponse.data.success && notesResponse.data.data) {
        const { notes, pagination } = notesResponse.data.data;
        setStats(prev => ({
          ...prev,
          totalNotes: pagination.total,
          recentNotes: notes,
          favoriteNotes: notes.filter((note: any) => note.is_favorite).length,
        }));
      }

      if (quotaResponse.data.success && quotaResponse.data.data) {
        const quota = quotaResponse.data.data;
        setStats(prev => ({
          ...prev,
          aiQuota: quota,
          aiUsageToday: quota.daily_used,
          aiUsageMonth: quota.monthly_used,
        }));
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    {
      title: '新建笔记',
      description: '开始创作新的笔记',
      icon: Plus,
      href: '/notes/new',
      color: 'from-blue-600 to-blue-700',
    },
    {
      title: 'AI文本优化',
      description: '使用AI改进您的文本',
      icon: Sparkles,
      href: '/ai-tools?tool=optimize',
      color: 'from-purple-600 to-purple-700',
    },
    {
      title: '内容分类',
      description: 'AI智能分类您的内容',
      icon: Tag,
      href: '/ai-tools?tool=classify',
      color: 'from-green-600 to-green-700',
    },
    {
      title: '查看所有笔记',
      description: '浏览您的笔记库',
      icon: FileText,
      href: '/notes',
      color: 'from-orange-600 to-orange-700',
    },
  ];

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 欢迎标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            欢迎回来，{user?.username}！
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            今天是 {new Date().toLocaleDateString('zh-CN', { 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric',
              weekday: 'long'
            })}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Calendar className="h-5 w-5 text-gray-400" />
          <span className="text-sm text-gray-500">
            {new Date().toLocaleDateString('zh-CN')}
          </span>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总笔记数</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalNotes}</div>
            <p className="text-xs text-muted-foreground">
              +2 较上周
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">今日AI使用</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.aiUsageToday}</div>
            <p className="text-xs text-muted-foreground">
              剩余 {stats.aiQuota?.daily_limit - stats.aiUsageToday || 0} 次
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">收藏笔记</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.favoriteNotes}</div>
            <p className="text-xs text-muted-foreground">
              精选内容
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">本月活跃度</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">85%</div>
            <p className="text-xs text-muted-foreground">
              +12% 较上月
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 快速操作 */}
      <div>
        <h2 className="text-xl font-semibold mb-4">快速操作</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action, index) => (
            <Link key={index} to={action.href}>
              <Card className="hover:shadow-lg transition-all duration-200 hover:-translate-y-1 cursor-pointer">
                <CardContent className="p-6">
                  <div className={`inline-flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-r ${action.color} mb-4`}>
                    <action.icon className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="font-semibold mb-2">{action.title}</h3>
                  <p className="text-sm text-muted-foreground">{action.description}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* 最近笔记和AI配额 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 最近笔记 */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Clock className="h-5 w-5 mr-2" />
              最近笔记
            </CardTitle>
            <CardDescription>
              您最近创建或编辑的笔记
            </CardDescription>
          </CardHeader>
          <CardContent>
            {stats.recentNotes.length > 0 ? (
              <div className="space-y-4">
                {stats.recentNotes.map((note: any) => (
                  <Link
                    key={note.id}
                    to={`/notes/${note.id}`}
                    className="block p-4 rounded-lg border hover:bg-accent transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium mb-1">{note.title}</h4>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {note.excerpt}
                        </p>
                        <div className="flex items-center mt-2 space-x-4 text-xs text-muted-foreground">
                          <span>{note.word_count} 字</span>
                          <span>{note.reading_time} 分钟阅读</span>
                          <span>{new Date(note.updated_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      {note.is_favorite && (
                        <Star className="h-4 w-4 text-yellow-500 fill-current" />
                      )}
                    </div>
                  </Link>
                ))}
                <div className="pt-4 border-t">
                  <Link to="/notes">
                    <Button variant="outline" className="w-full">
                      查看所有笔记
                    </Button>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground mb-4">还没有笔记</p>
                <Link to="/notes/new">
                  <Button>创建第一篇笔记</Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>

        {/* AI配额信息 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Sparkles className="h-5 w-5 mr-2" />
              AI 配额
            </CardTitle>
            <CardDescription>
              您的AI使用情况
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {stats.aiQuota && (
              <>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>今日使用</span>
                    <span>{stats.aiQuota.daily_used}/{stats.aiQuota.daily_limit}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full" 
                      style={{ 
                        width: `${(stats.aiQuota.daily_used / stats.aiQuota.daily_limit) * 100}%` 
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>本月使用</span>
                    <span>{stats.aiQuota.monthly_used}/{stats.aiQuota.monthly_limit}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-green-600 to-blue-600 h-2 rounded-full" 
                      style={{ 
                        width: `${(stats.aiQuota.monthly_used / stats.aiQuota.monthly_limit) * 100}%` 
                      }}
                    />
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <p className="text-xs text-muted-foreground mb-3">
                    计划类型: {stats.aiQuota.plan_type === 'free' ? '免费版' : '高级版'}
                  </p>
                  <Link to="/ai-tools">
                    <Button variant="gradient" className="w-full">
                      使用AI工具
                    </Button>
                  </Link>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
