"""
文本优化AI Agent - 基于AutoGen
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


class TextOptimizerAgent(BaseAgent):
    """文本优化AI Agent"""
    
    def __init__(self, name: str, model_config: Dict[str, Any]):
        super().__init__(name)
        self.model_config = model_config
        self.model_client = self._create_model_client(model_config)
        self.assistant = AssistantAgent(
            name=name,
            model_client=self.model_client,
            system_message=self._get_system_message()
        )
        logger.info(f"TextOptimizerAgent '{name}' initialized")
    
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
        return """你是一个专业的中文文本优化助手。你的任务是：

1. **语法修正**: 识别并修正语法错误、标点符号错误、错别字等
2. **表达改进**: 改善表达方式，使其更清晰、准确、流畅
3. **结构优化**: 优化文本结构，提高逻辑性和可读性
4. **风格适应**: 根据用户的写作风格偏好进行调整

**优化原则**:
- 保持原文的核心意思和语调不变
- 提供具体的修改建议和解释
- 根据不同的优化类型提供针对性的改进
- 评估优化质量的置信度

**输出格式**: 必须返回有效的JSON格式，包含以下字段：
- optimized_text: 优化后的完整文本
- suggestions: 具体的修改建议列表
- confidence: 优化质量的置信度(0-1)
- optimization_type: 主要优化类型

请始终保持专业、准确、有帮助的态度。"""
    
    async def optimize_text(
        self, 
        text: str, 
        optimization_type: str = "all",
        user_style: Optional[str] = None
    ) -> Dict[str, Any]:
        """优化文本内容"""
        try:
            prompt = self._build_optimization_prompt(text, optimization_type, user_style)
            
            # 调用AutoGen Assistant
            result = await self.assistant.run(task=prompt)
            
            # 解析结果
            optimized_result = self._parse_optimization_result(result.messages[-1].content)
            
            # 验证结果质量
            validated_result = self._validate_optimization_result(text, optimized_result)
            
            logger.info(f"Text optimization completed successfully")
            return validated_result
            
        except Exception as e:
            logger.error(f"Text optimization failed: {e}")
            return self._create_fallback_result(text, str(e))
    
    def _build_optimization_prompt(
        self, 
        text: str, 
        optimization_type: str,
        user_style: Optional[str]
    ) -> str:
        """构建优化提示词"""
        prompt = f"""请优化以下文本：

**原文**:
{text}

**优化要求**:
- 优化类型: {self._get_optimization_type_description(optimization_type)}
"""
        
        if user_style:
            prompt += f"- 用户写作风格偏好: {user_style}\n"
        
        prompt += """
**输出要求**:
请返回严格的JSON格式，包含以下字段：

```json
{
    "optimized_text": "优化后的完整文本",
    "suggestions": [
        {
            "type": "grammar|expression|structure",
            "original": "原始片段",
            "optimized": "优化片段",
            "explanation": "修改说明",
            "position": {"start": 0, "end": 10},
            "confidence": 0.95
        }
    ],
    "confidence": 0.92,
    "optimization_type": "主要优化类型",
    "summary": "优化总结"
}
```

**注意事项**:
1. 确保JSON格式完全正确
2. 保持原文的核心意思不变
3. 提供具体的修改理由
4. 评估每个建议的置信度
"""
        
        return prompt
    
    def _get_optimization_type_description(self, optimization_type: str) -> str:
        """获取优化类型描述"""
        descriptions = {
            "grammar": "语法修正 - 重点修正语法错误、标点符号、错别字",
            "expression": "表达改进 - 重点改善表达方式，使其更清晰准确",
            "structure": "结构优化 - 重点优化文本结构和逻辑性",
            "all": "全面优化 - 包括语法修正、表达改进和结构优化"
        }
        return descriptions.get(optimization_type, descriptions["all"])
    
    def _parse_optimization_result(self, result_text: str) -> Dict[str, Any]:
        """解析优化结果"""
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
            required_fields = ["optimized_text", "suggestions", "confidence"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse optimization result: {e}")
            # 尝试从原始文本中提取有用信息
            return self._extract_fallback_result(result_text)
    
    def _extract_fallback_result(self, result_text: str) -> Dict[str, Any]:
        """从原始文本中提取备用结果"""
        # 简单的文本处理，提取可能的优化内容
        lines = result_text.strip().split('\n')
        optimized_text = result_text  # 默认使用原始结果
        
        # 尝试找到优化后的文本
        for i, line in enumerate(lines):
            if "优化后" in line or "修改后" in line:
                if i + 1 < len(lines):
                    optimized_text = lines[i + 1].strip()
                break
        
        return {
            "optimized_text": optimized_text,
            "suggestions": [],
            "confidence": 0.5,
            "optimization_type": "unknown",
            "summary": "AI返回格式异常，已提取部分结果"
        }
    
    def _validate_optimization_result(
        self, 
        original_text: str, 
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证优化结果质量"""
        try:
            optimized_text = result.get("optimized_text", "")
            
            # 基本验证
            if not optimized_text or len(optimized_text.strip()) == 0:
                result["optimized_text"] = original_text
                result["confidence"] = 0.1
                result["summary"] = "优化失败，返回原文"
            
            # 长度合理性检查
            length_ratio = len(optimized_text) / len(original_text) if original_text else 1
            if length_ratio > 3 or length_ratio < 0.3:
                logger.warning(f"Unusual length ratio: {length_ratio}")
                result["confidence"] = min(result.get("confidence", 0.5), 0.7)
            
            # 确保建议列表存在
            if "suggestions" not in result or not isinstance(result["suggestions"], list):
                result["suggestions"] = []
            
            # 确保置信度在合理范围内
            confidence = result.get("confidence", 0.5)
            result["confidence"] = max(0.0, min(1.0, confidence))
            
            # 添加元数据
            result["original_length"] = len(original_text)
            result["optimized_length"] = len(optimized_text)
            result["length_change"] = len(optimized_text) - len(original_text)
            
            return result
            
        except Exception as e:
            logger.error(f"Result validation failed: {e}")
            return self._create_fallback_result(original_text, str(e))
    
    def _create_fallback_result(self, original_text: str, error: str) -> Dict[str, Any]:
        """创建备用结果"""
        return {
            "optimized_text": original_text,
            "suggestions": [],
            "confidence": 0.0,
            "optimization_type": "error",
            "summary": f"优化失败: {error}",
            "error": error,
            "original_length": len(original_text),
            "optimized_length": len(original_text),
            "length_change": 0
        }
    
    async def batch_optimize(self, texts: List[str], **kwargs) -> List[Dict[str, Any]]:
        """批量优化文本"""
        results = []
        for text in texts:
            try:
                result = await self.optimize_text(text, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch optimization failed for text: {e}")
                results.append(self._create_fallback_result(text, str(e)))
        
        return results
    
    def get_agent_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            "name": self.name,
            "type": "TextOptimizerAgent",
            "model_config": {
                "provider": self.model_config.get("provider"),
                "model": self.model_config.get("model"),
                "max_tokens": self.model_config.get("max_tokens"),
                "temperature": self.model_config.get("temperature")
            },
            "capabilities": [
                "grammar_correction",
                "expression_improvement", 
                "structure_optimization",
                "style_adaptation"
            ]
        }
