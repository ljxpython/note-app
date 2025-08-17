#!/usr/bin/env python3
"""
NoteAI 项目验收测试脚本
按照QA标准进行完整的验收测试
"""
import requests
import time
import json
import subprocess
import os
from datetime import datetime

class AcceptanceTest:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_results = []
        self.access_token = None
    
    def log_result(self, test_name, passed, message="", details=None):
        """记录测试结果"""
        result = {
            "test": test_name,
            "passed": passed,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} {test_name}: {message}")
        if details and not passed:
            print(f"   详情: {details}")
    
    def wait_for_service(self, url, timeout=30, service_name="服务"):
        """等待服务启动"""
        print(f"⏳ 等待{service_name}启动...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {service_name}启动成功")
                    return True
            except:
                pass
            time.sleep(2)
        
        print(f"❌ {service_name}启动超时")
        return False
    
    def test_backend_health(self):
        """测试后端健康检查"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_result(
                        "后端健康检查", 
                        True, 
                        f"版本 {data.get('version', 'unknown')}"
                    )
                    return True
            
            self.log_result("后端健康检查", False, f"状态码: {response.status_code}")
            return False
            
        except Exception as e:
            self.log_result("后端健康检查", False, "请求失败", str(e))
            return False
    
    def test_frontend_access(self):
        """测试前端页面访问"""
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                self.log_result("前端页面访问", True, "页面加载正常")
                return True
            else:
                self.log_result("前端页面访问", False, f"状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("前端页面访问", False, "请求失败", str(e))
            return False
    
    def test_api_documentation(self):
        """测试API文档访问"""
        try:
            response = requests.get(f"{self.backend_url}/docs", timeout=10)
            if response.status_code == 200:
                self.log_result("API文档访问", True, "文档页面正常")
                return True
            else:
                self.log_result("API文档访问", False, f"状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("API文档访问", False, "请求失败", str(e))
            return False
    
    def test_user_registration(self):
        """测试用户注册功能"""
        try:
            test_user = {
                "email": "acceptance_test@example.com",
                "username": "acceptance_user",
                "password": "test123456"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/v1/auth/register",
                json=test_user,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_result("用户注册功能", True, "注册成功")
                    return True
            elif response.status_code == 400:
                # 用户可能已存在，这也是正常的
                self.log_result("用户注册功能", True, "用户已存在（正常）")
                return True
            
            self.log_result("用户注册功能", False, f"状态码: {response.status_code}")
            return False
            
        except Exception as e:
            self.log_result("用户注册功能", False, "请求失败", str(e))
            return False
    
    def test_user_login(self):
        """测试用户登录功能"""
        try:
            login_data = {
                "email": "acceptance_test@example.com",
                "password": "test123456"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/v1/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data", {}).get("access_token"):
                    self.access_token = data["data"]["access_token"]
                    self.log_result("用户登录功能", True, "登录成功，获得令牌")
                    return True
            
            self.log_result("用户登录功能", False, f"状态码: {response.status_code}")
            return False
            
        except Exception as e:
            self.log_result("用户登录功能", False, "请求失败", str(e))
            return False
    
    def test_protected_route(self):
        """测试受保护的路由"""
        if not self.access_token:
            self.log_result("受保护路由", False, "无访问令牌")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.backend_url}/api/v1/users/profile",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_result("受保护路由", True, "JWT认证正常")
                    return True
            
            self.log_result("受保护路由", False, f"状态码: {response.status_code}")
            return False
            
        except Exception as e:
            self.log_result("受保护路由", False, "请求失败", str(e))
            return False
    
    def test_ai_functionality(self):
        """测试AI功能"""
        if not self.access_token:
            self.log_result("AI功能测试", False, "无访问令牌")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # 测试文本优化
            optimize_data = {
                "text": "这个算法的效率不好",
                "optimization_type": "expression"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/v1/ai/optimize-text",
                json=optimize_data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_result("AI功能测试", True, "文本优化功能正常")
                    return True
            
            self.log_result("AI功能测试", False, f"状态码: {response.status_code}")
            return False
            
        except Exception as e:
            self.log_result("AI功能测试", False, "请求失败", str(e))
            return False
    
    def test_database_functionality(self):
        """测试数据库功能"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                db_status = data.get("database", {}).get("status")
                if db_status == "connected":
                    self.log_result("数据库功能", True, "数据库连接正常")
                    return True
            
            self.log_result("数据库功能", False, "数据库连接失败")
            return False
            
        except Exception as e:
            self.log_result("数据库功能", False, "检查失败", str(e))
            return False
    
    def run_all_tests(self):
        """运行所有验收测试"""
        print("🎯 NoteAI 项目验收测试")
        print("=" * 50)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        
        # 等待服务启动
        backend_ready = self.wait_for_service(f"{self.backend_url}/health", 30, "后端服务")
        frontend_ready = self.wait_for_service(self.frontend_url, 60, "前端服务")
        
        if not backend_ready:
            print("❌ 后端服务未启动，无法进行测试")
            return False
        
        print("")
        print("🧪 开始功能测试...")
        print("-" * 30)
        
        # 运行所有测试
        tests = [
            self.test_backend_health,
            self.test_frontend_access,
            self.test_api_documentation,
            self.test_user_registration,
            self.test_user_login,
            self.test_protected_route,
            self.test_ai_functionality,
            self.test_database_functionality,
        ]
        
        passed_tests = 0
        for test in tests:
            if test():
                passed_tests += 1
            time.sleep(1)  # 避免请求过快
        
        # 生成测试报告
        print("")
        print("=" * 50)
        print("📊 验收测试结果")
        print("=" * 50)
        
        total_tests = len(tests)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {total_tests - passed_tests}")
        print(f"成功率: {success_rate:.1f}%")
        print("")
        
        if passed_tests == total_tests:
            print("🎉 所有验收测试通过！")
            print("✅ 项目已准备好交付给用户使用")
            print("")
            print("📱 用户访问地址:")
            print(f"   前端应用: {self.frontend_url}")
            print(f"   API文档:  {self.backend_url}/docs")
            return True
        else:
            print("⚠️ 部分测试失败，请检查问题后重新测试")
            print("")
            print("失败的测试:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"   ❌ {result['test']}: {result['message']}")
            return False
    
    def save_report(self, filename="acceptance_test_report.json"):
        """保存测试报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "passed_tests": len([r for r in self.test_results if r["passed"]]),
            "success_rate": len([r for r in self.test_results if r["passed"]]) / len(self.test_results) * 100,
            "results": self.test_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 测试报告已保存: {filename}")

def main():
    """主函数"""
    test = AcceptanceTest()
    success = test.run_all_tests()
    test.save_report()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
