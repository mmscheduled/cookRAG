"""
图结构数据模型定义
定义食谱知识图谱中的节点和边类型
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from enum import Enum
import json


class NodeType(Enum):
    """节点类型枚举"""
    DISH = "dish"           # 菜品
    INGREDIENT = "ingredient"  # 食材
    COOKING_METHOD = "cooking_method"  # 烹饪方法
    CATEGORY = "category"   # 分类
    TOOL = "tool"          # 工具
    SEASONING = "seasoning"  # 调料


class EdgeType(Enum):
    """边类型枚举"""
    CONTAINS = "contains"           # 包含关系（菜品包含食材）
    USES_METHOD = "uses_method"     # 使用烹饪方法
    BELONGS_TO = "belongs_to"       # 属于分类
    PAIRS_WITH = "pairs_with"       # 搭配关系（食材搭配）
    SIMILAR_TO = "similar_to"       # 相似关系
    REQUIRES_TOOL = "requires_tool"  # 需要工具
    USES_SEASONING = "uses_seasoning"  # 使用调料


@dataclass
class GraphNode:
    """图节点"""
    id: str
    node_type: NodeType
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return isinstance(other, GraphNode) and self.id == other.id


@dataclass
class GraphEdge:
    """图边"""
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash((self.source_id, self.target_id, self.edge_type))
    
    def __eq__(self, other):
        return (isinstance(other, GraphEdge) and 
                self.source_id == other.source_id and
                self.target_id == other.target_id and
                self.edge_type == other.edge_type)


class RecipeGraph:
    """食谱知识图谱"""
    
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.adjacency_list: Dict[str, Dict[str, List[GraphEdge]]] = {}
    
    def add_node(self, node: GraphNode) -> None:
        """添加节点"""
        self.nodes[node.id] = node
        if node.id not in self.adjacency_list:
            self.adjacency_list[node.id] = {}
    
    def add_edge(self, edge: GraphEdge) -> None:
        """添加边"""
        if edge not in self.edges:
            self.edges.append(edge)
            
            # 更新邻接表
            if edge.source_id not in self.adjacency_list:
                self.adjacency_list[edge.source_id] = {}
            if edge.target_id not in self.adjacency_list[edge.source_id]:
                self.adjacency_list[edge.source_id][edge.target_id] = []
            
            self.adjacency_list[edge.source_id][edge.target_id].append(edge)
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """获取节点"""
        return self.nodes.get(node_id)
    
    def get_neighbors(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[GraphNode]:
        """获取邻居节点"""
        neighbors = []
        
        # 查找从当前节点出发的边（出边）
        if node_id in self.adjacency_list:
            for target_id, edges in self.adjacency_list[node_id].items():
                if edge_type is None or any(edge.edge_type == edge_type for edge in edges):
                    neighbor = self.get_node(target_id)
                    if neighbor:
                        neighbors.append(neighbor)
        
        # 查找指向当前节点的边（入边）
        for source_id, target_dict in self.adjacency_list.items():
            if node_id in target_dict:
                edges = target_dict[node_id]
                if edge_type is None or any(edge.edge_type == edge_type for edge in edges):
                    neighbor = self.get_node(source_id)
                    if neighbor:
                        neighbors.append(neighbor)
        
        return neighbors
    
    def get_edges(self, source_id: str, target_id: str = None, edge_type: EdgeType = None) -> List[GraphEdge]:
        """获取边"""
        if source_id not in self.adjacency_list:
            return []
        
        edges = []
        for t_id, edge_list in self.adjacency_list[source_id].items():
            if target_id is None or t_id == target_id:
                for edge in edge_list:
                    if edge_type is None or edge.edge_type == edge_type:
                        edges.append(edge)
        
        return edges
    
    def find_nodes_by_type(self, node_type: NodeType) -> List[GraphNode]:
        """根据类型查找节点"""
        return [node for node in self.nodes.values() if node.node_type == node_type]
    
    def find_nodes_by_name(self, name: str, node_type: NodeType = None) -> List[GraphNode]:
        """根据名称查找节点"""
        nodes = [node for node in self.nodes.values() if name.lower() in node.name.lower()]
        if node_type:
            nodes = [node for node in nodes if node.node_type == node_type]
        return nodes
    
    def get_ingredient_pairs(self, ingredient_name: str) -> List[GraphNode]:
        """获取与指定食材搭配的食材"""
        ingredient_nodes = self.find_nodes_by_name(ingredient_name, NodeType.INGREDIENT)
        if not ingredient_nodes:
            return []
        
        pairs = set()
        for ingredient in ingredient_nodes:
            # 查找包含该食材的菜品
            dishes = self.get_neighbors(ingredient.id, EdgeType.CONTAINS)
            for dish in dishes:
                # 获取这些菜品中的其他食材
                dish_ingredients = self.get_neighbors(dish.id, EdgeType.CONTAINS)
                for other_ingredient in dish_ingredients:
                    if other_ingredient.id != ingredient.id:
                        pairs.add(other_ingredient)
        
        return list(pairs)
    
    def get_dishes_by_ingredients(self, ingredient_names: List[str]) -> List[GraphNode]:
        """根据食材列表查找菜品"""
        ingredient_nodes = []
        for name in ingredient_names:
            nodes = self.find_nodes_by_name(name, NodeType.INGREDIENT)
            ingredient_nodes.extend(nodes)
        
        if not ingredient_nodes:
            return []
        
        # 找到包含这些食材的菜品
        dish_scores = {}
        for ingredient in ingredient_nodes:
            dishes = self.get_neighbors(ingredient.id, EdgeType.CONTAINS)
            for dish in dishes:
                if dish.id not in dish_scores:
                    dish_scores[dish.id] = 0
                dish_scores[dish.id] += 1
        
        # 按匹配度排序
        sorted_dishes = sorted(dish_scores.items(), key=lambda x: x[1], reverse=True)
        return [self.get_node(dish_id) for dish_id, _ in sorted_dishes if self.get_node(dish_id)]
    
    def get_cooking_methods_for_dish(self, dish_name: str) -> List[GraphNode]:
        """获取菜品的烹饪方法"""
        dish_nodes = self.find_nodes_by_name(dish_name, NodeType.DISH)
        if not dish_nodes:
            return []
        
        methods = set()
        for dish in dish_nodes:
            method_nodes = self.get_neighbors(dish.id, EdgeType.USES_METHOD)
            methods.update(method_nodes)
        
        return list(methods)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        stats = {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "nodes_by_type": {},
            "edges_by_type": {}
        }
        
        # 统计节点类型
        for node in self.nodes.values():
            node_type = node.node_type.value
            if node_type not in stats["nodes_by_type"]:
                stats["nodes_by_type"][node_type] = 0
            stats["nodes_by_type"][node_type] += 1
        
        # 统计边类型
        for edge in self.edges:
            edge_type = edge.edge_type.value
            if edge_type not in stats["edges_by_type"]:
                stats["edges_by_type"][edge_type] = 0
            stats["edges_by_type"][edge_type] += 1
        
        return stats
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "nodes": [
                {
                    "id": node.id,
                    "type": node.node_type.value,
                    "name": node.name,
                    "properties": node.properties
                }
                for node in self.nodes.values()
            ],
            "edges": [
                {
                    "source": edge.source_id,
                    "target": edge.target_id,
                    "type": edge.edge_type.value,
                    "weight": edge.weight,
                    "properties": edge.properties
                }
                for edge in self.edges
            ]
        }
    
    def save_to_file(self, filepath: str) -> None:
        """保存到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'RecipeGraph':
        """从文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        graph = cls()
        
        # 加载节点
        for node_data in data["nodes"]:
            node = GraphNode(
                id=node_data["id"],
                node_type=NodeType(node_data["type"]),
                name=node_data["name"],
                properties=node_data.get("properties", {})
            )
            graph.add_node(node)
        
        # 加载边
        for edge_data in data["edges"]:
            edge = GraphEdge(
                source_id=edge_data["source"],
                target_id=edge_data["target"],
                edge_type=EdgeType(edge_data["type"]),
                weight=edge_data.get("weight", 1.0),
                properties=edge_data.get("properties", {})
            )
            graph.add_edge(edge)
        
        return graph
