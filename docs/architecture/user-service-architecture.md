# 🔐 用户服务架构设计
## User Service Architecture

**服务名称**: User Service  
**创建日期**: 2025-01-17  
**BMad Master**: AI BMad Master  
**服务职责**: 用户认证、授权、资料管理  

---

## 🎯 服务概述

### 核心职责
- **用户认证**: 注册、登录、第三方登录集成
- **权限管理**: 基于RBAC的权限控制
- **用户资料**: 个人信息管理和设置
- **会话管理**: JWT Token生成和验证

### 业务边界
- ✅ **包含**: 用户身份验证、权限控制、个人资料
- ❌ **不包含**: 笔记内容、AI功能、分享逻辑

---

## 🏗️ 技术架构

### 服务架构图
```
┌─────────────────────────────────────────────────────────┐
│                    User Service                         │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│ │ Auth        │ │ Profile     │ │ Permission          │ │
│ │ Controller  │ │ Controller  │ │ Controller          │ │
│ └─────────────┘ └─────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│ │ Auth        │ │ User        │ │ Permission          │ │
│ │ Service     │ │ Service     │ │ Service             │ │
│ └─────────────┘ └─────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│ │ User        │ │ Session     │ │ Permission          │ │
│ │ Repository  │ │ Repository  │ │ Repository          │ │
│ └─────────────┘ └─────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                   PostgreSQL                            │
└─────────────────────────────────────────────────────────┘
```

### 技术栈
- **框架**: Node.js + Express.js + TypeScript
- **数据库**: PostgreSQL (主数据库)
- **缓存**: Redis (会话缓存)
- **认证**: JWT + bcrypt
- **验证**: Joi/Yup 数据验证
- **第三方**: OAuth 2.0 (微信、GitHub等)

---

## 📊 数据模型设计

### 核心数据表
```sql
-- 用户基础信息表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    bio TEXT,
    phone VARCHAR(20),
    birth_date DATE,
    gender VARCHAR(10),
    location VARCHAR(100),
    website VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verified BOOLEAN DEFAULT false,
    phone_verified BOOLEAN DEFAULT false
);

-- 用户角色表
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_name VARCHAR(50) NOT NULL,
    granted_at TIMESTAMP DEFAULT NOW(),
    granted_by UUID REFERENCES users(id),
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(user_id, role_name)
);

-- 权限表
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 角色权限关联表
CREATE TABLE role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name VARCHAR(50) NOT NULL,
    permission_id UUID NOT NULL REFERENCES permissions(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(role_name, permission_id)
);

-- 用户会话表
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE NOT NULL,
    device_info JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    last_accessed_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- 第三方登录关联表
CREATE TABLE user_oauth_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL, -- 'github', 'wechat', 'google'
    provider_user_id VARCHAR(255) NOT NULL,
    provider_username VARCHAR(255),
    provider_email VARCHAR(255),
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(provider, provider_user_id)
);
```

### 索引策略
```sql
-- 性能优化索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_oauth_provider_user ON user_oauth_accounts(provider, provider_user_id);
```

---

## 🔌 API接口设计

### 认证相关API
```typescript
// POST /api/v1/auth/register
interface RegisterRequest {
  email: string
  username: string
  password: string
  confirmPassword: string
  inviteCode?: string
}

interface RegisterResponse {
  user: UserProfile
  tokens: AuthTokens
  message: string
}

// POST /api/v1/auth/login
interface LoginRequest {
  email: string
  password: string
  rememberMe?: boolean
}

interface LoginResponse {
  user: UserProfile
  tokens: AuthTokens
  sessionInfo: SessionInfo
}

// POST /api/v1/auth/refresh
interface RefreshTokenRequest {
  refreshToken: string
}

interface RefreshTokenResponse {
  tokens: AuthTokens
}

// POST /api/v1/auth/logout
interface LogoutRequest {
  refreshToken: string
}
```

### 用户资料API
```typescript
// GET /api/v1/users/profile
interface GetProfileResponse {
  user: UserProfile
  statistics: UserStatistics
}

// PUT /api/v1/users/profile
interface UpdateProfileRequest {
  username?: string
  bio?: string
  avatar?: File
  phone?: string
  location?: string
  website?: string
}

// POST /api/v1/users/change-password
interface ChangePasswordRequest {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}
```

### 权限管理API
```typescript
// GET /api/v1/users/permissions
interface GetUserPermissionsResponse {
  roles: string[]
  permissions: Permission[]
}

// POST /api/v1/admin/users/{userId}/roles
interface AssignRoleRequest {
  roleName: string
  expiresAt?: Date
}
```

---

## 🔐 安全设计

### 认证安全
```typescript
// JWT配置
const jwtConfig = {
  accessToken: {
    secret: process.env.JWT_ACCESS_SECRET,
    expiresIn: '15m',
    algorithm: 'RS256'
  },
  refreshToken: {
    secret: process.env.JWT_REFRESH_SECRET,
    expiresIn: '7d',
    algorithm: 'RS256'
  }
}

// 密码安全
const passwordConfig = {
  saltRounds: 12,
  minLength: 8,
  requireUppercase: true,
  requireLowercase: true,
  requireNumbers: true,
  requireSpecialChars: true
}
```

### 权限控制
```typescript
// RBAC权限模型
enum Role {
  USER = 'user',
  PREMIUM_USER = 'premium_user',
  MODERATOR = 'moderator',
  ADMIN = 'admin',
  SUPER_ADMIN = 'super_admin'
}

enum Permission {
  // 笔记权限
  NOTE_CREATE = 'note:create',
  NOTE_READ = 'note:read',
  NOTE_UPDATE = 'note:update',
  NOTE_DELETE = 'note:delete',
  
  // AI权限
  AI_OPTIMIZE = 'ai:optimize',
  AI_UNLIMITED = 'ai:unlimited',
  
  // 分享权限
  SHARE_PUBLIC = 'share:public',
  SHARE_CIRCLE = 'share:circle',
  
  // 管理权限
  USER_MANAGE = 'user:manage',
  CONTENT_MODERATE = 'content:moderate'
}
```

### 安全中间件
```typescript
// 认证中间件
export const authenticateToken = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const token = extractTokenFromHeader(req.headers.authorization)
    const decoded = jwt.verify(token, jwtConfig.accessToken.secret)
    req.user = await getUserById(decoded.userId)
    next()
  } catch (error) {
    return res.status(401).json({ error: 'Invalid token' })
  }
}

// 权限检查中间件
export const requirePermission = (permission: Permission) => {
  return async (req: Request, res: Response, next: NextFunction) => {
    const hasPermission = await checkUserPermission(req.user.id, permission)
    if (!hasPermission) {
      return res.status(403).json({ error: 'Insufficient permissions' })
    }
    next()
  }
}
```

---

## 📈 性能优化

### 缓存策略
```typescript
// Redis缓存配置
const cacheConfig = {
  userProfile: {
    key: (userId: string) => `user:profile:${userId}`,
    ttl: 3600 // 1小时
  },
  userPermissions: {
    key: (userId: string) => `user:permissions:${userId}`,
    ttl: 1800 // 30分钟
  },
  sessionData: {
    key: (sessionId: string) => `session:${sessionId}`,
    ttl: 900 // 15分钟
  }
}
```

### 数据库优化
- **连接池**: 最大50个连接，最小5个连接
- **查询优化**: 使用索引，避免N+1查询
- **分页查询**: 使用cursor-based分页
- **读写分离**: 读操作使用只读副本

---

## 🧪 测试策略

### 单元测试
```typescript
// 用户服务测试示例
describe('UserService', () => {
  describe('createUser', () => {
    it('should create user with valid data', async () => {
      const userData = {
        email: 'test@example.com',
        username: 'testuser',
        password: 'SecurePass123!'
      }
      
      const user = await userService.createUser(userData)
      
      expect(user.email).toBe(userData.email)
      expect(user.password_hash).not.toBe(userData.password)
      expect(user.is_active).toBe(true)
    })
    
    it('should throw error for duplicate email', async () => {
      // 测试邮箱重复的情况
    })
  })
})
```

### 集成测试
- API端点测试
- 数据库集成测试
- 第三方服务集成测试
- 权限验证测试

---

## 📊 监控指标

### 业务指标
- **注册转化率**: 访客到注册用户的转化率
- **登录成功率**: 登录尝试的成功率
- **用户活跃度**: DAU/MAU比例
- **权限使用**: 各权限的使用频率

### 技术指标
- **API响应时间**: 平均响应时间 < 200ms
- **数据库查询**: 查询时间 < 100ms
- **缓存命中率**: > 80%
- **错误率**: < 0.1%

---

## 🚀 部署配置

### Docker配置
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3001
CMD ["npm", "start"]
```

### 环境变量
```env
# 数据库配置
DATABASE_URL=postgresql://user:pass@postgres:5432/noteai
REDIS_URL=redis://redis:6379

# JWT配置
JWT_ACCESS_SECRET=your-access-secret
JWT_REFRESH_SECRET=your-refresh-secret

# 第三方登录
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
WECHAT_APP_ID=your-wechat-app-id
WECHAT_APP_SECRET=your-wechat-app-secret
```

---

**服务状态**: ✅ 架构设计完成  
**开发就绪度**: 🚀 95% - 可立即开始开发  
**相关Story**: 所有Story都依赖此服务的用户认证功能
