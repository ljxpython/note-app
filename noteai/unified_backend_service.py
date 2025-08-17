#!/usr/bin/env python3
"""
NoteAI 统一后端服务 - 集成所有功能
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Depends, status, Form, File, UploadFile, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, ValidationError
import uvicorn
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import asyncio
import os
import uuid
from pathlib import Path

# 导入所有服务
from services.auth_service import auth_service
from services.ai_service.autogen_service import autogen_service
from database.connection import init_database, db_manager
from database.repositories import UserRepository, NoteRepository, CategoryRepository, AIUsageRepository, FeedbackRepository
from database.models import User
from utils.logger import logger, log_startup, log_shutdown

# 创建FastAPI应用
app = FastAPI(
    title="NoteAI Unified Backend Service", 
    version="4.0.0",
    description="统一的后端服务，集成用户认证、AI功能、笔记管理"
)

# CORS中间件 - 增强配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRF-Token",
        "Cache-Control"
    ],
    expose_headers=["*"]
)

# 静态文件服务 - 用于图片访问
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 安全依赖
security = HTTPBearer()

# ==================== Pydantic模型 ====================

# 用户相关模型
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    bio: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class TokenRefresh(BaseModel):
    refresh_token: str

# AI相关模型
class OptimizationRequest(BaseModel):
    text: str
    optimization_type: str = "all"
    user_style: Optional[str] = None

class ClassificationRequest(BaseModel):
    content: str
    existing_categories: List[str] = []

class WritingAssistanceRequest(BaseModel):
    content: str
    task_type: str = "improve"

# 笔记相关模型
class NoteCreate(BaseModel):
    title: str
    content: str
    category_id: Optional[str] = None
    tags: List[str] = []
    is_public: bool = False

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    is_favorite: Optional[bool] = None

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None

# 反馈相关模型
class FeedbackCreate(BaseModel):
    type: str  # bug, feature, improvement, general
    title: str
    content: str
    category: Optional[str] = None  # ui, performance, ai, auth, other
    priority: Optional[str] = "medium"  # low, medium, high, critical
    rating: Optional[int] = None  # 1-5星评分
    page_url: Optional[str] = None
    browser_info: Optional[Dict[str, Any]] = None
    device_info: Optional[Dict[str, Any]] = None

class FeedbackUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    rating: Optional[int] = None

class FeedbackResponse(BaseModel):
    admin_response: str
    status: Optional[str] = "resolved"

# ==================== 依赖函数 ====================

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """获取当前认证用户"""
    return auth_service.get_current_user(credentials)

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户未激活"
        )
    return current_user

# ==================== 启动事件 ====================

@app.middleware("http")
async def log_requests(request, call_next):
    """详细请求日志中间件"""
    import time
    import json
    start_time = time.time()

    # 获取客户端IP
    client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()

    # 记录请求开始
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "path": str(request.url.path),
        "query_params": dict(request.query_params),
        "headers": dict(request.headers),
        "client_ip": client_ip
    }

    logger.debug(f"🔵 请求开始: {request.method} {request.url.path}", **request_info)

    try:
        response = await call_next(request)

        # 计算响应时间
        process_time = time.time() - start_time

        # 记录成功响应
        response_info = {
            "status_code": response.status_code,
            "response_time": process_time,
            "response_headers": dict(response.headers)
        }

        if response.status_code >= 400:
            logger.warning(f"⚠️ 请求失败: {request.method} {request.url.path} - {response.status_code}",
                         **{**request_info, **response_info})
        else:
            logger.info(f"✅ 请求成功: {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)",
                       **{**request_info, **response_info})

        return response

    except Exception as e:
        # 计算响应时间
        process_time = time.time() - start_time

        # 记录异常
        logger.error(f"❌ 请求异常: {request.method} {request.url.path} - {str(e)}",
                    **{**request_info, "exception": str(e), "response_time": process_time})
        raise

# 全局异常处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    logger.error(f"🔴 请求验证失败: {request.method} {request.url.path}",
                validation_errors=exc.errors(),
                request_body=await request.body() if hasattr(request, 'body') else None)

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "请求数据验证失败",
            "detail": exc.errors(),
            "path": str(request.url.path)
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """处理HTTP异常"""
    logger.error(f"🔴 HTTP异常: {request.method} {request.url.path} - {exc.status_code}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": "请求处理失败",
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""
    logger.error(f"🔴 未处理异常: {request.method} {request.url.path} - {type(exc).__name__}: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "detail": "请联系管理员",
            "error_type": type(exc).__name__
        }
    )

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    try:
        log_startup()
        init_database()
        logger.info("✅ 数据库初始化成功")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    log_shutdown()

# ==================== 健康检查 ====================

@app.get("/health")
def health_check():
    """统一健康检查"""
    db_health = db_manager.health_check()
    db_info = db_manager.get_database_info()
    
    return {
        "status": "healthy",
        "service": "unified_backend_service",
        "version": "4.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "用户认证管理",
            "AutoGen AI服务",
            "笔记管理系统",
            "分类管理",
            "SQLite数据库"
        ],
        "database": {
            "status": "connected" if db_health else "disconnected",
            "type": db_info.get("database_type", "unknown"),
            "tables": db_info.get("table_count", 0)
        },
        "ai": {
            "autogen_enabled": autogen_service.model_client is not None,
            "agents_available": len(autogen_service.agents)
        }
    }

# ==================== 用户认证路由 ====================

@app.post("/api/v1/auth/register")
def register_user(user_data: UserRegister):
    """用户注册"""
    try:
        result = auth_service.register_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            bio=user_data.bio
        )
        return {"success": True, "message": "用户注册成功", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")

@app.post("/api/v1/auth/login")
def login_user(credentials: UserLogin):
    """用户登录"""
    try:
        result = auth_service.login(
            email=credentials.email,
            password=credentials.password
        )
        return {"success": True, "message": "登录成功", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")

@app.post("/api/v1/auth/refresh")
def refresh_token(token_data: TokenRefresh):
    """刷新访问令牌"""
    try:
        result = auth_service.refresh_access_token(token_data.refresh_token)
        return {"success": True, "message": "令牌刷新成功", "data": result}
    except HTTPException:
        raise

@app.post("/api/v1/auth/logout")
def logout_user(current_user: User = Depends(get_current_active_user)):
    """用户登出"""
    try:
        success = auth_service.logout(current_user.id)
        return {"success": success, "message": "登出成功" if success else "登出失败"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登出失败: {str(e)}")

@app.get("/api/v1/users/profile")
def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """获取用户资料"""
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "bio": current_user.bio,
            "website": current_user.website,
            "role": current_user.role,
            "created_at": current_user.created_at.isoformat(),
            "updated_at": current_user.updated_at.isoformat()
        }
    }

@app.put("/api/v1/users/profile")
def update_user_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新用户资料"""
    try:
        with UserRepository() as user_repo:
            update_data = profile_data.dict(exclude_unset=True)
            updated_user = user_repo.update_user(current_user.id, **update_data)
            
            return {
                "success": True,
                "message": "用户资料更新成功",
                "data": {
                    "id": updated_user.id,
                    "username": updated_user.username,
                    "bio": updated_user.bio,
                    "website": updated_user.website,
                    "updated_at": updated_user.updated_at.isoformat()
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

# ==================== AI功能路由 ====================

@app.post("/api/v1/ai/optimize-text")
async def optimize_text(
    request: OptimizationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """AI文本优化"""
    try:
        result = await autogen_service.optimize_text(
            text=request.text,
            optimization_type=request.optimization_type,
            user_style=request.user_style
        )
        
        # 记录AI使用
        with AIUsageRepository() as ai_repo:
            ai_repo.create_usage_record(
                user_id=current_user.id,
                operation_type="optimize_text",
                processing_time=result.get("processing_time", 0),
                success=True
            )
        
        return {"success": True, "data": result, "message": "文本优化完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文本优化失败: {str(e)}")

@app.post("/api/v1/ai/classify-content")
async def classify_content(
    request: ClassificationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """AI内容分类"""
    try:
        result = await autogen_service.classify_content(
            content=request.content,
            existing_categories=request.existing_categories
        )
        
        # 记录AI使用
        with AIUsageRepository() as ai_repo:
            ai_repo.create_usage_record(
                user_id=current_user.id,
                operation_type="classify_content",
                processing_time=result.get("processing_time", 0),
                success=True
            )
        
        return {"success": True, "data": result, "message": "内容分类完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内容分类失败: {str(e)}")

@app.get("/api/v1/ai/quota")
def get_ai_quota(current_user: User = Depends(get_current_active_user)):
    """获取AI配额信息"""
    try:
        with AIUsageRepository() as ai_repo:
            daily_used = ai_repo.get_daily_usage(current_user.id)
            monthly_used = ai_repo.get_monthly_usage(current_user.id)
        
        return {
            "success": True,
            "data": {
                "plan_type": "free",
                "daily_limit": 50,
                "daily_used": daily_used,
                "monthly_limit": 1000,
                "monthly_used": monthly_used,
                "reset_date": "2025-02-01T00:00:00Z"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配额失败: {str(e)}")

# ==================== 笔记管理路由 ====================

@app.get("/api/v1/notes")
def get_notes(
    limit: int = 10,
    skip: int = 0,
    current_user: User = Depends(get_current_active_user)
):
    """获取用户笔记列表"""
    try:
        with NoteRepository() as note_repo:
            notes = note_repo.get_notes(
                user_id=current_user.id,
                skip=skip,
                limit=limit
            )

            result = []
            for note in notes:
                result.append({
                    "id": note.id,
                    "title": note.title,
                    "content": note.content[:200] + "..." if len(note.content) > 200 else note.content,
                    "category_id": note.category_id,
                    "tags": note.tags,
                    "created_at": note.created_at.isoformat(),
                    "updated_at": note.updated_at.isoformat()
                })

            return {
                "success": True,
                "data": {
                    "notes": result,
                    "pagination": {
                        "skip": skip,
                        "limit": limit,
                        "total": len(result)
                    }
                }
            }
    except Exception as e:
        logger.error(f"获取笔记列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取笔记列表失败: {str(e)}")

@app.post("/api/v1/notes")
def create_note(
    title: str = Form(...),
    content: str = Form(...),
    category_id: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user)
):
    """创建笔记"""
    try:
        with NoteRepository() as note_repo:
            # 处理标签
            tags_list = []
            if tags:
                tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

            note = note_repo.create_note(
                user_id=current_user.id,
                title=title,
                content=content,
                category_id=category_id,
                tags=tags_list
            )

            return {
                "success": True,
                "message": "笔记创建成功",
                "data": {
                    "id": note.id,
                    "title": note.title,
                    "created_at": note.created_at.isoformat()
                }
            }
    except Exception as e:
        logger.error(f"创建笔记失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建笔记失败: {str(e)}")

@app.get("/api/v1/notes/{note_id}")
def get_note(
    note_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取笔记详情"""
    try:
        with NoteRepository() as note_repo:
            note = note_repo.get_note_by_id(note_id)

            if not note:
                raise HTTPException(status_code=404, detail="笔记不存在")

            # 检查权限
            if note.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="权限不足")

            return {
                "success": True,
                "data": {
                    "id": note.id,
                    "title": note.title,
                    "content": note.content,
                    "category_id": note.category_id,
                    "tags": note.tags,
                    "created_at": note.created_at.isoformat(),
                    "updated_at": note.updated_at.isoformat()
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取笔记详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取笔记详情失败: {str(e)}")

# ==================== 用户反馈路由 ====================

@app.post("/api/v1/feedback")
async def create_feedback(
    feedback_type: str = Form(..., alias="type"),
    title: str = Form(...),
    content: str = Form(...),
    category: Optional[str] = Form(None),
    priority: Optional[str] = Form("medium"),
    rating: Optional[int] = Form(None),
    page_url: Optional[str] = Form(None),
    browser_info: Optional[str] = Form(None),
    device_info: Optional[str] = Form(None),
    images: List[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_active_user)
):
    """创建用户反馈（支持图片上传）"""
    try:
        # 验证和清理输入数据
        logger.info(f"创建反馈 - 用户: {current_user.id}, 标题: {title}")
        logger.debug(f"反馈类型: {feedback_type}")
        logger.debug(f"反馈内容: {content[:100]}...")
        logger.debug(f"内容类型: {type(content)}")
        logger.debug(f"内容长度: {len(content) if content else 0}")

        # 检查是否有图片数据混入content
        if isinstance(content, str) and content.startswith('\x89PNG'):
            logger.error("发现PNG图片数据被错误传入content字段！")
            raise HTTPException(status_code=400, detail="反馈内容格式错误：图片数据不应在文本字段中")

        # 确保content是字符串
        if isinstance(content, bytes):
            logger.error(f"收到bytes类型的content: {content[:50]}...")
            try:
                content = content.decode('utf-8')
                logger.info("成功将bytes转换为字符串")
            except UnicodeDecodeError:
                logger.error("无法解码bytes content")
                raise HTTPException(status_code=400, detail="反馈内容格式错误")

        # 处理JSON字符串
        import json
        browser_info_dict = None
        device_info_dict = None

        if browser_info:
            try:
                browser_info_dict = json.loads(browser_info)
            except:
                pass

        if device_info:
            try:
                device_info_dict = json.loads(device_info)
            except:
                pass

        # 创建上传目录
        upload_dir = Path("uploads/feedback")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 保存图片文件
        saved_images = []
        for image in images:
            if image.filename:
                # 生成唯一文件名
                file_extension = Path(image.filename).suffix
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                file_path = upload_dir / unique_filename

                # 保存文件
                image_data = await image.read()
                with open(file_path, "wb") as f:
                    f.write(image_data)

                saved_images.append({
                    "original_filename": image.filename,
                    "saved_filename": unique_filename,
                    "file_path": str(file_path),
                    "file_size": len(image_data),
                    "content_type": image.content_type,
                    "url": f"/uploads/feedback/{unique_filename}"
                })

        # 最后一次验证content
        logger.debug(f"准备存储到数据库 - content类型: {type(content)}")
        logger.debug(f"准备存储到数据库 - content内容: {content}")

        with FeedbackRepository() as feedback_repo:
            feedback = feedback_repo.create_feedback(
                user_id=current_user.id,
                feedback_type=feedback_type,
                title=title,
                content=content,
                category=category,
                priority=priority,
                rating=rating,
                page_url=page_url,
                browser_info=browser_info_dict,
                device_info=device_info_dict
            )

            # 验证存储后的数据
            logger.debug(f"存储后验证 - content类型: {type(feedback.content)}")
            logger.debug(f"存储后验证 - content长度: {len(feedback.content) if feedback.content else 0}")
            if isinstance(feedback.content, bytes):
                logger.error(f"❌ 存储后content变成了bytes: {feedback.content[:50]}...")
            else:
                logger.debug(f"✅ 存储后content仍是字符串: {feedback.content}")

            # 如果有图片，保存附件信息到数据库
            if saved_images:
                from database.models import FeedbackAttachment
                for img_info in saved_images:
                    attachment = FeedbackAttachment(
                        feedback_id=feedback.id,
                        filename=img_info["saved_filename"],
                        original_filename=img_info["original_filename"],
                        file_type=img_info["content_type"],
                        file_size=img_info["file_size"],
                        file_path=img_info["file_path"]
                    )
                    feedback_repo.session.add(attachment)

                feedback_repo.session.commit()
                logger.info(f"反馈 {feedback.id} 包含 {len(saved_images)} 个图片附件")

            return {
                "success": True,
                "message": "反馈提交成功",
                "data": {
                    "id": feedback.id,
                    "type": feedback.type,
                    "title": feedback.title,
                    "status": feedback.status,
                    "images_count": len(saved_images),
                    "created_at": feedback.created_at.isoformat()
                }
            }
    except Exception as e:
        logger.error(f"反馈提交失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"反馈提交失败: {str(e)}")

@app.post("/api/v1/feedback/json")
def create_feedback_json(
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_active_user)
):
    """创建用户反馈（JSON格式，不支持图片）"""
    try:
        with FeedbackRepository() as feedback_repo:
            feedback = feedback_repo.create_feedback(
                user_id=current_user.id,
                feedback_type=feedback_data.type,
                title=feedback_data.title,
                content=feedback_data.content,
                category=feedback_data.category,
                priority=feedback_data.priority,
                rating=feedback_data.rating,
                page_url=feedback_data.page_url,
                browser_info=feedback_data.browser_info,
                device_info=feedback_data.device_info
            )

            return {
                "success": True,
                "message": "反馈提交成功",
                "data": {
                    "id": feedback.id,
                    "type": feedback.type,
                    "title": feedback.title,
                    "status": feedback.status,
                    "images_count": 0,
                    "created_at": feedback.created_at.isoformat()
                }
            }
    except Exception as e:
        logger.error(f"反馈提交失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"反馈提交失败: {str(e)}")

@app.get("/api/v1/feedback/my")
def get_my_feedback(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user)
):
    """获取我的反馈列表"""
    try:
        with FeedbackRepository() as feedback_repo:
            feedback_list = feedback_repo.get_user_feedback(
                user_id=current_user.id,
                skip=skip,
                limit=limit
            )

            result = []
            for feedback in feedback_list:
                # 安全处理可能包含bytes的字段
                def safe_serialize(value):
                    if isinstance(value, bytes):
                        try:
                            decoded = value.decode('utf-8')
                            # 检查是否是图片数据（PNG/JPEG头部）
                            if decoded.startswith('\x89PNG') or decoded.startswith('\xff\xd8\xff'):
                                logger.error(f"发现图片数据被错误存储在文本字段: {value[:20]}...")
                                return "[数据存储错误，图片数据不应在此字段]"
                            return decoded
                        except UnicodeDecodeError:
                            # 如果是无法解码的bytes，可能是二进制数据
                            logger.error(f"发现无法解码的bytes数据: {value[:50]}...")
                            return "[数据损坏，请联系管理员]"
                    return value

                # 获取反馈的图片附件
                images = []
                if hasattr(feedback, 'attachments') and feedback.attachments:
                    for attachment in feedback.attachments:
                        images.append({
                            "id": attachment.id,
                            "filename": attachment.original_filename,
                            "url": f"/uploads/feedback/{attachment.filename}",
                            "size": attachment.file_size,
                            "type": attachment.file_type
                        })

                result.append({
                    "id": feedback.id,
                    "type": feedback.type,
                    "title": safe_serialize(feedback.title),
                    "content": safe_serialize(feedback.content),
                    "category": safe_serialize(feedback.category),
                    "priority": safe_serialize(feedback.priority),
                    "status": safe_serialize(feedback.status),
                    "rating": feedback.rating,
                    "admin_response": safe_serialize(feedback.admin_response),
                    "images": images,
                    "created_at": feedback.created_at.isoformat(),
                    "updated_at": feedback.updated_at.isoformat(),
                    "resolved_at": feedback.resolved_at.isoformat() if feedback.resolved_at else None
                })

            return {
                "success": True,
                "data": {
                    "feedback": result,
                    "pagination": {
                        "skip": skip,
                        "limit": limit,
                        "total": len(result)
                    }
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取反馈失败: {str(e)}")

@app.get("/api/v1/feedback/{feedback_id}")
def get_feedback_detail(
    feedback_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取反馈详情"""
    try:
        with FeedbackRepository() as feedback_repo:
            feedback = feedback_repo.get_feedback_by_id(feedback_id)

            if not feedback:
                raise HTTPException(status_code=404, detail="反馈不存在")

            # 检查权限：只能查看自己的反馈或管理员可以查看所有
            if feedback.user_id != current_user.id and current_user.role not in ["admin", "moderator"]:
                raise HTTPException(status_code=403, detail="权限不足")

            # 安全处理可能包含bytes的字段
            def safe_serialize(value):
                if isinstance(value, bytes):
                    try:
                        decoded = value.decode('utf-8')
                        # 检查是否是图片数据（PNG/JPEG头部）
                        if decoded.startswith('\x89PNG') or decoded.startswith('\xff\xd8\xff'):
                            logger.error(f"发现图片数据被错误存储在文本字段: {value[:20]}...")
                            return "[数据存储错误，图片数据不应在此字段]"
                        return decoded
                    except UnicodeDecodeError:
                        # 如果是无法解码的bytes，可能是二进制数据
                        logger.error(f"发现无法解码的bytes数据: {value[:50]}...")
                        return "[数据损坏，请联系管理员]"
                return value

            # 获取反馈的图片附件
            images = []
            if hasattr(feedback, 'attachments') and feedback.attachments:
                for attachment in feedback.attachments:
                    images.append({
                        "id": attachment.id,
                        "filename": attachment.original_filename,
                        "url": f"/uploads/feedback/{attachment.filename}",
                        "size": attachment.file_size,
                        "type": attachment.file_type
                    })

            return {
                "success": True,
                "data": {
                    "id": feedback.id,
                    "type": safe_serialize(feedback.type),
                    "title": safe_serialize(feedback.title),
                    "content": safe_serialize(feedback.content),
                    "category": safe_serialize(feedback.category),
                    "priority": safe_serialize(feedback.priority),
                    "status": safe_serialize(feedback.status),
                    "rating": feedback.rating,
                    "page_url": safe_serialize(feedback.page_url),
                    "browser_info": feedback.browser_info,
                    "device_info": feedback.device_info,
                    "admin_response": safe_serialize(feedback.admin_response),
                    "images": images,
                    "user": {
                        "id": feedback.user.id,
                        "username": safe_serialize(feedback.user.username),
                        "email": safe_serialize(feedback.user.email)
                    } if feedback.user else None,
                    "admin": {
                        "id": feedback.admin.id,
                        "username": safe_serialize(feedback.admin.username)
                    } if feedback.admin else None,
                    "created_at": feedback.created_at.isoformat(),
                    "updated_at": feedback.updated_at.isoformat(),
                    "resolved_at": feedback.resolved_at.isoformat() if feedback.resolved_at else None
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取反馈详情失败: {str(e)}")

@app.put("/api/v1/feedback/{feedback_id}")
def update_feedback(
    feedback_id: str,
    feedback_data: FeedbackUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新反馈"""
    try:
        with FeedbackRepository() as feedback_repo:
            feedback = feedback_repo.get_feedback_by_id(feedback_id)

            if not feedback:
                raise HTTPException(status_code=404, detail="反馈不存在")

            # 检查权限：只能编辑自己的反馈
            if feedback.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="只能编辑自己的反馈")

            # 检查状态：只能编辑未处理的反馈
            if feedback.status not in ["open"]:
                raise HTTPException(status_code=400, detail="只能编辑待处理状态的反馈")

            # 更新反馈
            update_data = feedback_data.dict(exclude_unset=True)
            updated_feedback = feedback_repo.update_feedback(feedback_id, **update_data)

            return {
                "success": True,
                "message": "反馈更新成功",
                "data": {
                    "id": updated_feedback.id,
                    "title": updated_feedback.title,
                    "content": updated_feedback.content,
                    "status": updated_feedback.status,
                    "updated_at": updated_feedback.updated_at.isoformat()
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新反馈失败: {str(e)}")

@app.delete("/api/v1/feedback/{feedback_id}")
def delete_feedback(
    feedback_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """删除反馈"""
    try:
        with FeedbackRepository() as feedback_repo:
            feedback = feedback_repo.get_feedback_by_id(feedback_id)

            if not feedback:
                raise HTTPException(status_code=404, detail="反馈不存在")

            # 检查权限：只能删除自己的反馈
            if feedback.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="只能删除自己的反馈")

            # 检查状态：只能删除未处理的反馈
            if feedback.status not in ["open"]:
                raise HTTPException(status_code=400, detail="只能删除待处理状态的反馈")

            # 删除反馈
            feedback_repo.session.delete(feedback)
            feedback_repo.session.commit()

            return {
                "success": True,
                "message": "反馈删除成功"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除反馈失败: {str(e)}")

# ==================== 管理员反馈管理路由 ====================

@app.get("/api/v1/admin/feedback")
def get_all_feedback(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    feedback_type: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """获取所有反馈（管理员）"""
    # 检查管理员权限
    if current_user.role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    try:
        with FeedbackRepository() as feedback_repo:
            feedback_list = feedback_repo.get_all_feedback(
                skip=skip,
                limit=limit,
                status=status,
                feedback_type=feedback_type,
                priority=priority
            )

            result = []
            for feedback in feedback_list:
                result.append({
                    "id": feedback.id,
                    "type": feedback.type,
                    "title": feedback.title,
                    "category": feedback.category,
                    "priority": feedback.priority,
                    "status": feedback.status,
                    "rating": feedback.rating,
                    "user": {
                        "id": feedback.user.id,
                        "username": feedback.user.username,
                        "email": feedback.user.email
                    } if feedback.user else None,
                    "created_at": feedback.created_at.isoformat(),
                    "updated_at": feedback.updated_at.isoformat()
                })

            return {
                "success": True,
                "data": {
                    "feedback": result,
                    "pagination": {
                        "skip": skip,
                        "limit": limit,
                        "total": len(result)
                    }
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取反馈列表失败: {str(e)}")

@app.post("/api/v1/admin/feedback/{feedback_id}/respond")
def respond_to_feedback(
    feedback_id: str,
    response_data: FeedbackResponse,
    current_user: User = Depends(get_current_active_user)
):
    """管理员回复反馈"""
    # 检查管理员权限
    if current_user.role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    try:
        with FeedbackRepository() as feedback_repo:
            feedback = feedback_repo.respond_to_feedback(
                feedback_id=feedback_id,
                admin_id=current_user.id,
                response=response_data.admin_response,
                status=response_data.status
            )

            if not feedback:
                raise HTTPException(status_code=404, detail="反馈不存在")

            return {
                "success": True,
                "message": "反馈回复成功",
                "data": {
                    "id": feedback.id,
                    "status": feedback.status,
                    "admin_response": feedback.admin_response,
                    "resolved_at": feedback.resolved_at.isoformat() if feedback.resolved_at else None
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回复反馈失败: {str(e)}")

@app.get("/api/v1/admin/feedback/stats")
def get_feedback_stats(current_user: User = Depends(get_current_active_user)):
    """获取反馈统计信息（管理员）"""
    # 检查管理员权限
    if current_user.role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    try:
        with FeedbackRepository() as feedback_repo:
            stats = feedback_repo.get_feedback_stats()

            return {
                "success": True,
                "data": stats
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@app.get("/api/v1/feedback/search")
def search_feedback(
    q: str,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user)
):
    """搜索反馈"""
    try:
        with FeedbackRepository() as feedback_repo:
            # 普通用户只能搜索自己的反馈
            if current_user.role in ["admin", "moderator"]:
                feedback_list = feedback_repo.search_feedback(q, skip, limit)
            else:
                # 对于普通用户，需要在搜索结果中过滤
                all_results = feedback_repo.search_feedback(q, 0, 1000)  # 获取更多结果进行过滤
                user_results = [f for f in all_results if f.user_id == current_user.id]
                feedback_list = user_results[skip:skip+limit]

            result = []
            for feedback in feedback_list:
                result.append({
                    "id": feedback.id,
                    "type": feedback.type,
                    "title": feedback.title,
                    "category": feedback.category,
                    "priority": feedback.priority,
                    "status": feedback.status,
                    "created_at": feedback.created_at.isoformat()
                })

            return {
                "success": True,
                "data": {
                    "feedback": result,
                    "query": q,
                    "pagination": {
                        "skip": skip,
                        "limit": limit,
                        "total": len(result)
                    }
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索反馈失败: {str(e)}")

# ==================== 日志管理路由 ====================

@app.get("/api/v1/admin/logs")
def get_logs(
    log_type: str = "all",  # all, error, auth, ai, db
    lines: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """获取系统日志（管理员）"""
    # 检查管理员权限
    if current_user.role not in ["admin"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    try:
        from pathlib import Path
        import json

        logs_dir = Path("logs")
        log_files = {
            "all": "noteai.log",
            "error": "error.log",
            "json": "noteai.json"
        }

        log_file = logs_dir / log_files.get(log_type, "noteai.log")

        if not log_file.exists():
            return {
                "success": True,
                "data": {
                    "logs": [],
                    "message": "日志文件不存在"
                }
            }

        # 读取最后N行
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        # 如果是JSON格式，解析每行
        if log_type == "json":
            parsed_logs = []
            for line in recent_lines:
                try:
                    parsed_logs.append(json.loads(line.strip()))
                except:
                    continue

            return {
                "success": True,
                "data": {
                    "logs": parsed_logs,
                    "total_lines": len(all_lines),
                    "returned_lines": len(parsed_logs)
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "logs": [line.strip() for line in recent_lines],
                    "total_lines": len(all_lines),
                    "returned_lines": len(recent_lines)
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")

@app.get("/api/v1/admin/logs/stats")
def get_log_stats(current_user: User = Depends(get_current_active_user)):
    """获取日志统计信息（管理员）"""
    # 检查管理员权限
    if current_user.role not in ["admin"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    try:
        from pathlib import Path
        import os

        logs_dir = Path("logs")
        stats = {}

        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                file_stat = os.stat(log_file)
                stats[log_file.name] = {
                    "size_bytes": file_stat.st_size,
                    "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                    "modified": file_stat.st_mtime,
                    "lines": sum(1 for _ in open(log_file, 'r', encoding='utf-8'))
                }

        return {
            "success": True,
            "data": {
                "log_files": stats,
                "logs_directory": str(logs_dir.absolute())
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志统计失败: {str(e)}")

if __name__ == "__main__":
    print("🚀 NoteAI 统一后端服务启动")
    print("🔗 集成所有功能于一个服务")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔍 健康检查: http://localhost:8000/health")
    print("")
    print("🌟 集成功能:")
    print("   - 用户认证管理")
    print("   - AutoGen AI服务")
    print("   - 笔记管理系统")
    print("   - SQLite数据库")
    print("")
    print("⏹️  按 Ctrl+C 停止服务")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
