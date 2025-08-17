"""
共享数据模型基类
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


class TimestampMixin(BaseModel):
    """时间戳混入类"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class APIResponse(BaseModel):
    """统一API响应格式"""
    success: bool = True
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )


class ErrorResponse(BaseModel):
    """错误响应格式"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    limit: int = Field(default=20, ge=1, le=100, description="每页数量")
    
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit


class PaginationResponse(BaseModel):
    """分页响应"""
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(cls, page: int, limit: int, total: int) -> "PaginationResponse":
        total_pages = (total + limit - 1) // limit
        return cls(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


# 用户相关模型
class UserRole(str, Enum):
    """用户角色"""
    USER = "user"
    PREMIUM_USER = "premium_user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserBase(BaseModel):
    """用户基础模型"""
    email: str = Field(..., description="邮箱地址")
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    location: Optional[str] = Field(None, max_length=100, description="位置")
    website: Optional[str] = Field(None, description="个人网站")


class UserCreate(UserBase):
    """创建用户模型"""
    password: str = Field(..., min_length=8, description="密码")


class UserUpdate(BaseModel):
    """更新用户模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = None


class UserResponse(UserBase, TimestampMixin):
    """用户响应模型"""
    id: str = Field(..., description="用户ID")
    role: UserRole = Field(default=UserRole.USER, description="用户角色")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="用户状态")
    is_verified: bool = Field(default=False, description="是否已验证")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")


# 认证相关模型
class LoginRequest(BaseModel):
    """登录请求"""
    email: str = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(default=False, description="记住我")


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str = Field(..., description="刷新令牌")


# 笔记相关模型
class NoteStatus(str, Enum):
    """笔记状态"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class SharePermission(str, Enum):
    """分享权限"""
    PRIVATE = "private"
    LINK = "link"
    PUBLIC = "public"
    CIRCLE = "circle"


class NoteBase(BaseModel):
    """笔记基础模型"""
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    content: str = Field(default="", description="内容")
    category_id: Optional[str] = Field(None, description="分类ID")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    is_public: bool = Field(default=False, description="是否公开")


class NoteCreate(NoteBase):
    """创建笔记模型"""
    pass


class NoteUpdate(BaseModel):
    """更新笔记模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    category_id: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[NoteStatus] = None
    is_public: Optional[bool] = None


class NoteResponse(NoteBase, TimestampMixin):
    """笔记响应模型"""
    id: str = Field(..., description="笔记ID")
    user_id: str = Field(..., description="用户ID")
    status: NoteStatus = Field(default=NoteStatus.DRAFT, description="状态")
    word_count: int = Field(default=0, description="字数")
    reading_time: int = Field(default=0, description="阅读时间(分钟)")
    is_favorite: bool = Field(default=False, description="是否收藏")


# AI相关模型
class OptimizationType(str, Enum):
    """优化类型"""
    GRAMMAR = "grammar"
    EXPRESSION = "expression"
    STRUCTURE = "structure"
    ALL = "all"


class OptimizationRequest(BaseModel):
    """文本优化请求"""
    text: str = Field(..., min_length=1, max_length=10000, description="待优化文本")
    optimization_type: OptimizationType = Field(default=OptimizationType.ALL, description="优化类型")
    user_style: Optional[str] = Field(None, description="用户写作风格")


class OptimizationSuggestion(BaseModel):
    """优化建议"""
    type: str = Field(..., description="建议类型")
    original: str = Field(..., description="原始文本")
    optimized: str = Field(..., description="优化后文本")
    explanation: str = Field(..., description="修改说明")
    confidence: float = Field(..., ge=0, le=1, description="置信度")


class OptimizationResponse(BaseModel):
    """文本优化响应"""
    optimized_text: str = Field(..., description="优化后的完整文本")
    suggestions: List[OptimizationSuggestion] = Field(default_factory=list, description="优化建议列表")
    confidence: float = Field(..., ge=0, le=1, description="整体置信度")
    processing_time: float = Field(..., description="处理时间(秒)")


class ClassificationRequest(BaseModel):
    """内容分类请求"""
    content: str = Field(..., min_length=1, max_length=50000, description="待分类内容")
    existing_categories: List[Dict[str, Any]] = Field(default_factory=list, description="现有分类")


class ClassificationSuggestion(BaseModel):
    """分类建议"""
    category_name: str = Field(..., description="分类名称")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    reasoning: str = Field(..., description="分类理由")


class ClassificationResponse(BaseModel):
    """内容分类响应"""
    suggestions: List[ClassificationSuggestion] = Field(default_factory=list, description="分类建议")
    detected_topics: List[str] = Field(default_factory=list, description="检测到的主题")
    key_phrases: List[str] = Field(default_factory=list, description="关键短语")
    content_type: str = Field(..., description="内容类型")
    processing_time: float = Field(..., description="处理时间(秒)")


# 文件相关模型
class FileInfo(BaseModel):
    """文件信息"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="文件ID")
    filename: str = Field(..., description="文件名")
    original_name: str = Field(..., description="原始文件名")
    mime_type: str = Field(..., description="MIME类型")
    size: int = Field(..., description="文件大小(字节)")
    url: str = Field(..., description="文件URL")
    thumbnail_url: Optional[str] = Field(None, description="缩略图URL")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="上传时间")


# 搜索相关模型
class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., min_length=1, description="搜索关键词")
    category_id: Optional[str] = Field(None, description="分类ID")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    user_id: Optional[str] = Field(None, description="用户ID")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")


class SearchResult(BaseModel):
    """搜索结果"""
    id: str = Field(..., description="文档ID")
    title: str = Field(..., description="标题")
    excerpt: str = Field(..., description="摘要")
    score: float = Field(..., description="相关性评分")
    highlights: List[str] = Field(default_factory=list, description="高亮片段")
    created_at: datetime = Field(..., description="创建时间")


class SearchResponse(BaseModel):
    """搜索响应"""
    results: List[SearchResult] = Field(default_factory=list, description="搜索结果")
    total: int = Field(..., description="总数")
    took: int = Field(..., description="耗时(毫秒)")
    pagination: PaginationResponse = Field(..., description="分页信息")
