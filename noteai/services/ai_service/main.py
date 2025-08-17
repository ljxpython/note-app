"""
AI服务主模块
"""
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import time
import logging

from .agents.text_optimizer import TextOptimizerAgent
from .agents.content_classifier import ContentClassifierAgent
from .cache_manager import CacheManager
from .quota_manager import QuotaManager
from ...shared.config.settings import get_settings
from ...shared.models.base import (
    APIResponse, OptimizationRequest, OptimizationResponse,
    ClassificationRequest, ClassificationResponse
)
from ...shared.utils.auth import get_current_user_from_token

settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NoteAI AI Service",
    description="AI文本处理和分类服务",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=settings.security.cors_allow_credentials,
    allow_methods=settings.security.cors_allow_methods,
    allow_headers=settings.security.cors_allow_headers,
)

# 全局组件
cache_manager = CacheManager()
quota_manager = QuotaManager()

# AI Agent实例
text_optimizer: TextOptimizerAgent = None
content_classifier: ContentClassifierAgent = None


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    global text_optimizer, content_classifier
    
    try:
        # 初始化AI模型配置
        model_config = {
            "provider": "deepseek",
            "model": settings.ai.deepseek_model,
            "api_key": settings.ai.deepseek_api_key,
            "base_url": settings.ai.deepseek_base_url,
            "max_tokens": settings.ai.deepseek_max_tokens,
            "temperature": settings.ai.deepseek_temperature,
        }
        
        # 初始化AI Agents
        text_optimizer = TextOptimizerAgent("text_optimizer", model_config)
        content_classifier = ContentClassifierAgent("content_classifier", model_config)
        
        # 初始化缓存管理器
        await cache_manager.initialize()
        
        # 初始化配额管理器
        await quota_manager.initialize()
        
        logger.info("AI Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start AI Service: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    try:
        await cache_manager.close()
        await quota_manager.close()
        logger.info("AI Service shutdown successfully")
    except Exception as e:
        logger.error(f"Error during AI Service shutdown: {e}")


@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查AI服务状态
        ai_status = await check_ai_service_health()
        cache_status = await cache_manager.health_check()
        
        return {
            "status": "healthy" if ai_status and cache_status else "unhealthy",
            "service": "ai_service",
            "ai_service": ai_status,
            "cache_service": cache_status,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "ai_service",
            "error": str(e),
            "timestamp": time.time()
        }


@app.post("/api/v1/ai/optimize-text", response_model=APIResponse)
async def optimize_text(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_from_token)
):
    """文本优化API"""
    start_time = time.time()
    
    try:
        user_id = current_user["user_id"]
        
        # 检查用户配额
        if not await quota_manager.check_quota(user_id, "text_optimization"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI配额已用完，请升级账户或等待配额重置"
            )
        
        # 检查缓存
        cache_key = f"optimize:{hash(request.text)}:{request.optimization_type}:{request.user_style}"
        cached_result = await cache_manager.get(cache_key)
        
        if cached_result:
            logger.info(f"Cache hit for text optimization: {user_id}")
            return APIResponse(
                success=True,
                data=cached_result,
                message="文本优化完成（缓存）"
            )
        
        # 调用AI Agent进行文本优化
        result = await text_optimizer.optimize_text(
            text=request.text,
            optimization_type=request.optimization_type,
            user_style=request.user_style
        )
        
        # 计算处理时间
        processing_time = time.time() - start_time
        result["processing_time"] = processing_time
        
        # 缓存结果
        await cache_manager.set(cache_key, result, ttl=settings.ai.ai_cache_ttl)
        
        # 扣除配额
        await quota_manager.use_quota(user_id, "text_optimization", 1)
        
        # 后台任务：记录使用情况
        background_tasks.add_task(
            log_ai_usage,
            user_id=user_id,
            operation="text_optimization",
            input_length=len(request.text),
            processing_time=processing_time,
            success=True
        )
        
        return APIResponse(
            success=True,
            data=result,
            message="文本优化完成"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text optimization failed for user {current_user.get('user_id')}: {e}")
        
        # 记录失败情况
        background_tasks.add_task(
            log_ai_usage,
            user_id=current_user.get("user_id"),
            operation="text_optimization",
            input_length=len(request.text),
            processing_time=time.time() - start_time,
            success=False,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文本优化失败: {str(e)}"
        )


@app.post("/api/v1/ai/classify-content", response_model=APIResponse)
async def classify_content(
    request: ClassificationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_from_token)
):
    """内容分类API"""
    start_time = time.time()
    
    try:
        user_id = current_user["user_id"]
        
        # 检查用户配额
        if not await quota_manager.check_quota(user_id, "content_classification"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI配额已用完，请升级账户或等待配额重置"
            )
        
        # 检查缓存
        cache_key = f"classify:{hash(request.content)}:{hash(str(request.existing_categories))}"
        cached_result = await cache_manager.get(cache_key)
        
        if cached_result:
            logger.info(f"Cache hit for content classification: {user_id}")
            return APIResponse(
                success=True,
                data=cached_result,
                message="内容分类完成（缓存）"
            )
        
        # 调用AI Agent进行内容分类
        result = await content_classifier.classify_content(
            content=request.content,
            existing_categories=request.existing_categories
        )
        
        # 计算处理时间
        processing_time = time.time() - start_time
        result["processing_time"] = processing_time
        
        # 缓存结果
        await cache_manager.set(cache_key, result, ttl=settings.ai.ai_cache_ttl)
        
        # 扣除配额
        await quota_manager.use_quota(user_id, "content_classification", 1)
        
        # 后台任务：记录使用情况
        background_tasks.add_task(
            log_ai_usage,
            user_id=user_id,
            operation="content_classification",
            input_length=len(request.content),
            processing_time=processing_time,
            success=True
        )
        
        return APIResponse(
            success=True,
            data=result,
            message="内容分类完成"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content classification failed for user {current_user.get('user_id')}: {e}")
        
        # 记录失败情况
        background_tasks.add_task(
            log_ai_usage,
            user_id=current_user.get("user_id"),
            operation="content_classification",
            input_length=len(request.content),
            processing_time=time.time() - start_time,
            success=False,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"内容分类失败: {str(e)}"
        )


@app.get("/api/v1/ai/quota", response_model=APIResponse)
async def get_user_quota(
    current_user: dict = Depends(get_current_user_from_token)
):
    """获取用户AI配额信息"""
    try:
        user_id = current_user["user_id"]
        quota_info = await quota_manager.get_quota_info(user_id)
        
        return APIResponse(
            success=True,
            data=quota_info,
            message="配额信息获取成功"
        )
        
    except Exception as e:
        logger.error(f"Failed to get quota info for user {current_user.get('user_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配额信息失败: {str(e)}"
        )


@app.get("/api/v1/ai/usage-stats", response_model=APIResponse)
async def get_usage_stats(
    current_user: dict = Depends(get_current_user_from_token)
):
    """获取用户AI使用统计"""
    try:
        user_id = current_user["user_id"]
        stats = await quota_manager.get_usage_stats(user_id)
        
        return APIResponse(
            success=True,
            data=stats,
            message="使用统计获取成功"
        )
        
    except Exception as e:
        logger.error(f"Failed to get usage stats for user {current_user.get('user_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取使用统计失败: {str(e)}"
        )


async def check_ai_service_health() -> bool:
    """检查AI服务健康状态"""
    try:
        if text_optimizer and content_classifier:
            # 可以添加简单的AI调用测试
            return True
        return False
    except Exception:
        return False


async def log_ai_usage(
    user_id: str,
    operation: str,
    input_length: int,
    processing_time: float,
    success: bool,
    error: str = None
):
    """记录AI使用情况"""
    try:
        # 这里可以记录到数据库或监控系统
        usage_data = {
            "user_id": user_id,
            "operation": operation,
            "input_length": input_length,
            "processing_time": processing_time,
            "success": success,
            "error": error,
            "timestamp": time.time()
        }
        
        # 记录到日志
        logger.info(f"AI usage logged: {usage_data}")
        
        # 可以发送到监控系统
        # await send_to_monitoring_system(usage_data)
        
    except Exception as e:
        logger.error(f"Failed to log AI usage: {e}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service.ai_service_port,
        reload=settings.debug
    )
