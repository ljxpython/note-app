# NoteAI 默认账号信息

## 🔑 管理员账号

### 默认管理员
- **邮箱**: `admin@noteai.com`
- **密码**: `AdminPass123!`
- **用户名**: `admin`
- **角色**: `admin`（管理员权限）
- **状态**: 已激活
- **权限**: 
  - 用户管理
  - 系统配置
  - 数据管理
  - AI服务管理

## 👥 测试账号

### 测试用户1
- **邮箱**: `test@example.com`
- **密码**: `test123456`
- **用户名**: `testuser`
- **角色**: `user`（普通用户）

### 演示用户
- **邮箱**: `demo@noteai.com`
- **密码**: `demo123456`
- **用户名**: `demouser`
- **角色**: `user`（普通用户）

### 验收测试用户
- **邮箱**: `acceptance_test@example.com`
- **密码**: `test123456`
- **用户名**: `acceptance_user`
- **角色**: `user`（普通用户）

## 🚀 快速登录

### 方式一：使用管理员账号
1. 访问 http://localhost:3000
2. 点击"登录"
3. 输入邮箱：`admin@noteai.com`
4. 输入密码：`AdminPass123!`
5. 点击登录

### 方式二：使用测试账号
1. 访问 http://localhost:3000
2. 点击"登录"
3. 输入邮箱：`test@example.com`
4. 输入密码：`test123456`
5. 点击登录

## 🔐 权限说明

### 管理员权限 (`admin`)
- ✅ 查看所有用户
- ✅ 管理用户账号
- ✅ 系统配置管理
- ✅ AI服务管理
- ✅ 数据库管理
- ✅ 所有笔记操作

### 普通用户权限 (`user`)
- ✅ 管理自己的笔记
- ✅ 使用AI功能
- ✅ 创建分类
- ✅ 修改个人资料
- ❌ 查看其他用户信息
- ❌ 系统管理功能

## ⚠️ 安全提醒

### 生产环境安全
1. **立即修改默认密码**
   - 管理员密码必须修改
   - 使用强密码（至少8位，包含大小写字母、数字、特殊字符）

2. **删除测试账号**
   - 生产环境应删除所有测试账号
   - 只保留必要的管理员账号

3. **密码策略**
   - 定期更新密码
   - 启用双因素认证（如需要）
   - 监控登录日志

### 开发环境使用
- 可以保留测试账号用于开发测试
- 定期清理测试数据
- 不要在测试环境使用真实用户数据

## 🛠️ 账号管理命令

### 初始化管理员账号
```bash
make init-admin
```

### 重置所有账号
```bash
# 清理数据库
make clean
# 重新设置
make setup
```

### 查看账号状态
```bash
# 启动服务后访问
curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/api/v1/users
```

## 📱 登录测试

### 测试管理员登录
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@noteai.com","password":"AdminPass123!"}'
```

### 测试普通用户登录
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123456"}'
```

## 🔄 密码修改

### 通过API修改密码
1. 先登录获取token
2. 使用token调用密码修改接口：
```bash
curl -X POST http://localhost:8000/api/v1/users/change-password \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"current_password":"admin123456","new_password":"new_secure_password"}'
```

### 通过前端修改密码
1. 登录系统
2. 进入个人设置页面
3. 找到"修改密码"选项
4. 输入当前密码和新密码
5. 保存修改

---

**🔐 请务必在首次使用后立即修改默认密码！**

*更新时间: 2025-01-17*
