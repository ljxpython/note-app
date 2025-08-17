# NoteAI - 智能笔记反馈系统

一个基于React + FastAPI的现代化反馈管理系统，支持图片上传、用户认证、管理员回复等功能。

## 🚀 功能特性

### 用户功能
- ✅ **用户注册/登录** - 完整的用户认证系统
- ✅ **反馈提交** - 支持多种类型的反馈（Bug、功能建议、其他）
- ✅ **图片上传** - 支持多种上传方式：
  - 文件选择上传
  - 拖拽上传
  - 复制粘贴上传 (Ctrl+V)
- ✅ **反馈管理** - 查看、编辑、删除自己的反馈
- ✅ **实时状态** - 反馈处理状态实时更新

### 管理员功能
- ✅ **反馈管理** - 查看所有用户反馈
- ✅ **状态更新** - 更改反馈处理状态
- ✅ **回复功能** - 对用户反馈进行回复
- ✅ **用户管理** - 管理系统用户

### 技术特性
- ✅ **现代化UI** - 基于Tailwind CSS的响应式设计
- ✅ **图片预览** - 支持图片预览和大图查看
- ✅ **文件管理** - 安全的文件上传和存储
- ✅ **API文档** - 完整的Swagger API文档
- ✅ **日志系统** - 详细的操作日志记录

## 🛠️ 技术栈

### 前端
- **React 18** - 现代化前端框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 实用优先的CSS框架
- **Axios** - HTTP客户端

### 后端
- **FastAPI** - 高性能Python Web框架
- **SQLAlchemy** - ORM数据库操作
- **SQLite** - 轻量级数据库
- **Loguru** - 现代化日志系统
- **Pillow** - 图片处理

## 📦 项目结构

```
note-app/
├── noteai/                     # 后端代码
│   ├── database/              # 数据库相关
│   │   ├── models.py         # 数据模型
│   │   └── repositories.py   # 数据访问层
│   ├── logs/                 # 日志文件
│   ├── uploads/              # 上传文件存储
│   └── unified_backend_service.py  # 主服务文件
├── noteai-frontend/           # 前端代码
│   ├── src/
│   │   ├── components/       # React组件
│   │   ├── contexts/         # React上下文
│   │   ├── pages/           # 页面组件
│   │   └── services/        # API服务
│   └── public/              # 静态资源
├── .gitignore               # Git忽略文件
└── README.md               # 项目说明
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 后端启动

1. 安装Python依赖：
```bash
cd noteai
pip install fastapi uvicorn sqlalchemy loguru pillow python-multipart
```

2. 启动后端服务：
```bash
python unified_backend_service.py
```

后端服务将在 `http://localhost:8000` 启动

### 前端启动

1. 安装依赖：
```bash
cd noteai-frontend
npm install
```

2. 启动开发服务器：
```bash
npm start
```

前端应用将在 `http://localhost:3000` 启动

### 默认账户

- **管理员账户**: admin@noteai.com / AdminPass123!
- **普通用户**: user@noteai.com / UserPass123!

## 📖 API文档

启动后端服务后，访问以下地址查看API文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔧 主要功能

### 反馈管理
- 创建、查看、编辑、删除反馈
- 支持多种反馈类型和优先级
- 反馈状态跟踪

### 图片上传
- 支持PNG、JPG、GIF格式
- 文件大小限制：5MB
- 多种上传方式支持
- 图片预览和管理

### 用户认证
- JWT Token认证
- 角色权限管理
- 安全的密码存储

## 🐛 已知问题

- [x] 图片显示问题 - 已修复
- [x] 用户输入内容显示异常 - 已修复
- [x] TypeScript编译错误 - 已修复

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目。

## 📄 许可证

MIT License

## 📞 联系方式

如有问题，请通过GitHub Issues联系。
