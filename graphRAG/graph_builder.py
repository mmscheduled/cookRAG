"""
图构建器
从食谱数据中提取实体和关系，构建知识图谱
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict

from graph_models import (
    RecipeGraph, GraphNode, GraphEdge,
    NodeType, EdgeType
)


class RecipeGraphBuilder:
    """食谱知识图谱构建器"""
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.graph = RecipeGraph()
        
        # 预定义的实体词典
        self.cooking_methods = {
            '炒', '煮', '蒸', '炸', '烤', '炖', '焖', '煎', '拌', '凉拌',
            '红烧', '清炒', '爆炒', '干煸', '水煮', '清蒸', '红烧', '糖醋',
            '麻辣', '香辣', '酸辣', '蒜蓉', '蚝油', '白灼', '上汤', '勾芡'
        }
        
        self.seasonings = {
            '盐', '糖', '酱油', '生抽', '老抽', '料酒', '醋', '香油', '味精',
            '鸡精', '胡椒粉', '白胡椒粉', '黑胡椒粉', '花椒', '八角', '桂皮',
            '香叶', '干辣椒', '辣椒', '蒜', '姜', '葱', '洋葱', '豆瓣酱',
            '番茄酱', '蚝油', '麻油', '花椒油', '辣椒油', '芝麻油', '橄榄油',
            '花生油', '菜籽油', '色拉油', '食用油', '油'
        }
        
        self.tools = {
            '锅', '炒锅', '平底锅', '砂锅', '电饭煲', '蒸锅', '烤箱', '微波炉',
            '空气炸锅', '高压锅', '汤锅', '炖锅', '刀', '菜刀', '砧板', '铲子',
            '勺子', '筷子', '打蛋器', '搅拌器', '榨汁机', '料理机'
        }
        
        # 食材分类
        self.ingredient_categories = {
            '肉类': {'鸡', '鸭', '猪', '牛', '羊', '鱼', '虾', '蟹', '肉', '排骨', '鸡腿', '鸡翅', '牛肉', '猪肉', '羊肉'},
            '蔬菜': {'白菜', '萝卜', '土豆', '西红柿', '黄瓜', '茄子', '豆角', '青椒', '红椒', '洋葱', '蒜', '姜', '葱', '韭菜', '菠菜', '芹菜', '花菜', '西兰花', '胡萝卜', '冬瓜', '南瓜', '丝瓜', '苦瓜', '豆芽', '蘑菇', '香菇', '金针菇', '木耳', '银耳'},
            '蛋类': {'鸡蛋', '鸭蛋', '鹌鹑蛋'},
            '豆制品': {'豆腐', '豆干', '豆皮', '腐竹', '豆浆'},
            '主食': {'米', '面', '面条', '挂面', '意面', '饺子', '包子', '馒头', '饼', '饭', '粥', '汤圆', '馄饨'},
            '调料': set(self.seasonings)
        }
    
    def build_graph(self) -> RecipeGraph:
        """构建完整的知识图谱"""
        print("开始构建食谱知识图谱...")
        
        # 1. 扫描所有食谱文件
        recipe_files = self._scan_recipe_files()
        print(f"找到 {len(recipe_files)} 个食谱文件")
        
        # 2. 处理每个食谱文件
        for i, file_path in enumerate(recipe_files):
            if i % 50 == 0:
                print(f"处理进度: {i}/{len(recipe_files)}")
            self._process_recipe_file(file_path)
        
        # 3. 构建食材搭配关系
        print("构建食材搭配关系...")
        self._build_ingredient_pairings()
        
        # 4. 构建相似菜品关系
        print("构建相似菜品关系...")
        self._build_similar_dishes()
        
        print(f"图谱构建完成！")
        print(f"节点数: {len(self.graph.nodes)}")
        print(f"边数: {len(self.graph.edges)}")
        
        return self.graph
    
    def _scan_recipe_files(self) -> List[Path]:
        """扫描所有食谱文件"""
        recipe_files = []
        for root, dirs, files in os.walk(self.data_path):
            for file in files:
                if file.endswith('.md'):
                    recipe_files.append(Path(root) / file)
        return recipe_files
    
    def _process_recipe_file(self, file_path: Path) -> None:
        """处理单个食谱文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取菜品名称
            dish_name = self._extract_dish_name(content, file_path)
            if not dish_name:
                return
            
            # 创建菜品节点
            dish_id = f"dish_{dish_name}"
            dish_node = GraphNode(
                id=dish_id,
                node_type=NodeType.DISH,
                name=dish_name,
                properties={
                    'file_path': str(file_path),
                    'content': content,
                    'category': self._extract_category(file_path),
                    'difficulty': self._extract_difficulty(content)
                }
            )
            self.graph.add_node(dish_node)
            
            # 提取并添加分类节点
            category = self._extract_category(file_path)
            if category:
                category_id = f"category_{category}"
                category_node = GraphNode(
                    id=category_id,
                    node_type=NodeType.CATEGORY,
                    name=category,
                    properties={}
                )
                self.graph.add_node(category_node)
                
                # 添加分类关系
                category_edge = GraphEdge(
                    source_id=dish_id,
                    target_id=category_id,
                    edge_type=EdgeType.BELONGS_TO
                )
                self.graph.add_edge(category_edge)
            
            # 提取食材
            ingredients = self._extract_ingredients(content)
            for ingredient in ingredients:
                ingredient_id = f"ingredient_{ingredient}"
                ingredient_node = GraphNode(
                    id=ingredient_id,
                    node_type=NodeType.INGREDIENT,
                    name=ingredient,
                    properties={
                        'category': self._get_ingredient_category(ingredient)
                    }
                )
                self.graph.add_node(ingredient_node)
                
                # 添加包含关系
                contains_edge = GraphEdge(
                    source_id=dish_id,
                    target_id=ingredient_id,
                    edge_type=EdgeType.CONTAINS
                )
                self.graph.add_edge(contains_edge)
            
            # 提取烹饪方法
            cooking_methods = self._extract_cooking_methods(content)
            for method in cooking_methods:
                method_id = f"method_{method}"
                method_node = GraphNode(
                    id=method_id,
                    node_type=NodeType.COOKING_METHOD,
                    name=method,
                    properties={}
                )
                self.graph.add_node(method_node)
                
                # 添加使用方法关系
                method_edge = GraphEdge(
                    source_id=dish_id,
                    target_id=method_id,
                    edge_type=EdgeType.USES_METHOD
                )
                self.graph.add_edge(method_edge)
            
            # 提取调料
            seasonings = self._extract_seasonings(content)
            for seasoning in seasonings:
                seasoning_id = f"seasoning_{seasoning}"
                seasoning_node = GraphNode(
                    id=seasoning_id,
                    node_type=NodeType.SEASONING,
                    name=seasoning,
                    properties={}
                )
                self.graph.add_node(seasoning_node)
                
                # 添加使用调料关系
                seasoning_edge = GraphEdge(
                    source_id=dish_id,
                    target_id=seasoning_id,
                    edge_type=EdgeType.USES_SEASONING
                )
                self.graph.add_edge(seasoning_edge)
            
            # 提取工具
            tools = self._extract_tools(content)
            for tool in tools:
                tool_id = f"tool_{tool}"
                tool_node = GraphNode(
                    id=tool_id,
                    node_type=NodeType.TOOL,
                    name=tool,
                    properties={}
                )
                self.graph.add_node(tool_node)
                
                # 添加需要工具关系
                tool_edge = GraphEdge(
                    source_id=dish_id,
                    target_id=tool_id,
                    edge_type=EdgeType.REQUIRES_TOOL
                )
                self.graph.add_edge(tool_edge)
                
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
    
    def _extract_dish_name(self, content: str, file_path: Path) -> Optional[str]:
        """提取菜品名称"""
        # 从标题中提取
        title_match = re.search(r'^#\s*(.+?)\s*的做法', content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()
        
        # 从文件名提取
        return file_path.stem
    
    def _extract_category(self, file_path: Path) -> Optional[str]:
        """从文件路径提取分类"""
        path_parts = file_path.parts
        if 'dishes' in path_parts:
            dishes_index = path_parts.index('dishes')
            if dishes_index + 1 < len(path_parts):
                return path_parts[dishes_index + 1]
        return None
    
    def _extract_difficulty(self, content: str) -> Optional[str]:
        """提取烹饪难度"""
        difficulty_match = re.search(r'预估烹饪难度：([★☆]+)', content)
        if difficulty_match:
            return difficulty_match.group(1)
        return None
    
    def _extract_ingredients(self, content: str) -> Set[str]:
        """提取食材"""
        ingredients = set()
        
        # 从必备原料部分提取
        ingredients_section = re.search(r'## 必备原料和工具\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if ingredients_section:
            ingredients_text = ingredients_section.group(1)
            # 提取列表项
            items = re.findall(r'[-*]\s*([^-\n]+)', ingredients_text)
            for item in items:
                item = item.strip()
                # 过滤掉明显的工具和调料
                if not self._is_tool_or_seasoning(item):
                    ingredients.add(item)
        
        # 从计算部分提取
        calculation_section = re.search(r'## 计算\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if calculation_section:
            calc_text = calculation_section.group(1)
            items = re.findall(r'[-*]\s*([^=]+?)\s*=', calc_text)
            for item in items:
                item = item.strip()
                if not self._is_tool_or_seasoning(item):
                    ingredients.add(item)
        
        return ingredients
    
    def _extract_cooking_methods(self, content: str) -> Set[str]:
        """提取烹饪方法"""
        methods = set()
        
        # 从操作部分提取
        operation_section = re.search(r'## 操作\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if operation_section:
            operation_text = operation_section.group(1)
            
            # 查找预定义的烹饪方法
            for method in self.cooking_methods:
                if method in operation_text:
                    methods.add(method)
        
        return methods
    
    def _extract_seasonings(self, content: str) -> Set[str]:
        """提取调料"""
        seasonings = set()
        
        # 从必备原料部分提取
        ingredients_section = re.search(r'## 必备原料和工具\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if ingredients_section:
            ingredients_text = ingredients_section.group(1)
            items = re.findall(r'[-*]\s*([^-\n]+)', ingredients_text)
            for item in items:
                item = item.strip()
                if self._is_seasoning(item):
                    seasonings.add(item)
        
        return seasonings
    
    def _extract_tools(self, content: str) -> Set[str]:
        """提取工具"""
        tools = set()
        
        # 从必备原料部分提取
        ingredients_section = re.search(r'## 必备原料和工具\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if ingredients_section:
            ingredients_text = ingredients_section.group(1)
            items = re.findall(r'[-*]\s*([^-\n]+)', ingredients_text)
            for item in items:
                item = item.strip()
                if self._is_tool(item):
                    tools.add(item)
        
        # 从操作部分提取
        operation_section = re.search(r'## 操作\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if operation_section:
            operation_text = operation_section.group(1)
            for tool in self.tools:
                if tool in operation_text:
                    tools.add(tool)
        
        return tools
    
    def _is_tool_or_seasoning(self, item: str) -> bool:
        """判断是否为工具或调料"""
        return self._is_tool(item) or self._is_seasoning(item)
    
    def _is_tool(self, item: str) -> bool:
        """判断是否为工具"""
        return any(tool in item for tool in self.tools)
    
    def _is_seasoning(self, item: str) -> bool:
        """判断是否为调料"""
        return any(seasoning in item for seasoning in self.seasonings)
    
    def _get_ingredient_category(self, ingredient: str) -> Optional[str]:
        """获取食材分类"""
        for category, ingredients in self.ingredient_categories.items():
            if any(ing in ingredient for ing in ingredients):
                return category
        return None
    
    def _build_ingredient_pairings(self) -> None:
        """构建食材搭配关系"""
        # 统计食材共现频率
        ingredient_cooccurrence = defaultdict(int)
        
        # 获取所有菜品
        dish_nodes = self.graph.find_nodes_by_type(NodeType.DISH)
        
        for dish in dish_nodes:
            # 获取该菜品的所有食材
            ingredients = self.graph.get_neighbors(dish.id, EdgeType.CONTAINS)
            ingredient_ids = [ing.id for ing in ingredients]
            
            # 计算食材对
            for i in range(len(ingredient_ids)):
                for j in range(i + 1, len(ingredient_ids)):
                    pair = tuple(sorted([ingredient_ids[i], ingredient_ids[j]]))
                    ingredient_cooccurrence[pair] += 1
        
        # 添加搭配关系（共现次数大于1的）
        for (ing1_id, ing2_id), count in ingredient_cooccurrence.items():
            if count > 1:  # 至少共同出现在2个菜品中
                pairing_edge = GraphEdge(
                    source_id=ing1_id,
                    target_id=ing2_id,
                    edge_type=EdgeType.PAIRS_WITH,
                    weight=count
                )
                self.graph.add_edge(pairing_edge)
    
    def _build_similar_dishes(self) -> None:
        """构建相似菜品关系"""
        dish_nodes = self.graph.find_nodes_by_type(NodeType.DISH)
        
        for i, dish1 in enumerate(dish_nodes):
            for dish2 in dish_nodes[i+1:]:
                similarity = self._calculate_dish_similarity(dish1, dish2)
                if similarity > 0.3:  # 相似度阈值
                    similar_edge = GraphEdge(
                        source_id=dish1.id,
                        target_id=dish2.id,
                        edge_type=EdgeType.SIMILAR_TO,
                        weight=similarity
                    )
                    self.graph.add_edge(similar_edge)
    
    def _calculate_dish_similarity(self, dish1: GraphNode, dish2: GraphNode) -> float:
        """计算菜品相似度"""
        # 获取两个菜品的食材
        ingredients1 = set(ing.id for ing in self.graph.get_neighbors(dish1.id, EdgeType.CONTAINS))
        ingredients2 = set(ing.id for ing in self.graph.get_neighbors(dish2.id, EdgeType.CONTAINS))
        
        if not ingredients1 or not ingredients2:
            return 0.0
        
        # 计算Jaccard相似度
        intersection = len(ingredients1 & ingredients2)
        union = len(ingredients1 | ingredients2)
        
        return intersection / union if union > 0 else 0.0
