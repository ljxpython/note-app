#!/usr/bin/env python3
"""
基础功能测试脚本
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试基础导入"""
    print("🧪 测试基础导入...")
    
    try:
        # 测试FastAPI
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
    except ImportError as e:
        print(f"❌ FastAPI导入失败: {e}")
        return False
    
    try:
        # 测试Pydantic
        import pydantic
        print(f"✅ Pydantic: {pydantic.__version__}")
    except ImportError as e:
        print(f"❌ Pydantic导入失败: {e}")
        return False
    
    try:
        # 测试AutoGen
        import autogen_core
        print(f"✅ AutoGen Core: {autogen_core.__version__}")
    except ImportError as e:
        print(f"❌ AutoGen Core导入失败: {e}")
        return False
    
    try:
        # 测试AutoGen AgentChat
        import autogen_agentchat
        print(f"✅ AutoGen AgentChat: {autogen_agentchat.__version__}")
    except ImportError as e:
        print(f"❌ AutoGen AgentChat导入失败: {e}")
        return False
    
    return True

def test_config():
    """测试配置加载"""
    print("\n🧪 测试配置加载...")
    
    try:
        from shared.config.settings import get_settings
        settings = get_settings()
        print(f"✅ 配置加载成功")
        print(f"   - 环境: {settings.environment}")
        print(f"   - 调试模式: {settings.debug}")
        print(f"   - 应用名称: {settings.app_name}")
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def test_models():
    """测试数据模型"""
    print("\n🧪 测试数据模型...")
    
    try:
        from shared.models.base import APIResponse, UserCreate, OptimizationRequest
        
        # 测试API响应模型
        response = APIResponse(success=True, message="测试成功")
        print(f"✅ APIResponse模型: {response.success}")
        
        # 测试用户创建模型
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPass123!"
        }
        user = UserCreate(**user_data)
        print(f"✅ UserCreate模型: {user.username}")
        
        # 测试AI优化请求模型
        opt_data = {
            "text": "这是一个测试文本",
            "optimization_type": "all"
        }
        opt_request = OptimizationRequest(**opt_data)
        print(f"✅ OptimizationRequest模型: {opt_request.text}")
        
        return True
    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        return False

def test_auth_utils():
    """测试认证工具"""
    print("\n🧪 测试认证工具...")
    
    try:
        from shared.utils.auth import hash_password, verify_password, validate_email
        
        # 测试密码哈希
        password = "TestPass123!"
        hashed = hash_password(password)
        print(f"✅ 密码哈希: {len(hashed)} 字符")
        
        # 测试密码验证
        is_valid = verify_password(password, hashed)
        print(f"✅ 密码验证: {is_valid}")
        
        # 测试邮箱验证
        email_valid = validate_email("test@example.com")
        print(f"✅ 邮箱验证: {email_valid}")
        
        return True
    except Exception as e:
        print(f"❌ 认证工具测试失败: {e}")
        return False

def test_simple_fastapi():
    """测试简单的FastAPI应用"""
    print("\n🧪 测试简单FastAPI应用...")
    
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        # 创建简单应用
        app = FastAPI(title="Test App")
        
        @app.get("/health")
        def health_check():
            return {"status": "healthy", "service": "test"}
        
        # 测试客户端
        client = TestClient(app)
        response = client.get("/health")
        
        print(f"✅ FastAPI应用测试: {response.status_code}")
        print(f"   - 响应: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ FastAPI应用测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 NoteAI 基础功能测试")
    print("=" * 50)
    
    tests = [
        ("基础导入", test_imports),
        ("配置加载", test_config),
        ("数据模型", test_models),
        ("认证工具", test_auth_utils),
        ("FastAPI应用", test_simple_fastapi),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️  部分测试失败，请检查环境配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())
