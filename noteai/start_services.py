#!/usr/bin/env python3
"""
启动NoteAI服务
"""
import sys
import os
import subprocess
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def start_user_service():
    """启动用户服务"""
    print("🚀 启动用户服务 (端口 8001)...")
    
    # 创建用户服务应用
    from test_user_service import test_user_service
    
    # 这里我们使用测试版本，您可以替换为真实的服务
    code = '''
import sys
sys.path.insert(0, ".")

from test_user_service import test_user_service
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import uvicorn

# 创建用户服务
app = FastAPI(title="NoteAI User Service", version="1.0.0")

# 简单的内存存储
users_db = {}

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
SECRET_KEY = "noteai-secret-key-change-in-production"
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
    return {"status": "healthy", "service": "user_service", "version": "1.0.0"}

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

@app.get("/api/v1/users/profile")
def get_profile():
    return {"message": "需要实现Token验证"}

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

if __name__ == "__main__":
    print("🚀 NoteAI 用户服务启动")
    print("📖 API文档: http://localhost:8001/docs")
    print("🔍 健康检查: http://localhost:8001/health")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
'''
    
    # 写入临时文件
    with open("temp_user_service.py", "w", encoding="utf-8") as f:
        f.write(code)
    
    # 启动服务
    try:
        subprocess.run([sys.executable, "temp_user_service.py"], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  用户服务已停止")
    finally:
        # 清理临时文件
        if os.path.exists("temp_user_service.py"):
            os.remove("temp_user_service.py")

def start_ai_service():
    """启动AI服务"""
    print("🚀 启动AI服务 (端口 8002)...")
    
    code = '''
import sys
sys.path.insert(0, ".")

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import time

# 创建AI服务
app = FastAPI(title="NoteAI AI Service", version="1.0.0")

class OptimizationRequest(BaseModel):
    text: str
    optimization_type: str = "all"
    user_style: str = None

class ClassificationRequest(BaseModel):
    content: str
    existing_categories: list = []

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ai_service", "version": "1.0.0"}

@app.post("/api/v1/ai/optimize-text")
def optimize_text(request: OptimizationRequest):
    # 模拟AI处理
    time.sleep(0.5)  # 模拟处理时间
    
    # 简单的文本优化规则
    optimized_text = request.text
    suggestions = []
    
    replacements = {
        "不好": "有待改进",
        "很差": "需要提升", 
        "不行": "需要优化",
        "糟糕": "有改进空间"
    }
    
    for original, optimized in replacements.items():
        if original in request.text:
            optimized_text = optimized_text.replace(original, optimized)
            suggestions.append({
                "type": "expression",
                "original": original,
                "optimized": optimized,
                "explanation": f"将'{original}'改为更专业的表达'{optimized}'",
                "confidence": 0.9
            })
    
    return {
        "optimized_text": optimized_text,
        "suggestions": suggestions,
        "confidence": 0.85 if suggestions else 0.5,
        "processing_time": 0.5,
        "optimization_type": request.optimization_type
    }

@app.post("/api/v1/ai/classify-content")
def classify_content(request: ClassificationRequest):
    content = request.content
    
    # 简单的关键词分类
    categories = []
    if any(word in content for word in ["技术", "代码", "编程", "算法"]):
        categories.append({"category_name": "技术文档", "confidence": 0.9, "reasoning": "包含技术相关关键词"})
    elif any(word in content for word in ["学习", "笔记", "总结", "知识"]):
        categories.append({"category_name": "学习笔记", "confidence": 0.8, "reasoning": "包含学习相关关键词"})
    elif any(word in content for word in ["工作", "项目", "任务", "计划"]):
        categories.append({"category_name": "工作总结", "confidence": 0.8, "reasoning": "包含工作相关关键词"})
    else:
        categories.append({"category_name": "其他", "confidence": 0.6, "reasoning": "未匹配到特定分类"})
    
    # 提取关键词
    import re
    words = re.findall(r'[\\u4e00-\\u9fff]+|[a-zA-Z]+', content)
    key_phrases = list(set(words))[:5]  # 取前5个不重复的词
    
    return {
        "suggestions": categories,
        "detected_topics": [cat["category_name"] for cat in categories],
        "key_phrases": key_phrases,
        "content_type": "文档",
        "processing_time": 0.3
    }

if __name__ == "__main__":
    print("🚀 NoteAI AI服务启动")
    print("📖 API文档: http://localhost:8002/docs")
    print("🔍 健康检查: http://localhost:8002/health")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
'''
    
    # 写入临时文件
    with open("temp_ai_service.py", "w", encoding="utf-8") as f:
        f.write(code)
    
    # 启动服务
    try:
        subprocess.run([sys.executable, "temp_ai_service.py"], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  AI服务已停止")
    finally:
        # 清理临时文件
        if os.path.exists("temp_ai_service.py"):
            os.remove("temp_ai_service.py")

def main():
    """主函数"""
    print("🚀 NoteAI 服务启动器")
    print("=" * 50)
    
    print("📋 可用服务:")
    print("1. 用户服务 (端口 8001)")
    print("2. AI服务 (端口 8002)")
    print("3. 退出")
    
    while True:
        try:
            choice = input("\n请选择要启动的服务 (1-3): ").strip()
            
            if choice == "1":
                start_user_service()
                break
            elif choice == "2":
                start_ai_service()
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

if __name__ == "__main__":
    main()
