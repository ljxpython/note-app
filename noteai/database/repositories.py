#!/usr/bin/env python3
"""
数据访问层 - Repository模式
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, timedelta
import logging

from .models import User, Note, Category, AIUsage, AIOperation, UserSession, SystemConfig, AuditLog, UserFeedback, FeedbackAttachment
from .connection import db_manager

logger = logging.getLogger(__name__)

class BaseRepository:
    """基础Repository类"""
    
    def __init__(self, session: Session = None):
        self.session = session or db_manager.get_session()
        self._should_close_session = session is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close_session:
            self.session.close()

class UserRepository(BaseRepository):
    """用户数据访问层"""
    
    def create_user(self, email: str, username: str, password_hash: str, **kwargs) -> User:
        """创建用户"""
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            **kwargs
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        return self.session.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.session.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.session.query(User).filter(User.username == username).first()
    
    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """更新用户信息"""
        user = self.get_user_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(user)
        return user
    
    def update_last_login(self, user_id: str) -> Optional[User]:
        """更新最后登录时间"""
        return self.update_user(user_id, last_login_at=datetime.utcnow())
    
    def get_users(self, skip: int = 0, limit: int = 100, status: str = None) -> List[User]:
        """获取用户列表"""
        query = self.session.query(User)
        if status:
            query = query.filter(User.status == status)
        return query.offset(skip).limit(limit).all()
    
    def count_users(self, status: str = None) -> int:
        """统计用户数量"""
        query = self.session.query(User)
        if status:
            query = query.filter(User.status == status)
        return query.count()

class NoteRepository(BaseRepository):
    """笔记数据访问层"""
    
    def create_note(self, user_id: str, title: str, content: str, **kwargs) -> Note:
        """创建笔记"""
        note = Note(
            user_id=user_id,
            title=title,
            content=content,
            word_count=len(content),
            reading_time=max(1, len(content) // 200),  # 简单计算阅读时间
            **kwargs
        )
        self.session.add(note)
        self.session.commit()
        self.session.refresh(note)
        return note
    
    def get_note_by_id(self, note_id: str, user_id: str = None) -> Optional[Note]:
        """根据ID获取笔记"""
        query = self.session.query(Note).filter(Note.id == note_id)
        if user_id:
            query = query.filter(Note.user_id == user_id)
        return query.first()
    
    def get_notes(self, user_id: str, skip: int = 0, limit: int = 20, 
                  category_id: str = None, tags: List[str] = None, 
                  search: str = None, status: str = None) -> List[Note]:
        """获取笔记列表"""
        query = self.session.query(Note).filter(Note.user_id == user_id)
        
        if category_id:
            query = query.filter(Note.category_id == category_id)
        
        if tags:
            # SQLite JSON查询
            for tag in tags:
                query = query.filter(Note.tags.contains(tag))
        
        if search:
            query = query.filter(
                or_(
                    Note.title.contains(search),
                    Note.content.contains(search)
                )
            )
        
        if status:
            query = query.filter(Note.status == status)
        else:
            query = query.filter(Note.status != "deleted")
        
        return query.order_by(desc(Note.updated_at)).offset(skip).limit(limit).all()
    
    def count_notes(self, user_id: str, category_id: str = None, 
                    tags: List[str] = None, search: str = None, status: str = None) -> int:
        """统计笔记数量"""
        query = self.session.query(Note).filter(Note.user_id == user_id)
        
        if category_id:
            query = query.filter(Note.category_id == category_id)
        
        if tags:
            for tag in tags:
                query = query.filter(Note.tags.contains(tag))
        
        if search:
            query = query.filter(
                or_(
                    Note.title.contains(search),
                    Note.content.contains(search)
                )
            )
        
        if status:
            query = query.filter(Note.status == status)
        else:
            query = query.filter(Note.status != "deleted")
        
        return query.count()
    
    def update_note(self, note_id: str, user_id: str, **kwargs) -> Optional[Note]:
        """更新笔记"""
        note = self.get_note_by_id(note_id, user_id)
        if note:
            for key, value in kwargs.items():
                if hasattr(note, key):
                    setattr(note, key, value)
            
            # 更新统计信息
            if 'content' in kwargs:
                note.word_count = len(kwargs['content'])
                note.reading_time = max(1, len(kwargs['content']) // 200)
            
            note.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(note)
        return note
    
    def delete_note(self, note_id: str, user_id: str, soft_delete: bool = True) -> bool:
        """删除笔记"""
        note = self.get_note_by_id(note_id, user_id)
        if note:
            if soft_delete:
                note.status = "deleted"
                note.updated_at = datetime.utcnow()
                self.session.commit()
            else:
                self.session.delete(note)
                self.session.commit()
            return True
        return False
    
    def search_notes(self, user_id: str, query: str, skip: int = 0, limit: int = 20) -> List[Note]:
        """全文搜索笔记"""
        # 简单的搜索实现
        notes = self.session.query(Note).filter(
            and_(
                Note.user_id == user_id,
                Note.status != "deleted",
                or_(
                    Note.title.contains(query),
                    Note.content.contains(query),
                    Note.tags.contains(query)
                )
            )
        ).order_by(desc(Note.updated_at)).offset(skip).limit(limit).all()
        
        return notes
    
    def get_favorite_notes(self, user_id: str, skip: int = 0, limit: int = 20) -> List[Note]:
        """获取收藏笔记"""
        return self.session.query(Note).filter(
            and_(
                Note.user_id == user_id,
                Note.is_favorite == True,
                Note.status != "deleted"
            )
        ).order_by(desc(Note.updated_at)).offset(skip).limit(limit).all()

class CategoryRepository(BaseRepository):
    """分类数据访问层"""
    
    def create_category(self, user_id: str, name: str, **kwargs) -> Category:
        """创建分类"""
        category = Category(
            user_id=user_id,
            name=name,
            **kwargs
        )
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return category
    
    def get_category_by_id(self, category_id: str, user_id: str = None) -> Optional[Category]:
        """根据ID获取分类"""
        query = self.session.query(Category).filter(Category.id == category_id)
        if user_id:
            query = query.filter(Category.user_id == user_id)
        return query.first()
    
    def get_categories(self, user_id: str) -> List[Category]:
        """获取用户的所有分类"""
        return self.session.query(Category).filter(Category.user_id == user_id).all()
    
    def update_category(self, category_id: str, user_id: str, **kwargs) -> Optional[Category]:
        """更新分类"""
        category = self.get_category_by_id(category_id, user_id)
        if category:
            for key, value in kwargs.items():
                if hasattr(category, key):
                    setattr(category, key, value)
            category.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(category)
        return category
    
    def delete_category(self, category_id: str, user_id: str) -> bool:
        """删除分类"""
        category = self.get_category_by_id(category_id, user_id)
        if category:
            # 将该分类下的笔记移到未分类
            self.session.query(Note).filter(Note.category_id == category_id).update(
                {"category_id": None}
            )
            self.session.delete(category)
            self.session.commit()
            return True
        return False
    
    def update_notes_count(self, category_id: str):
        """更新分类下的笔记数量"""
        category = self.session.query(Category).filter(Category.id == category_id).first()
        if category:
            count = self.session.query(Note).filter(
                and_(
                    Note.category_id == category_id,
                    Note.status != "deleted"
                )
            ).count()
            category.notes_count = count
            self.session.commit()

class AIUsageRepository(BaseRepository):
    """AI使用记录数据访问层"""
    
    def create_usage_record(self, user_id: str, operation_type: str, **kwargs) -> AIUsage:
        """创建AI使用记录"""
        usage = AIUsage(
            user_id=user_id,
            operation_type=operation_type,
            **kwargs
        )
        self.session.add(usage)
        self.session.commit()
        self.session.refresh(usage)
        return usage
    
    def get_daily_usage(self, user_id: str, date: datetime = None) -> int:
        """获取每日使用量"""
        if date is None:
            date = datetime.utcnow().date()
        
        start_date = datetime.combine(date, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        
        return self.session.query(AIUsage).filter(
            and_(
                AIUsage.user_id == user_id,
                AIUsage.created_at >= start_date,
                AIUsage.created_at < end_date,
                AIUsage.success == True
            )
        ).count()
    
    def get_monthly_usage(self, user_id: str, year: int = None, month: int = None) -> int:
        """获取每月使用量"""
        now = datetime.utcnow()
        if year is None:
            year = now.year
        if month is None:
            month = now.month
        
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        return self.session.query(AIUsage).filter(
            and_(
                AIUsage.user_id == user_id,
                AIUsage.created_at >= start_date,
                AIUsage.created_at < end_date,
                AIUsage.success == True
            )
        ).count()
    
    def get_usage_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """获取使用统计"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        usage_records = self.session.query(AIUsage).filter(
            and_(
                AIUsage.user_id == user_id,
                AIUsage.created_at >= start_date
            )
        ).all()
        
        stats = {
            "total_operations": len(usage_records),
            "successful_operations": len([r for r in usage_records if r.success]),
            "failed_operations": len([r for r in usage_records if not r.success]),
            "operation_types": {},
            "total_tokens": sum(r.tokens_used or 0 for r in usage_records),
            "total_cost": sum(r.cost or 0 for r in usage_records),
            "avg_processing_time": 0
        }
        
        # 按操作类型统计
        for record in usage_records:
            op_type = record.operation_type
            if op_type not in stats["operation_types"]:
                stats["operation_types"][op_type] = 0
            stats["operation_types"][op_type] += 1
        
        # 计算平均处理时间
        processing_times = [r.processing_time for r in usage_records if r.processing_time]
        if processing_times:
            stats["avg_processing_time"] = sum(processing_times) / len(processing_times)
        
        return stats

class SystemConfigRepository(BaseRepository):
    """系统配置数据访问层"""
    
    def get_config(self, key: str) -> Optional[SystemConfig]:
        """获取配置"""
        return self.session.query(SystemConfig).filter(SystemConfig.key == key).first()
    
    def get_config_value(self, key: str, default=None):
        """获取配置值"""
        config = self.get_config(key)
        return config.value if config else default
    
    def set_config(self, key: str, value: Any, description: str = None) -> SystemConfig:
        """设置配置"""
        config = self.get_config(key)
        if config:
            config.value = value
            if description:
                config.description = description
            config.updated_at = datetime.utcnow()
        else:
            config = SystemConfig(key=key, value=value, description=description)
            self.session.add(config)
        
        self.session.commit()
        self.session.refresh(config)
        return config
    
    def get_all_configs(self) -> List[SystemConfig]:
        """获取所有配置"""
        return self.session.query(SystemConfig).all()

class FeedbackRepository(BaseRepository):
    """用户反馈数据访问层"""

    def create_feedback(self, user_id: str, feedback_type: str, title: str,
                       content: str, **kwargs) -> UserFeedback:
        """创建用户反馈"""
        feedback = UserFeedback(
            user_id=user_id,
            type=feedback_type,
            title=title,
            content=content,
            **kwargs
        )
        self.session.add(feedback)
        self.session.commit()
        self.session.refresh(feedback)
        return feedback

    def get_feedback_by_id(self, feedback_id: str) -> Optional[UserFeedback]:
        """根据ID获取反馈"""
        return self.session.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()

    def get_user_feedback(self, user_id: str, skip: int = 0, limit: int = 20) -> List[UserFeedback]:
        """获取用户的反馈列表"""
        return self.session.query(UserFeedback).filter(
            UserFeedback.user_id == user_id
        ).order_by(desc(UserFeedback.created_at)).offset(skip).limit(limit).all()

    def get_all_feedback(self, skip: int = 0, limit: int = 50,
                        status: str = None, feedback_type: str = None,
                        priority: str = None) -> List[UserFeedback]:
        """获取所有反馈（管理员用）"""
        query = self.session.query(UserFeedback)

        if status:
            query = query.filter(UserFeedback.status == status)
        if feedback_type:
            query = query.filter(UserFeedback.type == feedback_type)
        if priority:
            query = query.filter(UserFeedback.priority == priority)

        return query.order_by(desc(UserFeedback.created_at)).offset(skip).limit(limit).all()

    def update_feedback(self, feedback_id: str, **kwargs) -> Optional[UserFeedback]:
        """更新反馈"""
        feedback = self.get_feedback_by_id(feedback_id)
        if feedback:
            for key, value in kwargs.items():
                if hasattr(feedback, key):
                    setattr(feedback, key, value)
            feedback.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(feedback)
        return feedback

    def respond_to_feedback(self, feedback_id: str, admin_id: str,
                           response: str, status: str = "resolved") -> Optional[UserFeedback]:
        """管理员回复反馈"""
        feedback = self.get_feedback_by_id(feedback_id)
        if feedback:
            feedback.admin_response = response
            feedback.admin_id = admin_id
            feedback.status = status
            feedback.resolved_at = datetime.utcnow()
            feedback.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(feedback)
        return feedback

    def get_feedback_stats(self) -> Dict[str, Any]:
        """获取反馈统计信息"""
        total = self.session.query(UserFeedback).count()
        open_count = self.session.query(UserFeedback).filter(UserFeedback.status == "open").count()
        resolved_count = self.session.query(UserFeedback).filter(UserFeedback.status == "resolved").count()

        # 按类型统计
        type_stats = {}
        types = self.session.query(UserFeedback.type, func.count(UserFeedback.id)).group_by(UserFeedback.type).all()
        for feedback_type, count in types:
            type_stats[feedback_type] = count

        # 按优先级统计
        priority_stats = {}
        priorities = self.session.query(UserFeedback.priority, func.count(UserFeedback.id)).group_by(UserFeedback.priority).all()
        for priority, count in priorities:
            priority_stats[priority] = count

        # 平均评分
        avg_rating = self.session.query(func.avg(UserFeedback.rating)).filter(
            UserFeedback.rating.isnot(None)
        ).scalar() or 0

        return {
            "total": total,
            "open": open_count,
            "resolved": resolved_count,
            "in_progress": total - open_count - resolved_count,
            "type_distribution": type_stats,
            "priority_distribution": priority_stats,
            "average_rating": round(float(avg_rating), 2)
        }

    def search_feedback(self, query: str, skip: int = 0, limit: int = 20) -> List[UserFeedback]:
        """搜索反馈"""
        return self.session.query(UserFeedback).filter(
            or_(
                UserFeedback.title.contains(query),
                UserFeedback.content.contains(query)
            )
        ).order_by(desc(UserFeedback.created_at)).offset(skip).limit(limit).all()
