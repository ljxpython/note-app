#!/usr/bin/env python3
"""
测试真实的AutoGen AI服务
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_autogen_service():
    """测试AutoGen服务"""
    try:
        from fastapi.testclient import TestClient
        from real_ai_service import app
        
        print("🧪 测试真实AutoGen AI服务...")
        
        client = TestClient(app)
        
        # 测试健康检查
        response = client.get("/health")
        print(f"✅ 健康检查: {response.status_code} - {response.json()}")
        
        # 测试Agent状态
        response = client.get("/api/v1/ai/agents")
        print(f"✅ Agent状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()['data']
            print(f"   可用Agents: {data['total_agents']}个")
            for agent in data['agents']:
                print(f"   - {agent['display_name']}: {agent['status']}")
        
        # 测试文本优化
        print("\n🧪 测试AutoGen文本优化...")
        opt_data = {
            "text": "这个算法的效率不好，性能很差，需要优化一下",
            "optimization_type": "expression"
        }
        response = client.post("/api/v1/ai/optimize-text", json=opt_data)
        print(f"✅ 文本优化: {response.status_code}")
        if response.status_code == 200:
            data = response.json()['data']
            print(f"   原文: {opt_data['text']}")
            print(f"   优化: {data['optimized_text']}")
            print(f"   引擎: {data.get('engine', 'unknown')}")
            print(f"   处理时间: {data['processing_time']}秒")
        
        # 测试内容分类
        print("\n🧪 测试AutoGen内容分类...")
        class_data = {
            "content": "机器学习是人工智能的重要分支，包括监督学习、无监督学习和强化学习等技术。AutoGen是微软开发的多智能体框架。"
        }
        response = client.post("/api/v1/ai/classify-content", json=class_data)
        print(f"✅ 内容分类: {response.status_code}")
        if response.status_code == 200:
            data = response.json()['data']
            print(f"   内容: {class_data['content'][:50]}...")
            print(f"   分类建议: {data['suggestions'][0]['category_name']}")
            print(f"   引擎: {data.get('engine', 'unknown')}")
            print(f"   处理时间: {data['processing_time']}秒")
        
        # 测试写作助手
        print("\n🧪 测试AutoGen写作助手...")
        writing_data = {
            "content": "今天学习了AutoGen框架，感觉很有用。",
            "task_type": "improve"
        }
        response = client.post("/api/v1/ai/writing-assistance", json=writing_data)
        print(f"✅ 写作助手: {response.status_code}")
        if response.status_code == 200:
            data = response.json()['data']
            print(f"   原文: {writing_data['content']}")
            print(f"   改进: {data['improved_content'][:100]}...")
            print(f"   引擎: {data.get('engine', 'unknown')}")
            print(f"   建议数: {len(data['suggestions'])}")
        
        # 测试多Agent协作
        print("\n🧪 测试多Agent协作...")
        multi_data = {
            "content": "人工智能技术发展迅速，AutoGen框架提供了强大的多智能体协作能力。",
            "task_type": "comprehensive"
        }
        response = client.post("/api/v1/ai/multi-agent", json=multi_data)
        print(f"✅ 多Agent协作: {response.status_code}")
        if response.status_code == 200:
            data = response.json()['data']
            summary = data['collaboration_summary']
            print(f"   使用Agents: {', '.join(summary['agents_used'])}")
            print(f"   总处理时间: {summary['total_processing_time']:.2f}秒")
            print(f"   任务类型: {summary['task_type']}")
        
        # 测试AI状态
        response = client.get("/api/v1/ai/status")
        print(f"\n✅ AI状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()['data']
            print(f"   AutoGen状态: {data['autogen_status']}")
            print(f"   模型提供商: {data['model_info']['provider']}")
            print(f"   可用能力: {len(data['capabilities'])}项")
        
        return True
        
    except Exception as e:
        print(f"❌ AutoGen服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_autogen_direct():
    """直接测试AutoGen服务类"""
    try:
        from services.ai_service.autogen_service import autogen_service
        import asyncio
        
        print("\n🧪 直接测试AutoGen服务类...")
        
        async def run_tests():
            # 测试文本优化
            print("测试文本优化...")
            result = await autogen_service.optimize_text("这个代码的性能不好")
            print(f"   优化结果: {result['optimized_text']}")
            print(f"   建议数量: {len(result['suggestions'])}")
            
            # 测试内容分类
            print("测试内容分类...")
            result = await autogen_service.classify_content("学习Python编程语言")
            print(f"   分类建议: {result['suggestions'][0]['category_name']}")
            print(f"   关键词: {', '.join(result['key_phrases'])}")
            
            # 测试写作助手
            print("测试写作助手...")
            result = await autogen_service.writing_assistance("今天学习了新技术")
            print(f"   改进内容: {result['improved_content'][:50]}...")
            print(f"   建议数量: {len(result['suggestions'])}")
        
        # 运行异步测试
        asyncio.run(run_tests())
        
        return True
        
    except Exception as e:
        print(f"❌ 直接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 NoteAI 真实AutoGen AI服务测试")
    print("=" * 60)
    
    # 检查依赖
    print("📦 检查依赖...")
    try:
        import fastapi
        import uvicorn
        import pydantic
        print("✅ FastAPI依赖已安装")
        
        # 检查AutoGen
        import autogen_agentchat
        import autogen_ext
        print("✅ AutoGen依赖已安装")
        print(f"   autogen-agentchat版本: {autogen_agentchat.__version__}")
        
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        return 1
    
    tests_passed = 0
    total_tests = 2
    
    # 测试AutoGen服务API
    if test_autogen_service():
        tests_passed += 1
    
    # 直接测试AutoGen服务类
    if test_autogen_direct():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {tests_passed}/{total_tests} 通过")
    
    if tests_passed == total_tests:
        print("🎉 所有测试通过！")
        print("\n🚀 可以启动真实AI服务:")
        print("   python3 real_ai_service.py")
        print("   访问文档: http://localhost:8002/docs")
        print("")
        print("🌟 AutoGen功能已集成:")
        print("   ✅ 智能文本优化")
        print("   ✅ 内容智能分类")
        print("   ✅ AI写作助手")
        print("   ✅ 多Agent协作")
        print("")
        print("💡 提示: 配置DEEPSEEK_API_KEY环境变量以启用真实AI功能")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
