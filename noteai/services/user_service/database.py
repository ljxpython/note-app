"""
用户服务数据库连接
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from .models import Base
from ...shared.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# 创建数据库引擎
engine = create_engine(
    settings.database.postgres_url,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,  # 开发环境下显示SQL
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def init_db() -> None:
    """初始化数据库"""
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # 创建默认数据
        await create_default_data()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def create_default_data() -> None:
    """创建默认数据"""
    db = SessionLocal()
    try:
        from .models import User, UserRole, UserStatus, UserAIQuota
        from ...shared.utils.auth import hash_password
        from datetime import datetime, timedelta
        
        # 检查是否已有管理员用户
        admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()
        
        if not admin_user:
            # 创建默认管理员用户
            admin_password = hash_password("admin123456")  # 生产环境应该使用随机密码
            admin_user = User(
                email="admin@noteai.com",
                username="admin",
                password_hash=admin_password,
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                is_verified=True,
                email_verified=True
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            # 为管理员创建AI配额
            admin_quota = UserAIQuota(
                user_id=admin_user.id,
                plan_type="admin",
                monthly_limit=10000,
                daily_limit=1000,
                monthly_reset_date=datetime.utcnow().replace(day=1) + timedelta(days=32),
                daily_reset_date=datetime.utcnow() + timedelta(days=1)
            )
            
            db.add(admin_quota)
            db.commit()
            
            logger.info("Default admin user created")
        
    except Exception as e:
        logger.error(f"Failed to create default data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection() -> bool:
    """检查数据库连接"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def get_db_stats() -> dict:
    """获取数据库统计信息"""
    try:
        db = SessionLocal()
        from .models import User, UserSession
        
        stats = {
            "total_users": db.query(User).count(),
            "active_users": db.query(User).filter(User.status == "active").count(),
            "verified_users": db.query(User).filter(User.is_verified == True).count(),
            "active_sessions": db.query(UserSession).filter(UserSession.is_active == True).count(),
        }
        
        db.close()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def create_tables(self):
        """创建表"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """删除表"""
        Base.metadata.drop_all(bind=self.engine)
    
    def reset_database(self):
        """重置数据库"""
        self.drop_tables()
        self.create_tables()
    
    def backup_database(self, backup_path: str):
        """备份数据库"""
        # 这里可以实现数据库备份逻辑
        pass
    
    def restore_database(self, backup_path: str):
        """恢复数据库"""
        # 这里可以实现数据库恢复逻辑
        pass


# 全局数据库管理器实例
db_manager = DatabaseManager()
