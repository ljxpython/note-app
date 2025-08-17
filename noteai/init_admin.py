#!/usr/bin/env python3
"""
初始化默认管理员账号
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.connection import init_database, db_manager
from database.repositories import UserRepository
from services.auth_service import auth_service
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_default_admin():
    """创建默认管理员账号"""
    try:
        # 确保数据库已初始化
        init_database()
        
        with UserRepository() as user_repo:
            # 检查是否已存在管理员账号
            admin_user = user_repo.get_user_by_email("admin@noteai.com")
            
            if admin_user:
                logger.info("✅ 管理员账号已存在")
                print("📋 默认管理员账号信息:")
                print(f"   邮箱: admin@noteai.com")
                print(f"   用户名: {admin_user.username}")
                print(f"   角色: {admin_user.role}")
                print(f"   状态: {admin_user.status}")
                return admin_user
            
            # 创建默认管理员账号
            logger.info("🔧 创建默认管理员账号...")
            
            admin_data = {
                "email": "admin@noteai.com",
                "username": "admin",
                "password": "admin123456",  # 默认密码
                "bio": "NoteAI系统管理员",
                "role": "admin",
                "status": "active",
                "is_verified": True,
                "email_verified": True
            }
            
            # 使用认证服务创建用户（会自动加密密码）
            password_hash = auth_service.hash_password(admin_data["password"])
            
            admin_user = user_repo.create_user(
                email=admin_data["email"],
                username=admin_data["username"],
                password_hash=password_hash,
                bio=admin_data["bio"],
                role=admin_data["role"],
                status=admin_data["status"],
                is_verified=admin_data["is_verified"],
                email_verified=admin_data["email_verified"]
            )
            
            logger.info("✅ 默认管理员账号创建成功")
            
            print("🎉 默认管理员账号创建成功！")
            print("📋 账号信息:")
            print(f"   邮箱: {admin_data['email']}")
            print(f"   用户名: {admin_data['username']}")
            print(f"   密码: {admin_data['password']}")
            print(f"   角色: {admin_data['role']}")
            print("")
            print("⚠️  安全提醒:")
            print("   请在首次登录后立即修改默认密码！")
            print("   建议使用强密码（至少8位，包含字母、数字、特殊字符）")
            
            return admin_user
            
    except Exception as e:
        logger.error(f"❌ 创建管理员账号失败: {e}")
        raise

def create_test_users():
    """创建测试用户"""
    try:
        with UserRepository() as user_repo:
            # 创建普通测试用户
            test_users = [
                {
                    "email": "user@noteai.com",
                    "username": "testuser",
                    "password": "user123456",
                    "bio": "普通测试用户",
                    "role": "user"
                },
                {
                    "email": "demo@noteai.com", 
                    "username": "demouser",
                    "password": "demo123456",
                    "bio": "演示用户",
                    "role": "user"
                }
            ]
            
            created_users = []
            
            for user_data in test_users:
                # 检查用户是否已存在
                existing_user = user_repo.get_user_by_email(user_data["email"])
                if existing_user:
                    logger.info(f"用户 {user_data['email']} 已存在")
                    continue
                
                # 创建用户
                password_hash = auth_service.hash_password(user_data["password"])
                
                user = user_repo.create_user(
                    email=user_data["email"],
                    username=user_data["username"],
                    password_hash=password_hash,
                    bio=user_data["bio"],
                    role=user_data["role"]
                )
                
                created_users.append(user_data)
                logger.info(f"✅ 创建测试用户: {user_data['email']}")
            
            if created_users:
                print("\n👥 测试用户创建成功:")
                for user_data in created_users:
                    print(f"   📧 {user_data['email']} / 🔑 {user_data['password']}")
            
            return created_users
            
    except Exception as e:
        logger.error(f"❌ 创建测试用户失败: {e}")
        return []

def main():
    """主函数"""
    print("🚀 NoteAI 初始化默认账号")
    print("=" * 40)
    
    try:
        # 创建管理员账号
        admin_user = create_default_admin()
        
        # 创建测试用户
        test_users = create_test_users()
        
        print("\n" + "=" * 40)
        print("📊 账号初始化完成")
        print("=" * 40)
        
        print("\n🔑 登录信息:")
        print("管理员账号:")
        print("   邮箱: admin@noteai.com")
        print("   密码: admin123456")
        print("   权限: 管理员")
        
        if test_users:
            print("\n测试账号:")
            for user_data in test_users:
                print(f"   邮箱: {user_data['email']}")
                print(f"   密码: {user_data['password']}")
                print(f"   权限: {user_data['role']}")
        
        print("\n🌐 访问地址:")
        print("   前端应用: http://localhost:3000")
        print("   后端API: http://localhost:8000/docs")
        
        print("\n⚠️  安全提醒:")
        print("   1. 请立即修改默认密码")
        print("   2. 生产环境请删除测试账号")
        print("   3. 定期更新密码策略")
        
        return 0
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
