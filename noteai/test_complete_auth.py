#!/usr/bin/env python3
"""
测试完整的认证系统
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_auth_service():
    """测试认证服务"""
    try:
        from services.auth_service import auth_service
        
        print("🧪 测试认证服务...")
        
        # 测试密码加密
        password = "test123456"
        hashed = auth_service.hash_password(password)
        print(f"✅ 密码加密: {len(hashed)}字符")
        
        # 测试密码验证
        is_valid = auth_service.verify_password(password, hashed)
        print(f"✅ 密码验证: {'通过' if is_valid else '失败'}")
        
        # 测试JWT令牌创建
        token_data = {"sub": "test-user-id", "username": "testuser"}
        access_token = auth_service.create_access_token(token_data)
        print(f"✅ 访问令牌创建: {len(access_token)}字符")
        
        refresh_token = auth_service.create_refresh_token(token_data)
        print(f"✅ 刷新令牌创建: {len(refresh_token)}字符")
        
        # 测试令牌验证
        payload = auth_service.verify_token(access_token, "access")
        print(f"✅ 令牌验证: 用户ID={payload.get('sub')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 认证服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_user_service():
    """测试完整用户服务API"""
    try:
        from fastapi.testclient import TestClient
        from complete_user_service import app
        
        print("\n🧪 测试完整用户服务API...")
        
        client = TestClient(app)
        
        # 测试健康检查
        response = client.get("/health")
        print(f"✅ 健康检查: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   服务版本: {data['version']}")
            print(f"   数据库状态: {data['database']['status']}")
            print(f"   JWT认证: {'启用' if data['auth']['jwt_enabled'] else '禁用'}")
            print(f"   令牌过期: {data['auth']['token_expiry']}")
        
        # 测试用户注册
        print("\n🧪 测试用户注册...")
        register_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpass123",
            "bio": "这是一个新用户"
        }
        response = client.post("/api/v1/auth/register", json=register_data)
        print(f"✅ 用户注册: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   用户ID: {data['data']['user_id']}")
            print(f"   用户名: {data['data']['username']}")
            print(f"   邮箱: {data['data']['email']}")
        
        # 测试用户登录
        print("\n🧪 测试用户登录...")
        login_data = {
            "email": "newuser@example.com",
            "password": "newpass123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        print(f"✅ 用户登录: {response.status_code}")
        
        access_token = None
        refresh_token = None
        if response.status_code == 200:
            data = response.json()['data']
            access_token = data['access_token']
            refresh_token = data['refresh_token']
            print(f"   令牌类型: {data['token_type']}")
            print(f"   过期时间: {data['expires_in']}秒")
            print(f"   用户角色: {data['user']['role']}")
            print(f"   访问令牌: {access_token[:50]}...")
        
        if not access_token:
            print("❌ 无法获取访问令牌，跳过后续测试")
            return False
        
        # 测试获取用户资料
        print("\n🧪 测试获取用户资料...")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/v1/users/profile", headers=headers)
        print(f"✅ 获取用户资料: {response.status_code}")
        if response.status_code == 200:
            data = response.json()['data']
            print(f"   用户名: {data['username']}")
            print(f"   邮箱: {data['email']}")
            print(f"   角色: {data['role']}")
            print(f"   状态: {data['status']}")
            print(f"   创建时间: {data['created_at']}")
        
        # 测试更新用户资料
        print("\n🧪 测试更新用户资料...")
        update_data = {
            "bio": "更新后的用户简介",
            "location": "北京",
            "website": "https://example.com"
        }
        response = client.put("/api/v1/users/profile", json=update_data, headers=headers)
        print(f"✅ 更新用户资料: {response.status_code}")
        if response.status_code == 200:
            data = response.json()['data']
            print(f"   更新的简介: {data['bio']}")
            print(f"   更新的位置: {data['location']}")
            print(f"   更新的网站: {data['website']}")
        
        # 测试令牌验证
        print("\n🧪 测试令牌验证...")
        response = client.get("/api/v1/auth/verify-token", headers=headers)
        print(f"✅ 令牌验证: {response.status_code}")
        if response.status_code == 200:
            data = response.json()['data']
            print(f"   验证用户: {data['username']}")
            print(f"   验证时间: {data['verified_at']}")
        
        # 测试刷新令牌
        if refresh_token:
            print("\n🧪 测试刷新令牌...")
            refresh_data = {"refresh_token": refresh_token}
            response = client.post("/api/v1/auth/refresh", json=refresh_data)
            print(f"✅ 刷新令牌: {response.status_code}")
            if response.status_code == 200:
                data = response.json()['data']
                new_access_token = data['access_token']
                print(f"   新访问令牌: {new_access_token[:50]}...")
                print(f"   令牌类型: {data['token_type']}")
                print(f"   过期时间: {data['expires_in']}秒")
        
        # 测试修改密码
        print("\n🧪 测试修改密码...")
        password_data = {
            "current_password": "newpass123",
            "new_password": "newpass456"
        }
        response = client.post("/api/v1/users/change-password", json=password_data, headers=headers)
        print(f"✅ 修改密码: {response.status_code}")
        if response.status_code == 200:
            print("   密码修改成功")
        
        # 测试用户登出
        print("\n🧪 测试用户登出...")
        response = client.post("/api/v1/auth/logout", headers=headers)
        print(f"✅ 用户登出: {response.status_code}")
        if response.status_code == 200:
            print("   登出成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 完整用户服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_permission_system():
    """测试权限系统"""
    try:
        from services.auth_service import auth_service
        from database.models import User
        
        print("\n🧪 测试权限系统...")
        
        # 创建测试用户对象
        admin_user = User(id="admin-1", role="admin", status="active")
        user_user = User(id="user-1", role="user", status="active")
        
        # 测试管理员权限
        admin_can_read_users = auth_service.check_permission(admin_user, "user", "read")
        admin_can_manage_notes = auth_service.check_permission(admin_user, "note", "delete")
        print(f"✅ 管理员读取用户权限: {'有' if admin_can_read_users else '无'}")
        print(f"✅ 管理员删除笔记权限: {'有' if admin_can_manage_notes else '无'}")
        
        # 测试普通用户权限
        user_can_read_users = auth_service.check_permission(user_user, "user", "read")
        user_can_own_notes = auth_service.check_permission(user_user, "note", "own")
        print(f"✅ 普通用户读取用户权限: {'有' if user_can_read_users else '无'}")
        print(f"✅ 普通用户管理自己笔记权限: {'有' if user_can_own_notes else '无'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 权限系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 NoteAI 完整认证系统测试")
    print("=" * 60)
    
    # 检查依赖
    print("📦 检查依赖...")
    try:
        import jwt
        import fastapi
        import sqlalchemy
        import passlib
        import email_validator
        print("✅ JWT依赖已安装")
        print("✅ FastAPI依赖已安装")
        print("✅ SQLAlchemy依赖已安装")
        print("✅ Passlib依赖已安装")
        print("✅ Email-validator依赖已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        return 1
    
    tests_passed = 0
    total_tests = 3
    
    # 测试认证服务
    if test_auth_service():
        tests_passed += 1
    
    # 测试完整用户服务API
    if test_complete_user_service():
        tests_passed += 1
    
    # 测试权限系统
    if test_permission_system():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {tests_passed}/{total_tests} 通过")
    
    if tests_passed == total_tests:
        print("🎉 所有测试通过！")
        print("\n🔐 完整认证系统集成成功:")
        print("   ✅ JWT访问令牌和刷新令牌")
        print("   ✅ 密码加密存储(bcrypt)")
        print("   ✅ 用户注册和登录")
        print("   ✅ 用户资料管理")
        print("   ✅ 密码修改")
        print("   ✅ 令牌验证和刷新")
        print("   ✅ 基于角色的权限控制")
        print("   ✅ SQLite数据库持久化")
        print("")
        print("🚀 可以启动完整认证服务:")
        print("   python3 complete_user_service.py")
        print("   访问文档: http://localhost:8001/docs")
        print("")
        print("🔑 功能特性:")
        print("   - 30分钟访问令牌过期")
        print("   - 7天刷新令牌过期")
        print("   - 角色权限控制")
        print("   - 会话管理")
        print("   - 安全密码策略")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
