#!/usr/bin/env python3
"""
直接运行用户服务
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timedelta
import uvicorn
import hashlib
import hmac
import json
import base64

# 创建用户服务
app = FastAPI(title="NoteAI User Service", version="1.0.0")

# 简单的内存存储
users_db = {}

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 简化的JWT实现（避免jose包问题）
SECRET_KEY = "noteai-secret-key-change-in-production"

def create_simple_token(data: dict, expires_minutes: int = 30) -> str:
    """创建简单的Token"""
    import time
    payload = {
        **data,
        "exp": int(time.time()) + (expires_minutes * 60),
        "iat": int(time.time())
    }
    
    # 简单的base64编码（生产环境应该使用真正的JWT）
    token_data = json.dumps(payload)
    encoded = base64.b64encode(token_data.encode()).decode()
    
    # 添加简单的签名
    signature = hmac.new(
        SECRET_KEY.encode(),
        encoded.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{encoded}.{signature}"

def verify_simple_token(token: str) -> dict:
    """验证简单Token"""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            raise ValueError("Invalid token format")
        
        encoded_data, signature = parts
        
        # 验证签名
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            encoded_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if signature != expected_signature:
            raise ValueError("Invalid signature")
        
        # 解码数据
        token_data = base64.b64decode(encoded_data.encode()).decode()
        payload = json.loads(token_data)
        
        # 检查过期时间
        import time
        if payload.get("exp", 0) < time.time():
            raise ValueError("Token expired")
        
        return payload
    except Exception:
        raise ValueError("Invalid token")

class UserCreate(BaseModel):
    email: str
    username: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "service": "user_service", 
        "version": "1.0.0",
        "users_count": len(users_db)
    }

@app.post("/api/v1/auth/register")
def register_user(user_data: UserCreate):
    if user_data.email in users_db:
        raise HTTPException(status_code=400, detail="用户已存在")
    
    # 简单的邮箱验证
    if "@" not in user_data.email:
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    
    # 简单的密码验证
    if len(user_data.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少6位")
    
    hashed_password = pwd_context.hash(user_data.password)
    users_db[user_data.email] = {
        "email": user_data.email,
        "username": user_data.username,
        "password_hash": hashed_password,
        "created_at": datetime.utcnow().isoformat(),
        "is_active": True
    }
    
    return {
        "success": True,
        "message": "用户注册成功", 
        "data": {
            "email": user_data.email,
            "username": user_data.username
        }
    }

@app.post("/api/v1/auth/login")
def login_user(credentials: UserLogin):
    user = users_db.get(credentials.email)
    if not user or not pwd_context.verify(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="账户已被禁用")
    
    # 创建Token
    access_token = create_simple_token({
        "sub": credentials.email,
        "username": user["username"]
    })
    
    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800  # 30分钟
        },
        "message": "登录成功"
    }

@app.get("/api/v1/users/profile")
def get_profile():
    return {
        "success": True,
        "message": "需要在请求头中提供Authorization: Bearer <token>",
        "data": {
            "note": "这是简化版本，完整版本需要Token验证"
        }
    }

@app.get("/api/v1/users")
def list_users():
    """获取用户列表（仅用于测试）"""
    user_list = []
    for email, user in users_db.items():
        user_list.append({
            "email": user["email"],
            "username": user["username"],
            "created_at": user["created_at"],
            "is_active": user.get("is_active", True)
        })
    
    return {
        "success": True,
        "data": {
            "users": user_list,
            "total": len(user_list)
        }
    }

if __name__ == "__main__":
    print("🚀 NoteAI 用户服务启动")
    print("📖 API文档: http://localhost:8001/docs")
    print("🔍 健康检查: http://localhost:8001/health")
    print("👥 用户列表: http://localhost:8001/api/v1/users")
    print("")
    print("📝 测试用例:")
    print("1. 注册用户: POST /api/v1/auth/register")
    print("   {\"email\":\"test@example.com\",\"username\":\"testuser\",\"password\":\"123456\"}")
    print("2. 用户登录: POST /api/v1/auth/login")
    print("   {\"email\":\"test@example.com\",\"password\":\"123456\"}")
    print("")
    print("⏹️  按 Ctrl+C 停止服务")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
