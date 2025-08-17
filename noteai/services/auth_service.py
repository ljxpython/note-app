#!/usr/bin/env python3
"""
完善的JWT认证服务
"""
import os
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from database.repositories import UserRepository, SystemConfigRepository
from database.models import User, UserSession

logger = logging.getLogger(__name__)

class AuthService:
    """认证服务类"""
    
    def __init__(self):
        """初始化认证服务"""
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer()
        
        # JWT配置
        self.secret_key = os.getenv("JWT_SECRET_KEY", self._generate_secret_key())
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        logger.info("✅ 认证服务初始化成功")
    
    def _generate_secret_key(self) -> str:
        """生成安全密钥"""
        return secrets.token_urlsafe(32)
    
    def hash_password(self, password: str) -> str:
        """加密密码"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_urlsafe(16)  # JWT ID
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查令牌类型
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            # 检查过期时间
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def register_user(self, email: str, username: str, password: str, **kwargs) -> Dict[str, Any]:
        """注册用户"""
        try:
            with UserRepository() as user_repo:
                # 检查邮箱是否已存在
                if user_repo.get_user_by_email(email):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="邮箱已被注册"
                    )
                
                # 检查用户名是否已存在
                if user_repo.get_user_by_username(username):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="用户名已被使用"
                    )
                
                # 验证密码强度
                self._validate_password(password)
                
                # 创建用户
                password_hash = self.hash_password(password)
                user = user_repo.create_user(
                    email=email,
                    username=username,
                    password_hash=password_hash,
                    **kwargs
                )
                
                logger.info(f"✅ 用户注册成功: {user.email}")
                
                return {
                    "user_id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "created_at": user.created_at.isoformat()
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 用户注册失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="注册失败"
            )
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """验证用户"""
        try:
            with UserRepository() as user_repo:
                user = user_repo.get_user_by_email(email)
                
                if not user:
                    return None
                
                if not self.verify_password(password, user.password_hash):
                    return None
                
                if user.status != "active":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="账户已被禁用"
                    )
                
                # 更新最后登录时间
                user_repo.update_last_login(user.id)
                
                return user
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 用户验证失败: {e}")
            return None
    
    def login(self, email: str, password: str, device_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """用户登录"""
        try:
            # 验证用户
            user = self.authenticate_user(email, password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="邮箱或密码错误"
                )
            
            # 创建令牌
            token_data = {
                "sub": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role
            }
            
            access_token = self.create_access_token(token_data)
            refresh_token = self.create_refresh_token({"sub": user.id})
            
            # 创建用户会话
            session_token = self._create_user_session(
                user.id, 
                access_token, 
                refresh_token, 
                device_info
            )
            
            logger.info(f"✅ 用户登录成功: {user.email}")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "role": user.role,
                    "avatar_url": user.avatar_url
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 用户登录失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="登录失败"
            )
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """刷新访问令牌"""
        try:
            # 验证刷新令牌
            payload = self.verify_token(refresh_token, "refresh")
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # 获取用户信息
            with UserRepository() as user_repo:
                user = user_repo.get_user_by_id(user_id)
                if not user or user.status != "active":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found or inactive"
                    )
            
            # 创建新的访问令牌
            token_data = {
                "sub": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role
            }
            
            new_access_token = self.create_access_token(token_data)
            
            logger.info(f"✅ 令牌刷新成功: {user.email}")
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 令牌刷新失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed"
            )
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials) -> User:
        """获取当前用户"""
        try:
            token = credentials.credentials
            payload = self.verify_token(token, "access")
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            with UserRepository() as user_repo:
                user = user_repo.get_user_by_id(user_id)
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found"
                    )
                
                if user.status != "active":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User account is inactive"
                    )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 获取当前用户失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    def logout(self, user_id: str, session_token: str = None) -> bool:
        """用户登出"""
        try:
            # 这里可以实现会话失效逻辑
            # 由于JWT是无状态的，主要是客户端删除令牌
            # 可以维护一个黑名单或会话表来管理
            
            logger.info(f"✅ 用户登出: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 用户登出失败: {e}")
            return False
    
    def _validate_password(self, password: str) -> None:
        """验证密码强度"""
        if len(password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码长度至少6位"
            )
        
        if len(password) > 128:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码长度不能超过128位"
            )
        
        # 可以添加更多密码强度检查
        # 如：必须包含大小写字母、数字、特殊字符等
    
    def _create_user_session(self, user_id: str, access_token: str, 
                           refresh_token: str, device_info: Dict[str, Any] = None) -> str:
        """创建用户会话"""
        try:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
            
            # 这里可以将会话信息存储到数据库
            # 暂时返回session_token
            
            return session_token
            
        except Exception as e:
            logger.error(f"❌ 创建用户会话失败: {e}")
            return ""
    
    def check_permission(self, user: User, resource: str, action: str) -> bool:
        """检查用户权限"""
        try:
            # 简单的基于角色的权限控制
            role_permissions = {
                "super_admin": ["*"],  # 所有权限
                "admin": ["user:*", "note:*", "category:*"],
                "moderator": ["note:read", "note:moderate", "user:read"],
                "premium_user": ["note:*", "category:*", "ai:premium"],
                "user": ["note:own", "category:own", "ai:basic"]
            }
            
            user_permissions = role_permissions.get(user.role, [])
            
            # 检查是否有全部权限
            if "*" in user_permissions:
                return True
            
            # 检查具体权限
            permission = f"{resource}:{action}"
            if permission in user_permissions:
                return True
            
            # 检查通配符权限
            wildcard_permission = f"{resource}:*"
            if wildcard_permission in user_permissions:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ 权限检查失败: {e}")
            return False

# 全局认证服务实例
auth_service = AuthService()
