# 📝 笔记服务架构设计
## Note Service Architecture

**服务名称**: Note Service  
**创建日期**: 2025-01-17  
**BMad Master**: AI BMad Master  
**服务职责**: 笔记CRUD、版本控制、自动保存  

---

## 🎯 服务概述

### 核心职责
- **笔记管理**: 创建、编辑、删除、查询笔记
- **版本控制**: 笔记版本历史管理和恢复
- **自动保存**: 实时自动保存机制
- **文件管理**: 图片、附件上传和管理
- **内容渲染**: Markdown到HTML的转换

### 业务边界
- ✅ **包含**: 笔记内容、版本历史、文件附件
- ❌ **不包含**: 用户认证、AI功能、分享逻辑

---

## 🏗️ 技术架构

### 服务架构图
```
┌─────────────────────────────────────────────────────────┐
│                   Note Service                          │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│ │ Note        │ │ Version     │ │ File                │ │
│ │ Controller  │ │ Controller  │ │ Controller          │ │
│ └─────────────┘ └─────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│ │ Note        │ │ Version     │ │ Auto Save           │ │
│ │ Service     │ │ Service     │ │ Service             │ │
│ └─────────────┘ └─────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│ │ Note        │ │ Search      │ │ File Storage        │ │
│ │ Repository  │ │ Engine      │ │ Manager             │ │
│ └─────────────┘ └─────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ MongoDB + Elasticsearch + OSS Storage                  │
└─────────────────────────────────────────────────────────┘
```

### 技术栈
- **框架**: Node.js + Express.js + TypeScript
- **数据库**: MongoDB (主存储)
- **搜索**: Elasticsearch (全文搜索)
- **缓存**: Redis (热点数据)
- **存储**: OSS/S3 (文件存储)
- **实时通信**: Socket.IO (自动保存)

---

## 📊 数据模型设计

### MongoDB数据模型
```javascript
// 笔记主文档
const noteSchema = {
  _id: ObjectId,
  userId: String,
  title: String,
  content: String,        // Markdown格式原始内容
  contentHtml: String,    // 渲染后的HTML内容
  excerpt: String,        // 摘要，用于列表显示
  
  // 元数据
  metadata: {
    wordCount: Number,
    characterCount: Number,
    readingTime: Number,    // 预估阅读时间（分钟）
    language: String,       // 检测到的语言
    lastEditedAt: Date,
    aiOptimizedAt: Date,    // 最后AI优化时间
    autoSaveVersion: Number // 自动保存版本号
  },
  
  // 分类和标签
  categoryId: String,
  tags: [String],
  
  // 状态
  status: String,         // 'draft', 'published', 'archived', 'deleted'
  isPublic: Boolean,
  isFavorite: Boolean,
  
  // 分享设置
  shareSettings: {
    isPublic: Boolean,
    allowComments: Boolean,
    allowDownload: Boolean,
    shareUrl: String,
    password: String,       // 分享密码
    expiresAt: Date,       // 分享过期时间
    circles: [String]       // 圈子ID列表
  },
  
  // 附件
  attachments: [{
    id: String,
    filename: String,
    originalName: String,
    mimeType: String,
    size: Number,
    url: String,
    thumbnailUrl: String,   // 图片缩略图
    uploadedAt: Date
  }],
  
  // 版本控制
  currentVersion: Number,
  versions: [{
    versionId: String,
    versionNumber: Number,
    content: String,
    contentHtml: String,
    changeDescription: String,
    changedBy: String,      // 用户ID或'system'
    createdAt: Date,
    wordCountDiff: Number,  // 字数变化
    changeType: String      // 'manual', 'auto_save', 'ai_optimize'
  }],
  
  // 协作信息
  collaboration: {
    isCollaborative: Boolean,
    collaborators: [{
      userId: String,
      permission: String,   // 'read', 'comment', 'edit'
      joinedAt: Date,
      lastActiveAt: Date
    }],
    lockInfo: {
      isLocked: Boolean,
      lockedBy: String,     // 用户ID
      lockedAt: Date,
      lockExpires: Date
    }
  },
  
  // 时间戳
  createdAt: Date,
  updatedAt: Date,
  deletedAt: Date         // 软删除时间
}

// 自动保存临时数据
const autoSaveSchema = {
  _id: ObjectId,
  noteId: String,
  userId: String,
  content: String,
  version: Number,
  createdAt: Date,
  expiresAt: Date         // TTL索引，自动清理
}
```

### Elasticsearch索引结构
```json
{
  "mappings": {
    "properties": {
      "noteId": {"type": "keyword"},
      "userId": {"type": "keyword"},
      "title": {
        "type": "text",
        "analyzer": "ik_max_word",
        "search_analyzer": "ik_smart"
      },
      "content": {
        "type": "text",
        "analyzer": "ik_max_word",
        "search_analyzer": "ik_smart"
      },
      "excerpt": {"type": "text"},
      "tags": {"type": "keyword"},
      "categoryId": {"type": "keyword"},
      "status": {"type": "keyword"},
      "isPublic": {"type": "boolean"},
      "createdAt": {"type": "date"},
      "updatedAt": {"type": "date"},
      "wordCount": {"type": "integer"},
      "readingTime": {"type": "integer"},
      "language": {"type": "keyword"}
    }
  }
}
```

---

## 🔌 API接口设计

### 笔记CRUD API
```typescript
// GET /api/v1/notes
interface GetNotesRequest {
  page?: number
  limit?: number
  categoryId?: string
  tags?: string[]
  status?: 'draft' | 'published' | 'archived'
  search?: string
  sortBy?: 'createdAt' | 'updatedAt' | 'title' | 'wordCount'
  sortOrder?: 'asc' | 'desc'
}

interface GetNotesResponse {
  notes: NoteListItem[]
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
    hasNext: boolean
    hasPrev: boolean
  }
  filters: {
    categories: CategoryCount[]
    tags: TagCount[]
    statusCounts: StatusCount[]
  }
}

// POST /api/v1/notes
interface CreateNoteRequest {
  title: string
  content?: string
  categoryId?: string
  tags?: string[]
  isPublic?: boolean
  templateId?: string
}

interface CreateNoteResponse {
  note: Note
  autoSaveToken: string
}

// PUT /api/v1/notes/:id
interface UpdateNoteRequest {
  title?: string
  content?: string
  categoryId?: string
  tags?: string[]
  status?: string
  isPublic?: boolean
  shareSettings?: ShareSettings
}

// GET /api/v1/notes/:id
interface GetNoteResponse {
  note: Note
  permissions: {
    canEdit: boolean
    canDelete: boolean
    canShare: boolean
    canComment: boolean
  }
  relatedNotes?: NoteListItem[]
}
```

### 版本控制API
```typescript
// GET /api/v1/notes/:id/versions
interface GetVersionsResponse {
  versions: NoteVersion[]
  currentVersion: number
}

// POST /api/v1/notes/:id/versions
interface CreateVersionRequest {
  changeDescription?: string
  changeType: 'manual' | 'auto_save' | 'ai_optimize'
}

// PUT /api/v1/notes/:id/restore/:versionId
interface RestoreVersionRequest {
  createBackup?: boolean
}
```

### 自动保存API
```typescript
// POST /api/v1/notes/:id/auto-save
interface AutoSaveRequest {
  content: string
  version: number
  autoSaveToken: string
}

interface AutoSaveResponse {
  success: boolean
  version: number
  savedAt: Date
  conflictDetected?: boolean
}

// WebSocket事件
interface AutoSaveEvents {
  'auto-save': {
    noteId: string
    content: string
    version: number
  }
  
  'save-success': {
    noteId: string
    version: number
    savedAt: Date
  }
  
  'save-error': {
    noteId: string
    error: string
  }
  
  'conflict-detected': {
    noteId: string
    serverVersion: number
    clientVersion: number
  }
}
```

---

## 🔄 核心功能实现

### 自动保存机制
```typescript
class AutoSaveService {
  private saveQueue: Map<string, NodeJS.Timeout> = new Map()
  private conflictResolver: ConflictResolver
  
  // 延迟保存策略
  scheduleAutoSave(noteId: string, content: string, version: number): void {
    // 清除之前的保存任务
    const existingTimeout = this.saveQueue.get(noteId)
    if (existingTimeout) {
      clearTimeout(existingTimeout)
    }
    
    // 设置新的保存任务（5秒延迟）
    const timeout = setTimeout(async () => {
      try {
        await this.performAutoSave(noteId, content, version)
        this.saveQueue.delete(noteId)
      } catch (error) {
        this.handleAutoSaveError(noteId, error)
      }
    }, 5000)
    
    this.saveQueue.set(noteId, timeout)
  }
  
  private async performAutoSave(noteId: string, content: string, version: number): Promise<void> {
    // 1. 获取当前服务器版本
    const currentNote = await this.noteRepository.findById(noteId)
    
    // 2. 检查版本冲突
    if (currentNote.metadata.autoSaveVersion > version) {
      await this.handleVersionConflict(noteId, content, version, currentNote)
      return
    }
    
    // 3. 执行保存
    await this.noteRepository.updateContent(noteId, {
      content,
      contentHtml: await this.markdownRenderer.render(content),
      'metadata.autoSaveVersion': version + 1,
      'metadata.lastEditedAt': new Date(),
      updatedAt: new Date()
    })
    
    // 4. 更新搜索索引
    await this.searchService.updateDocument(noteId, {
      content,
      updatedAt: new Date()
    })
    
    // 5. 通知客户端保存成功
    this.socketService.emit(`note:${noteId}`, 'save-success', {
      noteId,
      version: version + 1,
      savedAt: new Date()
    })
  }
}
```

### 版本控制系统
```typescript
class VersionService {
  // 创建版本快照
  async createVersion(noteId: string, options: CreateVersionOptions): Promise<NoteVersion> {
    const note = await this.noteRepository.findById(noteId)
    
    const version: NoteVersion = {
      versionId: generateUUID(),
      versionNumber: note.currentVersion + 1,
      content: note.content,
      contentHtml: note.contentHtml,
      changeDescription: options.changeDescription || 'Auto-generated version',
      changedBy: options.userId || 'system',
      createdAt: new Date(),
      wordCountDiff: this.calculateWordCountDiff(note.content, options.previousContent),
      changeType: options.changeType
    }
    
    // 更新笔记版本信息
    await this.noteRepository.updateOne(noteId, {
      $push: { versions: version },
      $set: { currentVersion: version.versionNumber }
    })
    
    // 版本清理策略（保留最近50个版本）
    await this.cleanupOldVersions(noteId, 50)
    
    return version
  }
  
  // 版本对比
  async compareVersions(noteId: string, version1: string, version2: string): Promise<VersionDiff> {
    const note = await this.noteRepository.findById(noteId)
    const v1 = note.versions.find(v => v.versionId === version1)
    const v2 = note.versions.find(v => v.versionId === version2)
    
    if (!v1 || !v2) {
      throw new Error('Version not found')
    }
    
    return this.diffService.generateDiff(v1.content, v2.content)
  }
  
  // 版本恢复
  async restoreVersion(noteId: string, versionId: string, options: RestoreOptions): Promise<Note> {
    const note = await this.noteRepository.findById(noteId)
    const targetVersion = note.versions.find(v => v.versionId === versionId)
    
    if (!targetVersion) {
      throw new Error('Version not found')
    }
    
    // 可选：创建当前状态的备份版本
    if (options.createBackup) {
      await this.createVersion(noteId, {
        changeDescription: 'Backup before restore',
        changeType: 'manual',
        userId: options.userId
      })
    }
    
    // 恢复内容
    const updatedNote = await this.noteRepository.updateOne(noteId, {
      $set: {
        content: targetVersion.content,
        contentHtml: targetVersion.contentHtml,
        'metadata.lastEditedAt': new Date(),
        updatedAt: new Date()
      }
    })
    
    // 更新搜索索引
    await this.searchService.updateDocument(noteId, {
      content: targetVersion.content,
      updatedAt: new Date()
    })
    
    return updatedNote
  }
}
```

### 文件管理系统
```typescript
class FileService {
  private ossClient: OSS
  private allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf']
  private maxFileSize = 10 * 1024 * 1024 // 10MB
  
  async uploadFile(file: Express.Multer.File, userId: string, noteId?: string): Promise<FileInfo> {
    // 1. 文件验证
    this.validateFile(file)
    
    // 2. 生成文件路径
    const fileKey = this.generateFileKey(userId, file.originalname)
    
    // 3. 上传到OSS
    const uploadResult = await this.ossClient.put(fileKey, file.buffer, {
      headers: {
        'Content-Type': file.mimetype,
        'Cache-Control': 'public, max-age=31536000' // 1年缓存
      }
    })
    
    // 4. 生成缩略图（如果是图片）
    let thumbnailUrl: string | undefined
    if (file.mimetype.startsWith('image/')) {
      thumbnailUrl = await this.generateThumbnail(fileKey, file.buffer)
    }
    
    // 5. 保存文件信息
    const fileInfo: FileInfo = {
      id: generateUUID(),
      filename: fileKey,
      originalName: file.originalname,
      mimeType: file.mimetype,
      size: file.size,
      url: uploadResult.url,
      thumbnailUrl,
      uploadedAt: new Date()
    }
    
    // 6. 关联到笔记（如果指定）
    if (noteId) {
      await this.noteRepository.updateOne(noteId, {
        $push: { attachments: fileInfo }
      })
    }
    
    return fileInfo
  }
  
  private async generateThumbnail(fileKey: string, buffer: Buffer): Promise<string> {
    const thumbnailBuffer = await sharp(buffer)
      .resize(300, 300, { fit: 'inside', withoutEnlargement: true })
      .jpeg({ quality: 80 })
      .toBuffer()
    
    const thumbnailKey = fileKey.replace(/\.[^.]+$/, '_thumb.jpg')
    const result = await this.ossClient.put(thumbnailKey, thumbnailBuffer)
    
    return result.url
  }
}
```

---

## 🔍 搜索功能实现

### 全文搜索服务
```typescript
class SearchService {
  private esClient: Client
  private indexName = 'noteai_notes'
  
  async searchNotes(query: SearchQuery): Promise<SearchResult> {
    const searchBody = this.buildSearchQuery(query)
    
    const response = await this.esClient.search({
      index: this.indexName,
      body: searchBody
    })
    
    return this.processSearchResponse(response)
  }
  
  private buildSearchQuery(query: SearchQuery): any {
    const must: any[] = []
    const filter: any[] = []
    
    // 文本搜索
    if (query.text) {
      must.push({
        multi_match: {
          query: query.text,
          fields: ['title^3', 'content^2', 'tags^2'],
          type: 'best_fields',
          fuzziness: 'AUTO'
        }
      })
    }
    
    // 用户过滤
    filter.push({ term: { userId: query.userId } })
    
    // 分类过滤
    if (query.categoryId) {
      filter.push({ term: { categoryId: query.categoryId } })
    }
    
    // 标签过滤
    if (query.tags && query.tags.length > 0) {
      filter.push({ terms: { tags: query.tags } })
    }
    
    // 状态过滤
    if (query.status) {
      filter.push({ term: { status: query.status } })
    }
    
    // 时间范围过滤
    if (query.dateRange) {
      filter.push({
        range: {
          createdAt: {
            gte: query.dateRange.from,
            lte: query.dateRange.to
          }
        }
      })
    }
    
    return {
      query: {
        bool: {
          must,
          filter
        }
      },
      sort: this.buildSortClause(query.sortBy, query.sortOrder),
      from: (query.page - 1) * query.limit,
      size: query.limit,
      highlight: {
        fields: {
          title: {},
          content: {
            fragment_size: 150,
            number_of_fragments: 3
          }
        }
      }
    }
  }
}
```

---

## 📈 性能优化

### 缓存策略
```typescript
class NoteCacheService {
  private redis: Redis
  
  // 热点笔记缓存
  async cacheHotNote(noteId: string, note: Note): Promise<void> {
    const cacheKey = `note:hot:${noteId}`
    await this.redis.setex(cacheKey, 3600, JSON.stringify(note)) // 1小时缓存
  }
  
  // 用户笔记列表缓存
  async cacheUserNotesList(userId: string, filters: any, notes: Note[]): Promise<void> {
    const cacheKey = `notes:user:${userId}:${this.hashFilters(filters)}`
    await this.redis.setex(cacheKey, 600, JSON.stringify(notes)) // 10分钟缓存
  }
  
  // 搜索结果缓存
  async cacheSearchResults(query: SearchQuery, results: SearchResult): Promise<void> {
    const cacheKey = `search:${this.hashQuery(query)}`
    await this.redis.setex(cacheKey, 300, JSON.stringify(results)) // 5分钟缓存
  }
}
```

### 数据库优化
```javascript
// MongoDB索引优化
db.notes.createIndex({ "userId": 1, "createdAt": -1 })
db.notes.createIndex({ "userId": 1, "status": 1, "updatedAt": -1 })
db.notes.createIndex({ "userId": 1, "categoryId": 1 })
db.notes.createIndex({ "userId": 1, "tags": 1 })
db.notes.createIndex({ "isPublic": 1, "status": 1, "createdAt": -1 })
db.notes.createIndex({ "shareSettings.shareUrl": 1 })

// 复合索引用于复杂查询
db.notes.createIndex({ 
  "userId": 1, 
  "status": 1, 
  "categoryId": 1, 
  "createdAt": -1 
})

// TTL索引用于自动保存数据清理
db.autoSaves.createIndex({ "expiresAt": 1 }, { expireAfterSeconds: 0 })
```

---

## 🧪 测试策略

### 单元测试
```typescript
describe('NoteService', () => {
  describe('createNote', () => {
    it('should create note with valid data', async () => {
      const noteData = {
        title: 'Test Note',
        content: '# Test Content',
        userId: 'test-user-id'
      }
      
      const note = await noteService.createNote(noteData)
      
      expect(note.title).toBe(noteData.title)
      expect(note.content).toBe(noteData.content)
      expect(note.contentHtml).toContain('<h1>Test Content</h1>')
      expect(note.status).toBe('draft')
    })
  })
  
  describe('autoSave', () => {
    it('should handle version conflicts', async () => {
      // 测试版本冲突处理
    })
  })
})
```

---

## 📊 监控指标

### 业务指标
- **笔记创建率**: 用户平均每天创建的笔记数
- **编辑活跃度**: 用户编辑笔记的频率
- **自动保存成功率**: 自动保存的成功率
- **搜索使用率**: 用户使用搜索功能的频率

### 技术指标
- **API响应时间**: 各API端点的响应时间
- **数据库查询性能**: MongoDB查询延迟
- **搜索性能**: Elasticsearch查询延迟
- **文件上传成功率**: 文件上传的成功率

---

**服务状态**: ✅ 架构设计完成  
**开发就绪度**: 🚀 95% - 可立即开始开发  
**相关Story**: 所有Story都需要此服务的笔记管理功能
