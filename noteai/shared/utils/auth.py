"""
认证工具模块
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
import secrets
import re

from ..config.settings import get_settings

settings = get_settings()

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer认证
security = HTTPBearer()


class PasswordValidator:
    """密码验证器"""
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """验证密码强度"""
        errors = []
        
        # 长度检查
        if len(password) < settings.security.password_min_length:
            errors.append(f"密码长度至少{settings.security.password_min_length}位")
        
        # 大写字母检查
        if settings.security.password_require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("密码必须包含大写字母")
        
        # 小写字母检查
        if settings.security.password_require_lowercase and not re.search(r'[a-z]', password):
            errors.append("密码必须包含小写字母")
        
        # 数字检查
        if settings.security.password_require_numbers and not re.search(r'\d', password):
            errors.append("密码必须包含数字")
        
        # 特殊字符检查
        if settings.security.password_require_special_chars and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("密码必须包含特殊字符")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "strength": calculate_password_strength(password)
        }


def calculate_password_strength(password: str) -> str:
    """计算密码强度"""
    score = 0
    
    # 长度评分
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1
    
    # 字符类型评分
    if re.search(r'[a-z]', password):
        score += 1
    if re.search(r'[A-Z]', password):
        score += 1
    if re.search(r'\d', password):
        score += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    
    # 复杂度评分
    if len(set(password)) > len(password) * 0.7:  # 字符多样性
        score += 1
    
    if score <= 3:
        return "weak"
    elif score <= 5:
        return "medium"
    elif score <= 7:
        return "strong"
    else:
        return "very_strong"


def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.security.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.security.jwt_secret_key, 
        algorithm=settings.security.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.security.jwt_refresh_token_expire_days)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.jwt_secret_key,
        algorithm=settings.security.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """验证令牌"""
    try:
        payload = jwt.decode(
            token,
            settings.security.jwt_secret_key,
            algorithms=[settings.security.jwt_algorithm]
        )
        
        # 检查令牌类型
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # 检查过期时间
        exp = payload.get("exp")
        if exp is None or datetime.utcfromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        
        return payload
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def generate_reset_token() -> str:
    """生成重置令牌"""
    return secrets.token_urlsafe(32)


def generate_verification_code() -> str:
    """生成验证码"""
    return secrets.token_hex(3).upper()  # 6位十六进制验证码


def hash_email(email: str) -> str:
    """哈希邮箱地址（用于匿名化）"""
    return hashlib.sha256(email.encode()).hexdigest()


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """从令牌获取当前用户信息"""
    try:
        payload = verify_token(credentials.credentials, "access")
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "permissions": payload.get("permissions", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )


class RoleChecker:
    """角色检查器"""
    
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: Dict[str, Any] = Depends(get_current_user_from_token)):
        user_role = current_user.get("role", "user")
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user


class PermissionChecker:
    """权限检查器"""
    
    def __init__(self, required_permission: str):
        self.required_permission = required_permission
    
    def __call__(self, current_user: Dict[str, Any] = Depends(get_current_user_from_token)):
        user_permissions = current_user.get("permissions", [])
        if self.required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {self.required_permission}"
            )
        return current_user


# 常用的权限检查器实例
require_admin = RoleChecker(["admin", "super_admin"])
require_moderator = RoleChecker(["moderator", "admin", "super_admin"])
require_premium = RoleChecker(["premium_user", "moderator", "admin", "super_admin"])

# 常用的功能权限检查器
require_ai_access = PermissionChecker("ai:access")
require_share_public = PermissionChecker("share:public")
require_user_manage = PermissionChecker("user:manage")


def create_user_tokens(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """为用户创建访问和刷新令牌"""
    token_data = {
        "sub": str(user_data["id"]),
        "email": user_data["email"],
        "role": user_data.get("role", "user"),
        "permissions": user_data.get("permissions", [])
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user_data["id"])})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.security.jwt_access_token_expire_minutes * 60
    }


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_username(username: str) -> Dict[str, Any]:
    """验证用户名"""
    errors = []
    
    # 长度检查
    if len(username) < 3:
        errors.append("用户名长度至少3位")
    elif len(username) > 50:
        errors.append("用户名长度不能超过50位")
    
    # 字符检查
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        errors.append("用户名只能包含字母、数字、下划线和连字符")
    
    # 开头检查
    if username.startswith(('_', '-')):
        errors.append("用户名不能以下划线或连字符开头")
    
    # 保留词检查
    reserved_words = ['admin', 'root', 'api', 'www', 'mail', 'ftp', 'system']
    if username.lower() in reserved_words:
        errors.append("用户名不能使用保留词")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }
