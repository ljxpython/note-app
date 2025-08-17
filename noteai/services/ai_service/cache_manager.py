"""
AI服务缓存管理器
"""
import redis
import json
import hashlib
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

from ...shared.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.is_connected = False
    
    async def initialize(self):
        """初始化缓存连接"""
        try:
            self.redis_client = redis.Redis(
                host=settings.database.redis_host,
                port=settings.database.redis_port,
                password=settings.database.redis_password,
                db=settings.database.redis_db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # 测试连接
            await self._test_connection()
            self.is_connected = True
            logger.info("Cache manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {e}")
            self.is_connected = False
            # 不抛出异常，允许服务在没有缓存的情况下运行
    
    async def _test_connection(self):
        """测试Redis连接"""
        try:
            self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.is_connected or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get cache key '{key}': {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存值"""
        if not self.is_connected or not self.redis_client:
            return False
        
        try:
            json_value = json.dumps(value, ensure_ascii=False, default=str)
            result = self.redis_client.setex(key, ttl, json_value)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set cache key '{key}': {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        if not self.is_connected or not self.redis_client:
            return False
        
        try:
            result = self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to delete cache key '{key}': {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存键是否存在"""
        if not self.is_connected or not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check cache key '{key}': {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置缓存过期时间"""
        if not self.is_connected or not self.redis_client:
            return False
        
        try:
            result = self.redis_client.expire(key, ttl)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set expiry for cache key '{key}': {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """获取缓存剩余时间"""
        if not self.is_connected or not self.redis_client:
            return -1
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Failed to get TTL for cache key '{key}': {e}")
            return -1
    
    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 创建唯一标识符
        key_parts = [prefix]
        
        # 添加位置参数
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                key_parts.append(str(hash(str(arg))))
        
        # 添加关键字参数
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = json.dumps(sorted_kwargs, sort_keys=True, ensure_ascii=False)
            kwargs_hash = hashlib.md5(kwargs_str.encode()).hexdigest()[:8]
            key_parts.append(kwargs_hash)
        
        return ":".join(key_parts)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if not self.is_connected or not self.redis_client:
            return {"connected": False}
        
        try:
            info = self.redis_client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"connected": False, "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """计算缓存命中率"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存键"""
        if not self.is_connected or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to clear cache pattern '{pattern}': {e}")
            return 0
    
    async def health_check(self) -> bool:
        """健康检查"""
        if not self.is_connected or not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            self.is_connected = False
            return False
    
    async def close(self):
        """关闭缓存连接"""
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Cache manager closed")
            except Exception as e:
                logger.error(f"Error closing cache manager: {e}")
        
        self.is_connected = False


# 缓存装饰器
def cache_result(prefix: str, ttl: int = 3600):
    """缓存结果装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 这里需要访问全局的cache_manager实例
            # 在实际使用中，可以通过依赖注入获取
            cache_manager = CacheManager()
            if not cache_manager.is_connected:
                return await func(*args, **kwargs)
            
            # 生成缓存键
            cache_key = cache_manager.generate_cache_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            logger.info(f"Cache set for key: {cache_key}")
            
            return result
        
        return wrapper
    return decorator
