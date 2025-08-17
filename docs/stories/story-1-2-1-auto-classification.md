# Story 1.2.1: 自动内容分类
## AI驱动的智能笔记分类系统

**Story ID**: STORY-003  
**Epic**: Epic 1.2 - 智能分类与组织  
**创建日期**: 2025-01-17  
**BMad Master**: AI BMad Master  
**优先级**: P0 (高)  
**估算**: 8 Story Points  

---

## 📋 用户故事

### 核心用户故事
**作为** 学习者  
**我希望** 系统自动识别笔记内容并分配到合适的分类  
**以便** 我不需要手动整理就能保持笔记有序  

### 详细场景
1. **场景1**: 用户创建新笔记时，系统自动推荐分类
2. **场景2**: 用户编辑现有笔记时，系统重新评估分类
3. **场景3**: 用户可以查看和调整AI推荐的分类

---

## ✅ 验收标准

### 功能验收标准
- [ ] **自动推荐**: 新建笔记时自动推荐分类
- [ ] **准确率**: 分类准确率达到80%以上
- [ ] **手动调整**: 支持用户手动调整分类
- [ ] **学习能力**: 系统学习用户的分类偏好
- [ ] **多级分类**: 支持主分类和子分类
- [ ] **实时更新**: 内容变化时实时更新分类建议

### 技术验收标准
- [ ] **响应时间**: 分类建议生成时间 < 1秒
- [ ] **内容分析**: 支持1-10000字符的内容分析
- [ ] **分类体系**: 支持自定义分类体系
- [ ] **批量处理**: 支持批量重新分类现有笔记
- [ ] **数据持久化**: 分类结果和用户偏好持久化存储

### 用户体验验收标准
- [ ] **建议展示**: 分类建议以直观方式展示
- [ ] **置信度**: 显示分类建议的置信度
- [ ] **快速操作**: 一键接受或拒绝分类建议
- [ ] **分类管理**: 支持创建、编辑、删除分类
- [ ] **统计信息**: 显示各分类的笔记数量统计

---

## 🏗️ 技术实现方案

### 前端实现
```typescript
interface ClassificationService {
  // 获取分类建议
  getClassificationSuggestions(content: string): Promise<ClassificationSuggestion[]>
  
  // 应用分类
  applyClassification(noteId: string, categoryId: string): Promise<void>
  
  // 获取用户分类体系
  getUserCategories(userId: string): Promise<Category[]>
  
  // 创建新分类
  createCategory(category: CreateCategoryRequest): Promise<Category>
}

interface ClassificationSuggestion {
  categoryId: string
  categoryName: string
  confidence: number
  reasoning: string
  isMainCategory: boolean
}

interface Category {
  id: string
  name: string
  description?: string
  parentId?: string
  color: string
  icon: string
  noteCount: number
  createdAt: Date
}
```

### 后端API设计
```typescript
// POST /api/v1/ai/classify-content
interface ClassifyContentRequest {
  content: string
  title?: string
  userId: string
  noteId?: string
  existingCategories?: string[]
}

interface ClassifyContentResponse {
  suggestions: ClassificationSuggestion[]
  contentAnalysis: {
    detectedTopics: string[]
    contentType: string
    language: string
    keyPhrases: string[]
  }
  processingTime: number
  requestId: string
}

// GET /api/v1/categories
interface GetCategoriesResponse {
  categories: Category[]
  statistics: {
    totalCategories: number
    totalNotes: number
    averageNotesPerCategory: number
  }
}
```

### AI分类算法
```typescript
class ContentClassificationEngine {
  async classifyContent(content: string, userCategories: Category[]): Promise<ClassificationResult> {
    // 1. 内容预处理
    const processedContent = this.preprocessContent(content)
    
    // 2. 特征提取
    const features = await this.extractFeatures(processedContent)
    
    // 3. 主题识别
    const topics = await this.identifyTopics(features)
    
    // 4. 分类匹配
    const suggestions = await this.matchCategories(topics, userCategories)
    
    // 5. 置信度计算
    return this.calculateConfidence(suggestions)
  }
  
  private async extractFeatures(content: string): Promise<ContentFeatures> {
    return {
      keywords: await this.extractKeywords(content),
      entities: await this.extractEntities(content),
      sentiment: await this.analyzeSentiment(content),
      structure: this.analyzeStructure(content)
    }
  }
}
```

---

## 🎨 用户界面设计

### 分类建议界面
```
┌─────────────────────────────────────────────────────────┐
│ 📝 新建笔记                                      [保存] │
├─────────────────────────────────────────────────────────┤
│ 标题: 机器学习算法基础                                  │
│                                                         │
│ 内容: 机器学习是人工智能的一个重要分支，主要研究如何... │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ 🤖 AI分类建议                                   [设置] │
│                                                         │
│ 推荐分类:                                               │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐ │
│ │ 📚 学习笔记     │ │ 💻 技术文档     │ │ 🧠 AI研究   │ │
│ │ 置信度: 92%     │ │ 置信度: 78%     │ │ 置信度: 85% │ │
│ │ [选择]          │ │ [选择]          │ │ [选择]      │ │
│ └─────────────────┘ └─────────────────┘ └─────────────┘ │
│                                                         │
│ 检测到的关键词: #机器学习 #算法 #人工智能 #数据科学     │
│                                                         │
│ [接受建议] [手动选择] [创建新分类] [跳过分类]           │
└─────────────────────────────────────────────────────────┘
```

### 分类管理界面
```
┌─────────────────────────────────────────────────────────┐
│ 📁 分类管理                                    [+ 新建] │
├─────────────────────────────────────────────────────────┤
│ 我的分类体系:                                           │
│                                                         │
│ 📚 学习笔记 (45篇)                              [编辑] │
│   ├─ 📖 课程笔记 (23篇)                                │
│   ├─ 📝 读书笔记 (15篇)                                │
│   └─ 🧠 思考总结 (7篇)                                 │
│                                                         │
│ 💻 技术文档 (32篇)                              [编辑] │
│   ├─ 🔧 开发工具 (12篇)                                │
│   ├─ 📊 数据分析 (8篇)                                 │
│   └─ 🤖 AI技术 (12篇)                                  │
│                                                         │
│ 💼 工作相关 (18篇)                              [编辑] │
│   ├─ 📋 会议记录 (10篇)                                │
│   └─ 💡 项目想法 (8篇)                                 │
│                                                         │
│ 分类统计:                                               │
│ • 总分类数: 9个 (3个主分类, 6个子分类)                 │
│ • 总笔记数: 95篇                                        │
│ • 平均每分类: 10.6篇                                    │
│ • 未分类笔记: 3篇                                       │
│                                                         │
│ [批量重新分类] [导入分类] [导出分类] [重置分类]        │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 数据模型设计

### 数据库表结构
```sql
-- 分类表
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES categories(id),
    color VARCHAR(7) DEFAULT '#3B82F6', -- 十六进制颜色
    icon VARCHAR(50) DEFAULT 'folder',
    sort_order INTEGER DEFAULT 0,
    is_system_category BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, name, parent_id)
);

-- 笔记分类关联表
CREATE TABLE note_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    note_id UUID NOT NULL REFERENCES notes(id),
    category_id UUID NOT NULL REFERENCES categories(id),
    confidence_score DECIMAL(3,2),
    is_auto_classified BOOLEAN DEFAULT TRUE,
    classified_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(note_id, category_id)
);

-- 分类建议表
CREATE TABLE classification_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    note_id UUID NOT NULL REFERENCES notes(id),
    category_id UUID NOT NULL REFERENCES categories(id),
    confidence_score DECIMAL(3,2) NOT NULL,
    reasoning TEXT,
    is_accepted BOOLEAN,
    user_feedback VARCHAR(20), -- 'accept', 'reject', 'modify'
    created_at TIMESTAMP DEFAULT NOW()
);

-- 用户分类偏好表
CREATE TABLE user_classification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    keyword VARCHAR(100) NOT NULL,
    preferred_category_id UUID NOT NULL REFERENCES categories(id),
    weight DECIMAL(3,2) DEFAULT 1.0,
    learned_from_feedback BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, keyword)
);
```

---

## 🧪 测试策略

### 单元测试
- [ ] 内容特征提取测试
- [ ] 分类算法准确性测试
- [ ] 置信度计算测试
- [ ] 用户偏好学习测试

### 集成测试
- [ ] 分类API集成测试
- [ ] 数据库操作测试
- [ ] 用户界面交互测试
- [ ] 批量分类处理测试

### 准确性测试
- [ ] 不同类型内容分类测试
- [ ] 多语言内容分类测试
- [ ] 短文本和长文本分类测试
- [ ] 边界情况处理测试

### 性能测试
- [ ] 分类速度测试 (< 1秒)
- [ ] 批量处理性能测试
- [ ] 并发分类请求测试
- [ ] 内存使用优化测试

---

## 📈 监控指标

### 业务指标
- **分类准确率**: AI分类建议的准确性
- **用户接受率**: 用户接受分类建议的比例
- **分类覆盖率**: 被自动分类的笔记比例
- **分类一致性**: 相似内容分类的一致性

### 技术指标
- **处理速度**: 分类建议生成时间
- **算法性能**: 分类算法的准确率和召回率
- **学习效果**: 用户偏好学习的改进效果
- **系统负载**: 分类服务的系统资源使用

---

## 🚀 实施计划

### Week 1: 核心算法
- [ ] 内容分析算法开发
- [ ] 分类匹配逻辑实现
- [ ] 置信度计算机制

### Week 2: 数据模型
- [ ] 数据库表结构创建
- [ ] 分类管理API开发
- [ ] 用户偏好学习机制

### Week 3: 用户界面
- [ ] 分类建议界面开发
- [ ] 分类管理界面实现
- [ ] 用户交互逻辑完善

### Week 4: 优化测试
- [ ] 算法准确性优化
- [ ] 性能测试和优化
- [ ] 用户体验测试

---

## 🔗 相关文档

- **Epic文档**: [Epic 1: 智能笔记创作系统](../epics/epic-1-intelligent-note-creation.md)
- **UX设计**: [智能笔记管理界面](../ux-design.md#智能笔记管理界面)
- **架构设计**: [AI服务架构](../architecture.md#ai服务)

---

**Story状态**: 📋 已分片，准备开发  
**下一步**: 开始分类算法开发和数据模型设计
