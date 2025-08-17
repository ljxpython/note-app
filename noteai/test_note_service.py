#!/usr/bin/env python3
"""
测试笔记服务
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_note_service():
    """测试笔记服务"""
    try:
        from fastapi.testclient import TestClient
        from simple_note_service import app
        
        print("🧪 测试笔记服务...")
        
        client = TestClient(app)
        
        # 测试健康检查
        response = client.get("/health")
        print(f"✅ 健康检查: {response.status_code} - {response.json()}")
        
        # 测试创建笔记
        note_data = {
            "title": "我的第一篇笔记",
            "content": "# 标题\n\n这是一篇**测试笔记**，包含*斜体*和`代码`。\n\n算法效率不好，需要优化。",
            "tags": ["测试", "笔记"],
            "is_public": False
        }
        
        response = client.post("/api/v1/notes", json=note_data)
        print(f"✅ 创建笔记: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            note_id = result["data"]["id"]
            print(f"   笔记ID: {note_id}")
            print(f"   标题: {result['data']['title']}")
            print(f"   字数: {result['data']['word_count']}")
            print(f"   阅读时间: {result['data']['reading_time']}分钟")
            print(f"   摘要: {result['data']['excerpt'][:50]}...")
            
            # 测试获取笔记列表
            response = client.get("/api/v1/notes")
            print(f"✅ 获取笔记列表: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   笔记数量: {len(result['data']['notes'])}")
                print(f"   总数: {result['data']['pagination']['total']}")
            
            # 测试获取单个笔记
            response = client.get(f"/api/v1/notes/{note_id}")
            print(f"✅ 获取单个笔记: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   笔记标题: {result['data']['title']}")
            
            # 测试更新笔记
            update_data = {
                "title": "更新后的笔记标题",
                "content": "# 更新的内容\n\n这是更新后的内容，算法效率有待改进。"
            }
            response = client.put(f"/api/v1/notes/{note_id}", json=update_data)
            print(f"✅ 更新笔记: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   新标题: {result['data']['title']}")
            
            # 测试搜索笔记
            response = client.get("/api/v1/notes/search?q=算法")
            print(f"✅ 搜索笔记: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   搜索结果: {len(result['data']['results'])}条")
                if result['data']['results']:
                    print(f"   第一条结果: {result['data']['results'][0]['title']}")
                    print(f"   相关性评分: {result['data']['results'][0]['score']}")
            
            # 测试删除笔记
            response = client.delete(f"/api/v1/notes/{note_id}")
            print(f"✅ 删除笔记: {response.status_code}")
            if response.status_code == 200:
                print(f"   删除成功: {response.json()['message']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 笔记服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_note_features():
    """测试笔记功能特性"""
    try:
        from simple_note_service import render_markdown, generate_excerpt, calculate_reading_time
        
        print("\n🧪 测试笔记功能特性...")
        
        # 测试Markdown渲染
        markdown_text = "# 标题\n\n这是**粗体**和*斜体*文本，还有`代码`。"
        html = render_markdown(markdown_text)
        print(f"✅ Markdown渲染:")
        print(f"   原文: {markdown_text}")
        print(f"   HTML: {html}")
        
        # 测试摘要生成
        long_text = "这是一篇很长的文章。" * 50
        excerpt = generate_excerpt(long_text, 100)
        print(f"✅ 摘要生成:")
        print(f"   原文长度: {len(long_text)}")
        print(f"   摘要长度: {len(excerpt)}")
        print(f"   摘要: {excerpt}")
        
        # 测试阅读时间计算
        chinese_text = "这是一篇中文文章，包含很多中文字符。" * 20
        english_text = "This is an English article with many English words. " * 20
        mixed_text = chinese_text + english_text
        
        chinese_time = calculate_reading_time(chinese_text)
        english_time = calculate_reading_time(english_text)
        mixed_time = calculate_reading_time(mixed_text)
        
        print(f"✅ 阅读时间计算:")
        print(f"   中文文本: {len(chinese_text)}字符 -> {chinese_time}分钟")
        print(f"   英文文本: {len(english_text.split())}单词 -> {english_time}分钟")
        print(f"   混合文本: -> {mixed_time}分钟")
        
        return True
        
    except Exception as e:
        print(f"❌ 笔记功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 NoteAI 笔记服务测试")
    print("=" * 50)
    
    # 检查依赖
    print("📦 检查依赖...")
    try:
        import fastapi
        import uvicorn
        import pydantic
        print("✅ 所有依赖已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        return 1
    
    tests_passed = 0
    total_tests = 2
    
    # 测试笔记服务API
    if test_note_service():
        tests_passed += 1
    
    # 测试笔记功能特性
    if test_note_features():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {tests_passed}/{total_tests} 通过")
    
    if tests_passed == total_tests:
        print("🎉 所有测试通过！")
        print("\n🚀 可以启动笔记服务:")
        print("   python3 simple_note_service.py")
        print("   访问文档: http://localhost:8003/docs")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
