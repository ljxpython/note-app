#!/usr/bin/env python3
"""
NoteAI 快速验收测试
"""
import requests
import time
import subprocess
import os
import signal
from datetime import datetime

def start_backend():
    """启动后端服务"""
    print("🚀 启动后端服务...")
    process = subprocess.Popen(
        ["python3", "unified_backend_service.py"],
        cwd="noteai",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid
    )
    
    # 等待服务启动
    for i in range(15):
        try:
            response = requests.get("http://localhost:8000/health", timeout=3)
            if response.status_code == 200:
                print("✅ 后端服务启动成功")
                return process
        except:
            pass
        time.sleep(2)
        print(f"⏳ 等待后端启动... ({i*2}s)")
    
    print("❌ 后端服务启动失败")
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    return None

def test_backend_functionality(process):
    """测试后端功能"""
    print("\n🧪 测试后端功能...")
    
    tests_passed = 0
    total_tests = 5
    
    # 1. 健康检查
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200 and response.json().get("status") == "healthy":
            print("✅ 健康检查通过")
            tests_passed += 1
        else:
            print("❌ 健康检查失败")
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
    
    # 2. API文档
    try:
        response = requests.get("http://localhost:8000/docs", timeout=10)
        if response.status_code == 200:
            print("✅ API文档可访问")
            tests_passed += 1
        else:
            print("❌ API文档不可访问")
    except Exception as e:
        print(f"❌ API文档异常: {e}")
    
    # 3. 用户注册
    try:
        user_data = {
            "email": "quicktest@example.com",
            "username": "quicktest",
            "password": "test123456"
        }
        response = requests.post("http://localhost:8000/api/v1/auth/register", json=user_data, timeout=10)
        if response.status_code == 200 or response.status_code == 400:  # 400可能是用户已存在
            print("✅ 用户注册功能正常")
            tests_passed += 1
        else:
            print(f"❌ 用户注册失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 用户注册异常: {e}")
    
    # 4. 用户登录
    access_token = None
    try:
        login_data = {
            "email": "quicktest@example.com",
            "password": "test123456"
        }
        response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data", {}).get("access_token"):
                access_token = data["data"]["access_token"]
                print("✅ 用户登录功能正常")
                tests_passed += 1
            else:
                print("❌ 用户登录响应格式错误")
        else:
            print(f"❌ 用户登录失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 用户登录异常: {e}")
    
    # 5. AI功能测试
    if access_token:
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            ai_data = {
                "text": "这个算法效率不好",
                "optimization_type": "expression"
            }
            response = requests.post(
                "http://localhost:8000/api/v1/ai/optimize-text", 
                json=ai_data, 
                headers=headers, 
                timeout=15
            )
            if response.status_code == 200:
                print("✅ AI功能正常")
                tests_passed += 1
            else:
                print(f"❌ AI功能失败: {response.status_code}")
        except Exception as e:
            print(f"❌ AI功能异常: {e}")
    else:
        print("❌ AI功能测试跳过（无访问令牌）")
    
    return tests_passed, total_tests

def stop_backend(process):
    """停止后端服务"""
    if process:
        print("\n🛑 停止后端服务...")
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
            print("✅ 后端服务已停止")
        except:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                print("⚠️ 后端服务强制停止")
            except:
                print("❌ 停止后端服务失败")

def main():
    """主函数"""
    print("🎯 NoteAI 快速验收测试")
    print("=" * 40)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 启动后端服务
    backend_process = start_backend()
    if not backend_process:
        print("❌ 无法启动后端服务，测试终止")
        return 1
    
    try:
        # 测试后端功能
        passed, total = test_backend_functionality(backend_process)
        
        # 输出结果
        print("\n" + "=" * 40)
        print("📊 测试结果")
        print("=" * 40)
        print(f"总测试数: {total}")
        print(f"通过测试: {passed}")
        print(f"失败测试: {total - passed}")
        print(f"成功率: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 所有测试通过！")
            print("✅ 后端服务可以交付给用户使用")
            print("")
            print("📱 访问地址:")
            print("   API文档: http://localhost:8000/docs")
            print("   健康检查: http://localhost:8000/health")
            result = 0
        else:
            print("\n⚠️ 部分测试失败")
            print("请检查失败的功能后重新测试")
            result = 1
            
    finally:
        # 清理
        stop_backend(backend_process)
    
    return result

if __name__ == "__main__":
    exit(main())
