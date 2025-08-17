#!/usr/bin/env python3
"""
直接运行AI服务
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import time
import re
import random

# 创建AI服务
app = FastAPI(title="NoteAI AI Service", version="1.0.0")

class OptimizationRequest(BaseModel):
    text: str
    optimization_type: str = "all"
    user_style: str = None

class ClassificationRequest(BaseModel):
    content: str
    existing_categories: list = []

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "service": "ai_service", 
        "version": "1.0.0",
        "features": ["text_optimization", "content_classification"]
    }

@app.post("/api/v1/ai/optimize-text")
def optimize_text(request: OptimizationRequest):
    """文本优化API"""
    start_time = time.time()
    
    # 模拟AI处理时间
    time.sleep(random.uniform(0.5, 1.5))
    
    # 智能文本优化规则
    optimized_text = request.text
    suggestions = []
    
    # 表达优化规则
    expression_rules = {
        "不好": "有待改进",
        "很差": "需要提升", 
        "不行": "需要优化",
        "糟糕": "有改进空间",
        "太慢": "效率有待提升",
        "很烂": "质量需要改善",
        "没用": "效果不明显",
        "不对": "存在问题"
    }
    
    # 语法优化规则
    grammar_rules = {
        "的的": "的",
        "了了": "了",
        "。。": "。",
        "，，": "，",
        "  ": " "  # 多余空格
    }
    
    # 应用优化规则
    if request.optimization_type in ["expression", "all"]:
        for original, optimized in expression_rules.items():
            if original in request.text:
                optimized_text = optimized_text.replace(original, optimized)
                suggestions.append({
                    "type": "expression",
                    "original": original,
                    "optimized": optimized,
                    "explanation": f"将'{original}'改为更专业的表达'{optimized}'",
                    "confidence": round(random.uniform(0.8, 0.95), 2)
                })
    
    if request.optimization_type in ["grammar", "all"]:
        for original, optimized in grammar_rules.items():
            if original in request.text:
                optimized_text = optimized_text.replace(original, optimized)
                suggestions.append({
                    "type": "grammar",
                    "original": original,
                    "optimized": optimized,
                    "explanation": f"修正语法错误",
                    "confidence": round(random.uniform(0.9, 0.98), 2)
                })
    
    # 结构优化建议
    if request.optimization_type in ["structure", "all"]:
        sentences = re.split(r'[。！？]', request.text)
        if len(sentences) > 3:
            suggestions.append({
                "type": "structure",
                "original": "长段落",
                "optimized": "分段处理",
                "explanation": "建议将长段落分解为多个短段落，提高可读性",
                "confidence": 0.85
            })
    
    processing_time = time.time() - start_time
    
    return {
        "success": True,
        "data": {
            "optimized_text": optimized_text,
            "suggestions": suggestions,
            "confidence": round(sum(s["confidence"] for s in suggestions) / len(suggestions), 2) if suggestions else 0.5,
            "processing_time": round(processing_time, 2),
            "optimization_type": request.optimization_type,
            "original_length": len(request.text),
            "optimized_length": len(optimized_text)
        },
        "message": "文本优化完成"
    }

@app.post("/api/v1/ai/classify-content")
def classify_content(request: ClassificationRequest):
    """内容分类API"""
    start_time = time.time()
    content = request.content
    
    # 模拟AI处理时间
    time.sleep(random.uniform(0.3, 0.8))
    
    # 智能分类规则
    categories = []
    
    # 技术相关
    tech_keywords = ["技术", "代码", "编程", "算法", "开发", "软件", "系统", "架构", "数据库", "API"]
    if any(keyword in content for keyword in tech_keywords):
        categories.append({
            "category_name": "技术文档",
            "confidence": round(random.uniform(0.85, 0.95), 2),
            "reasoning": "包含技术开发相关关键词",
            "is_existing": True
        })
    
    # 学习相关
    study_keywords = ["学习", "笔记", "总结", "知识", "教程", "课程", "理解", "掌握", "复习"]
    if any(keyword in content for keyword in study_keywords):
        categories.append({
            "category_name": "学习笔记",
            "confidence": round(random.uniform(0.80, 0.92), 2),
            "reasoning": "包含学习和知识相关关键词",
            "is_existing": True
        })
    
    # 工作相关
    work_keywords = ["工作", "项目", "任务", "计划", "会议", "报告", "进度", "目标", "团队"]
    if any(keyword in content for keyword in work_keywords):
        categories.append({
            "category_name": "工作总结",
            "confidence": round(random.uniform(0.78, 0.90), 2),
            "reasoning": "包含工作和项目相关关键词",
            "is_existing": True
        })
    
    # 生活相关
    life_keywords = ["生活", "日记", "感想", "心情", "体验", "感受", "思考", "随笔"]
    if any(keyword in content for keyword in life_keywords):
        categories.append({
            "category_name": "生活随笔",
            "confidence": round(random.uniform(0.75, 0.88), 2),
            "reasoning": "包含生活和个人感受相关关键词",
            "is_existing": False
        })
    
    # 如果没有匹配到特定分类
    if not categories:
        categories.append({
            "category_name": "其他",
            "confidence": 0.6,
            "reasoning": "未匹配到特定分类关键词",
            "is_existing": True
        })
    
    # 提取关键词和主题
    import re
    words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', content)
    key_phrases = list(set([w for w in words if len(w) > 1]))[:8]
    
    detected_topics = [cat["category_name"] for cat in categories]
    
    # 判断内容类型
    content_types = {
        "技术文档": "technical_document",
        "学习笔记": "study_notes", 
        "工作总结": "work_summary",
        "生活随笔": "life_essay",
        "其他": "general"
    }
    
    main_category = categories[0]["category_name"] if categories else "其他"
    content_type = content_types.get(main_category, "general")
    
    processing_time = time.time() - start_time
    
    return {
        "success": True,
        "data": {
            "suggestions": categories,
            "detected_topics": detected_topics,
            "key_phrases": key_phrases,
            "content_type": content_type,
            "processing_time": round(processing_time, 2),
            "content_length": len(content)
        },
        "message": "内容分类完成"
    }

@app.get("/api/v1/ai/quota")
def get_quota():
    """获取AI配额信息（模拟）"""
    return {
        "success": True,
        "data": {
            "plan_type": "free",
            "daily_limit": 50,
            "daily_used": random.randint(5, 25),
            "monthly_limit": 1000,
            "monthly_used": random.randint(100, 500),
            "reset_date": "2025-02-01T00:00:00Z"
        },
        "message": "配额信息获取成功"
    }

if __name__ == "__main__":
    print("🚀 NoteAI AI服务启动")
    print("📖 API文档: http://localhost:8002/docs")
    print("🔍 健康检查: http://localhost:8002/health")
    print("🤖 AI配额: http://localhost:8002/api/v1/ai/quota")
    print("")
    print("📝 测试用例:")
    print("1. 文本优化: POST /api/v1/ai/optimize-text")
    print("   {\"text\":\"这个算法的效率不好\",\"optimization_type\":\"expression\"}")
    print("2. 内容分类: POST /api/v1/ai/classify-content")
    print("   {\"content\":\"机器学习是人工智能的重要分支\"}")
    print("")
    print("⏹️  按 Ctrl+C 停止服务")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
