"""
用户服务数据模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    USER = "user"
    PREMIUM_USER = "premium_user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class UserStatus(str, enum.Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    # 基础字段
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # 个人信息
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # 状态字段
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    phone_verified = Column(Boolean, default=False, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "location": self.location,
            "website": self.website,
            "phone": self.phone,
            "role": self.role.value,
            "status": self.status.value,
            "is_verified": self.is_verified,
            "email_verified": self.email_verified,
            "phone_verified": self.phone_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }


class UserSession(Base):
    """用户会话模型"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # 设备信息
    device_info = Column(Text, nullable=True)  # JSON格式
    ip_address = Column(String(45), nullable=True)  # 支持IPv6
    user_agent = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"


class UserPermission(Base):
    """用户权限模型"""
    __tablename__ = "user_permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    permission_name = Column(String(100), nullable=False)
    resource = Column(String(50), nullable=False)  # 资源类型
    action = Column(String(50), nullable=False)    # 操作类型
    
    # 权限元数据
    granted_by = Column(UUID(as_uuid=True), nullable=True)  # 授权者
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # 权限过期时间
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<UserPermission(user_id={self.user_id}, permission={self.permission_name})>"


class UserProfile(Base):
    """用户扩展资料模型"""
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    
    # 扩展个人信息
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    birth_date = Column(DateTime, nullable=True)
    gender = Column(String(10), nullable=True)
    
    # 偏好设置
    language = Column(String(10), default="zh", nullable=False)
    timezone = Column(String(50), default="Asia/Shanghai", nullable=False)
    theme = Column(String(20), default="light", nullable=False)  # light, dark, auto
    
    # 通知设置
    email_notifications = Column(Boolean, default=True, nullable=False)
    push_notifications = Column(Boolean, default=True, nullable=False)
    marketing_emails = Column(Boolean, default=False, nullable=False)
    
    # 隐私设置
    profile_visibility = Column(String(20), default="public", nullable=False)  # public, friends, private
    show_email = Column(Boolean, default=False, nullable=False)
    show_location = Column(Boolean, default=True, nullable=False)
    
    # 统计信息
    notes_count = Column(String, default=0, nullable=False)
    followers_count = Column(String, default=0, nullable=False)
    following_count = Column(String, default=0, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id})>"


class UserOAuthAccount(Base):
    """第三方登录账户模型"""
    __tablename__ = "user_oauth_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # OAuth信息
    provider = Column(String(50), nullable=False)  # github, wechat, google等
    provider_user_id = Column(String(255), nullable=False)
    provider_username = Column(String(255), nullable=True)
    provider_email = Column(String(255), nullable=True)
    
    # Token信息
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<UserOAuthAccount(user_id={self.user_id}, provider={self.provider})>"


class UserAIQuota(Base):
    """用户AI配额模型"""
    __tablename__ = "user_ai_quotas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    
    # 配额设置
    plan_type = Column(String(20), default="free", nullable=False)  # free, premium, team
    monthly_limit = Column(String, default=50, nullable=False)
    monthly_used = Column(String, default=0, nullable=False)
    daily_limit = Column(String, default=10, nullable=False)
    daily_used = Column(String, default=0, nullable=False)
    
    # 重置时间
    monthly_reset_date = Column(DateTime, nullable=False)
    daily_reset_date = Column(DateTime, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<UserAIQuota(user_id={self.user_id}, plan={self.plan_type})>"
    
    def can_use_ai(self, request_count: int = 1) -> bool:
        """检查是否可以使用AI功能"""
        return (self.daily_used + request_count <= self.daily_limit and 
                self.monthly_used + request_count <= self.monthly_limit)
    
    def use_quota(self, request_count: int = 1) -> bool:
        """使用配额"""
        if self.can_use_ai(request_count):
            self.daily_used += request_count
            self.monthly_used += request_count
            return True
        return False
