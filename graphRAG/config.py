"""
GraphRAG系统配置文件
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class GraphRAGConfig:
    """GraphRAG系统配置"""
    
    # 数据路径配置
    data_path: str = "../data/cook"
    storage_dir: str = "graph_storage"
    
    # 图构建配置
    min_cooccurrence_threshold: int = 2  # 最小共现阈值
    similarity_threshold: float = 0.3    # 相似度阈值
    
    # 查询配置
    max_search_results: int = 10         # 最大搜索结果数
    max_recommendations: int = 10        # 最大推荐数
    
    # 推荐算法配置
    ingredient_weight: float = 0.4       # 食材权重
    method_weight: float = 0.3           # 烹饪方法权重
    category_weight: float = 0.2         # 分类权重
    similarity_weight: float = 0.1       # 相似度权重
    
    # LLM配置
    llm_model: str = "kimi-k2-0711-preview"  # LLM模型名称
    llm_temperature: float = 0.1             # LLM生成温度
    llm_max_tokens: int = 2048               # LLM最大token数
    enable_llm: bool = True                  # 是否启用LLM功能
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


# 默认配置
DEFAULT_CONFIG = GraphRAGConfig()
