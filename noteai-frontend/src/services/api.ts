import axios, { AxiosInstance, AxiosResponse } from 'axios';

// API配置
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加认证token
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // 处理401错误（token过期）
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data.data;
          localStorage.setItem('access_token', access_token);

          // 重试原始请求
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // 刷新token失败，清除本地存储并跳转到登录页
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// API响应类型
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// 用户相关API
export const userAPI = {
  // 用户注册
  register: (userData: {
    email: string;
    username: string;
    password: string;
  }): Promise<AxiosResponse<APIResponse>> => {
    return api.post('/api/v1/auth/register', userData);
  },

  // 用户登录
  login: (credentials: {
    email: string;
    password: string;
  }): Promise<AxiosResponse<APIResponse<{
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
  }>>> => {
    return api.post('/api/v1/auth/login', credentials);
  },

  // 获取用户资料
  getProfile: (): Promise<AxiosResponse<APIResponse>> => {
    return api.get('/api/v1/users/profile');
  },

  // 更新用户资料
  updateProfile: (profileData: {
    username?: string;
    avatar_url?: string;
    bio?: string;
    location?: string;
    website?: string;
  }): Promise<AxiosResponse<APIResponse>> => {
    return api.put('/api/v1/users/profile', profileData);
  },

  // 用户登出
  logout: (): Promise<AxiosResponse<APIResponse>> => {
    return api.post('/api/v1/auth/logout');
  },
};

// AI相关API
export const aiAPI = {
  // 文本优化
  optimizeText: (data: {
    text: string;
    optimization_type?: string;
    user_style?: string;
  }): Promise<AxiosResponse<APIResponse<{
    optimized_text: string;
    suggestions: Array<{
      type: string;
      original: string;
      optimized: string;
      explanation: string;
      confidence: number;
    }>;
    confidence: number;
    processing_time: number;
  }>>> => {
    return api.post('/api/v1/ai/optimize-text', data);
  },

  // 内容分类
  classifyContent: (data: {
    content: string;
    existing_categories?: string[];
  }): Promise<AxiosResponse<APIResponse<{
    suggestions: Array<{
      category_name: string;
      confidence: number;
      reasoning: string;
      is_existing: boolean;
    }>;
    detected_topics: string[];
    key_phrases: string[];
    content_type: string;
  }>>> => {
    return api.post('/api/v1/ai/classify-content', data);
  },

  // 获取AI配额
  getQuota: (): Promise<AxiosResponse<APIResponse<{
    plan_type: string;
    daily_limit: number;
    daily_used: number;
    monthly_limit: number;
    monthly_used: number;
    reset_date: string;
  }>>> => {
    return api.get('/api/v1/ai/quota');
  },
};

// 笔记相关API
export const noteAPI = {
  // 创建笔记
  createNote: (noteData: {
    title: string;
    content: string;
    category_id?: string;
    tags?: string[];
    is_public?: boolean;
  }): Promise<AxiosResponse<APIResponse>> => {
    return api.post('/api/v1/notes', noteData);
  },

  // 获取笔记列表
  getNotes: (params?: {
    page?: number;
    limit?: number;
    category_id?: string;
    tags?: string;
    search?: string;
    status?: string;
  }): Promise<AxiosResponse<APIResponse<{
    notes: any[];
    pagination: {
      page: number;
      limit: number;
      total: number;
      total_pages: number;
      has_next: boolean;
      has_prev: boolean;
    };
  }>>> => {
    return api.get('/api/v1/notes', { params });
  },

  // 获取单个笔记
  getNote: (noteId: string): Promise<AxiosResponse<APIResponse>> => {
    return api.get(`/api/v1/notes/${noteId}`);
  },

  // 更新笔记
  updateNote: (noteId: string, noteData: {
    title?: string;
    content?: string;
    category_id?: string;
    tags?: string[];
    status?: string;
    is_public?: boolean;
  }): Promise<AxiosResponse<APIResponse>> => {
    return api.put(`/api/v1/notes/${noteId}`, noteData);
  },

  // 删除笔记
  deleteNote: (noteId: string): Promise<AxiosResponse<APIResponse>> => {
    return api.delete(`/api/v1/notes/${noteId}`);
  },

  // 搜索笔记
  searchNotes: (params: {
    q: string;
    page?: number;
    limit?: number;
  }): Promise<AxiosResponse<APIResponse<{
    results: Array<{
      id: string;
      title: string;
      excerpt: string;
      score: number;
      highlights: string[];
      created_at: string;
      tags: string[];
    }>;
    total: number;
    took: number;
    pagination: any;
  }>>> => {
    return api.get('/api/v1/notes/search', { params });
  },
};

export default api;
