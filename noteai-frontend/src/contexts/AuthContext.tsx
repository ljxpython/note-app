import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { User, AuthTokens } from '../types';
import { userAPI } from '../services/api';

// 认证状态类型
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

// 认证动作类型
type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: User }
  | { type: 'AUTH_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'CLEAR_ERROR' }
  | { type: 'UPDATE_USER'; payload: Partial<User> };

// 认证上下文类型
interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
  updateProfile: (profileData: Partial<User>) => Promise<void>;
  clearError: () => void;
}

// 初始状态
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  loading: true,
  error: null,
};

// 认证reducer
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        loading: true,
        error: null,
      };
    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        loading: false,
        error: null,
      };
    case 'AUTH_FAILURE':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        loading: false,
        error: action.payload,
      };
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        loading: false,
        error: null,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    case 'UPDATE_USER':
      return {
        ...state,
        user: state.user ? { ...state.user, ...action.payload } : null,
      };
    default:
      return state;
  }
};

// 创建上下文
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// 认证提供者组件
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // 检查本地存储的token并验证用户
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');

      if (!token) {
        // 没有token时，不设置错误状态，保持初始状态
        dispatch({ type: 'LOGOUT' });
        return;
      }

      try {
        dispatch({ type: 'AUTH_START' });
        const response = await userAPI.getProfile();

        if (response.data.success && response.data.data) {
          dispatch({ type: 'AUTH_SUCCESS', payload: response.data.data });
        } else {
          throw new Error('Failed to get user profile');
        }
      } catch (error: any) {
        // 只有在token验证失败时才清除并显示错误
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        dispatch({ type: 'AUTH_FAILURE', payload: 'Session expired, please login again' });
      }
    };

    checkAuth();
  }, []);

  // 登录函数
  const login = async (email: string, password: string): Promise<void> => {
    try {
      dispatch({ type: 'AUTH_START' });
      
      const response = await userAPI.login({ email, password });
      
      if (response.data.success && response.data.data) {
        const { access_token, refresh_token } = response.data.data;
        
        // 存储tokens
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        
        // 获取用户信息
        const profileResponse = await userAPI.getProfile();
        
        if (profileResponse.data.success && profileResponse.data.data) {
          dispatch({ type: 'AUTH_SUCCESS', payload: profileResponse.data.data });
        } else {
          throw new Error('Failed to get user profile after login');
        }
      } else {
        throw new Error(response.data.message || 'Login failed');
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || error.message || 'Login failed';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw new Error(errorMessage);
    }
  };

  // 注册函数
  const register = async (email: string, username: string, password: string): Promise<void> => {
    try {
      dispatch({ type: 'AUTH_START' });
      
      const response = await userAPI.register({ email, username, password });
      
      if (response.data.success) {
        // 注册成功后自动登录
        await login(email, password);
      } else {
        throw new Error(response.data.message || 'Registration failed');
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || error.message || 'Registration failed';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw new Error(errorMessage);
    }
  };

  // 登出函数
  const logout = (): void => {
    try {
      // 调用后端登出API（可选）
      userAPI.logout().catch(() => {
        // 忽略登出API错误
      });
    } catch (error) {
      // 忽略错误
    } finally {
      // 清除本地存储
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      // 更新状态
      dispatch({ type: 'LOGOUT' });
    }
  };

  // 更新用户资料
  const updateProfile = async (profileData: Partial<User>): Promise<void> => {
    try {
      const response = await userAPI.updateProfile(profileData);
      
      if (response.data.success && response.data.data) {
        dispatch({ type: 'UPDATE_USER', payload: response.data.data });
      } else {
        throw new Error(response.data.message || 'Profile update failed');
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || error.message || 'Profile update failed';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw new Error(errorMessage);
    }
  };

  // 清除错误
  const clearError = (): void => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    updateProfile,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// 使用认证上下文的Hook
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};
