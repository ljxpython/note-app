"""
内容分类AI Agent - 基于AutoGen
"""
from autogen_core import BaseAgent, MessageContext
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from typing import Dict, Any, Optional, List
import asyncio
import json
import re
import logging

logger = logging.getLogger(__name__)


class ContentClassifierAgent(BaseAgent):
    """内容分类AI Agent"""
    
    def __init__(self, name: str, model_config: Dict[str, Any]):
        super().__init__(name)
        self.model_config = model_config
        self.model_client = self._create_model_client(model_config)
        self.assistant = AssistantAgent(
            name=name,
            model_client=self.model_client,
            system_message=self._get_system_message()
        )
        logger.info(f"ContentClassifierAgent '{name}' initialized")
    
    def _create_model_client(self, config: Dict[str, Any]):
        """创建模型客户端"""
        try:
            if config.get("provider") == "deepseek":
                return OpenAIChatCompletionClient(
                    model=config.get("model", "deepseek-chat"),
                    api_key=config.get("api_key"),
                    base_url=config.get("base_url", "https://api.deepseek.com"),
                    max_tokens=config.get("max_tokens", 4000),
                    temperature=config.get("temperature", 0.7)
                )
            else:
                # 默认使用OpenAI
                return OpenAIChatCompletionClient(
                    model=config.get("model", "gpt-4"),
                    api_key=config.get("api_key"),
                    max_tokens=config.get("max_tokens", 4000),
                    temperature=config.get("temperature", 0.7)
                )
        except Exception as e:
            logger.error(f"Failed to create model client: {e}")
            raise
    
    def _get_system_message(self) -> str:
        """获取系统消息"""
        return """你是一个专业的内容分类助手。你的任务是：

1. **主题识别**: 分析文本内容的主要主题和领域
2. **分类推荐**: 根据现有分类体系推荐最合适的分类
3. **关键词提取**: 提取能代表内容特征的关键词和短语
4. **内容类型判断**: 判断内容的类型（技术文档、学习笔记、工作总结等）

**分类原则**:
- 准确识别内容的核心主题
- 优先匹配现有分类体系
- 提供分类的置信度和理由
- 考虑内容的深度和专业程度

**输出格式**: 必须返回有效的JSON格式，包含以下字段：
- suggestions: 分类建议列表
- detected_topics: 检测到的主题
- key_phrases: 关键短语
- content_type: 内容类型

请始终保持专业、准确、有帮助的态度。"""
    
    async def classify_content(
        self, 
        content: str, 
        existing_categories: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分类内容"""
        try:
            if existing_categories is None:
                existing_categories = []
            
            prompt = self._build_classification_prompt(content, existing_categories)
            
            # 调用AutoGen Assistant
            result = await self.assistant.run(task=prompt)
            
            # 解析结果
            classification_result = self._parse_classification_result(result.messages[-1].content)
            
            # 验证结果质量
            validated_result = self._validate_classification_result(content, classification_result)
            
            logger.info(f"Content classification completed successfully")
            return validated_result
            
        except Exception as e:
            logger.error(f"Content classification failed: {e}")
            return self._create_fallback_result(content, str(e))
    
    def _build_classification_prompt(
        self, 
        content: str, 
        existing_categories: List[Dict[str, Any]]
    ) -> str:
        """构建分类提示词"""
        
        # 构建现有分类信息
        categories_text = ""
        if existing_categories:
            categories_text = "现有分类体系:\n"
            for i, cat in enumerate(existing_categories, 1):
                categories_text += f"{i}. {cat.get('name', '未知')}: {cat.get('description', '无描述')}\n"
        else:
            categories_text = "现有分类体系: 暂无，请根据内容推荐合适的分类名称"
        
        prompt = f"""请分析以下内容并进行分类：

**待分类内容**:
{content[:2000]}  # 限制长度避免token超限

**{categories_text}**

**分析要求**:
1. 仔细分析内容的主题和领域
2. 如果有现有分类，优先推荐匹配的分类
3. 如果没有合适的现有分类，推荐新的分类名称
4. 提取3-5个最重要的关键词
5. 判断内容类型

**输出要求**:
请返回严格的JSON格式：

```json
{{
    "suggestions": [
        {{
            "category_name": "分类名称",
            "confidence": 0.92,
            "reasoning": "选择此分类的详细理由",
            "is_existing": true
        }}
    ],
    "detected_topics": ["主题1", "主题2", "主题3"],
    "key_phrases": ["关键词1", "关键词2", "关键词3"],
    "content_type": "技术文档|学习笔记|工作总结|创意想法|其他",
    "summary": "内容主题总结"
}}
```

**注意事项**:
1. 确保JSON格式完全正确
2. confidence值在0-1之间
3. 至少提供1个分类建议，最多3个
4. reasoning要具体说明选择理由
"""
        
        return prompt
    
    def _parse_classification_result(self, result_text: str) -> Dict[str, Any]:
        """解析分类结果"""
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接提取JSON
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                else:
                    raise ValueError("No JSON found in result")
            
            # 解析JSON
            result = json.loads(json_str)
            
            # 验证必需字段
            required_fields = ["suggestions", "detected_topics", "key_phrases", "content_type"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse classification result: {e}")
            # 尝试从原始文本中提取有用信息
            return self._extract_fallback_result(result_text)
    
    def _extract_fallback_result(self, result_text: str) -> Dict[str, Any]:
        """从原始文本中提取备用结果"""
        # 简单的文本处理，提取可能的分类信息
        lines = result_text.strip().split('\n')
        
        # 尝试提取分类建议
        suggestions = []
        detected_topics = []
        key_phrases = []
        
        for line in lines:
            line = line.strip()
            if "分类" in line or "类别" in line:
                # 提取可能的分类名称
                category_match = re.search(r'[：:]\s*([^，,。.]+)', line)
                if category_match:
                    suggestions.append({
                        "category_name": category_match.group(1).strip(),
                        "confidence": 0.5,
                        "reasoning": "从AI回复中提取",
                        "is_existing": False
                    })
            elif "主题" in line or "话题" in line:
                # 提取主题
                topic_match = re.search(r'[：:]\s*([^，,。.]+)', line)
                if topic_match:
                    detected_topics.append(topic_match.group(1).strip())
            elif "关键" in line:
                # 提取关键词
                keywords = re.findall(r'[a-zA-Z\u4e00-\u9fff]+', line)
                key_phrases.extend(keywords[:3])
        
        return {
            "suggestions": suggestions if suggestions else [
                {"category_name": "其他", "confidence": 0.3, "reasoning": "无法准确分类", "is_existing": False}
            ],
            "detected_topics": detected_topics[:3] if detected_topics else ["未知主题"],
            "key_phrases": key_phrases[:5] if key_phrases else ["关键词提取失败"],
            "content_type": "其他",
            "summary": "AI返回格式异常，已提取部分信息"
        }
    
    def _validate_classification_result(
        self, 
        original_content: str, 
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证分类结果质量"""
        try:
            # 确保建议列表存在且不为空
            if "suggestions" not in result or not result["suggestions"]:
                result["suggestions"] = [
                    {"category_name": "其他", "confidence": 0.3, "reasoning": "无分类建议", "is_existing": False}
                ]
            
            # 验证每个建议的格式
            for suggestion in result["suggestions"]:
                if "confidence" not in suggestion:
                    suggestion["confidence"] = 0.5
                else:
                    # 确保置信度在合理范围内
                    suggestion["confidence"] = max(0.0, min(1.0, suggestion["confidence"]))
                
                if "category_name" not in suggestion:
                    suggestion["category_name"] = "其他"
                
                if "reasoning" not in suggestion:
                    suggestion["reasoning"] = "无具体理由"
                
                if "is_existing" not in suggestion:
                    suggestion["is_existing"] = False
            
            # 确保其他字段存在
            if "detected_topics" not in result or not result["detected_topics"]:
                result["detected_topics"] = ["未知主题"]
            
            if "key_phrases" not in result or not result["key_phrases"]:
                result["key_phrases"] = ["关键词提取失败"]
            
            if "content_type" not in result:
                result["content_type"] = "其他"
            
            # 添加元数据
            result["content_length"] = len(original_content)
            result["suggestions_count"] = len(result["suggestions"])
            
            return result
            
        except Exception as e:
            logger.error(f"Result validation failed: {e}")
            return self._create_fallback_result(original_content, str(e))
    
    def _create_fallback_result(self, original_content: str, error: str) -> Dict[str, Any]:
        """创建备用结果"""
        return {
            "suggestions": [
                {
                    "category_name": "其他",
                    "confidence": 0.0,
                    "reasoning": f"分类失败: {error}",
                    "is_existing": False
                }
            ],
            "detected_topics": ["分类失败"],
            "key_phrases": ["错误"],
            "content_type": "其他",
            "summary": f"分类失败: {error}",
            "error": error,
            "content_length": len(original_content),
            "suggestions_count": 1
        }
    
    async def batch_classify(self, contents: List[str], **kwargs) -> List[Dict[str, Any]]:
        """批量分类内容"""
        results = []
        for content in contents:
            try:
                result = await self.classify_content(content, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch classification failed for content: {e}")
                results.append(self._create_fallback_result(content, str(e)))
        
        return results
    
    def get_agent_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            "name": self.name,
            "type": "ContentClassifierAgent",
            "model_config": {
                "provider": self.model_config.get("provider"),
                "model": self.model_config.get("model"),
                "max_tokens": self.model_config.get("max_tokens"),
                "temperature": self.model_config.get("temperature")
            },
            "capabilities": [
                "topic_identification",
                "category_recommendation",
                "keyword_extraction",
                "content_type_detection"
            ]
        }
