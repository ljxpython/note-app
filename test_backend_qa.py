#!/usr/bin/env python3
"""
后端QA质量检查脚本
"""
import subprocess
import os
import time
import requests
import json
import signal
from pathlib import Path

def run_command(command, cwd=None, timeout=60):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timeout"
    except Exception as e:
        return False, "", str(e)

def check_backend_structure():
    """检查后端项目结构"""
    print("🔍 检查后端项目结构...")
    
    required_files = [
        "noteai/complete_user_service.py",
        "noteai/real_ai_service.py",
        "noteai/simple_note_service.py",
        "noteai/services/auth_service.py",
        "noteai/services/ai_service/autogen_service.py",
        "noteai/database/models.py",
        "noteai/database/connection.py",
        "noteai/database/repositories.py",
        "noteai/requirements.txt",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 缺少文件: {', '.join(missing_files)}")
        return False
    else:
        print("✅ 所有必需文件存在")
        return True

def check_python_dependencies():
    """检查Python依赖"""
    print("\n📦 检查Python依赖...")
    
    required_packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("sqlalchemy", "sqlalchemy"),
        ("pydantic", "pydantic"),
        ("passlib", "passlib"),
        ("PyJWT", "jwt"),
        ("autogen-agentchat", "autogen_agentchat"),
    ]

    missing_packages = []
    for package_name, import_name in required_packages:
        success, _, _ = run_command(f"python3 -c 'import {import_name}'")
        if not success:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"❌ 缺少依赖: {', '.join(missing_packages)}")
        return False
    else:
        print("✅ 所有依赖已安装")
        return True

def start_service(service_name, script_path, port):
    """启动服务"""
    print(f"\n🚀 启动{service_name}...")
    
    process = subprocess.Popen(
        ["python3", script_path],
        cwd="noteai",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid
    )
    
    # 等待服务启动
    max_wait = 30
    wait_time = 0
    
    while wait_time < max_wait:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}启动成功")
                return process
        except:
            pass
        
        time.sleep(2)
        wait_time += 2
        print(f"⏳ 等待{service_name}启动... ({wait_time}s)")
    
    print(f"❌ {service_name}启动失败")
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    return None

def test_service_endpoints(service_name, base_url, endpoints):
    """测试服务端点"""
    print(f"\n🌐 测试{service_name}端点...")
    
    all_passed = True
    
    for endpoint_name, endpoint_path in endpoints.items():
        try:
            url = f"{base_url}{endpoint_path}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint_name}: {response.status_code}")
            else:
                print(f"❌ {endpoint_name}: {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"❌ {endpoint_name}: 请求失败 - {e}")
            all_passed = False
    
    return all_passed

def test_user_service():
    """测试用户服务"""
    print("\n🧪 测试用户服务功能...")
    
    base_url = "http://localhost:8001"
    
    try:
        # 测试用户注册
        register_data = {
            "email": "qa_test@example.com",
            "username": "qa_test_user",
            "password": "qa_test123"
        }
        response = requests.post(f"{base_url}/api/v1/auth/register", json=register_data, timeout=10)
        if response.status_code == 200:
            print("✅ 用户注册功能正常")
        else:
            print(f"❌ 用户注册失败: {response.status_code}")
            return False
        
        # 测试用户登录
        login_data = {
            "email": "qa_test@example.com",
            "password": "qa_test123"
        }
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            print("✅ 用户登录功能正常")
            return True
        else:
            print(f"❌ 用户登录失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 用户服务测试失败: {e}")
        return False

def test_ai_service():
    """测试AI服务"""
    print("\n🧪 测试AI服务功能...")
    
    base_url = "http://localhost:8002"
    
    try:
        # 测试文本优化
        optimize_data = {
            "text": "这个算法的效率不好",
            "optimization_type": "expression"
        }
        response = requests.post(f"{base_url}/api/v1/ai/optimize-text", json=optimize_data, timeout=15)
        if response.status_code == 200:
            print("✅ AI文本优化功能正常")
        else:
            print(f"❌ AI文本优化失败: {response.status_code}")
            return False
        
        # 测试内容分类
        classify_data = {
            "content": "机器学习是人工智能的重要分支"
        }
        response = requests.post(f"{base_url}/api/v1/ai/classify-content", json=classify_data, timeout=15)
        if response.status_code == 200:
            print("✅ AI内容分类功能正常")
            return True
        else:
            print(f"❌ AI内容分类失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ AI服务测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 NoteAI 后端QA质量检查")
    print("=" * 60)
    
    # 检查项目结构
    structure_ok = check_backend_structure()
    
    # 检查依赖
    deps_ok = check_python_dependencies()
    
    # 启动服务并测试
    services = []
    user_service_ok = False
    ai_service_ok = False
    
    if structure_ok and deps_ok:
        # 启动用户服务
        user_service = start_service("用户认证服务", "complete_user_service.py", 8001)
        if user_service:
            services.append(("用户服务", user_service))
            
            # 测试用户服务端点
            user_endpoints = {
                "健康检查": "/health",
                "API文档": "/docs",
            }
            endpoints_ok = test_service_endpoints("用户服务", "http://localhost:8001", user_endpoints)
            
            if endpoints_ok:
                user_service_ok = test_user_service()
        
        # 启动AI服务
        ai_service = start_service("AI服务", "real_ai_service.py", 8002)
        if ai_service:
            services.append(("AI服务", ai_service))
            
            # 测试AI服务端点
            ai_endpoints = {
                "健康检查": "/health",
                "API文档": "/docs",
                "Agent状态": "/api/v1/ai/agents",
            }
            endpoints_ok = test_service_endpoints("AI服务", "http://localhost:8002", ai_endpoints)
            
            if endpoints_ok:
                ai_service_ok = test_ai_service()
    
    # 清理服务
    print("\n🛑 停止所有服务...")
    for service_name, process in services:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
            print(f"✅ {service_name}已停止")
        except:
            print(f"⚠️ {service_name}强制停止")
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 后端QA检查结果:")
    print(f"   项目结构: {'✅ 通过' if structure_ok else '❌ 失败'}")
    print(f"   Python依赖: {'✅ 通过' if deps_ok else '❌ 失败'}")
    print(f"   用户服务: {'✅ 通过' if user_service_ok else '❌ 失败'}")
    print(f"   AI服务: {'✅ 通过' if ai_service_ok else '❌ 失败'}")
    
    all_passed = all([structure_ok, deps_ok, user_service_ok, ai_service_ok])
    
    if all_passed:
        print("\n🎉 所有后端QA检查通过！后端可以交付给用户使用。")
        return 0
    else:
        print("\n⚠️ 后端QA检查失败！请修复问题后重新测试。")
        return 1

if __name__ == "__main__":
    exit(main())
