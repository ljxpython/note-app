"""
用户服务Pydantic模式
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


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
    """用户基础模式"""
    email: EmailStr = Field(..., description="邮箱地址")
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    location: Optional[str] = Field(None, max_length=100, description="位置")
    website: Optional[str] = Field(None, description="个人网站")


class UserCreate(UserBase):
    """创建用户模式"""
    password: str = Field(..., min_length=8, description="密码")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "username": "testuser",
                "password": "SecurePass123!",
                "bio": "这是我的个人简介",
                "location": "北京"
            }
        }
    )


class UserUpdate(BaseModel):
    """更新用户模式"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    location: Optional[str] = Field(None, max_length=100, description="位置")
    website: Optional[str] = Field(None, description="个人网站")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "newusername",
                "bio": "更新后的个人简介",
                "location": "上海"
            }
        }
    )


class UserResponse(UserBase):
    """用户响应模式"""
    id: str = Field(..., description="用户ID")
    role: UserRole = Field(default=UserRole.USER, description="用户角色")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="用户状态")
    is_verified: bool = Field(default=False, description="是否已验证")
    email_verified: bool = Field(default=False, description="邮箱是否已验证")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    
    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """用户列表响应模式"""
    users: List[UserResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    limit: int = Field(..., description="每页数量")


class LoginRequest(BaseModel):
    """登录请求模式"""
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(default=False, description="记住我")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "remember_me": False
            }
        }
    )


class TokenResponse(BaseModel):
    """Token响应模式"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }
    )


class RefreshTokenRequest(BaseModel):
    """刷新Token请求模式"""
    refresh_token: str = Field(..., description="刷新令牌")


class ChangePasswordRequest(BaseModel):
    """修改密码请求模式"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "OldPass123!",
                "new_password": "NewPass123!",
                "confirm_password": "NewPass123!"
            }
        }
    )


class ResetPasswordRequest(BaseModel):
    """重置密码请求模式"""
    email: EmailStr = Field(..., description="邮箱地址")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com"
            }
        }
    )


class ResetPasswordConfirm(BaseModel):
    """确认重置密码模式"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")


class UserProfileResponse(BaseModel):
    """用户详细资料响应模式"""
    user: UserResponse = Field(..., description="用户基本信息")
    profile: Optional[dict] = Field(None, description="扩展资料")
    statistics: Optional[dict] = Field(None, description="统计信息")
    ai_quota: Optional[dict] = Field(None, description="AI配额信息")


class UserAIQuotaResponse(BaseModel):
    """用户AI配额响应模式"""
    plan_type: str = Field(..., description="计划类型")
    monthly_limit: int = Field(..., description="月度限制")
    monthly_used: int = Field(..., description="月度已使用")
    daily_limit: int = Field(..., description="日限制")
    daily_used: int = Field(..., description="日已使用")
    monthly_remaining: int = Field(..., description="月度剩余")
    daily_remaining: int = Field(..., description="日剩余")
    reset_date: datetime = Field(..., description="重置日期")
    
    model_config = ConfigDict(from_attributes=True)


class UserPermissionResponse(BaseModel):
    """用户权限响应模式"""
    permissions: List[str] = Field(..., description="权限列表")
    roles: List[str] = Field(..., description="角色列表")


class UserSessionResponse(BaseModel):
    """用户会话响应模式"""
    id: str = Field(..., description="会话ID")
    device_info: Optional[str] = Field(None, description="设备信息")
    ip_address: Optional[str] = Field(None, description="IP地址")
    created_at: datetime = Field(..., description="创建时间")
    last_accessed_at: datetime = Field(..., description="最后访问时间")
    is_active: bool = Field(..., description="是否活跃")
    
    model_config = ConfigDict(from_attributes=True)


class UserStatisticsResponse(BaseModel):
    """用户统计响应模式"""
    notes_count: int = Field(default=0, description="笔记数量")
    public_notes_count: int = Field(default=0, description="公开笔记数量")
    followers_count: int = Field(default=0, description="粉丝数量")
    following_count: int = Field(default=0, description="关注数量")
    ai_requests_count: int = Field(default=0, description="AI请求数量")
    total_words: int = Field(default=0, description="总字数")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "notes_count": 25,
                "public_notes_count": 10,
                "followers_count": 15,
                "following_count": 8,
                "ai_requests_count": 120,
                "total_words": 50000
            }
        }
    )


class EmailVerificationRequest(BaseModel):
    """邮箱验证请求模式"""
    email: EmailStr = Field(..., description="邮箱地址")


class EmailVerificationConfirm(BaseModel):
    """确认邮箱验证模式"""
    token: str = Field(..., description="验证令牌")


class UserSearchRequest(BaseModel):
    """用户搜索请求模式"""
    query: str = Field(..., min_length=1, description="搜索关键词")
    role: Optional[UserRole] = Field(None, description="角色过滤")
    status: Optional[UserStatus] = Field(None, description="状态过滤")
    verified_only: bool = Field(default=False, description="仅已验证用户")
    page: int = Field(default=1, ge=1, description="页码")
    limit: int = Field(default=20, ge=1, le=100, description="每页数量")


class UserBatchUpdateRequest(BaseModel):
    """批量更新用户请求模式"""
    user_ids: List[str] = Field(..., description="用户ID列表")
    updates: dict = Field(..., description="更新字段")


class UserExportRequest(BaseModel):
    """用户导出请求模式"""
    format: str = Field(default="csv", description="导出格式")
    fields: Optional[List[str]] = Field(None, description="导出字段")
    filters: Optional[dict] = Field(None, description="过滤条件")
