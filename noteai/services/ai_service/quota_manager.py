"""
AI服务配额管理器
"""
import redis
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx

from ...shared.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class QuotaManager:
    """配额管理器"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.is_connected = False
        self.user_service_url = settings.service.user_service_url
    
    async def initialize(self):
        """初始化配额管理器"""
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
            self.redis_client.ping()
            self.is_connected = True
            logger.info("Quota manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize quota manager: {e}")
            self.is_connected = False
    
    async def check_quota(self, user_id: str, operation: str) -> bool:
        """检查用户配额"""
        try:
            # 获取用户配额信息
            quota_info = await self.get_quota_info(user_id)
            
            if not quota_info:
                logger.warning(f"No quota info found for user {user_id}")
                return False
            
            # 检查日配额
            daily_used = quota_info.get("daily_used", 0)
            daily_limit = quota_info.get("daily_limit", 10)
            
            if daily_used >= daily_limit:
                logger.info(f"Daily quota exceeded for user {user_id}: {daily_used}/{daily_limit}")
                return False
            
            # 检查月配额
            monthly_used = quota_info.get("monthly_used", 0)
            monthly_limit = quota_info.get("monthly_limit", 50)
            
            if monthly_used >= monthly_limit:
                logger.info(f"Monthly quota exceeded for user {user_id}: {monthly_used}/{monthly_limit}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check quota for user {user_id}: {e}")
            # 在错误情况下，允许使用（宽松策略）
            return True
    
    async def use_quota(self, user_id: str, operation: str, count: int = 1) -> bool:
        """使用配额"""
        try:
            if not self.is_connected:
                logger.warning("Quota manager not connected, skipping quota usage")
                return True
            
            # 获取当前日期
            today = datetime.now().strftime("%Y-%m-%d")
            current_month = datetime.now().strftime("%Y-%m")
            
            # 更新日配额
            daily_key = f"quota:daily:{user_id}:{today}"
            daily_used = self.redis_client.incr(daily_key, count)
            
            # 设置日配额过期时间（到明天凌晨）
            tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            expire_seconds = int((tomorrow - datetime.now()).total_seconds())
            self.redis_client.expire(daily_key, expire_seconds)
            
            # 更新月配额
            monthly_key = f"quota:monthly:{user_id}:{current_month}"
            monthly_used = self.redis_client.incr(monthly_key, count)
            
            # 设置月配额过期时间（到下月1号）
            next_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if next_month.month == 12:
                next_month = next_month.replace(year=next_month.year + 1, month=1)
            else:
                next_month = next_month.replace(month=next_month.month + 1)
            
            expire_seconds = int((next_month - datetime.now()).total_seconds())
            self.redis_client.expire(monthly_key, expire_seconds)
            
            # 记录使用情况
            await self._log_usage(user_id, operation, count, daily_used, monthly_used)
            
            logger.info(f"Quota used for user {user_id}: daily={daily_used}, monthly={monthly_used}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to use quota for user {user_id}: {e}")
            return True  # 宽松策略
    
    async def get_quota_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户配额信息"""
        try:
            # 首先尝试从用户服务获取配额信息
            user_quota = await self._get_user_quota_from_service(user_id)
            
            if not user_quota:
                # 使用默认配额
                user_quota = {
                    "plan_type": "free",
                    "daily_limit": settings.ai.free_user_daily_limit,
                    "monthly_limit": settings.ai.free_user_monthly_limit
                }
            
            # 获取当前使用情况
            today = datetime.now().strftime("%Y-%m-%d")
            current_month = datetime.now().strftime("%Y-%m")
            
            daily_key = f"quota:daily:{user_id}:{today}"
            monthly_key = f"quota:monthly:{user_id}:{current_month}"
            
            daily_used = 0
            monthly_used = 0
            
            if self.is_connected:
                daily_used = int(self.redis_client.get(daily_key) or 0)
                monthly_used = int(self.redis_client.get(monthly_key) or 0)
            
            return {
                "plan_type": user_quota.get("plan_type", "free"),
                "daily_limit": user_quota.get("daily_limit", 10),
                "daily_used": daily_used,
                "daily_remaining": max(0, user_quota.get("daily_limit", 10) - daily_used),
                "monthly_limit": user_quota.get("monthly_limit", 50),
                "monthly_used": monthly_used,
                "monthly_remaining": max(0, user_quota.get("monthly_limit", 50) - monthly_used),
                "reset_date": self._get_next_reset_date()
            }
            
        except Exception as e:
            logger.error(f"Failed to get quota info for user {user_id}: {e}")
            return None
    
    async def _get_user_quota_from_service(self, user_id: str) -> Optional[Dict[str, Any]]:
        """从用户服务获取配额信息"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.user_service_url}/api/v1/users/{user_id}/ai-quota",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        return data.get("data")
                
                return None
                
        except Exception as e:
            logger.warning(f"Failed to get user quota from service: {e}")
            return None
    
    def _get_next_reset_date(self) -> str:
        """获取下次重置日期"""
        # 月配额重置日期（下月1号）
        next_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if next_month.month == 12:
            next_month = next_month.replace(year=next_month.year + 1, month=1)
        else:
            next_month = next_month.replace(month=next_month.month + 1)
        
        return next_month.isoformat()
    
    async def _log_usage(self, user_id: str, operation: str, count: int, daily_used: int, monthly_used: int):
        """记录使用情况"""
        try:
            usage_data = {
                "user_id": user_id,
                "operation": operation,
                "count": count,
                "daily_used": daily_used,
                "monthly_used": monthly_used,
                "timestamp": datetime.now().isoformat()
            }
            
            # 记录到Redis（可选）
            if self.is_connected:
                usage_key = f"usage:log:{user_id}:{datetime.now().strftime('%Y%m%d%H%M%S')}"
                self.redis_client.setex(usage_key, 86400 * 7, json.dumps(usage_data))  # 保存7天
            
            logger.info(f"Usage logged: {usage_data}")
            
        except Exception as e:
            logger.error(f"Failed to log usage: {e}")
    
    async def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户使用统计"""
        try:
            if not self.is_connected:
                return {"error": "Quota manager not connected"}
            
            # 获取最近7天的使用情况
            stats = {"daily_usage": {}, "total_requests": 0}
            
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                daily_key = f"quota:daily:{user_id}:{date}"
                daily_used = int(self.redis_client.get(daily_key) or 0)
                stats["daily_usage"][date] = daily_used
                stats["total_requests"] += daily_used
            
            # 获取当月使用情况
            current_month = datetime.now().strftime("%Y-%m")
            monthly_key = f"quota:monthly:{user_id}:{current_month}"
            stats["monthly_used"] = int(self.redis_client.get(monthly_key) or 0)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get usage stats for user {user_id}: {e}")
            return {"error": str(e)}
    
    async def reset_user_quota(self, user_id: str, quota_type: str = "all") -> bool:
        """重置用户配额"""
        try:
            if not self.is_connected:
                return False
            
            today = datetime.now().strftime("%Y-%m-%d")
            current_month = datetime.now().strftime("%Y-%m")
            
            if quota_type in ["daily", "all"]:
                daily_key = f"quota:daily:{user_id}:{today}"
                self.redis_client.delete(daily_key)
            
            if quota_type in ["monthly", "all"]:
                monthly_key = f"quota:monthly:{user_id}:{current_month}"
                self.redis_client.delete(monthly_key)
            
            logger.info(f"Quota reset for user {user_id}, type: {quota_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset quota for user {user_id}: {e}")
            return False
    
    async def health_check(self) -> bool:
        """健康检查"""
        if not self.is_connected or not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Quota manager health check failed: {e}")
            self.is_connected = False
            return False
    
    async def close(self):
        """关闭配额管理器"""
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Quota manager closed")
            except Exception as e:
                logger.error(f"Error closing quota manager: {e}")
        
        self.is_connected = False
