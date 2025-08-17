#!/usr/bin/env python3
"""
测试正在运行的服务
"""
import requests
import json
import time

def test_user_service():
    """测试用户服务"""
    base_url = "http://localhost:8001"
    
    print("🧪 测试用户服务 (http://localhost:8001)")
    print("-" * 50)
    
    try:
        # 1. 健康检查
        print("1. 健康检查...")
        response = requests.get(f"{base_url}/health")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   服务状态: {data['status']}")
            print(f"   用户数量: {data['users_count']}")
        
        # 2. 注册用户
        print("\n2. 注册用户...")
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "123456"
        }
        response = requests.post(f"{base_url}/api/v1/auth/register", json=user_data)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   注册成功: {data['message']}")
            print(f"   用户邮箱: {data['data']['email']}")
            print(f"   用户名: {data['data']['username']}")
        else:
            print(f"   错误: {response.text}")
        
        # 3. 用户登录
        print("\n3. 用户登录...")
        login_data = {
            "email": "test@example.com",
            "password": "123456"
        }
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   登录成功: {data['message']}")
            print(f"   Token类型: {data['data']['token_type']}")
            print(f"   过期时间: {data['data']['expires_in']}秒")
            print(f"   Token: {data['data']['access_token'][:50]}...")
            return data['data']['access_token']
        else:
            print(f"   错误: {response.text}")
        
        # 4. 获取用户列表
        print("\n4. 获取用户列表...")
        response = requests.get(f"{base_url}/api/v1/users")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   用户总数: {data['data']['total']}")
            for user in data['data']['users']:
                print(f"   - {user['username']} ({user['email']})")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到用户服务，请确保服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_ai_service():
    """测试AI服务"""
    base_url = "http://localhost:8002"
    
    print("\n🧪 测试AI服务 (http://localhost:8002)")
    print("-" * 50)
    
    try:
        # 1. 健康检查
        print("1. 健康检查...")
        response = requests.get(f"{base_url}/health")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   服务状态: {data['status']}")
            print(f"   功能: {', '.join(data['features'])}")
        else:
            print("   AI服务未启动")
            return False
        
        # 2. 文本优化
        print("\n2. 文本优化...")
        opt_data = {
            "text": "这个算法的效率不好，性能很差，需要优化",
            "optimization_type": "expression"
        }
        response = requests.post(f"{base_url}/api/v1/ai/optimize-text", json=opt_data)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()['data']
            print(f"   原文: {opt_data['text']}")
            print(f"   优化: {data['optimized_text']}")
            print(f"   置信度: {data['confidence']}")
            print(f"   处理时间: {data['processing_time']}秒")
            print(f"   建议数量: {len(data['suggestions'])}")
        
        # 3. 内容分类
        print("\n3. 内容分类...")
        class_data = {
            "content": "机器学习是人工智能的重要分支，包括监督学习、无监督学习和强化学习等技术"
        }
        response = requests.post(f"{base_url}/api/v1/ai/classify-content", json=class_data)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()['data']
            print(f"   内容: {class_data['content'][:50]}...")
            print(f"   分类建议: {data['suggestions'][0]['category_name']}")
            print(f"   置信度: {data['suggestions'][0]['confidence']}")
            print(f"   检测主题: {', '.join(data['detected_topics'])}")
            print(f"   关键词: {', '.join(data['key_phrases'][:5])}")
        
        # 4. 获取配额
        print("\n4. 获取AI配额...")
        response = requests.get(f"{base_url}/api/v1/ai/quota")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()['data']
            print(f"   计划类型: {data['plan_type']}")
            print(f"   日配额: {data['daily_used']}/{data['daily_limit']}")
            print(f"   月配额: {data['monthly_used']}/{data['monthly_limit']}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到AI服务，请启动AI服务")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_note_service():
    """测试笔记服务"""
    base_url = "http://localhost:8003"
    
    print("\n🧪 测试笔记服务 (http://localhost:8003)")
    print("-" * 50)
    
    try:
        # 1. 健康检查
        print("1. 健康检查...")
        response = requests.get(f"{base_url}/health")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   服务状态: {data['status']}")
            print(f"   笔记数量: {data['notes_count']}")
        else:
            print("   笔记服务未启动")
            return False
        
        # 2. 创建笔记
        print("\n2. 创建笔记...")
        note_data = {
            "title": "AI技术学习笔记",
            "content": "# 机器学习基础\n\n机器学习是人工智能的重要分支，算法效率不好需要优化。\n\n## 主要类型\n- 监督学习\n- 无监督学习\n- 强化学习",
            "tags": ["AI", "机器学习", "技术"],
            "is_public": False
        }
        response = requests.post(f"{base_url}/api/v1/notes", json=note_data)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()['data']
            note_id = data['id']
            print(f"   笔记ID: {note_id}")
            print(f"   标题: {data['title']}")
            print(f"   字数: {data['word_count']}")
            print(f"   阅读时间: {data['reading_time']}分钟")
            print(f"   摘要: {data['excerpt'][:50]}...")
            
            # 3. 获取笔记列表
            print("\n3. 获取笔记列表...")
            response = requests.get(f"{base_url}/api/v1/notes")
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()['data']
                print(f"   笔记总数: {data['pagination']['total']}")
                for note in data['notes']:
                    print(f"   - {note['title']} ({note['word_count']}字)")
            
            # 4. 搜索笔记
            print("\n4. 搜索笔记...")
            response = requests.get(f"{base_url}/api/v1/notes/search?q=机器学习")
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()['data']
                print(f"   搜索结果: {len(data['results'])}条")
                if data['results']:
                    result = data['results'][0]
                    print(f"   第一条: {result['title']}")
                    print(f"   相关性: {result['score']}")
            
            return note_id
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到笔记服务，请启动笔记服务")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 NoteAI 服务测试")
    print("=" * 60)
    
    # 测试用户服务
    user_token = None
    if test_user_service():
        print("✅ 用户服务测试通过")
    else:
        print("❌ 用户服务测试失败")
    
    # 测试AI服务
    if test_ai_service():
        print("✅ AI服务测试通过")
    else:
        print("❌ AI服务测试失败")
    
    # 测试笔记服务
    if test_note_service():
        print("✅ 笔记服务测试通过")
    else:
        print("❌ 笔记服务测试失败")
    
    print("\n" + "=" * 60)
    print("📊 测试完成")
    print("\n🌐 服务访问地址:")
    print("   用户服务: http://localhost:8001/docs")
    print("   AI服务:   http://localhost:8002/docs")
    print("   笔记服务: http://localhost:8003/docs")

if __name__ == "__main__":
    main()
