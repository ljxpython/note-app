# 🤖 AI服务架构设计
## AI Service Architecture

**服务名称**: AI Service  
**创建日期**: 2025-01-17  
**BMad Master**: AI BMad Master  
**服务职责**: DeepSeek集成、内容优化、智能分类  

---

## 🎯 服务概述

### 核心职责
- **内容优化**: 文本语法和表达优化
- **智能续写**: 基于上下文的内容续写
- **自动分类**: 内容主题识别和分类
- **对话交互**: 多轮AI对话和建议
- **风格学习**: 用户写作风格学习和适应

### 业务边界
- ✅ **包含**: AI模型调用、内容分析、智能建议
- ❌ **不包含**: 用户管理、笔记存储、分享逻辑

---

## 🏗️ 技术架构

### 服务架构图
```
┌─────────────────────────────────────────────────────────┐
│                    AI Service                           │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│ │ Optimization│ │ Classification│ │ Conversation      │ │
│ │ Controller  │ │ Controller   │ │ Controller        │ │
│ └─────────────┘ └─────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│ │ Text        │ │ Content     │ │ Style Learning      │ │
│ │ Optimizer   │ │ Classifier  │ │ Engine              │ │
│ └─────────────┘ └─────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│ │ DeepSeek    │ │ Prompt      │ │ Cache               │ │
│ │ Client      │ │ Manager     │ │ Manager             │ │
│ └─────────────┘ └─────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│ │ Request     │ │ Response    │ │ Analytics           │ │
│ │ Queue       │ │ Cache       │ │ Storage             │ │
│ └─────────────┘ └─────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│          Redis + MongoDB + PostgreSQL                  │
└─────────────────────────────────────────────────────────┘
```

### 技术栈
- **框架**: Node.js + Express.js + TypeScript
- **AI集成**: DeepSeek API + OpenAI SDK
- **队列**: Bull Queue + Redis
- **缓存**: Redis (多层缓存)
- **数据库**: MongoDB (AI会话) + PostgreSQL (配额管理)
- **监控**: Prometheus + Custom Metrics

---

## 🔌 DeepSeek API集成

### API客户端设计
```typescript
interface DeepSeekClient {
  // 文本优化
  optimizeText(request: OptimizationRequest): Promise<OptimizationResponse>
  
  // 内容续写
  continueText(request: ContinuationRequest): Promise<ContinuationResponse>
  
  // 内容分类
  classifyContent(request: ClassificationRequest): Promise<ClassificationResponse>
  
  // 对话交互
  chatCompletion(request: ChatRequest): Promise<ChatResponse>
}

class DeepSeekService implements DeepSeekClient {
  private apiKey: string
  private baseURL: string
  private rateLimiter: RateLimiter
  private circuitBreaker: CircuitBreaker
  
  constructor(config: DeepSeekConfig) {
    this.apiKey = config.apiKey
    this.baseURL = config.baseURL
    this.rateLimiter = new RateLimiter(config.rateLimit)
    this.circuitBreaker = new CircuitBreaker(config.circuitBreaker)
  }
  
  async optimizeText(request: OptimizationRequest): Promise<OptimizationResponse> {
    // 1. 请求验证和预处理
    await this.validateRequest(request)
    
    // 2. 限流检查
    await this.rateLimiter.checkLimit(request.userId)
    
    // 3. 缓存检查
    const cacheKey = this.generateCacheKey('optimize', request)
    const cached = await this.cache.get(cacheKey)
    if (cached) return cached
    
    // 4. 构建Prompt
    const prompt = this.buildOptimizationPrompt(request)
    
    // 5. API调用 (带熔断器)
    const response = await this.circuitBreaker.execute(() => 
      this.callDeepSeekAPI(prompt)
    )
    
    // 6. 响应处理和缓存
    const result = this.processOptimizationResponse(response)
    await this.cache.set(cacheKey, result, 1800) // 30分钟缓存
    
    return result
  }
}
```

### Prompt工程
```typescript
class PromptManager {
  // 文本优化Prompt模板
  buildOptimizationPrompt(request: OptimizationRequest): string {
    const { text, optimizationType, userStyle } = request
    
    return `你是一个专业的文本优化助手。请优化以下文本：

原文：
${text}

优化要求：
- 类型：${optimizationType} (grammar/expression/structure)
- 用户风格：${userStyle || '通用'}
- 保持原意不变
- 提供具体的改进建议

请返回JSON格式：
{
  "optimizedText": "优化后的文本",
  "suggestions": [
    {
      "type": "grammar|expression|structure",
      "original": "原始片段",
      "optimized": "优化片段", 
      "explanation": "优化说明"
    }
  ],
  "confidence": 0.95
}`
  }
  
  // 内容分类Prompt模板
  buildClassificationPrompt(request: ClassificationRequest): string {
    const { content, existingCategories } = request
    
    return `请分析以下内容并进行分类：

内容：
${content}

现有分类：
${existingCategories.map(cat => `- ${cat.name}: ${cat.description}`).join('\n')}

请返回JSON格式：
{
  "suggestions": [
    {
      "categoryName": "分类名称",
      "confidence": 0.92,
      "reasoning": "分类理由"
    }
  ],
  "detectedTopics": ["主题1", "主题2"],
  "keyPhrases": ["关键词1", "关键词2"]
}`
  }
}
```

---

## 📊 数据模型设计

### AI请求记录
```sql
-- AI请求记录表 (PostgreSQL)
CREATE TABLE ai_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    request_type VARCHAR(50) NOT NULL, -- 'optimize', 'continue', 'classify', 'chat'
    input_text TEXT NOT NULL,
    input_length INTEGER NOT NULL,
    model_used VARCHAR(50) NOT NULL,
    tokens_used INTEGER,
    processing_time_ms INTEGER,
    cost_cents INTEGER, -- 成本（分）
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- 用户AI配额表
CREATE TABLE user_ai_quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,
    plan_type VARCHAR(20) NOT NULL DEFAULT 'free', -- 'free', 'premium', 'team'
    monthly_limit INTEGER NOT NULL DEFAULT 50,
    monthly_used INTEGER DEFAULT 0,
    daily_limit INTEGER NOT NULL DEFAULT 10,
    daily_used INTEGER DEFAULT 0,
    reset_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### AI会话数据 (MongoDB)
```javascript
// AI对话会话集合
const conversationSchema = {
  _id: ObjectId,
  userId: String,
  noteId: String, // 关联的笔记ID
  sessionId: String,
  messages: [{
    role: String, // 'user' | 'assistant'
    content: String,
    timestamp: Date,
    metadata: {
      tokens: Number,
      model: String,
      processingTime: Number
    }
  }],
  context: {
    noteContent: String, // 笔记上下文
    userStyle: String,   // 用户写作风格
    previousOptimizations: [String] // 之前的优化记录
  },
  status: String, // 'active' | 'completed' | 'expired'
  createdAt: Date,
  updatedAt: Date,
  expiresAt: Date
}

// 用户风格学习数据
const userStyleSchema = {
  _id: ObjectId,
  userId: String,
  styleProfile: {
    formalityLevel: Number,    // 正式程度 0-1
    sentenceLength: String,    // 'short' | 'medium' | 'long'
    vocabularyLevel: String,   // 'simple' | 'advanced' | 'technical'
    tone: String,             // 'professional' | 'casual' | 'academic'
    preferredStructure: String // 'linear' | 'hierarchical' | 'narrative'
  },
  learningData: [{
    optimizationType: String,
    userChoice: String,      // 'accept' | 'reject' | 'modify'
    originalText: String,
    optimizedText: String,
    userModification: String,
    timestamp: Date
  }],
  confidence: Number,        // 风格识别置信度
  lastUpdated: Date,
  createdAt: Date
}
```

---

## 🔄 请求处理流程

### 异步处理架构
```typescript
// 请求队列处理
class AIRequestProcessor {
  private optimizationQueue: Queue
  private classificationQueue: Queue
  private conversationQueue: Queue
  
  constructor() {
    this.optimizationQueue = new Queue('text-optimization', {
      redis: redisConfig,
      defaultJobOptions: {
        removeOnComplete: 100,
        removeOnFail: 50,
        attempts: 3,
        backoff: 'exponential'
      }
    })
    
    this.setupQueueProcessors()
  }
  
  private setupQueueProcessors() {
    // 文本优化处理器
    this.optimizationQueue.process('optimize-text', 5, async (job) => {
      const { userId, text, options } = job.data
      
      try {
        // 1. 配额检查
        await this.checkUserQuota(userId, 'optimize')
        
        // 2. 内容预处理
        const processedText = this.preprocessText(text)
        
        // 3. AI调用
        const result = await this.deepSeekService.optimizeText({
          text: processedText,
          ...options
        })
        
        // 4. 后处理
        const finalResult = this.postprocessOptimization(result)
        
        // 5. 配额更新
        await this.updateUserQuota(userId, 'optimize', 1)
        
        return finalResult
      } catch (error) {
        await this.handleProcessingError(error, job)
        throw error
      }
    })
  }
}
```

### 缓存策略
```typescript
class AICache {
  private redis: Redis
  
  // 多层缓存策略
  async get(key: string): Promise<any> {
    // L1: 内存缓存 (最快)
    const memoryResult = this.memoryCache.get(key)
    if (memoryResult) return memoryResult
    
    // L2: Redis缓存 (快)
    const redisResult = await this.redis.get(key)
    if (redisResult) {
      const parsed = JSON.parse(redisResult)
      this.memoryCache.set(key, parsed, 300) // 5分钟内存缓存
      return parsed
    }
    
    return null
  }
  
  async set(key: string, value: any, ttl: number): Promise<void> {
    // 同时设置内存和Redis缓存
    this.memoryCache.set(key, value, Math.min(ttl, 300))
    await this.redis.setex(key, ttl, JSON.stringify(value))
  }
  
  // 缓存键生成策略
  generateCacheKey(type: string, request: any): string {
    const hash = crypto.createHash('md5')
      .update(JSON.stringify({
        type,
        text: request.text,
        options: request.options
      }))
      .digest('hex')
    
    return `ai:${type}:${hash}`
  }
}
```

---

## 📈 性能优化

### 请求优化
```typescript
// 批量处理优化
class BatchProcessor {
  private batchSize = 10
  private batchTimeout = 2000 // 2秒
  private pendingRequests: Map<string, PendingRequest[]> = new Map()
  
  async processBatch(type: string, requests: any[]): Promise<any[]> {
    // 将多个相似请求合并为一个批量请求
    const batchPrompt = this.buildBatchPrompt(type, requests)
    const batchResponse = await this.deepSeekService.batchProcess(batchPrompt)
    
    // 拆分批量响应为单独的结果
    return this.splitBatchResponse(batchResponse, requests.length)
  }
}

// 智能预加载
class PreloadManager {
  async preloadUserStyle(userId: string): Promise<void> {
    // 预加载用户写作风格数据
    const styleData = await this.getUserStyle(userId)
    await this.cache.set(`user:style:${userId}`, styleData, 3600)
  }
  
  async preloadCommonOptimizations(): Promise<void> {
    // 预加载常见优化模式
    const commonPatterns = await this.getCommonOptimizationPatterns()
    for (const pattern of commonPatterns) {
      await this.cache.set(`pattern:${pattern.id}`, pattern, 7200)
    }
  }
}
```

### 成本控制
```typescript
class CostManager {
  // 智能配额管理
  async checkAndAllocateQuota(userId: string, requestType: string): Promise<boolean> {
    const quota = await this.getUserQuota(userId)
    const cost = this.calculateRequestCost(requestType)
    
    if (quota.remaining < cost) {
      // 配额不足，检查是否可以使用备用策略
      return await this.tryFallbackStrategy(userId, requestType)
    }
    
    await this.deductQuota(userId, cost)
    return true
  }
  
  // 成本预测
  async estimateRequestCost(request: any): Promise<number> {
    const textLength = request.text.length
    const complexity = this.analyzeComplexity(request.text)
    
    // 基于文本长度和复杂度估算token使用量
    const estimatedTokens = Math.ceil(textLength * 1.3 * complexity)
    return this.tokensToCredits(estimatedTokens)
  }
}
```

---

## 🧪 测试策略

### 单元测试
```typescript
describe('AIService', () => {
  describe('optimizeText', () => {
    it('should optimize text successfully', async () => {
      const request = {
        text: '这个算法的效率不是很好',
        optimizationType: 'expression',
        userId: 'test-user-id'
      }
      
      const result = await aiService.optimizeText(request)
      
      expect(result.optimizedText).toBeDefined()
      expect(result.suggestions).toHaveLength(1)
      expect(result.confidence).toBeGreaterThan(0.8)
    })
    
    it('should handle quota exceeded', async () => {
      // 测试配额超限情况
    })
  })
})
```

### 集成测试
- DeepSeek API集成测试
- 缓存系统测试
- 队列处理测试
- 配额管理测试

---

## 📊 监控指标

### 业务指标
- **AI使用率**: 用户AI功能使用频率
- **建议采纳率**: 用户采纳AI建议的比例
- **用户满意度**: AI建议质量评分
- **配额使用**: 各用户群体的配额使用情况

### 技术指标
- **API响应时间**: DeepSeek API调用延迟
- **处理吞吐量**: 每秒处理的AI请求数
- **缓存命中率**: 各级缓存的命中率
- **错误率**: AI请求失败率
- **成本效率**: 每次请求的平均成本

---

## 🚀 部署配置

### Docker配置
```dockerfile
FROM node:18-alpine
WORKDIR /app

# 安装依赖
COPY package*.json ./
RUN npm ci --only=production

# 复制源码
COPY . .

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3002/health || exit 1

EXPOSE 3002
CMD ["npm", "start"]
```

### 环境变量
```env
# DeepSeek配置
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 缓存配置
REDIS_URL=redis://redis:6379
CACHE_TTL_OPTIMIZATION=1800
CACHE_TTL_CLASSIFICATION=3600

# 队列配置
QUEUE_CONCURRENCY=5
QUEUE_MAX_ATTEMPTS=3

# 配额配置
FREE_USER_MONTHLY_LIMIT=50
PREMIUM_USER_MONTHLY_LIMIT=1000
```

---

**服务状态**: ✅ 架构设计完成  
**开发就绪度**: 🚀 90% - 需要DeepSeek API密钥配置  
**相关Story**: Story 1.1.1, 1.1.2, 1.2.1 都依赖此服务
