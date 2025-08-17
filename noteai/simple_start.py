#!/usr/bin/env python3
"""
简化的启动脚本 - 用于测试基础功能
"""
import sys
import os
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False
    print(f"✅ Python版本: {sys.version}")
    return True

def install_basic_deps():
    """安装基础依赖"""
    import subprocess
    
    basic_deps = [
        "fastapi",
        "uvicorn[standard]", 
        "pydantic",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart"
    ]
    
    print("📦 安装基础依赖...")
    for dep in basic_deps:
        try:
            print(f"   安装 {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep], 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
            print(f"   ✅ {dep} 安装成功")
        except subprocess.CalledProcessError:
            print(f"   ❌ {dep} 安装失败")
            return False
    
    return True

def create_simple_user_service():
    """创建简化的用户服务"""
    from fastapi import FastAPI, HTTPException, Depends
    from fastapi.security import HTTPBearer
    from pydantic import BaseModel, EmailStr
    from passlib.context import CryptContext
    from jose import jwt
    from datetime import datetime, timedelta
    import json
    import os
    
    app = FastAPI(title="NoteAI User Service (Simple)", version="1.0.0")
    
    # 简单的内存存储
    users_db = {}
    
    # 密码加密
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    security = HTTPBearer()
    
    # JWT配置
    SECRET_KEY = "simple-test-secret-key"
    ALGORITHM = "HS256"
    
    class UserCreate(BaseModel):
        email: str
        username: str
        password: str
    
    class UserLogin(BaseModel):
        email: str
        password: str
    
    class Token(BaseModel):
        access_token: str
        token_type: str
    
    @app.get("/health")
    def health_check():
        return {"status": "healthy", "service": "user_service_simple"}
    
    @app.post("/api/v1/auth/register")
    def register_user(user_data: UserCreate):
        # 检查用户是否存在
        if user_data.email in users_db:
            raise HTTPException(status_code=400, detail="用户已存在")
        
        # 创建用户
        hashed_password = pwd_context.hash(user_data.password)
        users_db[user_data.email] = {
            "email": user_data.email,
            "username": user_data.username,
            "password_hash": hashed_password,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {"message": "用户注册成功", "email": user_data.email}
    
    @app.post("/api/v1/auth/login", response_model=Token)
    def login_user(credentials: UserLogin):
        # 验证用户
        user = users_db.get(credentials.email)
        if not user or not pwd_context.verify(credentials.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="邮箱或密码错误")
        
        # 创建Token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": credentials.email}, 
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    
    @app.get("/api/v1/users/profile")
    def get_profile(token: str = Depends(security)):
        try:
            payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
            user = users_db.get(email)
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            return {
                "email": user["email"],
                "username": user["username"],
                "created_at": user["created_at"]
            }
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Token无效")
    
    def create_access_token(data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    return app

def create_simple_ai_service():
    """创建简化的AI服务"""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import random
    import time
    
    app = FastAPI(title="NoteAI AI Service (Simple)", version="1.0.0")
    
    class OptimizationRequest(BaseModel):
        text: str
        optimization_type: str = "all"
    
    @app.get("/health")
    def health_check():
        return {"status": "healthy", "service": "ai_service_simple"}
    
    @app.post("/api/v1/ai/optimize-text")
    def optimize_text(request: OptimizationRequest):
        # 模拟AI处理
        time.sleep(1)  # 模拟处理时间
        
        # 简单的文本优化模拟
        optimized_text = request.text.replace("不好", "有待改进").replace("很差", "需要提升")
        
        return {
            "optimized_text": optimized_text,
            "suggestions": [
                {
                    "type": "expression",
                    "original": "不好",
                    "optimized": "有待改进",
                    "explanation": "使用更专业的表达",
                    "confidence": 0.9
                }
            ],
            "confidence": 0.85,
            "processing_time": 1.0
        }
    
    @app.post("/api/v1/ai/classify-content")
    def classify_content(request: dict):
        # 模拟内容分类
        content = request.get("content", "")
        
        # 简单的关键词分类
        categories = []
        if "技术" in content or "代码" in content:
            categories.append("技术文档")
        elif "学习" in content or "笔记" in content:
            categories.append("学习笔记")
        else:
            categories.append("其他")
        
        return {
            "suggestions": [
                {
                    "category_name": categories[0],
                    "confidence": 0.8,
                    "reasoning": "基于关键词分析"
                }
            ],
            "detected_topics": categories,
            "key_phrases": ["关键词1", "关键词2"],
            "content_type": "文档"
        }
    
    return app

def start_service(app, port, service_name):
    """启动服务"""
    import uvicorn
    
    print(f"🚀 启动 {service_name} (端口 {port})")
    print(f"   访问地址: http://localhost:{port}/docs")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except KeyboardInterrupt:
        print(f"\n⏹️  {service_name} 已停止")
    except Exception as e:
        print(f"❌ {service_name} 启动失败: {e}")

def main():
    """主函数"""
    print("🚀 NoteAI 简化启动脚本")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        return 1
    
    # 安装基础依赖
    if not install_basic_deps():
        print("❌ 依赖安装失败")
        return 1
    
    print("\n📋 可用服务:")
    print("1. 用户服务 (端口 8001)")
    print("2. AI服务 (端口 8002)")
    print("3. 退出")
    
    while True:
        try:
            choice = input("\n请选择要启动的服务 (1-3): ").strip()
            
            if choice == "1":
                app = create_simple_user_service()
                start_service(app, 8001, "用户服务")
                break
            elif choice == "2":
                app = create_simple_ai_service()
                start_service(app, 8002, "AI服务")
                break
            elif choice == "3":
                print("👋 再见！")
                break
            else:
                print("❌ 无效选择，请输入 1-3")
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
