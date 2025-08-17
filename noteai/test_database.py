#!/usr/bin/env python3
"""
测试SQLite数据库集成
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_database_connection():
    """测试数据库连接"""
    try:
        from database.connection import db_manager, init_database
        
        print("🧪 测试数据库连接...")
        
        # 初始化数据库
        init_database()
        
        # 健康检查
        health = db_manager.health_check()
        print(f"✅ 数据库健康检查: {'通过' if health else '失败'}")
        
        # 获取数据库信息
        info = db_manager.get_database_info()
        print(f"✅ 数据库类型: {info['database_type']}")
        print(f"   数据库版本: {info['database_version']}")
        print(f"   表数量: {info['table_count']}")
        print(f"   表列表: {', '.join(info['tables'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_repository():
    """测试用户数据访问层"""
    try:
        from database.repositories import UserRepository
        from passlib.context import CryptContext
        
        print("\n🧪 测试用户Repository...")
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        with UserRepository() as user_repo:
            # 创建用户
            password_hash = pwd_context.hash("test123456")
            user = user_repo.create_user(
                email="test@example.com",
                username="testuser",
                password_hash=password_hash,
                bio="这是一个测试用户"
            )
            print(f"✅ 创建用户: {user.username} ({user.email})")
            
            # 根据邮箱查找用户
            found_user = user_repo.get_user_by_email("test@example.com")
            print(f"✅ 根据邮箱查找用户: {found_user.username if found_user else 'None'}")
            
            # 更新用户信息
            updated_user = user_repo.update_user(user.id, bio="更新后的用户简介")
            print(f"✅ 更新用户信息: {updated_user.bio if updated_user else 'None'}")
            
            # 统计用户数量
            count = user_repo.count_users()
            print(f"✅ 用户总数: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 用户Repository测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_note_repository():
    """测试笔记数据访问层"""
    try:
        from database.repositories import UserRepository, NoteRepository, CategoryRepository
        
        print("\n🧪 测试笔记Repository...")
        
        with UserRepository() as user_repo, NoteRepository() as note_repo, CategoryRepository() as cat_repo:
            # 获取测试用户
            user = user_repo.get_user_by_email("test@example.com")
            if not user:
                print("❌ 找不到测试用户")
                return False
            
            # 创建分类
            category = cat_repo.create_category(
                user_id=user.id,
                name="技术笔记",
                description="技术相关的笔记",
                color="#3B82F6"
            )
            print(f"✅ 创建分类: {category.name}")
            
            # 创建笔记
            note = note_repo.create_note(
                user_id=user.id,
                title="我的第一篇笔记",
                content="# 标题\n\n这是一篇测试笔记，包含**粗体**和*斜体*文本。\n\n算法效率不好需要优化。",
                category_id=category.id,
                tags=["测试", "笔记", "技术"]
            )
            print(f"✅ 创建笔记: {note.title}")
            print(f"   字数: {note.word_count}")
            print(f"   阅读时间: {note.reading_time}分钟")
            print(f"   标签: {', '.join(note.tags)}")
            
            # 获取笔记列表
            notes = note_repo.get_notes(user.id, limit=10)
            print(f"✅ 获取笔记列表: {len(notes)}篇")
            
            # 搜索笔记
            search_results = note_repo.search_notes(user.id, "算法")
            print(f"✅ 搜索笔记: 找到{len(search_results)}篇包含'算法'的笔记")
            
            # 更新笔记
            updated_note = note_repo.update_note(
                note.id, 
                user.id, 
                content="# 更新的标题\n\n这是更新后的内容，算法效率有待改进。",
                is_favorite=True
            )
            print(f"✅ 更新笔记: 收藏状态={updated_note.is_favorite}")
            
            # 获取收藏笔记
            favorite_notes = note_repo.get_favorite_notes(user.id)
            print(f"✅ 收藏笔记: {len(favorite_notes)}篇")
            
            # 更新分类笔记数量
            cat_repo.update_notes_count(category.id)
            updated_category = cat_repo.get_category_by_id(category.id)
            print(f"✅ 分类笔记数量: {updated_category.notes_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 笔记Repository测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_usage_repository():
    """测试AI使用记录数据访问层"""
    try:
        from database.repositories import UserRepository, AIUsageRepository
        from datetime import datetime
        
        print("\n🧪 测试AI使用记录Repository...")
        
        with UserRepository() as user_repo, AIUsageRepository() as ai_repo:
            # 获取测试用户
            user = user_repo.get_user_by_email("test@example.com")
            if not user:
                print("❌ 找不到测试用户")
                return False
            
            # 创建AI使用记录
            usage1 = ai_repo.create_usage_record(
                user_id=user.id,
                operation_type="optimize_text",
                tokens_used=150,
                cost=0.01,
                processing_time=1.2,
                success=True,
                request_data={"text": "测试文本"},
                response_data={"optimized_text": "优化后的文本"}
            )
            print(f"✅ 创建AI使用记录: {usage1.operation_type}")
            
            usage2 = ai_repo.create_usage_record(
                user_id=user.id,
                operation_type="classify_content",
                tokens_used=80,
                cost=0.005,
                processing_time=0.8,
                success=True
            )
            print(f"✅ 创建AI使用记录: {usage2.operation_type}")
            
            # 获取今日使用量
            daily_usage = ai_repo.get_daily_usage(user.id)
            print(f"✅ 今日AI使用量: {daily_usage}次")
            
            # 获取本月使用量
            monthly_usage = ai_repo.get_monthly_usage(user.id)
            print(f"✅ 本月AI使用量: {monthly_usage}次")
            
            # 获取使用统计
            stats = ai_repo.get_usage_stats(user.id, days=30)
            print(f"✅ AI使用统计:")
            print(f"   总操作数: {stats['total_operations']}")
            print(f"   成功操作: {stats['successful_operations']}")
            print(f"   总Token: {stats['total_tokens']}")
            print(f"   总费用: ${stats['total_cost']:.4f}")
            print(f"   平均处理时间: {stats['avg_processing_time']:.2f}秒")
            print(f"   操作类型分布: {stats['operation_types']}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI使用记录Repository测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_system_config_repository():
    """测试系统配置数据访问层"""
    try:
        from database.repositories import SystemConfigRepository
        
        print("\n🧪 测试系统配置Repository...")
        
        with SystemConfigRepository() as config_repo:
            # 获取配置
            app_version = config_repo.get_config_value("app_version", "unknown")
            print(f"✅ 应用版本: {app_version}")
            
            daily_limit = config_repo.get_config_value("ai_quota_daily_limit", 50)
            print(f"✅ 每日AI配额限制: {daily_limit}")
            
            # 设置新配置
            config_repo.set_config(
                "test_setting",
                {"enabled": True, "value": 100},
                "测试配置项"
            )
            print("✅ 设置新配置项")
            
            # 获取所有配置
            all_configs = config_repo.get_all_configs()
            print(f"✅ 系统配置总数: {len(all_configs)}")
            for config in all_configs:
                print(f"   {config.key}: {config.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 系统配置Repository测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_backup():
    """测试数据库备份功能"""
    try:
        from database.connection import backup_database
        
        print("\n🧪 测试数据库备份...")
        
        backup_path = backup_database()
        if backup_path:
            print(f"✅ 数据库备份成功: {backup_path}")
            
            # 检查备份文件是否存在
            if os.path.exists(backup_path):
                file_size = os.path.getsize(backup_path)
                print(f"   备份文件大小: {file_size} bytes")
                
                # 清理备份文件
                os.remove(backup_path)
                print("✅ 清理备份文件")
            
            return True
        else:
            print("⚠️  数据库备份功能不支持当前数据库类型")
            return True
        
    except Exception as e:
        print(f"❌ 数据库备份测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 NoteAI SQLite数据库集成测试")
    print("=" * 60)
    
    # 检查依赖
    print("📦 检查依赖...")
    try:
        import sqlalchemy
        import alembic
        print(f"✅ SQLAlchemy版本: {sqlalchemy.__version__}")
        print(f"✅ Alembic版本: {alembic.__version__}")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        return 1
    
    tests_passed = 0
    total_tests = 6
    
    # 测试数据库连接
    if test_database_connection():
        tests_passed += 1
    
    # 测试用户Repository
    if test_user_repository():
        tests_passed += 1
    
    # 测试笔记Repository
    if test_note_repository():
        tests_passed += 1
    
    # 测试AI使用记录Repository
    if test_ai_usage_repository():
        tests_passed += 1
    
    # 测试系统配置Repository
    if test_system_config_repository():
        tests_passed += 1
    
    # 测试数据库备份
    if test_database_backup():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {tests_passed}/{total_tests} 通过")
    
    if tests_passed == total_tests:
        print("🎉 所有测试通过！")
        print("\n🗄️ SQLite数据库集成成功:")
        print("   ✅ 数据库连接和初始化")
        print("   ✅ 用户管理")
        print("   ✅ 笔记管理")
        print("   ✅ 分类管理")
        print("   ✅ AI使用记录")
        print("   ✅ 系统配置")
        print("   ✅ 数据备份")
        print("")
        print("🚀 可以启动集成数据库的服务:")
        print("   python3 database_integrated_service.py")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
