# 🏗️ 系统架构设计文档
## NoteAI - AI驱动笔记分享平台

**文档版本**: v1.0  
**创建日期**: 2025-01-17  
**架构师**: AI Architect  
**最后更新**: 2025-01-17  

---

## 📋 架构概览

### 整体架构模式
采用**微服务架构 + 前后端分离**的设计模式，确保系统的可扩展性和维护性。

### 核心架构图
```
前端层: Web应用(React) + 移动端(React Native) + 管理后台(Vue.js)
    ↓
网关层: API Gateway(Kong) + 负载均衡(Nginx)
    ↓
服务层: 用户服务 + 笔记服务 + AI服务 + 分享服务 + 社区服务
    ↓
数据层: PostgreSQL + MongoDB + Redis + Elasticsearch
    ↓
外部服务: DeepSeek API + OSS存储 + CDN
```

---

## 🔧 技术栈选择

### 前端技术栈
- **Web端**: React 18 + TypeScript + Vite + Tailwind CSS
- **移动端**: React Native + Expo (未来扩展)
- **状态管理**: Zustand + React Query
- **UI组件库**: Ant Design + 自定义组件

### 后端技术栈
- **API框架**: Node.js + Express.js + TypeScript
- **数据库**: PostgreSQL (主库) + MongoDB (文档存储) + Redis (缓存)
- **搜索引擎**: Elasticsearch
- **消息队列**: Redis + Bull Queue
- **API网关**: Kong Gateway

### 基础设施
- **容器化**: Docker + Docker Compose
- **编排**: Kubernetes (生产环境)
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack
- **CI/CD**: GitHub Actions

---

## 🏛️ 核心服务架构

### 1. 用户服务 (User Service)
**职责**: 用户注册、登录、认证、权限控制

**核心功能**:
- 用户注册/登录 (邮箱、第三方登录)
- JWT Token认证
- 基于RBAC的权限管理
- 用户资料管理

**数据模型**:
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    bio TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false
);
```

### 2. 笔记服务 (Note Service)
**职责**: 笔记CRUD、版本控制、自动保存

**核心功能**:
- 笔记创建/编辑/删除
- Markdown编辑器支持
- 版本历史管理
- 自动保存机制
- 文件上传管理

**数据模型** (MongoDB):
```javascript
const noteSchema = {
  _id: ObjectId,
  userId: String,
  title: String,
  content: String, // Markdown格式
  contentHtml: String, // 渲染后的HTML
  tags: [String],
  category: String,
  isPublic: Boolean,
  shareSettings: {
    isPublic: Boolean,
    allowComments: Boolean,
    shareUrl: String,
    circles: [String]
  },
  metadata: {
    wordCount: Number,
    readingTime: Number,
    lastEditedAt: Date,
    aiOptimizedAt: Date
  },
  versions: [{
    versionId: String,
    content: String,
    createdAt: Date,
    changeDescription: String
  }],
  createdAt: Date,
  updatedAt: Date
}
```

### 3. AI服务 (AI Service)
**职责**: DeepSeek API集成、内容优化、自动分类

**核心功能**:
- 文本语法和表达优化
- 内容结构建议
- 智能分类和标签生成
- 多轮对话交互
- 写作风格学习

**API集成**:
- DeepSeek API调用
- 请求限流和配额管理
- 降级策略和错误处理
- 响应缓存优化

### 4. 分享服务 (Share Service)
**职责**: 分享链接生成、权限控制、访问统计

**核心功能**:
- 分享链接生成和管理
- 多级权限控制 (公开/链接/圈子/私人)
- 访问统计和分析
- SEO优化

### 5. 社区服务 (Community Service)
**职责**: 社交功能、内容推荐、评论系统

**核心功能**:
- 关注/粉丝系统
- 评论和回复
- 点赞和收藏
- 圈子创建和管理
- 内容推荐算法

---

## 🗄️ 数据架构设计

### 数据库选择策略

#### PostgreSQL (主数据库)
**用途**: 用户数据、关系数据、事务数据
- 用户信息、角色权限
- 社交关系 (关注、圈子成员)
- 分享链接、访问日志
- 评论和互动数据

#### MongoDB (文档数据库)
**用途**: 笔记内容、版本历史、AI对话记录
- 笔记内容和元数据
- 版本历史记录
- AI对话会话
- 富文本和媒体文件

#### Redis (缓存数据库)
**用途**: 会话管理、缓存、消息队列
- 用户会话和Token
- 热点数据缓存
- AI配额管理
- 异步任务队列

#### Elasticsearch (搜索引擎)
**用途**: 全文搜索、内容推荐
- 笔记全文搜索
- 用户和内容发现
- 推荐算法数据
- 搜索分析统计

---

## 🔐 安全架构

### 认证与授权
- **JWT Token**: 访问令牌(15分钟) + 刷新令牌(7天)
- **RBAC权限模型**: 用户/高级用户/管理员/超级管理员
- **API限流**: 基于用户和IP的请求限制
- **数据验证**: 输入验证和SQL注入防护

### 数据安全
- **传输加密**: TLS 1.3
- **存储加密**: AES-256字段级加密
- **密码安全**: bcrypt哈希 (cost: 12)
- **敏感数据脱敏**: 邮箱、手机号等信息脱敏

---

## 🚀 性能优化

### 缓存策略
- **浏览器缓存**: 静态资源长期缓存
- **CDN缓存**: 全球内容分发
- **API网关缓存**: 接口响应缓存
- **应用缓存**: Redis多级缓存
- **数据库缓存**: 查询结果缓存

### 数据库优化
- **索引策略**: 基于查询模式的索引设计
- **分库分表**: 按用户ID进行笔记数据分片
- **读写分离**: 主从复制和读写分离
- **连接池**: 数据库连接池优化

---

## 📊 监控与运维

### 监控体系
- **应用监控**: Prometheus + Grafana
- **日志监控**: ELK Stack (Elasticsearch + Logstash + Kibana)
- **错误追踪**: Sentry错误监控
- **性能监控**: APM性能分析

### 部署架构
- **开发环境**: Docker Compose本地部署
- **测试环境**: Kubernetes集群部署
- **生产环境**: 多可用区Kubernetes部署
- **CI/CD**: GitHub Actions自动化部署

---

## 🎯 技术决策总结

### 架构优势
- ✅ **可扩展性**: 微服务架构支持独立扩展
- ✅ **高性能**: 多级缓存 + 数据库优化
- ✅ **高可用**: 容器化部署 + 负载均衡
- ✅ **安全性**: 多层安全防护
- ✅ **可维护性**: 清晰的服务边界和接口

### 技术风险与应对
- **DeepSeek API依赖**: 实现降级策略和备用方案
- **数据一致性**: 事件溯源 + 最终一致性
- **性能瓶颈**: 预设扩展点和监控告警

### 成本优化
- **资源利用**: 容器化 + 自动扩缩容
- **存储成本**: 冷热数据分离
- **API成本**: 智能缓存 + 配额管理

---

## 📋 下一步行动

1. **UX设计**: 需要UX专家设计用户界面和交互流程
2. **开发计划**: 制定详细的开发里程碑和任务分解
3. **技术选型确认**: 确认具体的技术栈版本和配置
4. **环境搭建**: 搭建开发、测试、生产环境

---

## 🔧 详细技术实现

### API设计规范
```typescript
// RESTful API设计标准
interface APIResponse<T> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
    details?: any
  }
  pagination?: {
    page: number
    limit: number
    total: number
    hasNext: boolean
  }
}

// 统一错误码
enum ErrorCode {
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',
  NOT_FOUND = 'NOT_FOUND',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  AI_SERVICE_ERROR = 'AI_SERVICE_ERROR',
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED'
}
```

### 环境配置
```typescript
// 环境变量配置
interface Config {
  // 服务配置
  PORT: number
  NODE_ENV: 'development' | 'test' | 'production'

  // 数据库配置
  DATABASE_URL: string
  MONGODB_URL: string
  REDIS_URL: string
  ELASTICSEARCH_URL: string

  // 外部服务
  DEEPSEEK_API_KEY: string
  DEEPSEEK_API_URL: string

  // 安全配置
  JWT_SECRET: string
  JWT_REFRESH_SECRET: string
  ENCRYPTION_KEY: string

  // 存储配置
  OSS_ACCESS_KEY: string
  OSS_SECRET_KEY: string
  OSS_BUCKET: string
  CDN_DOMAIN: string
}
```

### Docker部署配置
```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - MONGODB_URL=${MONGODB_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - mongodb
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: noteai
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  mongodb:
    image: mongo:6
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
    volumes:
      - mongodb_data:/data/db
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    restart: unless-stopped

volumes:
  postgres_data:
  mongodb_data:
  redis_data:
  elasticsearch_data:
```

---

**文档状态**: ✅ 已完成
**下一个角色**: UX Expert 或 Product Owner
