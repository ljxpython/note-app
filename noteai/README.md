# 🤖 NoteAI - AI驱动的智能笔记分享平台

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![AutoGen](https://img.shields.io/badge/AutoGen-0.4+-purple.svg)](https://github.com/microsoft/autogen)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

NoteAI是一个基于Microsoft AutoGen框架的AI驱动智能笔记分享平台，提供文本优化、智能分类、协作编辑等功能。

## ✨ 核心功能

### 🧠 AI智能功能
- **文本优化**: 基于AutoGen的语法修正、表达改进、结构优化
- **智能续写**: 上下文感知的内容续写建议
- **自动分类**: AI驱动的内容主题识别和分类
- **风格学习**: 个性化写作风格适应

### 📝 笔记管理
- **实时编辑**: 支持Markdown的实时编辑器
- **版本控制**: 完整的笔记版本历史管理
- **自动保存**: 智能自动保存机制
- **全文搜索**: 基于Elasticsearch的高性能搜索

### 🤝 协作分享
- **多级权限**: 灵活的分享权限控制
- **圈子协作**: 团队协作和知识共享
- **评论互动**: 实时评论和反馈系统
- **关注推荐**: 智能内容推荐算法

## 🏗️ 技术架构

### 核心技术栈
- **后端框架**: FastAPI + Python 3.12
- **AI框架**: Microsoft AutoGen v0.4
- **数据库**: PostgreSQL + MongoDB + Redis
- **搜索引擎**: Elasticsearch
- **容器化**: Docker + Docker Compose

### 微服务架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Service  │    │   AI Service    │    │  Note Service   │
│     (8001)      │    │     (8002)      │    │     (8003)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  API Gateway    │
                    │     (8000)      │
                    └─────────────────┘
```

## 🚀 快速开始

### 环境要求
- Python 3.12+
- Docker & Docker Compose
- Git

### 1. 克隆项目
```bash
git clone https://github.com/noteai/noteai.git
cd noteai
```

### 2. 配置环境
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件，填入必要的配置
vim .env
```

**重要配置项**:
```env
# DeepSeek API密钥 (必需)
DEEPSEEK_API_KEY=your-deepseek-api-key-here

# JWT密钥 (必需，生产环境请使用强密钥)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# 数据库密码 (可选，开发环境使用默认值)
POSTGRES_PASSWORD=noteai_dev_pass
MONGODB_PASSWORD=noteai_dev_pass
REDIS_PASSWORD=noteai_dev_pass
```

### 3. 启动开发环境
```bash
# 启动所有服务
./scripts/start-dev.sh

# 或者后台启动
./scripts/start-dev.sh -d

# 启动并包含开发工具
./scripts/start-dev.sh -t
```

### 4. 验证服务
访问以下地址验证服务是否正常启动：

- **API网关**: http://localhost:8000/health
- **用户服务**: http://localhost:8001/docs
- **AI服务**: http://localhost:8002/docs  
- **笔记服务**: http://localhost:8003/docs

### 5. 开发工具
- **Adminer** (数据库管理): http://localhost:8080
- **Mongo Express** (MongoDB管理): http://localhost:8081
- **Redis Commander** (Redis管理): http://localhost:8082

## 📖 API文档

### 用户服务 API
```bash
# 用户注册
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "username": "testuser",
  "password": "SecurePass123!"
}

# 用户登录
POST /api/v1/auth/login
{
  "email": "user@example.com", 
  "password": "SecurePass123!"
}

# 获取用户资料
GET /api/v1/users/profile
Authorization: Bearer <access_token>
```

### AI服务 API
```bash
# 文本优化
POST /api/v1/ai/optimize-text
Authorization: Bearer <access_token>
{
  "text": "这个算法的效率不是很好",
  "optimization_type": "expression"
}

# 内容分类
POST /api/v1/ai/classify-content
Authorization: Bearer <access_token>
{
  "content": "机器学习是人工智能的重要分支...",
  "existing_categories": [...]
}
```

### 笔记服务 API
```bash
# 创建笔记
POST /api/v1/notes
Authorization: Bearer <access_token>
{
  "title": "我的笔记",
  "content": "# 标题\n内容..."
}

# 获取笔记列表
GET /api/v1/notes?page=1&limit=20
Authorization: Bearer <access_token>
```

## 🧪 开发指南

### 本地开发
```bash
# 安装Python依赖
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"

# 运行代码格式化
black .
isort .

# 运行类型检查
mypy .

# 运行测试
pytest
```

### 服务开发
```bash
# 仅启动数据库服务
./scripts/start-dev.sh -s "postgres mongodb redis elasticsearch"

# 本地运行用户服务
cd services/user_service
uvicorn main:app --reload --port 8001

# 本地运行AI服务
cd services/ai_service  
uvicorn main:app --reload --port 8002
```

### AutoGen Agent开发
```python
# 创建自定义AI Agent
from autogen_core import BaseAgent
from autogen_agentchat.agents import AssistantAgent

class CustomAgent(BaseAgent):
    def __init__(self, name: str, model_config: dict):
        super().__init__(name)
        self.assistant = AssistantAgent(
            name=name,
            model_client=create_model_client(model_config),
            system_message="你的系统消息..."
        )
    
    async def process_request(self, request: dict):
        result = await self.assistant.run(task=request["task"])
        return self.parse_result(result)
```

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定服务测试
pytest tests/test_user_service.py

# 运行集成测试
pytest tests/integration/

# 生成测试覆盖率报告
pytest --cov=noteai --cov-report=html
```

### 测试用户
开发环境会自动创建以下测试用户：

- **管理员**: admin@noteai.com / admin123456
- **测试用户**: test@noteai.com / TestPass123!

## 📦 部署

### Docker部署
```bash
# 构建生产镜像
docker-compose -f docker-compose.prod.yml build

# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes部署
```bash
# 应用Kubernetes配置
kubectl apply -f k8s/

# 检查部署状态
kubectl get pods -n noteai
```

## 🔧 配置说明

### 环境变量
详细的环境变量配置请参考 [.env.example](.env.example) 文件。

### AI模型配置
```env
# DeepSeek配置 (推荐)
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MAX_TOKENS=4000

# OpenAI配置 (备用)
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4
```

### 数据库配置
```env
# PostgreSQL (用户数据)
POSTGRES_HOST=localhost
POSTGRES_DB=noteai_users

# MongoDB (笔记数据)
MONGODB_HOST=localhost
MONGODB_DB=noteai_notes

# Redis (缓存)
REDIS_HOST=localhost
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码规范
- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 使用 mypy 进行类型检查
- 编写单元测试和集成测试
- 遵循 FastAPI 最佳实践

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [Microsoft AutoGen](https://github.com/microsoft/autogen) - 强大的多智能体框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [DeepSeek](https://www.deepseek.com/) - 优秀的AI模型服务

## 📞 联系我们

- 项目主页: https://github.com/noteai/noteai
- 问题反馈: https://github.com/noteai/noteai/issues
- 邮箱: dev@noteai.com

---

**⭐ 如果这个项目对你有帮助，请给我们一个星标！**
