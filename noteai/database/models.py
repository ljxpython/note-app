#!/usr/bin/env python3
"""
SQLite数据库模型定义
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    """生成UUID"""
    return str(uuid.uuid4())

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # 用户信息
    avatar_url = Column(String(500))
    bio = Column(Text)
    location = Column(String(100))
    website = Column(String(255))
    
    # 权限和状态
    role = Column(String(20), default="user")  # user, premium_user, moderator, admin, super_admin
    status = Column(String(20), default="active")  # active, inactive, suspended, deleted
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime)
    
    # 关系
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    ai_usage = relationship("AIUsage", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

class Category(Base):
    """分类模型"""
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    color = Column(String(7))  # 十六进制颜色代码
    icon = Column(String(50))
    parent_id = Column(String, ForeignKey("categories.id"))
    
    # 统计信息
    notes_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="categories")
    notes = relationship("Note", back_populates="category")
    parent = relationship("Category", remote_side=[id])
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, user_id={self.user_id})>"

class Note(Base):
    """笔记模型"""
    __tablename__ = "notes"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    category_id = Column(String, ForeignKey("categories.id"))
    
    # 内容
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    content_html = Column(Text)  # 渲染后的HTML
    excerpt = Column(String(500))  # 摘要
    
    # 统计信息
    word_count = Column(Integer, default=0)
    reading_time = Column(Integer, default=0)  # 分钟
    
    # 标签（JSON数组）
    tags = Column(JSON, default=list)
    
    # 状态和设置
    status = Column(String(20), default="draft")  # draft, published, archived, deleted
    is_public = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    
    # AI相关
    ai_optimized = Column(Boolean, default=False)
    ai_classified = Column(Boolean, default=False)
    ai_suggestions = Column(JSON)  # AI建议
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    published_at = Column(DateTime)
    
    # 关系
    user = relationship("User", back_populates="notes")
    category = relationship("Category", back_populates="notes")
    ai_operations = relationship("AIOperation", back_populates="note", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Note(id={self.id}, title={self.title[:50]}, user_id={self.user_id})>"

class AIUsage(Base):
    """AI使用记录"""
    __tablename__ = "ai_usage"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # 使用信息
    operation_type = Column(String(50), nullable=False)  # optimize, classify, writing_assistance
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    
    # 请求和响应
    request_data = Column(JSON)
    response_data = Column(JSON)
    
    # 性能指标
    processing_time = Column(Float)  # 秒
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    user = relationship("User", back_populates="ai_usage")
    
    def __repr__(self):
        return f"<AIUsage(id={self.id}, operation_type={self.operation_type}, user_id={self.user_id})>"

class AIOperation(Base):
    """AI操作记录"""
    __tablename__ = "ai_operations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    note_id = Column(String, ForeignKey("notes.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # 操作信息
    operation_type = Column(String(50), nullable=False)
    agent_name = Column(String(100))  # AutoGen Agent名称
    
    # 输入和输出
    input_text = Column(Text)
    output_text = Column(Text)
    suggestions = Column(JSON)
    
    # 质量指标
    confidence = Column(Float)
    improvement_score = Column(Float)
    user_rating = Column(Integer)  # 1-5星评分
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    note = relationship("Note", back_populates="ai_operations")
    
    def __repr__(self):
        return f"<AIOperation(id={self.id}, operation_type={self.operation_type}, note_id={self.note_id})>"

class UserSession(Base):
    """用户会话"""
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # 会话信息
    session_token = Column(String(255), unique=True, nullable=False)
    refresh_token = Column(String(255), unique=True)
    device_info = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # 状态
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    last_accessed_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"

class SystemConfig(Base):
    """系统配置"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSON)
    description = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemConfig(key={self.key}, value={self.value})>"

class UserFeedback(Base):
    """用户反馈"""
    __tablename__ = "user_feedback"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))

    # 反馈内容
    type = Column(String(50), nullable=False)  # bug, feature, improvement, general
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50))  # ui, performance, ai, auth, other

    # 优先级和状态
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    status = Column(String(20), default="open")  # open, in_progress, resolved, closed

    # 技术信息
    browser_info = Column(JSON)
    device_info = Column(JSON)
    page_url = Column(String(500))
    user_agent = Column(Text)

    # 评分
    rating = Column(Integer)  # 1-5星评分

    # 管理员处理
    admin_response = Column(Text)
    admin_id = Column(String, ForeignKey("users.id"))
    resolved_at = Column(DateTime)

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", foreign_keys=[user_id])
    admin = relationship("User", foreign_keys=[admin_id])

    def __repr__(self):
        return f"<UserFeedback(id={self.id}, type={self.type}, title={self.title[:30]})>"

class FeedbackAttachment(Base):
    """反馈附件"""
    __tablename__ = "feedback_attachments"

    id = Column(String, primary_key=True, default=generate_uuid)
    feedback_id = Column(String, ForeignKey("user_feedback.id"), nullable=False)

    # 文件信息
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    file_path = Column(String(500))

    # 时间戳
    created_at = Column(DateTime, default=func.now())

    # 关系
    feedback = relationship("UserFeedback", backref="attachments")

    def __repr__(self):
        return f"<FeedbackAttachment(id={self.id}, filename={self.filename})>"

class AuditLog(Base):
    """审计日志"""
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))

    # 操作信息
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String)

    # 详细信息
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)

    # 时间戳
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"
