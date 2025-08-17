"""
共享配置模块
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    
    # PostgreSQL (用户数据)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "noteai"
    postgres_password: str = "noteai_dev_pass"
    postgres_db: str = "noteai_users"
    
    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    # MongoDB (笔记和AI会话)
    mongodb_host: str = "localhost"
    mongodb_port: int = 27017
    mongodb_user: str = "noteai"
    mongodb_password: str = "noteai_dev_pass"
    mongodb_db: str = "noteai_notes"
    
    @property
    def mongodb_url(self) -> str:
        return f"mongodb://{self.mongodb_user}:{self.mongodb_password}@{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_db}"
    
    # Redis (缓存和消息队列)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "noteai_dev_pass"
    redis_db: int = 0
    
    @property
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # Elasticsearch (搜索)
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    elasticsearch_user: Optional[str] = None
    elasticsearch_password: Optional[str] = None
    
    @property
    def elasticsearch_url(self) -> str:
        if self.elasticsearch_user and self.elasticsearch_password:
            return f"http://{self.elasticsearch_user}:{self.elasticsearch_password}@{self.elasticsearch_host}:{self.elasticsearch_port}"
        return f"http://{self.elasticsearch_host}:{self.elasticsearch_port}"


class SecuritySettings(BaseSettings):
    """安全配置"""
    
    # JWT配置
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # 密码配置
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special_chars: bool = True
    
    # CORS配置
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]


class AISettings(BaseSettings):
    """AI服务配置"""
    
    # DeepSeek配置
    deepseek_api_key: str = "your-deepseek-api-key"
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_max_tokens: int = 4000
    deepseek_temperature: float = 0.7
    
    # OpenAI配置 (备用)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.7
    
    # AI服务配置
    ai_request_timeout: int = 30  # 秒
    ai_max_retries: int = 3
    ai_cache_ttl: int = 1800  # 30分钟
    
    # 配额配置
    free_user_monthly_limit: int = 50
    premium_user_monthly_limit: int = 1000
    free_user_daily_limit: int = 10
    premium_user_daily_limit: int = 100


class ServiceSettings(BaseSettings):
    """服务配置"""
    
    # 服务端口
    user_service_port: int = 8001
    ai_service_port: int = 8002
    note_service_port: int = 8003
    api_gateway_port: int = 8000
    
    # 服务URL
    user_service_url: str = "http://localhost:8001"
    ai_service_url: str = "http://localhost:8002"
    note_service_url: str = "http://localhost:8003"
    
    # 文件上传配置
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "text/plain", "text/markdown"
    ]
    upload_path: str = "/tmp/noteai_uploads"
    
    # 分页配置
    default_page_size: int = 20
    max_page_size: int = 100


class LoggingSettings(BaseSettings):
    """日志配置"""
    
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5


class Settings(BaseSettings):
    """主配置类"""
    
    # 环境配置
    environment: str = "development"  # development, testing, production
    debug: bool = True
    
    # 应用信息
    app_name: str = "NoteAI"
    app_version: str = "1.0.0"
    app_description: str = "AI-powered note-taking and sharing platform"
    
    # 子配置
    database: DatabaseSettings = DatabaseSettings()
    security: SecuritySettings = SecuritySettings()
    ai: AISettings = AISettings()
    service: ServiceSettings = ServiceSettings()
    logging: LoggingSettings = LoggingSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False


# 全局设置实例
settings = Settings()


def get_settings() -> Settings:
    """获取设置实例"""
    return settings


# 环境特定配置
def is_development() -> bool:
    return settings.environment == "development"


def is_testing() -> bool:
    return settings.environment == "testing"


def is_production() -> bool:
    return settings.environment == "production"
