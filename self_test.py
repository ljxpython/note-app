#!/usr/bin/env python3
"""
NoteAI 完整自测脚本 - 确保所有功能正常
"""
import requests
import time
import subprocess
import os
import signal
import json
from datetime import datetime

class SelfTest:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.test_accounts = [
            {"email": "admin@noteai.com", "password": "AdminPass123!", "role": "admin"},
            {"email": "test@example.com", "password": "test123456", "role": "user"}
        ]
        self.results = []
    
    def log_test(self, test_name, success, details=""):
        """记录测试结果"""
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        return success
    
    def wait_for_backend(self, timeout=30):
        """等待后端服务启动"""
        print("⏳ 等待后端服务启动...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.backend_url}/health", timeout=3)
                if response.status_code == 200:
                    return self.log_test("后端服务启动", True, "服务正常响应")
            except:
                pass
            time.sleep(2)
        
        return self.log_test("后端服务启动", False, "启动超时")
    
    def test_health_check(self):
        """测试健康检查"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    return self.log_test("健康检查", True, f"版本: {data.get('version')}")
            
            return self.log_test("健康检查", False, f"状态码: {response.status_code}")
        except Exception as e:
            return self.log_test("健康检查", False, f"异常: {e}")
    
    def test_account_login(self, email, password, expected_role):
        """测试账号登录"""
        try:
            login_data = {"email": email, "password": password}
            response = requests.post(
                f"{self.backend_url}/api/v1/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data", {}).get("access_token"):
                    user_role = data["data"]["user"]["role"]
                    if user_role == expected_role:
                        return self.log_test(
                            f"账号登录 ({email})", 
                            True, 
                            f"角色: {user_role}, 令牌长度: {len(data['data']['access_token'])}"
                        )
                    else:
                        return self.log_test(
                            f"账号登录 ({email})", 
                            False, 
                            f"角色不匹配: 期望{expected_role}, 实际{user_role}"
                        )
                else:
                    return self.log_test(f"账号登录 ({email})", False, "响应格式错误")
            else:
                return self.log_test(f"账号登录 ({email})", False, f"状态码: {response.status_code}")
                
        except Exception as e:
            return self.log_test(f"账号登录 ({email})", False, f"异常: {e}")
    
    def test_protected_api(self, access_token):
        """测试受保护的API"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(
                f"{self.backend_url}/api/v1/users/profile",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return self.log_test("受保护API", True, "JWT认证正常")
            
            return self.log_test("受保护API", False, f"状态码: {response.status_code}")
        except Exception as e:
            return self.log_test("受保护API", False, f"异常: {e}")
    
    def test_ai_functionality(self, access_token):
        """测试AI功能"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            ai_data = {
                "text": "这个算法效率不好",
                "optimization_type": "expression"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/v1/ai/optimize-text",
                json=ai_data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return self.log_test("AI功能", True, "文本优化正常")
            
            return self.log_test("AI功能", False, f"状态码: {response.status_code}")
        except Exception as e:
            return self.log_test("AI功能", False, f"异常: {e}")
    
    def run_complete_test(self):
        """运行完整测试"""
        print("🧪 NoteAI 完整自测")
        print("=" * 40)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        
        # 等待后端服务
        if not self.wait_for_backend():
            print("❌ 后端服务未启动，测试终止")
            return False
        
        # 健康检查
        if not self.test_health_check():
            print("❌ 健康检查失败，测试终止")
            return False
        
        # 测试所有账号登录
        admin_token = None
        for account in self.test_accounts:
            success = self.test_account_login(
                account["email"], 
                account["password"], 
                account["role"]
            )
            
            if success and account["role"] == "admin":
                # 获取管理员token用于后续测试
                try:
                    response = requests.post(
                        f"{self.backend_url}/api/v1/auth/login",
                        json={"email": account["email"], "password": account["password"]},
                        timeout=10
                    )
                    if response.status_code == 200:
                        admin_token = response.json()["data"]["access_token"]
                except:
                    pass
        
        # 测试受保护API
        if admin_token:
            self.test_protected_api(admin_token)
            self.test_ai_functionality(admin_token)
        else:
            self.log_test("受保护API", False, "无管理员令牌")
            self.log_test("AI功能", False, "无管理员令牌")
        
        # 生成测试报告
        self.generate_report()
        
        # 返回测试结果
        passed_tests = len([r for r in self.results if r["success"]])
        total_tests = len(self.results)
        
        return passed_tests == total_tests
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 40)
        print("📊 自测结果")
        print("=" * 40)
        
        passed = len([r for r in self.results if r["success"]])
        total = len(self.results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"总测试数: {total}")
        print(f"通过测试: {passed}")
        print(f"失败测试: {total - passed}")
        print(f"成功率: {success_rate:.1f}%")
        
        if passed == total:
            print("\n🎉 所有自测通过！")
            print("✅ 系统可以正常交付给用户")
            print("\n🔑 确认可用的账号:")
            for account in self.test_accounts:
                print(f"   📧 {account['email']} / 🔑 {account['password']} ({account['role']})")
        else:
            print("\n⚠️ 部分自测失败")
            print("失败的测试:")
            for result in self.results:
                if not result["success"]:
                    print(f"   ❌ {result['test']}: {result['details']}")
        
        # 保存详细报告
        with open("self_test_report.json", "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tests": total,
                    "passed_tests": passed,
                    "success_rate": success_rate
                },
                "results": self.results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存: self_test_report.json")

def main():
    """主函数"""
    test = SelfTest()
    success = test.run_complete_test()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
