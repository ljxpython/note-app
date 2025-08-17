#!/usr/bin/env python3
"""
修复版本的服务启动器
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
    
    # 创建修复版本的用户服务
    code = '''
import sys
sys.path.insert(0, ".")

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
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
'''
    
    # 写入临时文件
    with open("fixed_user_service.py", "w", encoding="utf-8") as f:
        f.write(code)
    
    # 启动服务
    try:
        subprocess.run([sys.executable, "fixed_user_service.py"], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  用户服务已停止")
    finally:
        # 清理临时文件
        if os.path.exists("fixed_user_service.py"):
            os.remove("fixed_user_service.py")

def start_ai_service():
    """启动AI服务"""
    print("🚀 启动AI服务 (端口 8002)...")
    
    code = '''
import sys
sys.path.insert(0, ".")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import time
import re
import random

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
    return {
        "status": "healthy", 
        "service": "ai_service", 
        "version": "1.0.0",
        "features": ["text_optimization", "content_classification"]
    }

@app.post("/api/v1/ai/optimize-text")
def optimize_text(request: OptimizationRequest):
    """文本优化API"""
    start_time = time.time()
    
    # 模拟AI处理时间
    time.sleep(random.uniform(0.5, 1.5))
    
    # 智能文本优化规则
    optimized_text = request.text
    suggestions = []
    
    # 表达优化规则
    expression_rules = {
        "不好": "有待改进",
        "很差": "需要提升", 
        "不行": "需要优化",
        "糟糕": "有改进空间",
        "太慢": "效率有待提升",
        "很烂": "质量需要改善",
        "没用": "效果不明显",
        "不对": "存在问题"
    }
    
    # 语法优化规则
    grammar_rules = {
        "的的": "的",
        "了了": "了",
        "。。": "。",
        "，，": "，",
        "  ": " "  # 多余空格
    }
    
    # 应用优化规则
    if request.optimization_type in ["expression", "all"]:
        for original, optimized in expression_rules.items():
            if original in request.text:
                optimized_text = optimized_text.replace(original, optimized)
                suggestions.append({
                    "type": "expression",
                    "original": original,
                    "optimized": optimized,
                    "explanation": f"将'{original}'改为更专业的表达'{optimized}'",
                    "confidence": round(random.uniform(0.8, 0.95), 2)
                })
    
    if request.optimization_type in ["grammar", "all"]:
        for original, optimized in grammar_rules.items():
            if original in request.text:
                optimized_text = optimized_text.replace(original, optimized)
                suggestions.append({
                    "type": "grammar",
                    "original": original,
                    "optimized": optimized,
                    "explanation": f"修正语法错误",
                    "confidence": round(random.uniform(0.9, 0.98), 2)
                })
    
    # 结构优化建议
    if request.optimization_type in ["structure", "all"]:
        sentences = re.split(r'[。！？]', request.text)
        if len(sentences) > 3:
            suggestions.append({
                "type": "structure",
                "original": "长段落",
                "optimized": "分段处理",
                "explanation": "建议将长段落分解为多个短段落，提高可读性",
                "confidence": 0.85
            })
    
    processing_time = time.time() - start_time
    
    return {
        "success": True,
        "data": {
            "optimized_text": optimized_text,
            "suggestions": suggestions,
            "confidence": round(sum(s["confidence"] for s in suggestions) / len(suggestions), 2) if suggestions else 0.5,
            "processing_time": round(processing_time, 2),
            "optimization_type": request.optimization_type,
            "original_length": len(request.text),
            "optimized_length": len(optimized_text)
        },
        "message": "文本优化完成"
    }

@app.post("/api/v1/ai/classify-content")
def classify_content(request: ClassificationRequest):
    """内容分类API"""
    start_time = time.time()
    content = request.content
    
    # 模拟AI处理时间
    time.sleep(random.uniform(0.3, 0.8))
    
    # 智能分类规则
    categories = []
    
    # 技术相关
    tech_keywords = ["技术", "代码", "编程", "算法", "开发", "软件", "系统", "架构", "数据库", "API"]
    if any(keyword in content for keyword in tech_keywords):
        categories.append({
            "category_name": "技术文档",
            "confidence": round(random.uniform(0.85, 0.95), 2),
            "reasoning": "包含技术开发相关关键词",
            "is_existing": True
        })
    
    # 学习相关
    study_keywords = ["学习", "笔记", "总结", "知识", "教程", "课程", "理解", "掌握", "复习"]
    if any(keyword in content for keyword in study_keywords):
        categories.append({
            "category_name": "学习笔记",
            "confidence": round(random.uniform(0.80, 0.92), 2),
            "reasoning": "包含学习和知识相关关键词",
            "is_existing": True
        })
    
    # 工作相关
    work_keywords = ["工作", "项目", "任务", "计划", "会议", "报告", "进度", "目标", "团队"]
    if any(keyword in content for keyword in work_keywords):
        categories.append({
            "category_name": "工作总结",
            "confidence": round(random.uniform(0.78, 0.90), 2),
            "reasoning": "包含工作和项目相关关键词",
            "is_existing": True
        })
    
    # 生活相关
    life_keywords = ["生活", "日记", "感想", "心情", "体验", "感受", "思考", "随笔"]
    if any(keyword in content for keyword in life_keywords):
        categories.append({
            "category_name": "生活随笔",
            "confidence": round(random.uniform(0.75, 0.88), 2),
            "reasoning": "包含生活和个人感受相关关键词",
            "is_existing": False
        })
    
    # 如果没有匹配到特定分类
    if not categories:
        categories.append({
            "category_name": "其他",
            "confidence": 0.6,
            "reasoning": "未匹配到特定分类关键词",
            "is_existing": True
        })
    
    # 提取关键词和主题
    import re
    words = re.findall(r'[\\u4e00-\\u9fff]+|[a-zA-Z]+', content)
    key_phrases = list(set([w for w in words if len(w) > 1]))[:8]
    
    detected_topics = [cat["category_name"] for cat in categories]
    
    # 判断内容类型
    content_types = {
        "技术文档": "technical_document",
        "学习笔记": "study_notes", 
        "工作总结": "work_summary",
        "生活随笔": "life_essay",
        "其他": "general"
    }
    
    main_category = categories[0]["category_name"] if categories else "其他"
    content_type = content_types.get(main_category, "general")
    
    processing_time = time.time() - start_time
    
    return {
        "success": True,
        "data": {
            "suggestions": categories,
            "detected_topics": detected_topics,
            "key_phrases": key_phrases,
            "content_type": content_type,
            "processing_time": round(processing_time, 2),
            "content_length": len(content)
        },
        "message": "内容分类完成"
    }

@app.get("/api/v1/ai/quota")
def get_quota():
    """获取AI配额信息（模拟）"""
    return {
        "success": True,
        "data": {
            "plan_type": "free",
            "daily_limit": 50,
            "daily_used": random.randint(5, 25),
            "monthly_limit": 1000,
            "monthly_used": random.randint(100, 500),
            "reset_date": "2025-02-01T00:00:00Z"
        },
        "message": "配额信息获取成功"
    }

if __name__ == "__main__":
    print("🚀 NoteAI AI服务启动")
    print("📖 API文档: http://localhost:8002/docs")
    print("🔍 健康检查: http://localhost:8002/health")
    print("🤖 AI配额: http://localhost:8002/api/v1/ai/quota")
    print("")
    print("📝 测试用例:")
    print("1. 文本优化: POST /api/v1/ai/optimize-text")
    print("   {\"text\":\"这个算法的效率不好\",\"optimization_type\":\"expression\"}")
    print("2. 内容分类: POST /api/v1/ai/classify-content")
    print("   {\"content\":\"机器学习是人工智能的重要分支\"}")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
'''
    
    # 写入临时文件
    with open("fixed_ai_service.py", "w", encoding="utf-8") as f:
        f.write(code)
    
    # 启动服务
    try:
        subprocess.run([sys.executable, "fixed_ai_service.py"], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  AI服务已停止")
    finally:
        # 清理临时文件
        if os.path.exists("fixed_ai_service.py"):
            os.remove("fixed_ai_service.py")

def main():
    """主函数"""
    print("🚀 NoteAI 修复版服务启动器")
    print("=" * 50)
    
    print("📋 可用服务:")
    print("1. 用户服务 (端口 8001)")
    print("2. AI服务 (端口 8002)")
    print("3. 笔记服务 (端口 8003)")
    print("4. 退出")
    
    while True:
        try:
            choice = input("\n请选择要启动的服务 (1-4): ").strip()
            
            if choice == "1":
                start_user_service()
                break
            elif choice == "2":
                start_ai_service()
                break
            elif choice == "3":
                print("🚀 启动笔记服务...")
                print("请在另一个终端运行: python3 simple_note_service.py")
                break
            elif choice == "4":
                print("👋 再见！")
                break
            else:
                print("❌ 无效选择，请输入 1-4")
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()
