#!/usr/bin/env python3
"""
完整的用户认证服务 - 集成JWT、数据库、权限控制
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import uvicorn
from typing import Optional, List
from datetime import datetime

# 导入服务和模型
from services.auth_service import auth_service
from database.connection import init_database, db_manager
from database.repositories import UserRepository
from database.models import User

# 创建FastAPI应用
app = FastAPI(
    title="NoteAI Complete User Service", 
    version="3.0.0",
    description="完整的用户认证服务，集成JWT、SQLite数据库、权限控制"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全依赖
security = HTTPBearer()

# Pydantic模型
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    bio: Optional[str] = None
    location: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False

class UserUpdate(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    avatar_url: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class TokenRefresh(BaseModel):
    refresh_token: str

# 依赖函数
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

def require_permission(resource: str, action: str):
    """权限检查装饰器"""
    def permission_checker(current_user: User = Depends(get_current_active_user)):
        if not auth_service.check_permission(current_user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        return current_user
    return permission_checker

# 路由
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    try:
        init_database()
        print("✅ 数据库初始化成功")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")

@app.get("/health")
def health_check():
    """健康检查"""
    db_health = db_manager.health_check()
    db_info = db_manager.get_database_info()
    
    return {
        "status": "healthy",
        "service": "complete_user_service",
        "version": "3.0.0",
        "features": [
            "JWT认证",
            "SQLite数据库",
            "权限控制",
            "用户管理",
            "会话管理"
        ],
        "database": {
            "status": "connected" if db_health else "disconnected",
            "type": db_info.get("database_type", "unknown"),
            "tables": db_info.get("table_count", 0)
        },
        "auth": {
            "jwt_enabled": True,
            "password_hashing": "bcrypt",
            "token_expiry": f"{auth_service.access_token_expire_minutes}分钟"
        }
    }

@app.post("/api/v1/auth/register")
def register_user(user_data: UserRegister):
    """用户注册"""
    try:
        result = auth_service.register_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            bio=user_data.bio,
            location=user_data.location
        )
        
        return {
            "success": True,
            "message": "用户注册成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )

@app.post("/api/v1/auth/login")
def login_user(credentials: UserLogin):
    """用户登录"""
    try:
        device_info = {
            "remember_me": credentials.remember_me,
            "login_time": datetime.utcnow().isoformat()
        }
        
        result = auth_service.login(
            email=credentials.email,
            password=credentials.password,
            device_info=device_info
        )
        
        return {
            "success": True,
            "message": "登录成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )

@app.post("/api/v1/auth/refresh")
def refresh_token(token_data: TokenRefresh):
    """刷新访问令牌"""
    try:
        result = auth_service.refresh_access_token(token_data.refresh_token)
        
        return {
            "success": True,
            "message": "令牌刷新成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌刷新失败: {str(e)}"
        )

@app.post("/api/v1/auth/logout")
def logout_user(current_user: User = Depends(get_current_active_user)):
    """用户登出"""
    try:
        success = auth_service.logout(current_user.id)
        
        return {
            "success": success,
            "message": "登出成功" if success else "登出失败"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登出失败: {str(e)}"
        )

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
            "location": current_user.location,
            "website": current_user.website,
            "avatar_url": current_user.avatar_url,
            "role": current_user.role,
            "status": current_user.status,
            "is_verified": current_user.is_verified,
            "email_verified": current_user.email_verified,
            "created_at": current_user.created_at.isoformat(),
            "updated_at": current_user.updated_at.isoformat(),
            "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None
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
            # 检查用户名是否已被使用
            if profile_data.username and profile_data.username != current_user.username:
                existing_user = user_repo.get_user_by_username(profile_data.username)
                if existing_user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="用户名已被使用"
                    )
            
            # 更新用户信息
            update_data = profile_data.dict(exclude_unset=True)
            updated_user = user_repo.update_user(current_user.id, **update_data)
            
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            return {
                "success": True,
                "message": "用户资料更新成功",
                "data": {
                    "id": updated_user.id,
                    "username": updated_user.username,
                    "bio": updated_user.bio,
                    "location": updated_user.location,
                    "website": updated_user.website,
                    "avatar_url": updated_user.avatar_url,
                    "updated_at": updated_user.updated_at.isoformat()
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )

@app.post("/api/v1/users/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user)
):
    """修改密码"""
    try:
        # 验证当前密码
        if not auth_service.verify_password(password_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )
        
        # 验证新密码强度（在auth_service中实现）
        auth_service._validate_password(password_data.new_password)
        
        # 更新密码
        with UserRepository() as user_repo:
            new_password_hash = auth_service.hash_password(password_data.new_password)
            updated_user = user_repo.update_user(
                current_user.id,
                password_hash=new_password_hash
            )
            
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            return {
                "success": True,
                "message": "密码修改成功"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码修改失败: {str(e)}"
        )

@app.get("/api/v1/users")
def list_users(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(require_permission("user", "read"))
):
    """获取用户列表（需要管理员权限）"""
    try:
        with UserRepository() as user_repo:
            users = user_repo.get_users(skip=skip, limit=limit, status="active")
            total = user_repo.count_users(status="active")
            
            user_list = []
            for user in users:
                user_list.append({
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "role": user.role,
                    "status": user.status,
                    "is_verified": user.is_verified,
                    "created_at": user.created_at.isoformat(),
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
                })
            
            return {
                "success": True,
                "data": {
                    "users": user_list,
                    "pagination": {
                        "skip": skip,
                        "limit": limit,
                        "total": total,
                        "has_next": skip + limit < total
                    }
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )

@app.get("/api/v1/auth/verify-token")
def verify_token(current_user: User = Depends(get_current_active_user)):
    """验证令牌有效性"""
    return {
        "success": True,
        "message": "令牌有效",
        "data": {
            "user_id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "verified_at": datetime.utcnow().isoformat()
        }
    }

if __name__ == "__main__":
    print("🚀 NoteAI 完整用户认证服务启动")
    print("🔐 集成JWT认证、SQLite数据库、权限控制")
    print("📖 API文档: http://localhost:8001/docs")
    print("🔍 健康检查: http://localhost:8001/health")
    print("👥 用户管理: http://localhost:8001/api/v1/users")
    print("")
    print("🌟 认证功能:")
    print("   - JWT访问令牌和刷新令牌")
    print("   - 密码加密存储(bcrypt)")
    print("   - 基于角色的权限控制")
    print("   - 用户会话管理")
    print("   - 数据库持久化")
    print("")
    print("🔑 测试账户:")
    print("   邮箱: test@example.com")
    print("   密码: test123456")
    print("")
    print("⏹️  按 Ctrl+C 停止服务")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
