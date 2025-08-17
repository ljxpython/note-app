#!/usr/bin/env python3
"""
数据库连接和配置
"""
import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging

from .models import Base

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, database_url: str = None):
        """初始化数据库管理器"""
        if database_url is None:
            # 默认使用SQLite数据库
            db_path = os.getenv("DATABASE_PATH", "noteai.db")
            database_url = f"sqlite:///{db_path}"
        
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """初始化数据库引擎"""
        try:
            # SQLite特殊配置
            if self.database_url.startswith("sqlite"):
                self.engine = create_engine(
                    self.database_url,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 20
                    },
                    echo=os.getenv("DATABASE_DEBUG", "false").lower() == "true"
                )
                
                # 启用SQLite外键约束
                @event.listens_for(self.engine, "connect")
                def set_sqlite_pragma(dbapi_connection, connection_record):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                    cursor.execute("PRAGMA cache_size=1000")
                    cursor.execute("PRAGMA temp_store=MEMORY")
                    cursor.close()
            
            else:
                # 其他数据库配置
                self.engine = create_engine(
                    self.database_url,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    echo=os.getenv("DATABASE_DEBUG", "false").lower() == "true"
                )
            
            # 创建会话工厂
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"✅ 数据库引擎初始化成功: {self.database_url}")
            
        except Exception as e:
            logger.error(f"❌ 数据库引擎初始化失败: {e}")
            raise
    
    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ 数据库表创建成功")
        except Exception as e:
            logger.error(f"❌ 数据库表创建失败: {e}")
            raise
    
    def drop_tables(self):
        """删除所有表"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("✅ 数据库表删除成功")
        except Exception as e:
            logger.error(f"❌ 数据库表删除失败: {e}")
            raise
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self):
        """数据库会话上下文管理器"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """数据库健康检查"""
        try:
            with self.session_scope() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"❌ 数据库健康检查失败: {e}")
            return False
    
    def get_database_info(self) -> dict:
        """获取数据库信息"""
        try:
            with self.session_scope() as session:
                # 获取数据库版本
                if self.database_url.startswith("sqlite"):
                    result = session.execute(text("SELECT sqlite_version()")).fetchone()
                    db_version = result[0] if result else "unknown"
                    db_type = "SQLite"
                else:
                    db_version = "unknown"
                    db_type = "Other"

                # 获取表信息
                if self.database_url.startswith("sqlite"):
                    tables_result = session.execute(
                        text("SELECT name FROM sqlite_master WHERE type='table'")
                    ).fetchall()
                    tables = [row[0] for row in tables_result]
                else:
                    tables = []
                
                return {
                    "database_type": db_type,
                    "database_version": db_version,
                    "database_url": self.database_url.split("://")[0] + "://***",
                    "tables": tables,
                    "table_count": len(tables)
                }
        except Exception as e:
            logger.error(f"❌ 获取数据库信息失败: {e}")
            return {
                "database_type": "unknown",
                "database_version": "unknown",
                "database_url": "unknown",
                "tables": [],
                "table_count": 0,
                "error": str(e)
            }

# 全局数据库管理器实例
db_manager = DatabaseManager()

# 便捷函数
def get_db() -> Session:
    """获取数据库会话（用于FastAPI依赖注入）"""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """初始化数据库"""
    try:
        logger.info("🚀 开始初始化数据库...")
        
        # 创建表
        db_manager.create_tables()
        
        # 插入默认数据
        _insert_default_data()
        
        logger.info("✅ 数据库初始化完成")
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise

def _insert_default_data():
    """插入默认数据"""
    try:
        from .models import SystemConfig, Category
        
        with db_manager.session_scope() as session:
            # 检查是否已有数据
            config_count = session.query(SystemConfig).count()
            if config_count > 0:
                logger.info("数据库已有数据，跳过默认数据插入")
                return
            
            # 插入系统配置
            default_configs = [
                {
                    "key": "app_version",
                    "value": "1.0.0",
                    "description": "应用版本号"
                },
                {
                    "key": "ai_quota_daily_limit",
                    "value": 50,
                    "description": "每日AI使用配额限制"
                },
                {
                    "key": "ai_quota_monthly_limit", 
                    "value": 1000,
                    "description": "每月AI使用配额限制"
                },
                {
                    "key": "max_note_length",
                    "value": 100000,
                    "description": "笔记最大长度限制"
                },
                {
                    "key": "supported_languages",
                    "value": ["zh-CN", "en-US"],
                    "description": "支持的语言列表"
                }
            ]
            
            for config_data in default_configs:
                config = SystemConfig(**config_data)
                session.add(config)
            
            logger.info("✅ 默认系统配置插入成功")
            
    except Exception as e:
        logger.error(f"❌ 插入默认数据失败: {e}")
        raise

def reset_database():
    """重置数据库"""
    try:
        logger.warning("⚠️  开始重置数据库...")
        
        # 删除所有表
        db_manager.drop_tables()
        
        # 重新创建表
        db_manager.create_tables()
        
        # 插入默认数据
        _insert_default_data()
        
        logger.info("✅ 数据库重置完成")
        
    except Exception as e:
        logger.error(f"❌ 数据库重置失败: {e}")
        raise

def backup_database(backup_path: str = None):
    """备份数据库"""
    try:
        if not backup_path:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"noteai_backup_{timestamp}.db"
        
        if db_manager.database_url.startswith("sqlite"):
            import shutil
            db_path = db_manager.database_url.replace("sqlite:///", "")
            shutil.copy2(db_path, backup_path)
            logger.info(f"✅ 数据库备份成功: {backup_path}")
            return backup_path
        else:
            logger.warning("⚠️  当前数据库类型不支持简单备份")
            return None
            
    except Exception as e:
        logger.error(f"❌ 数据库备份失败: {e}")
        raise

def restore_database(backup_path: str):
    """恢复数据库"""
    try:
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"备份文件不存在: {backup_path}")
        
        if db_manager.database_url.startswith("sqlite"):
            import shutil
            db_path = db_manager.database_url.replace("sqlite:///", "")
            shutil.copy2(backup_path, db_path)
            logger.info(f"✅ 数据库恢复成功: {backup_path}")
        else:
            logger.warning("⚠️  当前数据库类型不支持简单恢复")
            
    except Exception as e:
        logger.error(f"❌ 数据库恢复失败: {e}")
        raise
