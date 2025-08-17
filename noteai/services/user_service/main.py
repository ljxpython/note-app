"""
用户服务主模块
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uvicorn

from .database import get_db, init_db
from .models import User
from .schemas import UserCreate, UserResponse, LoginRequest, TokenResponse, UserUpdate
from ...shared.config.settings import get_settings
from ...shared.utils.auth import (
    hash_password, verify_password, create_user_tokens,
    get_current_user_from_token, PasswordValidator, validate_email, validate_username
)
from ...shared.models.base import APIResponse, ErrorResponse

settings = get_settings()

app = FastAPI(
    title="NoteAI User Service",
    description="用户认证和管理服务",
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


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    await init_db()


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "user_service"}


@app.post("/api/v1/auth/register", response_model=APIResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        # 验证邮箱格式
        if not validate_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱格式不正确"
            )
        
        # 验证用户名
        username_validation = validate_username(user_data.username)
        if not username_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=username_validation["errors"][0]
            )
        
        # 验证密码强度
        password_validation = PasswordValidator.validate_password(user_data.password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=password_validation["errors"][0]
            )
        
        # 检查用户是否已存在
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被注册"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已被使用"
                )
        
        # 创建新用户
        hashed_password = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=hashed_password,
            avatar_url=user_data.avatar_url,
            bio=user_data.bio,
            location=user_data.location,
            website=user_data.website
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # 创建响应数据
        user_response = UserResponse.from_orm(new_user)
        
        return APIResponse(
            success=True,
            data=user_response,
            message="用户注册成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@app.post("/api/v1/auth/login", response_model=APIResponse)
async def login_user(credentials: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    try:
        # 查找用户
        user = db.query(User).filter(User.email == credentials.email).first()
        
        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误"
            )
        
        # 检查用户状态
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户已被禁用"
            )
        
        # 更新最后登录时间
        from datetime import datetime
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        # 创建令牌
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "permissions": []  # 这里可以从数据库加载用户权限
        }
        
        tokens = create_user_tokens(user_data)
        
        return APIResponse(
            success=True,
            data=tokens,
            message="登录成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@app.get("/api/v1/users/profile", response_model=APIResponse)
async def get_user_profile(
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """获取用户资料"""
    try:
        user = db.query(User).filter(User.id == current_user["user_id"]).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        user_response = UserResponse.from_orm(user)
        
        return APIResponse(
            success=True,
            data=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户资料失败: {str(e)}"
        )


@app.put("/api/v1/users/profile", response_model=APIResponse)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """更新用户资料"""
    try:
        user = db.query(User).filter(User.id == current_user["user_id"]).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新字段
        update_data = user_data.dict(exclude_unset=True)
        
        # 验证用户名（如果要更新）
        if "username" in update_data:
            username_validation = validate_username(update_data["username"])
            if not username_validation["is_valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=username_validation["errors"][0]
                )
            
            # 检查用户名是否已被使用
            existing_user = db.query(User).filter(
                User.username == update_data["username"],
                User.id != user.id
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已被使用"
                )
        
        # 应用更新
        for field, value in update_data.items():
            setattr(user, field, value)
        
        from datetime import datetime
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        user_response = UserResponse.from_orm(user)
        
        return APIResponse(
            success=True,
            data=user_response,
            message="用户资料更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户资料失败: {str(e)}"
        )


@app.post("/api/v1/auth/refresh", response_model=APIResponse)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """刷新访问令牌"""
    try:
        from ...shared.utils.auth import verify_token, create_access_token
        
        # 验证刷新令牌
        payload = verify_token(refresh_token, "refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        # 获取用户信息
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )
        
        # 创建新的访问令牌
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "permissions": []
        }
        
        new_access_token = create_access_token(token_data)
        
        return APIResponse(
            success=True,
            data={
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": settings.security.jwt_access_token_expire_minutes * 60
            },
            message="令牌刷新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌刷新失败: {str(e)}"
        )


@app.post("/api/v1/auth/logout", response_model=APIResponse)
async def logout_user(
    current_user: dict = Depends(get_current_user_from_token)
):
    """用户登出"""
    # 在实际应用中，这里应该将令牌加入黑名单
    # 目前简单返回成功响应
    return APIResponse(
        success=True,
        message="登出成功"
    )


@app.get("/api/v1/auth/validate", response_model=APIResponse)
async def validate_token(
    current_user: dict = Depends(get_current_user_from_token)
):
    """验证令牌（供其他服务调用）"""
    return APIResponse(
        success=True,
        data=current_user,
        message="令牌有效"
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service.user_service_port,
        reload=settings.debug
    )
