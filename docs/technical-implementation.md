# 🛠️ 技术实现文档
## NoteAI - Python + AutoGen 技术实现指南

**文档版本**: v1.0  
**创建日期**: 2025-01-17  
**技术栈**: Python 3.12 + FastAPI + AutoGen v0.4  
**Scrum Master**: AI Scrum Master  

---

## 🎯 技术架构概览

### 核心技术栈
- **后端框架**: FastAPI + Python 3.12
- **AI框架**: Microsoft AutoGen v0.4 (autogen-core + autogen-agentchat)
- **数据库**: PostgreSQL (用户数据) + MongoDB (笔记/AI会话) + Redis (缓存)
- **消息队列**: Celery + Redis
- **搜索引擎**: Elasticsearch
- **容器化**: Docker + Docker Compose
- **API文档**: FastAPI自动生成 + Swagger UI

### 项目结构
```
noteai/
├── services/
│   ├── user_service/           # 用户服务 (Port 8001)
│   ├── ai_service/             # AI服务 (Port 8002)
│   ├── note_service/           # 笔记服务 (Port 8003)
│   └── api_gateway/            # API网关 (Port 8000)
├── shared/
│   ├── models/                 # 共享数据模型
│   ├── utils/                  # 工具函数
│   └── config/                 # 配置管理
├── tests/                      # 测试文件
├── docker/                     # Docker配置
├── scripts/                    # 部署脚本
└── requirements/               # 依赖管理
```

---

## 🔧 环境配置

### Python环境设置
```bash
# 创建Python虚拟环境
python3.12 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装核心依赖
pip install -U pip setuptools wheel

# 安装AutoGen
pip install -U "autogen-agentchat" "autogen-ext[openai]" "autogen-core"

# 安装FastAPI和其他依赖
pip install fastapi uvicorn sqlalchemy psycopg2-binary
pip install motor pymongo redis celery elasticsearch
pip install pydantic python-jose[cryptography] passlib[bcrypt]
pip install pytest pytest-asyncio httpx
```

### Docker开发环境
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  # PostgreSQL - 用户数据
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: noteai_users
      POSTGRES_USER: noteai
      POSTGRES_PASSWORD: noteai_dev_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # MongoDB - 笔记和AI会话
  mongodb:
    image: mongo:6
    environment:
      MONGO_INITDB_ROOT_USERNAME: noteai
      MONGO_INITDB_ROOT_PASSWORD: noteai_dev_pass
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

  # Redis - 缓存和消息队列
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass noteai_dev_pass
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Elasticsearch - 搜索引擎
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

volumes:
  postgres_data:
  mongodb_data:
  redis_data:
  elasticsearch_data:
```

---

## 🤖 AutoGen AI服务实现

### AI Agent架构设计
```python
# ai_service/agents/base_agent.py
from autogen_core import BaseAgent, MessageContext
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from typing import Dict, Any, Optional
import asyncio
import json

class NoteAIBaseAgent(BaseAgent):
    """NoteAI基础Agent类"""
    
    def __init__(self, name: str, model_config: Dict[str, Any]):
        super().__init__(name)
        self.model_client = self._create_model_client(model_config)
        self.assistant = AssistantAgent(
            name=name,
            model_client=self.model_client,
            system_message=self._get_system_message()
        )
    
    def _create_model_client(self, config: Dict[str, Any]):
        """创建模型客户端"""
        if config.get("provider") == "deepseek":
            return OpenAIChatCompletionClient(
                model=config.get("model", "deepseek-chat"),
                api_key=config.get("api_key"),
                base_url="https://api.deepseek.com"
            )
        else:
            return OpenAIChatCompletionClient(
                model=config.get("model", "gpt-4"),
                api_key=config.get("api_key")
            )
    
    def _get_system_message(self) -> str:
        """获取系统消息，子类需要重写"""
        return "You are a helpful AI assistant."
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求，子类需要重写"""
        raise NotImplementedError
```

### 文本优化Agent
```python
# ai_service/agents/text_optimizer.py
from .base_agent import NoteAIBaseAgent
from typing import Dict, Any, List
import re

class TextOptimizerAgent(NoteAIBaseAgent):
    """文本优化AI Agent"""
    
    def _get_system_message(self) -> str:
        return """你是一个专业的中文文本优化助手。你的任务是：

1. 识别并修正语法错误
2. 改善表达方式，使其更清晰、准确
3. 优化文本结构，提高可读性
4. 保持原文的核心意思不变
5. 根据用户的写作风格偏好进行调整

请始终返回JSON格式的结果，包含：
- optimized_text: 优化后的完整文本
- suggestions: 具体的修改建议列表
- confidence: 优化质量的置信度(0-1)
"""
    
    async def optimize_text(self, text: str, user_style: Optional[str] = None) -> Dict[str, Any]:
        """优化文本内容"""
        prompt = self._build_optimization_prompt(text, user_style)
        
        try:
            result = await self.assistant.run(task=prompt)
            return self._parse_optimization_result(result.messages[-1].content)
        except Exception as e:
            return {
                "error": str(e),
                "optimized_text": text,
                "suggestions": [],
                "confidence": 0.0
            }
    
    def _build_optimization_prompt(self, text: str, user_style: Optional[str]) -> str:
        """构建优化提示词"""
        prompt = f"""请优化以下文本：

原文：
{text}

"""
        if user_style:
            prompt += f"用户写作风格偏好：{user_style}\n"
        
        prompt += """
请返回JSON格式的结果：
{
    "optimized_text": "优化后的完整文本",
    "suggestions": [
        {
            "type": "grammar|expression|structure",
            "original": "原始片段",
            "optimized": "优化片段",
            "explanation": "修改说明",
            "position": {"start": 0, "end": 10}
        }
    ],
    "confidence": 0.95
}
"""
        return prompt
    
    def _parse_optimization_result(self, result_text: str) -> Dict[str, Any]:
        """解析优化结果"""
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # 如果没有找到JSON，返回默认结构
                return {
                    "optimized_text": result_text,
                    "suggestions": [],
                    "confidence": 0.5
                }
        except json.JSONDecodeError:
            return {
                "optimized_text": result_text,
                "suggestions": [],
                "confidence": 0.3
            }
```

### 内容分类Agent
```python
# ai_service/agents/content_classifier.py
from .base_agent import NoteAIBaseAgent
from typing import Dict, Any, List

class ContentClassifierAgent(NoteAIBaseAgent):
    """内容分类AI Agent"""
    
    def _get_system_message(self) -> str:
        return """你是一个专业的内容分类助手。你的任务是：

1. 分析文本内容的主题和类型
2. 根据现有分类体系推荐最合适的分类
3. 提取关键词和主题标签
4. 评估分类的置信度

请始终返回JSON格式的结果。
"""
    
    async def classify_content(self, content: str, existing_categories: List[Dict]) -> Dict[str, Any]:
        """分类内容"""
        prompt = self._build_classification_prompt(content, existing_categories)
        
        try:
            result = await self.assistant.run(task=prompt)
            return self._parse_classification_result(result.messages[-1].content)
        except Exception as e:
            return {
                "error": str(e),
                "suggestions": [],
                "detected_topics": [],
                "key_phrases": []
            }
    
    def _build_classification_prompt(self, content: str, categories: List[Dict]) -> str:
        """构建分类提示词"""
        categories_text = "\n".join([
            f"- {cat['name']}: {cat.get('description', '')}" 
            for cat in categories
        ])
        
        return f"""请分析以下内容并进行分类：

内容：
{content}

现有分类：
{categories_text}

请返回JSON格式的结果：
{{
    "suggestions": [
        {{
            "category_name": "分类名称",
            "confidence": 0.92,
            "reasoning": "分类理由"
        }}
    ],
    "detected_topics": ["主题1", "主题2"],
    "key_phrases": ["关键词1", "关键词2"],
    "content_type": "技术文档|学习笔记|工作总结|创意想法|其他"
}}
"""
    
    def _parse_classification_result(self, result_text: str) -> Dict[str, Any]:
        """解析分类结果"""
        try:
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "suggestions": [],
                    "detected_topics": [],
                    "key_phrases": [],
                    "content_type": "其他"
                }
        except json.JSONDecodeError:
            return {
                "suggestions": [],
                "detected_topics": [],
                "key_phrases": [],
                "content_type": "其他"
            }
```

---

## 🚀 FastAPI服务实现

### 用户服务 (Port 8001)
```python
# user_service/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

app = FastAPI(
    title="NoteAI User Service",
    description="用户认证和管理服务",
    version="1.0.0"
)

# 安全配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# 数据模型
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    created_at: datetime
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

# API端点
@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户是否已存在
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已存在"
        )
    
    # 创建新用户
    hashed_password = pwd_context.hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse.from_orm(new_user)

@app.post("/api/v1/auth/login", response_model=Token)
async def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not pwd_context.verify(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )
    
    # 生成JWT Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, 
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.get("/api/v1/users/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """获取用户资料"""
    return UserResponse.from_orm(current_user)

# 工具函数
def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取当前用户"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

### AI服务 (Port 8002)
```python
# ai_service/main.py
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import redis
import json
from .agents.text_optimizer import TextOptimizerAgent
from .agents.content_classifier import ContentClassifierAgent

app = FastAPI(
    title="NoteAI AI Service",
    description="AI文本处理和分类服务",
    version="1.0.0"
)

# Redis连接
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True
)

# AI Agent实例
model_config = {
    "provider": "deepseek",
    "model": "deepseek-chat",
    "api_key": os.getenv("DEEPSEEK_API_KEY")
}

text_optimizer = TextOptimizerAgent("text_optimizer", model_config)
content_classifier = ContentClassifierAgent("content_classifier", model_config)

# 请求模型
class OptimizationRequest(BaseModel):
    text: str
    user_id: str
    user_style: Optional[str] = None
    optimization_type: str = "all"  # grammar, expression, structure, all

class ClassificationRequest(BaseModel):
    content: str
    user_id: str
    existing_categories: List[Dict[str, Any]] = []

# API端点
@app.post("/api/v1/ai/optimize-text")
async def optimize_text(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_token)
):
    """文本优化API"""
    # 检查缓存
    cache_key = f"optimize:{hash(request.text)}:{request.user_style}"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return json.loads(cached_result)
    
    try:
        # 调用AI Agent
        result = await text_optimizer.optimize_text(
            text=request.text,
            user_style=request.user_style
        )
        
        # 缓存结果
        redis_client.setex(cache_key, 1800, json.dumps(result))  # 30分钟缓存
        
        # 后台任务：记录使用情况
        background_tasks.add_task(
            log_ai_usage,
            user_id=request.user_id,
            operation="text_optimization",
            input_length=len(request.text)
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI处理失败: {str(e)}")

@app.post("/api/v1/ai/classify-content")
async def classify_content(
    request: ClassificationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_token)
):
    """内容分类API"""
    cache_key = f"classify:{hash(request.content)}"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return json.loads(cached_result)
    
    try:
        result = await content_classifier.classify_content(
            content=request.content,
            existing_categories=request.existing_categories
        )
        
        # 缓存结果
        redis_client.setex(cache_key, 3600, json.dumps(result))  # 1小时缓存
        
        # 记录使用情况
        background_tasks.add_task(
            log_ai_usage,
            user_id=request.user_id,
            operation="content_classification",
            input_length=len(request.content)
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分类失败: {str(e)}")

async def log_ai_usage(user_id: str, operation: str, input_length: int):
    """记录AI使用情况"""
    # 这里可以记录到数据库或监控系统
    pass

async def verify_token(authorization: str = Depends(HTTPBearer())):
    """验证JWT Token"""
    # 调用用户服务验证Token
    # 这里简化处理，实际应该调用用户服务API
    return {"user_id": "test-user"}
```

---

## 📝 笔记服务实现 (Port 8003)

### 笔记数据模型 (MongoDB)
```python
# note_service/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class NoteCreate(BaseModel):
    title: str
    content: str = ""
    category_id: Optional[str] = None
    tags: List[str] = []
    is_public: bool = False

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    is_public: Optional[bool] = None

class Note(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    title: str
    content: str
    content_html: str = ""
    excerpt: str = ""

    # 元数据
    word_count: int = 0
    character_count: int = 0
    reading_time: int = 0  # 分钟
    language: str = "zh"

    # 分类和标签
    category_id: Optional[str] = None
    tags: List[str] = []

    # 状态
    status: str = "draft"  # draft, published, archived, deleted
    is_public: bool = False
    is_favorite: bool = False

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
```

### 笔记服务API
```python
# note_service/main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
import os
import asyncio
from datetime import datetime

app = FastAPI(
    title="NoteAI Note Service",
    description="笔记管理服务",
    version="1.0.0"
)

# MongoDB连接
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGODB_URL)
database = client.noteai
notes_collection = database.notes

@app.post("/api/v1/notes", response_model=Note)
async def create_note(
    note_data: NoteCreate,
    current_user: dict = Depends(verify_token)
):
    """创建笔记"""
    # 处理内容
    content_html = await render_markdown(note_data.content)
    excerpt = generate_excerpt(note_data.content)

    note_dict = {
        "user_id": current_user["user_id"],
        "title": note_data.title,
        "content": note_data.content,
        "content_html": content_html,
        "excerpt": excerpt,
        "word_count": len(note_data.content),
        "character_count": len(note_data.content),
        "reading_time": calculate_reading_time(note_data.content),
        "category_id": note_data.category_id,
        "tags": note_data.tags,
        "is_public": note_data.is_public,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await notes_collection.insert_one(note_dict)
    note_dict["_id"] = result.inserted_id

    # 异步任务：AI自动分类
    asyncio.create_task(auto_classify_note(str(result.inserted_id), note_data.content))

    return Note(**note_dict)

@app.get("/api/v1/notes", response_model=List[Note])
async def get_notes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    current_user: dict = Depends(verify_token)
):
    """获取笔记列表"""
    skip = (page - 1) * limit

    # 构建查询条件
    query = {"user_id": current_user["user_id"], "status": {"$ne": "deleted"}}

    if category_id:
        query["category_id"] = category_id

    if tags:
        query["tags"] = {"$in": tags}

    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}}
        ]

    # 执行查询
    cursor = notes_collection.find(query).sort("updated_at", -1).skip(skip).limit(limit)
    notes = await cursor.to_list(length=limit)

    return [Note(**note) for note in notes]

@app.get("/api/v1/notes/{note_id}", response_model=Note)
async def get_note(
    note_id: str,
    current_user: dict = Depends(verify_token)
):
    """获取单个笔记"""
    note = await notes_collection.find_one({
        "_id": ObjectId(note_id),
        "user_id": current_user["user_id"]
    })

    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    return Note(**note)

@app.put("/api/v1/notes/{note_id}", response_model=Note)
async def update_note(
    note_id: str,
    note_data: NoteUpdate,
    current_user: dict = Depends(verify_token)
):
    """更新笔记"""
    update_data = {"updated_at": datetime.utcnow()}

    # 只更新提供的字段
    for field, value in note_data.dict(exclude_unset=True).items():
        if field == "content":
            update_data["content"] = value
            update_data["content_html"] = await render_markdown(value)
            update_data["excerpt"] = generate_excerpt(value)
            update_data["word_count"] = len(value)
            update_data["character_count"] = len(value)
            update_data["reading_time"] = calculate_reading_time(value)
        else:
            update_data[field] = value

    result = await notes_collection.update_one(
        {"_id": ObjectId(note_id), "user_id": current_user["user_id"]},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="笔记不存在")

    # 获取更新后的笔记
    updated_note = await notes_collection.find_one({"_id": ObjectId(note_id)})
    return Note(**updated_note)

@app.delete("/api/v1/notes/{note_id}")
async def delete_note(
    note_id: str,
    current_user: dict = Depends(verify_token)
):
    """删除笔记（软删除）"""
    result = await notes_collection.update_one(
        {"_id": ObjectId(note_id), "user_id": current_user["user_id"]},
        {"$set": {"status": "deleted", "updated_at": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="笔记不存在")

    return {"message": "笔记已删除"}

# 工具函数
async def render_markdown(content: str) -> str:
    """渲染Markdown为HTML"""
    import markdown
    return markdown.markdown(content)

def generate_excerpt(content: str, max_length: int = 200) -> str:
    """生成摘要"""
    # 移除Markdown标记
    import re
    clean_content = re.sub(r'[#*`\[\]()]', '', content)
    return clean_content[:max_length] + "..." if len(clean_content) > max_length else clean_content

def calculate_reading_time(content: str) -> int:
    """计算阅读时间（分钟）"""
    words = len(content.split())
    return max(1, words // 200)  # 假设每分钟200字

async def auto_classify_note(note_id: str, content: str):
    """自动分类笔记"""
    # 调用AI服务进行分类
    # 这里简化处理，实际应该调用AI服务API
    pass
```

---

## 🐳 Docker部署配置

### 服务Dockerfile
```dockerfile
# Dockerfile.user_service
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements/user_service.txt .
RUN pip install --no-cache-dir -r user_service.txt

# 复制应用代码
COPY user_service/ ./user_service/
COPY shared/ ./shared/

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["uvicorn", "user_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Docker Compose生产配置
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  # API网关
  api-gateway:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - user-service
      - note-service
      - ai-service

  # 用户服务
  user-service:
    build:
      context: .
      dockerfile: Dockerfile.user_service
    environment:
      - DATABASE_URL=${USER_DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 2

  # AI服务
  ai-service:
    build:
      context: .
      dockerfile: Dockerfile.ai_service
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - REDIS_URL=${REDIS_URL}
      - MONGODB_URL=${MONGODB_URL}
    depends_on:
      - mongodb
      - redis
    deploy:
      replicas: 2

  # 笔记服务
  note-service:
    build:
      context: .
      dockerfile: Dockerfile.note_service
    environment:
      - MONGODB_URL=${MONGODB_URL}
      - ELASTICSEARCH_URL=${ELASTICSEARCH_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - mongodb
      - elasticsearch
      - redis
    deploy:
      replicas: 2

  # 数据库服务
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      replicas: 1

  mongodb:
    image: mongo:6
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
    volumes:
      - mongodb_data:/data/db
    deploy:
      replicas: 1

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    deploy:
      replicas: 1

  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    deploy:
      replicas: 1

volumes:
  postgres_data:
  mongodb_data:
  redis_data:
  elasticsearch_data:
```

---

## 🧪 测试配置

### 测试依赖
```txt
# requirements/test.txt
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
pytest-mock==3.12.0
factory-boy==3.3.0
faker==20.1.0
```

### 测试示例
```python
# tests/test_ai_service.py
import pytest
import asyncio
from unittest.mock import Mock, patch
from ai_service.agents.text_optimizer import TextOptimizerAgent

@pytest.fixture
def mock_model_config():
    return {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "api_key": "test-api-key"
    }

@pytest.fixture
def text_optimizer(mock_model_config):
    return TextOptimizerAgent("test_optimizer", mock_model_config)

@pytest.mark.asyncio
async def test_optimize_text_success(text_optimizer):
    """测试文本优化成功场景"""
    test_text = "这个算法的效率不是很好"

    # Mock AutoGen Assistant
    with patch.object(text_optimizer.assistant, 'run') as mock_run:
        mock_result = Mock()
        mock_result.messages = [Mock()]
        mock_result.messages[-1].content = '''
        {
            "optimized_text": "这个算法的效率有待提升",
            "suggestions": [
                {
                    "type": "expression",
                    "original": "不是很好",
                    "optimized": "有待提升",
                    "explanation": "使用更专业的表达"
                }
            ],
            "confidence": 0.9
        }
        '''
        mock_run.return_value = mock_result

        result = await text_optimizer.optimize_text(test_text)

        assert result["optimized_text"] == "这个算法的效率有待提升"
        assert len(result["suggestions"]) == 1
        assert result["confidence"] == 0.9

@pytest.mark.asyncio
async def test_optimize_text_error_handling(text_optimizer):
    """测试文本优化错误处理"""
    test_text = "测试文本"

    with patch.object(text_optimizer.assistant, 'run', side_effect=Exception("API Error")):
        result = await text_optimizer.optimize_text(test_text)

        assert "error" in result
        assert result["optimized_text"] == test_text
        assert result["confidence"] == 0.0
```

---

**技术实现文档状态**: ✅ 已完成
**包含内容**: Python + AutoGen完整技术栈实现
**下一步**: 切换到 @dev 角色开始代码实现
