"""
图存储和查询接口
提供图数据的持久化存储和高效查询功能
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Set, Optional, Any, Tuple
from collections import defaultdict, deque

from graph_models import RecipeGraph, GraphNode, GraphEdge, NodeType, EdgeType


class GraphStorage:
    """图存储管理器"""
    
    def __init__(self, storage_dir: str = "graph_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # 存储文件路径
        self.graph_file = self.storage_dir / "recipe_graph.json"
        self.index_file = self.storage_dir / "graph_index.pkl"
        
        # 索引缓存
        self._name_index: Dict[str, Set[str]] = defaultdict(set)
        self._type_index: Dict[NodeType, Set[str]] = defaultdict(set)
        self._reverse_adjacency: Dict[str, Dict[str, List[GraphEdge]]] = defaultdict(lambda: defaultdict(list))
    
    def save_graph(self, graph: RecipeGraph) -> None:
        """保存图到文件"""
        print("保存图谱到文件...")
        
        # 保存图数据
        graph.save_to_file(self.graph_file)
        
        # 构建并保存索引
        self._build_indexes(graph)
        self._save_indexes()
        
        print(f"图谱已保存到: {self.storage_dir}")
    
    def load_graph(self) -> Optional[RecipeGraph]:
        """从文件加载图"""
        if not self.graph_file.exists():
            return None
        
        print("从文件加载图谱...")
        
        # 加载图数据
        graph = RecipeGraph.load_from_file(self.graph_file)
        
        # 加载索引
        self._load_indexes()
        
        print(f"图谱加载完成，节点数: {len(graph.nodes)}, 边数: {len(graph.edges)}")
        return graph
    
    def _build_indexes(self, graph: RecipeGraph) -> None:
        """构建索引"""
        print("构建索引...")
        
        # 清空索引
        self._name_index.clear()
        self._type_index.clear()
        self._reverse_adjacency.clear()
        
        # 构建名称索引
        for node in graph.nodes.values():
            # 精确匹配
            self._name_index[node.name].add(node.id)
            # 部分匹配
            words = node.name.split()
            for word in words:
                if len(word) > 1:  # 忽略单字符
                    self._name_index[word].add(node.id)
        
        # 构建类型索引
        for node in graph.nodes.values():
            self._type_index[node.node_type].add(node.id)
        
        # 构建反向邻接表
        for edge in graph.edges:
            self._reverse_adjacency[edge.target_id][edge.source_id].append(edge)
    
    def _save_indexes(self) -> None:
        """保存索引到文件"""
        index_data = {
            'name_index': dict(self._name_index),
            'type_index': {k.value: list(v) for k, v in self._type_index.items()},
            'reverse_adjacency': dict(self._reverse_adjacency)
        }
        
        with open(self.index_file, 'wb') as f:
            pickle.dump(index_data, f)
    
    def _load_indexes(self) -> None:
        """从文件加载索引"""
        if not self.index_file.exists():
            return
        
        with open(self.index_file, 'rb') as f:
            index_data = pickle.load(f)
        
        # 恢复索引
        self._name_index = defaultdict(set, index_data['name_index'])
        
        self._type_index = defaultdict(set)
        for type_str, node_ids in index_data['type_index'].items():
            self._type_index[NodeType(type_str)] = set(node_ids)
        
        self._reverse_adjacency = defaultdict(lambda: defaultdict(list))
        for target, sources in index_data['reverse_adjacency'].items():
            for source, edges in sources.items():
                self._reverse_adjacency[target][source] = edges


class GraphQueryEngine:
    """图查询引擎"""
    
    def __init__(self, graph: RecipeGraph, storage: GraphStorage):
        self.graph = graph
        self.storage = storage
    
    def search_nodes(self, query: str, node_type: Optional[NodeType] = None, limit: int = 10) -> List[GraphNode]:
        """搜索节点"""
        query_lower = query.lower()
        candidates = set()
        
        # 从名称索引中查找
        for name, node_ids in self.storage._name_index.items():
            if query_lower in name.lower():
                candidates.update(node_ids)
        
        # 过滤类型
        if node_type:
            candidates = candidates & self.storage._type_index[node_type]
        
        # 转换为节点对象并排序
        nodes = []
        for node_id in candidates:
            node = self.graph.get_node(node_id)
            if node:
                nodes.append(node)
        
        # 按名称相似度排序
        nodes.sort(key=lambda n: self._calculate_name_similarity(query, n.name), reverse=True)
        
        return nodes[:limit]
    
    def find_ingredient_pairs(self, ingredient_name: str, min_cooccurrence: int = 2) -> List[Tuple[GraphNode, int]]:
        """查找与指定食材搭配的食材"""
        # 查找食材节点
        ingredient_nodes = self.search_nodes(ingredient_name, NodeType.INGREDIENT)
        if not ingredient_nodes:
            return []
        
        # 统计共现频率
        pair_counts = defaultdict(int)
        
        for ingredient in ingredient_nodes:
            # 获取包含该食材的菜品
            dishes = self.graph.get_neighbors(ingredient.id, EdgeType.CONTAINS)
            
            for dish in dishes:
                # 获取该菜品的其他食材
                other_ingredients = self.graph.get_neighbors(dish.id, EdgeType.CONTAINS)
                for other_ingredient in other_ingredients:
                    if other_ingredient.id != ingredient.id:
                        pair_counts[other_ingredient.id] += 1
        
        # 过滤并排序
        pairs = []
        for ingredient_id, count in pair_counts.items():
            if count >= min_cooccurrence:
                ingredient = self.graph.get_node(ingredient_id)
                if ingredient:
                    pairs.append((ingredient, count))
        
        pairs.sort(key=lambda x: x[1], reverse=True)
        return pairs
    
    def find_dishes_by_ingredients(self, ingredient_names: List[str], 
                                 require_all: bool = False) -> List[Tuple[GraphNode, int]]:
        """根据食材查找菜品"""
        # 查找食材节点
        ingredient_nodes = []
        for name in ingredient_names:
            nodes = self.search_nodes(name, NodeType.INGREDIENT)
            ingredient_nodes.extend(nodes)
        
        if not ingredient_nodes:
            return []
        
        # 统计匹配度
        dish_scores = defaultdict(int)
        
        for ingredient in ingredient_nodes:
            dishes = self.graph.get_neighbors(ingredient.id, EdgeType.CONTAINS)
            for dish in dishes:
                dish_scores[dish.id] += 1
        
        # 过滤结果
        results = []
        for dish_id, score in dish_scores.items():
            if require_all and score < len(ingredient_names):
                continue
            
            dish = self.graph.get_node(dish_id)
            if dish:
                results.append((dish, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def find_similar_dishes(self, dish_name: str, limit: int = 5) -> List[Tuple[GraphNode, float]]:
        """查找相似菜品"""
        # 查找菜品节点
        dish_nodes = self.search_nodes(dish_name, NodeType.DISH)
        if not dish_nodes:
            return []
        
        similar_dishes = []
        for dish in dish_nodes:
            # 获取相似关系
            similar_edges = self.graph.get_edges(dish.id, edge_type=EdgeType.SIMILAR_TO)
            for edge in similar_edges:
                similar_dish = self.graph.get_node(edge.target_id)
                if similar_dish:
                    similar_dishes.append((similar_dish, edge.weight))
        
        # 排序并限制数量
        similar_dishes.sort(key=lambda x: x[1], reverse=True)
        return similar_dishes[:limit]
    
    def find_cooking_methods_for_ingredient(self, ingredient_name: str) -> List[Tuple[GraphNode, int]]:
        """查找食材的常用烹饪方法"""
        # 查找食材节点
        ingredient_nodes = self.search_nodes(ingredient_name, NodeType.INGREDIENT)
        if not ingredient_nodes:
            return []
        
        # 统计烹饪方法使用频率
        method_counts = defaultdict(int)
        
        for ingredient in ingredient_nodes:
            # 获取包含该食材的菜品
            dishes = self.graph.get_neighbors(ingredient.id, EdgeType.CONTAINS)
            
            for dish in dishes:
                # 获取该菜品的烹饪方法
                methods = self.graph.get_neighbors(dish.id, EdgeType.USES_METHOD)
                for method in methods:
                    method_counts[method.id] += 1
        
        # 转换为结果列表
        results = []
        for method_id, count in method_counts.items():
            method = self.graph.get_node(method_id)
            if method:
                results.append((method, count))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def find_ingredients_by_cooking_method(self, method_name: str) -> List[Tuple[GraphNode, int]]:
        """根据烹饪方法查找常用食材"""
        # 查找烹饪方法节点
        method_nodes = self.search_nodes(method_name, NodeType.COOKING_METHOD)
        if not method_nodes:
            return []
        
        # 统计食材使用频率
        ingredient_counts = defaultdict(int)
        
        for method in method_nodes:
            # 获取使用该方法的菜品
            dishes = self.graph.get_neighbors(method.id, EdgeType.USES_METHOD)
            
            for dish in dishes:
                # 获取该菜品的食材
                ingredients = self.graph.get_neighbors(dish.id, EdgeType.CONTAINS)
                for ingredient in ingredients:
                    ingredient_counts[ingredient.id] += 1
        
        # 转换为结果列表
        results = []
        for ingredient_id, count in ingredient_counts.items():
            ingredient = self.graph.get_node(ingredient_id)
            if ingredient:
                results.append((ingredient, count))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def get_ingredient_substitution_suggestions(self, ingredient_name: str) -> List[Tuple[GraphNode, float]]:
        """获取食材替代建议"""
        # 查找食材节点
        ingredient_nodes = self.search_nodes(ingredient_name, NodeType.INGREDIENT)
        if not ingredient_nodes:
            return []
        
        suggestions = []
        for ingredient in ingredient_nodes:
            # 获取与该食材搭配的其他食材
            pairs = self.graph.get_neighbors(ingredient.id, EdgeType.PAIRS_WITH)
            
            for pair_ingredient in pairs:
                # 计算替代可能性（基于搭配频率和相似性）
                substitution_score = self._calculate_substitution_score(ingredient, pair_ingredient)
                if substitution_score > 0.1:  # 阈值
                    suggestions.append((pair_ingredient, substitution_score))
        
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:10]  # 返回前10个建议
    
    def find_path_between_ingredients(self, ingredient1: str, ingredient2: str, 
                                    max_depth: int = 3) -> List[List[GraphNode]]:
        """查找两个食材之间的路径"""
        # 查找食材节点
        nodes1 = self.search_nodes(ingredient1, NodeType.INGREDIENT)
        nodes2 = self.search_nodes(ingredient2, NodeType.INGREDIENT)
        
        if not nodes1 or not nodes2:
            return []
        
        paths = []
        for start_node in nodes1:
            for end_node in nodes2:
                path = self._find_shortest_path(start_node, end_node, max_depth)
                if path:
                    paths.append(path)
        
        return paths
    
    def _calculate_name_similarity(self, query: str, name: str) -> float:
        """计算名称相似度"""
        query_lower = query.lower()
        name_lower = name.lower()
        
        if query_lower == name_lower:
            return 1.0
        
        if query_lower in name_lower:
            return 0.8
        
        # 简单的字符重叠度
        query_chars = set(query_lower)
        name_chars = set(name_lower)
        intersection = len(query_chars & name_chars)
        union = len(query_chars | name_chars)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_substitution_score(self, original: GraphNode, substitute: GraphNode) -> float:
        """计算替代分数"""
        # 获取两个食材的搭配食材
        original_pairs = set(ing.id for ing in self.graph.get_neighbors(original.id, EdgeType.PAIRS_WITH))
        substitute_pairs = set(ing.id for ing in self.graph.get_neighbors(substitute.id, EdgeType.PAIRS_WITH))
        
        if not original_pairs or not substitute_pairs:
            return 0.0
        
        # 计算搭配相似度
        intersection = len(original_pairs & substitute_pairs)
        union = len(original_pairs | substitute_pairs)
        
        return intersection / union if union > 0 else 0.0
    
    def _find_shortest_path(self, start: GraphNode, end: GraphNode, max_depth: int) -> Optional[List[GraphNode]]:
        """查找最短路径（BFS）"""
        if start.id == end.id:
            return [start]
        
        queue = deque([(start, [start])])
        visited = {start.id}
        
        while queue:
            current, path = queue.popleft()
            
            if len(path) > max_depth:
                continue
            
            # 获取邻居节点
            neighbors = self.graph.get_neighbors(current.id)
            
            for neighbor in neighbors:
                if neighbor.id == end.id:
                    return path + [neighbor]
                
                if neighbor.id not in visited:
                    visited.add(neighbor.id)
                    queue.append((neighbor, path + [neighbor]))
        
        return None
