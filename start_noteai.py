#!/usr/bin/env python3
"""
NoteAI 项目启动脚本 - 一键启动所有服务
"""
import subprocess
import os
import time
import signal
import sys
import requests
from pathlib import Path

class NoteAILauncher:
    def __init__(self):
        self.processes = []
        self.services = [
            {
                "name": "用户认证服务",
                "script": "complete_user_service.py",
                "port": 8001,
                "cwd": "noteai",
                "health_url": "http://localhost:8001/health"
            },
            {
                "name": "AI服务",
                "script": "real_ai_service.py", 
                "port": 8002,
                "cwd": "noteai",
                "health_url": "http://localhost:8002/health"
            },
            {
                "name": "前端应用",
                "script": "npm start",
                "port": 3000,
                "cwd": "noteai-frontend",
                "health_url": "http://localhost:3000"
            }
        ]
    
    def check_prerequisites(self):
        """检查前置条件"""
        print("🔍 检查前置条件...")
        
        # 检查Python
        try:
            result = subprocess.run(["python3", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Python: {result.stdout.strip()}")
            else:
                print("❌ Python3 未安装")
                return False
        except:
            print("❌ Python3 未安装")
            return False
        
        # 检查Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js: {result.stdout.strip()}")
            else:
                print("❌ Node.js 未安装")
                return False
        except:
            print("❌ Node.js 未安装")
            return False
        
        # 检查npm
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ npm: {result.stdout.strip()}")
            else:
                print("❌ npm 未安装")
                return False
        except:
            print("❌ npm 未安装")
            return False
        
        # 检查项目文件
        required_files = [
            "noteai/complete_user_service.py",
            "noteai/real_ai_service.py",
            "noteai-frontend/package.json",
            "noteai-frontend/src/App.tsx"
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                print(f"❌ 缺少文件: {file_path}")
                return False
        
        print("✅ 所有前置条件满足")
        return True
    
    def start_service(self, service):
        """启动单个服务"""
        print(f"\n🚀 启动 {service['name']}...")
        
        try:
            if service['name'] == '前端应用':
                # 前端使用npm start
                process = subprocess.Popen(
                    service['script'].split(),
                    cwd=service['cwd'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=os.setsid
                )
            else:
                # 后端使用python3
                process = subprocess.Popen(
                    ["python3", service['script']],
                    cwd=service['cwd'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=os.setsid
                )
            
            # 等待服务启动
            max_wait = 60 if service['name'] == '前端应用' else 30
            wait_time = 0
            
            while wait_time < max_wait:
                try:
                    response = requests.get(service['health_url'], timeout=5)
                    if response.status_code == 200:
                        print(f"✅ {service['name']} 启动成功 (端口 {service['port']})")
                        self.processes.append((service['name'], process))
                        return True
                except:
                    pass
                
                time.sleep(3)
                wait_time += 3
                print(f"⏳ 等待 {service['name']} 启动... ({wait_time}s)")
            
            print(f"❌ {service['name']} 启动超时")
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            return False
            
        except Exception as e:
            print(f"❌ {service['name']} 启动失败: {e}")
            return False
    
    def start_all_services(self):
        """启动所有服务"""
        print("🚀 NoteAI 项目启动中...")
        print("=" * 60)
        
        if not self.check_prerequisites():
            return False
        
        success_count = 0
        for service in self.services:
            if self.start_service(service):
                success_count += 1
            else:
                print(f"❌ {service['name']} 启动失败，停止启动流程")
                break
        
        if success_count == len(self.services):
            print("\n" + "=" * 60)
            print("🎉 所有服务启动成功！")
            print("\n📱 访问地址:")
            print("   前端应用: http://localhost:3000")
            print("   用户服务API: http://localhost:8001/docs")
            print("   AI服务API: http://localhost:8002/docs")
            print("\n🔑 测试账户:")
            print("   邮箱: test@example.com")
            print("   密码: test123456")
            print("\n⏹️  按 Ctrl+C 停止所有服务")
            return True
        else:
            print(f"\n❌ 只有 {success_count}/{len(self.services)} 个服务启动成功")
            return False
    
    def stop_all_services(self):
        """停止所有服务"""
        print("\n🛑 停止所有服务...")
        
        for service_name, process in self.processes:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
                print(f"✅ {service_name} 已停止")
            except:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    print(f"⚠️ {service_name} 强制停止")
                except:
                    print(f"❌ {service_name} 停止失败")
        
        print("👋 所有服务已停止，感谢使用 NoteAI！")
    
    def run(self):
        """运行启动器"""
        try:
            if self.start_all_services():
                # 等待用户中断
                while True:
                    time.sleep(1)
            else:
                self.stop_all_services()
                sys.exit(1)
                
        except KeyboardInterrupt:
            self.stop_all_services()
            sys.exit(0)
        except Exception as e:
            print(f"❌ 启动器异常: {e}")
            self.stop_all_services()
            sys.exit(1)

def main():
    """主函数"""
    print("🌟 NoteAI - AI驱动的智能笔记平台")
    print("🚀 一键启动所有服务")
    print("")
    
    launcher = NoteAILauncher()
    launcher.run()

if __name__ == "__main__":
    main()
