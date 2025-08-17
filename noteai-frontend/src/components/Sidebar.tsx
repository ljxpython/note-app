import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Home,
  FileText,
  Sparkles,
  User,
  Settings,
  Plus,
  Search,
  Tag,
  Star,
  Archive,
  X,
  MessageSquare
} from 'lucide-react';
import { cn } from '../utils/cn';
import { Button } from './ui/Button';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const navigation = [
  { name: '仪表板', href: '/dashboard', icon: Home },
  { name: '我的笔记', href: '/notes', icon: FileText },
  { name: 'AI工具', href: '/ai-tools', icon: Sparkles },
  { name: '用户反馈', href: '/feedback', icon: MessageSquare },
  { name: '个人资料', href: '/profile', icon: User },
  { name: '设置', href: '/settings', icon: Settings },
];

const quickActions = [
  { name: '新建笔记', href: '/notes/new', icon: Plus, variant: 'gradient' as const },
  { name: '搜索笔记', href: '/notes?search=true', icon: Search, variant: 'ghost' as const },
];

const categories = [
  { name: '收藏夹', href: '/notes?filter=favorites', icon: Star, count: 12 },
  { name: '标签', href: '/notes?filter=tags', icon: Tag, count: 8 },
  { name: '归档', href: '/notes?filter=archived', icon: Archive, count: 24 },
];

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const location = useLocation();

  return (
    <>
      {/* 桌面端侧边栏 */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col">
        <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 px-6 pb-4">
          <div className="flex h-16 shrink-0 items-center">
            <div className="flex items-center space-x-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-r from-blue-600 to-purple-600">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold gradient-text">NoteAI</span>
            </div>
          </div>
          
          <SidebarContent location={location} />
        </div>
      </div>

      {/* 移动端侧边栏 */}
      <div className={cn(
        "fixed inset-y-0 z-50 flex w-64 flex-col transition-transform duration-300 ease-in-out lg:hidden",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 px-6 pb-4">
          <div className="flex h-16 shrink-0 items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-r from-blue-600 to-purple-600">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold gradient-text">NoteAI</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="lg:hidden"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
          
          <SidebarContent location={location} />
        </div>
      </div>
    </>
  );
};

const SidebarContent: React.FC<{ location: any }> = ({ location }) => {
  return (
    <nav className="flex flex-1 flex-col">
      <ul role="list" className="flex flex-1 flex-col gap-y-7">
        {/* 快速操作 */}
        <li>
          <div className="space-y-2">
            {quickActions.map((item) => (
              <Link key={item.name} to={item.href}>
                <Button
                  variant={item.variant}
                  className="w-full justify-start"
                  leftIcon={<item.icon className="h-4 w-4" />}
                >
                  {item.name}
                </Button>
              </Link>
            ))}
          </div>
        </li>

        {/* 主导航 */}
        <li>
          <ul role="list" className="-mx-2 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href || 
                (item.href !== '/dashboard' && location.pathname.startsWith(item.href));
              
              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={cn(
                      'group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold transition-colors',
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                    )}
                  >
                    <item.icon
                      className={cn(
                        'h-5 w-5 shrink-0',
                        isActive ? 'text-primary-foreground' : 'text-muted-foreground group-hover:text-foreground'
                      )}
                    />
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>
        </li>

        {/* 分类和过滤器 */}
        <li>
          <div className="text-xs font-semibold leading-6 text-muted-foreground">
            分类
          </div>
          <ul role="list" className="-mx-2 mt-2 space-y-1">
            {categories.map((item) => (
              <li key={item.name}>
                <Link
                  to={item.href}
                  className="group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold text-muted-foreground hover:text-foreground hover:bg-accent"
                >
                  <item.icon className="h-4 w-4 shrink-0" />
                  <span className="flex-1">{item.name}</span>
                  {item.count && (
                    <span className="ml-auto w-6 h-5 text-center text-xs bg-muted text-muted-foreground rounded-full">
                      {item.count}
                    </span>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        </li>

        {/* 底部空间 */}
        <li className="mt-auto">
          <div className="rounded-lg bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950 p-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <Sparkles className="h-6 w-6 text-blue-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  AI 配额
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  今日已用 15/50
                </p>
              </div>
            </div>
            <div className="mt-3">
              <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full" 
                  style={{ width: '30%' }}
                />
              </div>
            </div>
          </div>
        </li>
      </ul>
    </nav>
  );
};

export default Sidebar;
