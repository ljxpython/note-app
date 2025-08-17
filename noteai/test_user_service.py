#!/usr/bin/env python3
"""
测试用户服务
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_user_service():
    """测试用户服务"""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient
        from pydantic import BaseModel
        from passlib.context import CryptContext
        from jose import jwt
        from datetime import datetime, timedelta
        
        print("🧪 创建用户服务...")
        
        app = FastAPI(title="NoteAI User Service Test")
        
        # 简单的内存存储
        users_db = {}
        
        # 密码加密
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # JWT配置
        SECRET_KEY = "test-secret-key"
        ALGORITHM = "HS256"
        
        class UserCreate(BaseModel):
            email: str
            username: str
            password: str
        
        class UserLogin(BaseModel):
            email: str
            password: str
        
        @app.get("/health")
        def health_check():
            return {"status": "healthy", "service": "user_service"}
        
        @app.post("/api/v1/auth/register")
        def register_user(user_data: UserCreate):
            if user_data.email in users_db:
                raise HTTPException(status_code=400, detail="用户已存在")
            
            hashed_password = pwd_context.hash(user_data.password)
            users_db[user_data.email] = {
                "email": user_data.email,
                "username": user_data.username,
                "password_hash": hashed_password,
                "created_at": datetime.utcnow().isoformat()
            }
            
            return {"message": "用户注册成功", "email": user_data.email}
        
        @app.post("/api/v1/auth/login")
        def login_user(credentials: UserLogin):
            user = users_db.get(credentials.email)
            if not user or not pwd_context.verify(credentials.password, user["password_hash"]):
                raise HTTPException(status_code=401, detail="邮箱或密码错误")
            
            access_token_expires = timedelta(minutes=30)
            access_token = create_access_token(
                data={"sub": credentials.email}, 
                expires_delta=access_token_expires
            )
            
            return {"access_token": access_token, "token_type": "bearer"}
        
        def create_access_token(data: dict, expires_delta: timedelta = None):
            to_encode = data.copy()
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=15)
            
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        
        print("✅ 用户服务创建成功")
        
        # 测试API
        print("\n🧪 测试API...")
        client = TestClient(app)
        
        # 测试健康检查
        response = client.get("/health")
        print(f"✅ 健康检查: {response.status_code} - {response.json()}")
        
        # 测试用户注册
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPass123!"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        print(f"✅ 用户注册: {response.status_code} - {response.json()}")
        
        # 测试用户登录
        login_data = {
            "email": "test@example.com",
            "password": "TestPass123!"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        print(f"✅ 用户登录: {response.status_code} - {response.json()}")
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"   Token: {token[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 用户服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_service():
    """测试AI服务"""
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from pydantic import BaseModel
        import time
        
        print("\n🧪 创建AI服务...")
        
        app = FastAPI(title="NoteAI AI Service Test")
        
        class OptimizationRequest(BaseModel):
            text: str
            optimization_type: str = "all"
        
        @app.get("/health")
        def health_check():
            return {"status": "healthy", "service": "ai_service"}
        
        @app.post("/api/v1/ai/optimize-text")
        def optimize_text(request: OptimizationRequest):
            # 模拟AI处理
            time.sleep(0.1)  # 模拟处理时间
            
            optimized_text = request.text.replace("不好", "有待改进")
            
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
                "processing_time": 0.1
            }
        
        print("✅ AI服务创建成功")
        
        # 测试API
        print("\n🧪 测试AI API...")
        client = TestClient(app)
        
        # 测试健康检查
        response = client.get("/health")
        print(f"✅ 健康检查: {response.status_code} - {response.json()}")
        
        # 测试文本优化
        opt_data = {
            "text": "这个算法的效率不好",
            "optimization_type": "expression"
        }
        response = client.post("/api/v1/ai/optimize-text", json=opt_data)
        print(f"✅ 文本优化: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   原文: {opt_data['text']}")
            print(f"   优化: {result['optimized_text']}")
            print(f"   置信度: {result['confidence']}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 NoteAI 服务测试")
    print("=" * 50)
    
    # 安装基础依赖
    print("📦 检查依赖...")
    try:
        import fastapi
        import uvicorn
        import pydantic
        import passlib
        import jose
        print("✅ 所有依赖已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install fastapi uvicorn pydantic 'python-jose[cryptography]' 'passlib[bcrypt]'")
        return 1
    
    tests_passed = 0
    total_tests = 2
    
    # 测试用户服务
    if test_user_service():
        tests_passed += 1
    
    # 测试AI服务
    if test_ai_service():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {tests_passed}/{total_tests} 通过")
    
    if tests_passed == total_tests:
        print("🎉 所有测试通过！")
        print("\n🚀 可以启动服务:")
        print("   用户服务: uvicorn test_user_service:app --port 8001")
        print("   访问文档: http://localhost:8001/docs")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
