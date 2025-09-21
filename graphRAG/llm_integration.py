"""
GraphRAG LLM集成模块
基于KimiLLM的智能回答生成和查询处理
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_community.chat_models.moonshot import MoonshotChat
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from graph_models import GraphNode, GraphEdge, NodeType, EdgeType

logger = logging.getLogger(__name__)


@dataclass
class GraphContext:
    """图上下文信息"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    relationships: List[Dict[str, Any]]
    statistics: Dict[str, Any]


class GraphLLMIntegration:
    """GraphRAG LLM集成模块"""
    
    def __init__(self, model_name: str = "kimi-k2-0711-preview", 
                 temperature: float = 0.1, max_tokens: int = 2048):
        """
        初始化LLM集成模块
        
        Args:
            model_name: 模型名称
            temperature: 生成温度
            max_tokens: 最大token数
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.llm = None
        self.setup_llm()
    
    def setup_llm(self):
        """初始化大语言模型"""
        logger.info(f"正在初始化LLM: {self.model_name}")

        api_key = os.getenv("MOONSHOT_API_KEY")
        if not api_key:
            raise ValueError("请设置 MOONSHOT_API_KEY 环境变量")

        self.llm = MoonshotChat(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            moonshot_api_key=api_key
        )
        
        logger.info("LLM初始化完成")
    
    def build_graph_context(self, nodes: List[GraphNode], edges: List[GraphEdge] = None) -> str:
        """
        构建图上下文信息
        
        Args:
            nodes: 图节点列表
            edges: 图边列表
            
        Returns:
            格式化的上下文字符串
        """
        context_parts = []
        
        # 添加节点信息
        if nodes:
            context_parts.append("## 相关实体信息:")
            for node in nodes:
                node_info = f"- {node.name} ({node.node_type.value})"
                if node.properties:
                    # 添加重要属性
                    if 'category' in node.properties:
                        node_info += f" [分类: {node.properties['category']}]"
                    if 'difficulty' in node.properties:
                        node_info += f" [难度: {node.properties['difficulty']}]"
                context_parts.append(node_info)
        
        # 添加边关系信息
        if edges:
            context_parts.append("\n## 关系信息:")
            for edge in edges:
                source_node = next((n for n in nodes if n.id == edge.source_id), None)
                target_node = next((n for n in nodes if n.id == edge.target_id), None)
                if source_node and target_node:
                    relationship = f"- {source_node.name} {self._get_relationship_description(edge.edge_type)} {target_node.name}"
                    if edge.weight > 1:
                        relationship += f" (权重: {edge.weight})"
                    context_parts.append(relationship)
        
        return "\n".join(context_parts)
    
    def _get_relationship_description(self, edge_type: EdgeType) -> str:
        """获取关系描述"""
        descriptions = {
            EdgeType.CONTAINS: "包含",
            EdgeType.USES_METHOD: "使用烹饪方法",
            EdgeType.BELONGS_TO: "属于分类",
            EdgeType.PAIRS_WITH: "搭配",
            EdgeType.SIMILAR_TO: "相似于",
            EdgeType.REQUIRES_TOOL: "需要工具",
            EdgeType.USES_SEASONING: "使用调料"
        }
        return descriptions.get(edge_type, "关联")
    
    def generate_intelligent_answer(self, query: str, graph_context: GraphContext) -> str:
        """
        生成智能回答
        
        Args:
            query: 用户查询
            graph_context: 图上下文信息
            
        Returns:
            智能生成的回答
        """
        context = self.build_graph_context(graph_context.nodes, graph_context.edges)
        
        prompt = ChatPromptTemplate.from_template("""
你是一个专业的食谱知识图谱助手，能够基于图结构信息提供准确、有用的回答。

用户问题: {question}

相关图谱信息:
{context}

请基于提供的图谱信息，给出详细、实用的回答。注意：
1. 充分利用图结构中的实体和关系信息
2. 如果涉及食材搭配，请说明搭配的原因和效果
3. 如果涉及烹饪方法，请提供具体的操作建议
4. 如果信息不足，请诚实说明
5. 回答要结构清晰，便于理解

回答:""")

        chain = (
            {"question": RunnablePassthrough(), "context": lambda _: context}
            | prompt
            | self.llm
            | StrOutputParser()
        )

        response = chain.invoke(query)
        return response
    
    def generate_analysis_report(self, target_name: str, analysis_data: Dict[str, Any]) -> str:
        """
        生成分析报告
        
        Args:
            target_name: 分析目标名称
            analysis_data: 分析数据
            
        Returns:
            格式化的分析报告
        """
        # 构建分析数据上下文
        context_parts = [f"## {target_name} 分析数据:"]
        
        for key, value in analysis_data.items():
            if key == "error":
                continue
            elif isinstance(value, list):
                if value and isinstance(value[0], tuple):
                    # 处理 (item, count) 格式的列表
                    context_parts.append(f"{key}:")
                    for item, count in value[:5]:  # 只显示前5个
                        if hasattr(item, 'name'):
                            context_parts.append(f"  - {item.name} ({count})")
                        else:
                            context_parts.append(f"  - {item} ({count})")
                else:
                    context_parts.append(f"{key}: {', '.join(map(str, value))}")
            else:
                context_parts.append(f"{key}: {value}")
        
        context = "\n".join(context_parts)
        
        prompt = ChatPromptTemplate.from_template("""
你是一个专业的食谱分析专家，请基于以下分析数据生成一份详细的分析报告。

分析目标: {target_name}

分析数据:
{context}

请生成一份结构化的分析报告，包括：
1. 概述：简要介绍分析目标的特点
2. 关键发现：基于数据的重要发现
3. 建议：基于分析结果给出的实用建议
4. 总结：整体评价和结论

分析报告:""")

        chain = (
            {"target_name": lambda _: target_name, "context": lambda _: context}
            | prompt
            | self.llm
            | StrOutputParser()
        )

        response = chain.invoke("")
        return response
    
    def generate_recommendation_explanation(self, recommendations: List[tuple], query: str) -> str:
        """
        生成推荐解释
        
        Args:
            recommendations: 推荐结果列表 [(item, score), ...]
            query: 原始查询
            
        Returns:
            推荐解释文本
        """
        if not recommendations:
            return "抱歉，没有找到相关的推荐结果。"
        
        # 构建推荐数据上下文
        context_parts = [f"## 推荐结果 (基于查询: {query}):"]
        for i, (item, score) in enumerate(recommendations[:10], 1):
            if hasattr(item, 'name'):
                context_parts.append(f"{i}. {item.name} (推荐度: {score:.2f})")
            else:
                context_parts.append(f"{i}. {item} (推荐度: {score:.2f})")
        
        context = "\n".join(context_parts)
        
        prompt = ChatPromptTemplate.from_template("""
你是一个专业的食谱推荐专家，请基于以下推荐结果生成详细的推荐解释。

推荐数据:
{context}

请生成一份推荐解释，包括：
1. 推荐理由：解释为什么推荐这些结果
2. 特点分析：分析每个推荐项的特点
3. 使用建议：给出具体的使用建议
4. 注意事项：提醒用户注意的事项

推荐解释:""")

        chain = (
            {"context": lambda _: context}
            | prompt
            | self.llm
            | StrOutputParser()
        )

        response = chain.invoke("")
        return response
    
    def enhance_query_understanding(self, query: str) -> Dict[str, Any]:
        """
        增强查询理解
        
        Args:
            query: 原始查询
            
        Returns:
            增强后的查询信息
        """
        prompt = ChatPromptTemplate.from_template("""
你是一个专业的查询理解专家，请分析以下用户查询并提供增强信息。

用户查询: {query}

请分析并返回以下信息（以JSON格式）：
1. intent: 查询意图（如：搭配查询、推荐查询、分析查询等）
2. entities: 查询中识别的实体列表
3. enhanced_query: 增强后的查询（如果需要）
4. confidence: 理解置信度（0-1）

分析结果:""")

        chain = (
            {"query": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

        response = chain.invoke(query)
        
        # 尝试解析JSON响应
        try:
            import json
            # 简单的JSON提取（实际应用中可能需要更复杂的解析）
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
        
        # 如果解析失败，返回默认结构
        return {
            "intent": "general",
            "entities": [],
            "enhanced_query": query,
            "confidence": 0.5
        }
    
    def generate_streaming_answer(self, query: str, graph_context: GraphContext):
        """
        生成流式回答
        
        Args:
            query: 用户查询
            graph_context: 图上下文信息
            
        Yields:
            回答的各个部分
        """
        context = self.build_graph_context(graph_context.nodes, graph_context.edges)
        
        prompt = ChatPromptTemplate.from_template("""
你是一个专业的食谱知识图谱助手，能够基于图结构信息提供准确、有用的回答。

用户问题: {question}

相关图谱信息:
{context}

请基于提供的图谱信息，给出详细、实用的回答。注意：
1. 充分利用图结构中的实体和关系信息
2. 如果涉及食材搭配，请说明搭配的原因和效果
3. 如果涉及烹饪方法，请提供具体的操作建议
4. 如果信息不足，请诚实说明
5. 回答要结构清晰，便于理解

回答:""")

        chain = (
            {"question": RunnablePassthrough(), "context": lambda _: context}
            | prompt
            | self.llm
        )

        # 流式生成
        for chunk in chain.stream(query):
            if hasattr(chunk, 'content'):
                yield chunk.content
            else:
                yield str(chunk)

    def generate_fallback_answer(self, query: str) -> str:
        """
        当图谱信息不足时，基于通用知识生成回答
        
        Args:
            query: 用户查询
            
        Returns:
            基于通用知识的回答
        """
        prompt = ChatPromptTemplate.from_template("""
你是一个专业的食谱知识图谱助手。用户提出了以下问题：

{question}

虽然当前的知识图谱中没有直接相关的信息，但请基于你的专业知识提供有用的回答。

请根据问题类型提供相应的建议：

1. 如果是关于图谱可视化的询问，请说明：
- 图谱可视化的概念和意义
- 常见的可视化工具和方法
- 如何构建食谱知识图谱的可视化

2. 如果是关于食谱相关的问题，请提供：
- 相关的烹饪知识和建议
- 食材搭配的一般原则
- 烹饪方法的技巧

3. 如果是关于系统功能的询问，请说明：
- 系统的可用功能
- 如何使用这些功能
- 相关的操作建议

请提供详细、实用的回答，即使没有具体的图谱数据支持。

回答:""")

        chain = (
            {"question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

        response = chain.invoke(query)
        return response