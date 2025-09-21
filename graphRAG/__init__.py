"""
GraphRAG - 基于图结构的食谱知识图谱系统

这个包提供了基于图结构的食谱知识图谱功能，包括：
- 图结构数据模型
- 图构建器
- 图存储和查询
- 复杂关系查询
- 推荐算法
- 主接口

主要组件：
- GraphRAGSystem: 主系统类
- RecipeGraph: 知识图谱
- GraphQueryEngine: 查询引擎
- ComplexQueryProcessor: 复杂查询处理器
- GraphRecommendationEngine: 推荐引擎
"""

from .main import GraphRAGSystem
from .graph_models import RecipeGraph, GraphNode, GraphEdge, NodeType, EdgeType
from .graph_builder import RecipeGraphBuilder
from .graph_storage import GraphStorage, GraphQueryEngine
from .complex_queries import ComplexQueryProcessor
from .recommendation_engine import GraphRecommendationEngine
from .config import GraphRAGConfig, DEFAULT_CONFIG

__version__ = "1.0.0"
__author__ = "GraphRAG Team"

__all__ = [
    "GraphRAGSystem",
    "RecipeGraph",
    "GraphNode", 
    "GraphEdge",
    "NodeType",
    "EdgeType",
    "RecipeGraphBuilder",
    "GraphStorage",
    "GraphQueryEngine",
    "ComplexQueryProcessor",
    "GraphRecommendationEngine",
    "GraphRAGConfig",
    "DEFAULT_CONFIG"
]
