// 用户相关类型
export interface User {
  id: string;
  email: string;
  username: string;
  avatar_url?: string;
  bio?: string;
  location?: string;
  website?: string;
  role: 'user' | 'premium_user' | 'moderator' | 'admin' | 'super_admin';
  status: 'active' | 'inactive' | 'suspended' | 'deleted';
  is_verified: boolean;
  email_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// 笔记相关类型
export interface Note {
  id: string;
  user_id: string;
  title: string;
  content: string;
  content_html: string;
  excerpt: string;
  word_count: number;
  reading_time: number;
  category_id?: string;
  tags: string[];
  status: 'draft' | 'published' | 'archived' | 'deleted';
  is_public: boolean;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
}

export interface NoteCreate {
  title: string;
  content: string;
  category_id?: string;
  tags?: string[];
  is_public?: boolean;
}

export interface NoteUpdate {
  title?: string;
  content?: string;
  category_id?: string;
  tags?: string[];
  status?: string;
  is_public?: boolean;
}

// 分类相关类型
export interface Category {
  id: string;
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  parent_id?: string;
  user_id: string;
  notes_count: number;
  created_at: string;
  updated_at: string;
}

// AI相关类型
export interface OptimizationSuggestion {
  type: 'grammar' | 'expression' | 'structure';
  original: string;
  optimized: string;
  explanation: string;
  confidence: number;
  position?: {
    start: number;
    end: number;
  };
}

export interface OptimizationResult {
  optimized_text: string;
  suggestions: OptimizationSuggestion[];
  confidence: number;
  processing_time: number;
  optimization_type: string;
  original_length: number;
  optimized_length: number;
}

export interface ClassificationSuggestion {
  category_name: string;
  confidence: number;
  reasoning: string;
  is_existing: boolean;
}

export interface ClassificationResult {
  suggestions: ClassificationSuggestion[];
  detected_topics: string[];
  key_phrases: string[];
  content_type: string;
  processing_time: number;
  content_length: number;
}

export interface AIQuota {
  plan_type: string;
  daily_limit: number;
  daily_used: number;
  daily_remaining: number;
  monthly_limit: number;
  monthly_used: number;
  monthly_remaining: number;
  reset_date: string;
}

// 搜索相关类型
export interface SearchResult {
  id: string;
  title: string;
  excerpt: string;
  score: number;
  highlights: string[];
  created_at: string;
  tags: string[];
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  took: number;
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// 分页相关类型
export interface PaginationParams {
  page: number;
  limit: number;
}

export interface PaginationResponse {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// 表单相关类型
export interface LoginForm {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterForm {
  email: string;
  username: string;
  password: string;
  confirm_password: string;
}

export interface ProfileForm {
  username: string;
  bio?: string;
  location?: string;
  website?: string;
}

// 应用状态类型
export interface AppState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

export interface NotesState {
  notes: Note[];
  currentNote: Note | null;
  categories: Category[];
  loading: boolean;
  error: string | null;
  pagination: PaginationResponse | null;
}

export interface AIState {
  quota: AIQuota | null;
  optimizing: boolean;
  classifying: boolean;
  lastOptimization: OptimizationResult | null;
  lastClassification: ClassificationResult | null;
  error: string | null;
}

// 主题相关类型
export type Theme = 'light' | 'dark' | 'system';

// 通知相关类型
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// 路由相关类型
export interface RouteConfig {
  path: string;
  component: React.ComponentType;
  exact?: boolean;
  protected?: boolean;
  title?: string;
}

// 菜单相关类型
export interface MenuItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  path?: string;
  children?: MenuItem[];
  badge?: string | number;
  disabled?: boolean;
}

// 设置相关类型
export interface UserSettings {
  theme: Theme;
  language: string;
  timezone: string;
  email_notifications: boolean;
  push_notifications: boolean;
  marketing_emails: boolean;
  auto_save: boolean;
  auto_save_interval: number;
  default_note_visibility: 'private' | 'public';
  editor_font_size: number;
  editor_theme: 'light' | 'dark';
}
