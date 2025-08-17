#!/usr/bin/env python3
"""
前端QA质量检查脚本
"""
import subprocess
import os
import time
import requests
import json
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

def check_file_exists(file_path):
    """检查文件是否存在"""
    return Path(file_path).exists()

def check_frontend_structure():
    """检查前端项目结构"""
    print("🔍 检查前端项目结构...")
    
    required_files = [
        "noteai-frontend/package.json",
        "noteai-frontend/tsconfig.json",
        "noteai-frontend/tailwind.config.js",
        "noteai-frontend/craco.config.js",
        "noteai-frontend/public/index.html",
        "noteai-frontend/public/manifest.json",
        "noteai-frontend/src/App.tsx",
        "noteai-frontend/src/index.tsx",
        "noteai-frontend/src/index.css",
        "noteai-frontend/src/contexts/AuthContext.tsx",
        "noteai-frontend/src/components/ui/Button.tsx",
        "noteai-frontend/src/components/ui/Input.tsx",
        "noteai-frontend/src/components/ui/Card.tsx",
        "noteai-frontend/src/utils/cn.ts",
        "noteai-frontend/src/services/api.ts",
        "noteai-frontend/src/types/index.ts",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not check_file_exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 缺少文件: {', '.join(missing_files)}")
        return False
    else:
        print("✅ 所有必需文件存在")
        return True

def check_dependencies():
    """检查依赖安装"""
    print("\n📦 检查依赖安装...")
    
    success, stdout, stderr = run_command(
        "npm list --depth=0", 
        cwd="noteai-frontend"
    )
    
    if success:
        print("✅ 依赖检查通过")
        return True
    else:
        print(f"❌ 依赖检查失败: {stderr}")
        return False

def check_typescript_compilation():
    """检查TypeScript编译"""
    print("\n🔧 检查TypeScript编译...")
    
    success, stdout, stderr = run_command(
        "npx tsc --noEmit", 
        cwd="noteai-frontend"
    )
    
    if success:
        print("✅ TypeScript编译通过")
        return True
    else:
        print(f"❌ TypeScript编译失败:")
        print(stderr)
        return False

def check_build():
    """检查构建"""
    print("\n🏗️ 检查项目构建...")
    
    success, stdout, stderr = run_command(
        "npm run build", 
        cwd="noteai-frontend",
        timeout=120
    )
    
    if success:
        print("✅ 项目构建成功")
        return True
    else:
        print(f"❌ 项目构建失败:")
        print(stderr)
        return False

def start_frontend_server():
    """启动前端服务器"""
    print("\n🚀 启动前端服务器...")
    
    # 启动开发服务器
    process = subprocess.Popen(
        ["npm", "start"],
        cwd="noteai-frontend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 等待服务器启动
    max_wait = 60
    wait_time = 0
    
    while wait_time < max_wait:
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                print("✅ 前端服务器启动成功")
                return process
        except:
            pass
        
        time.sleep(2)
        wait_time += 2
        print(f"⏳ 等待服务器启动... ({wait_time}s)")
    
    print("❌ 前端服务器启动失败")
    process.terminate()
    return None

def check_frontend_pages():
    """检查前端页面"""
    print("\n🌐 检查前端页面...")
    
    pages_to_check = [
        ("主页", "http://localhost:3000"),
        ("登录页", "http://localhost:3000/login"),
        ("注册页", "http://localhost:3000/register"),
    ]
    
    all_passed = True
    
    for page_name, url in pages_to_check:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {page_name}: {response.status_code}")
            else:
                print(f"❌ {page_name}: {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"❌ {page_name}: 请求失败 - {e}")
            all_passed = False
    
    return all_passed

def check_console_errors():
    """检查控制台错误（简化版）"""
    print("\n🔍 检查控制台错误...")
    
    # 这里可以集成更复杂的浏览器自动化测试
    # 目前只是检查服务器是否正常响应
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if "error" in response.text.lower() or "cannot find module" in response.text.lower():
            print("❌ 页面包含错误信息")
            return False
        else:
            print("✅ 页面加载正常")
            return True
    except Exception as e:
        print(f"❌ 页面检查失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 NoteAI 前端QA质量检查")
    print("=" * 60)
    
    # 检查项目结构
    structure_ok = check_frontend_structure()
    
    # 检查依赖
    deps_ok = check_dependencies()
    
    # 检查TypeScript编译
    ts_ok = check_typescript_compilation()
    
    # 检查构建
    build_ok = check_build()
    
    # 启动服务器并测试
    server_process = None
    pages_ok = False
    console_ok = False
    
    if structure_ok and deps_ok and ts_ok and build_ok:
        server_process = start_frontend_server()
        if server_process:
            pages_ok = check_frontend_pages()
            console_ok = check_console_errors()
    
    # 清理
    if server_process:
        print("\n🛑 停止前端服务器...")
        server_process.terminate()
        server_process.wait()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 QA检查结果:")
    print(f"   项目结构: {'✅ 通过' if structure_ok else '❌ 失败'}")
    print(f"   依赖安装: {'✅ 通过' if deps_ok else '❌ 失败'}")
    print(f"   TS编译: {'✅ 通过' if ts_ok else '❌ 失败'}")
    print(f"   项目构建: {'✅ 通过' if build_ok else '❌ 失败'}")
    print(f"   页面访问: {'✅ 通过' if pages_ok else '❌ 失败'}")
    print(f"   控制台: {'✅ 通过' if console_ok else '❌ 失败'}")
    
    all_passed = all([structure_ok, deps_ok, ts_ok, build_ok, pages_ok, console_ok])
    
    if all_passed:
        print("\n🎉 所有QA检查通过！前端可以交付给用户使用。")
        return 0
    else:
        print("\n⚠️ QA检查失败！请修复问题后重新测试。")
        return 1

if __name__ == "__main__":
    exit(main())
