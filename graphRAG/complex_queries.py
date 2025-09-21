"""
复杂关系查询功能
实现高级的图查询和关系分析功能
"""

import re
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict, Counter
from dataclasses import dataclass

from graph_models import RecipeGraph, GraphNode, NodeType, EdgeType
from graph_storage import GraphQueryEngine


@dataclass
class QueryResult:
    """查询结果"""
    query_type: str
    results: List[Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ComplexQueryProcessor:
    """复杂查询处理器"""
    
    def __init__(self, query_engine: GraphQueryEngine, recommendation_engine=None, llm_integration=None):
        self.query_engine = query_engine
        self.graph = query_engine.graph
        self.recommendation_engine = recommendation_engine
        self.llm_integration = llm_integration
    
    def process_natural_language_query(self, query: str) -> QueryResult:
        """处理自然语言查询"""
        query_lower = query.lower()
        
        # 查询类型识别（按优先级排序，更具体的查询类型优先）
        if any(keyword in query_lower for keyword in ['发现', '热门', '流行', '趋势']):
            return self._process_discovery_query(query)
        elif any(keyword in query_lower for keyword in ['相似', '类似', '像']):
            return self._process_similarity_query(query)
        elif any(keyword in query_lower for keyword in ['推荐', '建议', '可以']):
            return self._process_recommendation_query(query)
        elif any(keyword in query_lower for keyword in ['替代', '替换', '代替']):
            return self._process_substitution_query(query)
        elif any(keyword in query_lower for keyword in ['搭配', '配', '和', '一起']):
            return self._process_pairing_query(query)
        elif any(keyword in query_lower for keyword in ['方法', '做法', '烹饪']):
            return self._process_cooking_method_query(query)
        elif any(keyword in query_lower for keyword in ['食材', '原料', '材料']):
            return self._process_ingredient_query(query)
        elif any(keyword in query_lower for keyword in ['分析', '了解', '介绍', '说明']):
            return self._process_analysis_query(query)
        else:
            return self._process_general_query(query)
    
    def _process_pairing_query(self, query: str) -> QueryResult:
        """处理搭配查询"""
        # 提取食材名称
        ingredients = self._extract_ingredients_from_query(query)
        
        if not ingredients:
            return QueryResult("pairing", [], {"error": "未找到食材信息"})
        
        # 查找搭配关系
        all_pairs = []
        for ingredient in ingredients:
            pairs = self.query_engine.find_ingredient_pairs(ingredient)
            all_pairs.extend(pairs)
        
        # 去重并排序
        pair_dict = {}
        for ingredient, count in all_pairs:
            if ingredient.name not in pair_dict:
                pair_dict[ingredient.name] = (ingredient, count)
            else:
                # 取更高的频率
                if count > pair_dict[ingredient.name][1]:
                    pair_dict[ingredient.name] = (ingredient, count)
        
        results = list(pair_dict.values())
        results.sort(key=lambda x: x[1], reverse=True)
        
        return QueryResult("pairing", results, {
            "query_ingredients": ingredients,
            "total_pairs": len(results)
        })
    
    def _process_recommendation_query(self, query: str) -> QueryResult:
        """处理推荐查询"""
        # 提取食材或菜品信息
        ingredients = self._extract_ingredients_from_query(query)
        dishes = self._extract_dishes_from_query(query)
        
        recommendations = []
        
        if ingredients:
            # 基于食材推荐菜品
            dish_recommendations = self.query_engine.find_dishes_by_ingredients(ingredients)
            recommendations.extend(dish_recommendations)
        
        if dishes:
            # 基于菜品推荐相似菜品
            for dish in dishes:
                similar_dishes = self.query_engine.find_similar_dishes(dish)
                recommendations.extend(similar_dishes)
        
        # 去重并排序
        unique_recommendations = {}
        for item, score in recommendations:
            if item.name not in unique_recommendations:
                unique_recommendations[item.name] = (item, score)
            else:
                if score > unique_recommendations[item.name][1]:
                    unique_recommendations[item.name] = (item, score)
        
        results = list(unique_recommendations.values())
        results.sort(key=lambda x: x[1], reverse=True)
        
        return QueryResult("recommendation", results, {
            "query_ingredients": ingredients,
            "query_dishes": dishes,
            "total_recommendations": len(results)
        })
    
    def _process_substitution_query(self, query: str) -> QueryResult:
        """处理替代查询"""
        ingredients = self._extract_ingredients_from_query(query)
        
        if not ingredients:
            return QueryResult("substitution", [], {"error": "未找到食材信息"})
        
        substitutions = []
        for ingredient in ingredients:
            suggestions = self.query_engine.get_ingredient_substitution_suggestions(ingredient)
            substitutions.extend(suggestions)
        
        # 去重并排序
        sub_dict = {}
        for ingredient, score in substitutions:
            if ingredient.name not in sub_dict:
                sub_dict[ingredient.name] = (ingredient, score)
            else:
                if score > sub_dict[ingredient.name][1]:
                    sub_dict[ingredient.name] = (ingredient, score)
        
        results = list(sub_dict.values())
        results.sort(key=lambda x: x[1], reverse=True)
        
        return QueryResult("substitution", results, {
            "query_ingredients": ingredients,
            "total_substitutions": len(results)
        })
    
    def _process_similarity_query(self, query: str) -> QueryResult:
        """处理相似性查询"""
        dishes = self._extract_dishes_from_query(query)
        
        if not dishes:
            return QueryResult("similarity", [], {"error": "未找到菜品信息"})
        
        similar_dishes = []
        for dish in dishes:
            similar = self.query_engine.find_similar_dishes(dish)
            similar_dishes.extend(similar)
        
        # 去重并排序
        sim_dict = {}
        for dish, score in similar_dishes:
            if dish.name not in sim_dict:
                sim_dict[dish.name] = (dish, score)
            else:
                if score > sim_dict[dish.name][1]:
                    sim_dict[dish.name] = (dish, score)
        
        results = list(sim_dict.values())
        results.sort(key=lambda x: x[1], reverse=True)
        
        return QueryResult("similarity", results, {
            "query_dishes": dishes,
            "total_similar": len(results)
        })
    
    def _process_cooking_method_query(self, query: str) -> QueryResult:
        """处理烹饪方法查询"""
        ingredients = self._extract_ingredients_from_query(query)
        methods = self._extract_cooking_methods_from_query(query)
        
        results = []
        
        if ingredients:
            # 查找食材的常用烹饪方法
            for ingredient in ingredients:
                methods_for_ingredient = self.query_engine.find_cooking_methods_for_ingredient(ingredient)
                results.extend(methods_for_ingredient)
        
        if methods:
            # 查找烹饪方法的常用食材
            for method in methods:
                ingredients_for_method = self.query_engine.find_ingredients_by_cooking_method(method)
                results.extend(ingredients_for_method)
        
        # 去重并排序
        result_dict = {}
        for item, count in results:
            if item.name not in result_dict:
                result_dict[item.name] = (item, count)
            else:
                if count > result_dict[item.name][1]:
                    result_dict[item.name] = (item, count)
        
        final_results = list(result_dict.values())
        final_results.sort(key=lambda x: x[1], reverse=True)
        
        return QueryResult("cooking_method", final_results, {
            "query_ingredients": ingredients,
            "query_methods": methods,
            "total_results": len(final_results)
        })
    
    def _process_ingredient_query(self, query: str) -> QueryResult:
        """处理食材查询"""
        dishes = self._extract_dishes_from_query(query)
        
        if not dishes:
            return QueryResult("ingredient", [], {"error": "未找到菜品信息"})
        
        all_ingredients = []
        for dish in dishes:
            # 查找菜品节点
            dish_nodes = self.query_engine.search_nodes(dish, NodeType.DISH)
            for dish_node in dish_nodes:
                ingredients = self.graph.get_neighbors(dish_node.id, EdgeType.CONTAINS)
                all_ingredients.extend(ingredients)
        
        # 统计食材频率
        ingredient_counts = Counter(ingredient.name for ingredient in all_ingredients)
        
        # 转换为结果格式
        results = []
        for ingredient_name, count in ingredient_counts.most_common():
            ingredient_node = self.query_engine.search_nodes(ingredient_name, NodeType.INGREDIENT)
            if ingredient_node:
                results.append((ingredient_node[0], count))
        
        return QueryResult("ingredient", results, {
            "query_dishes": dishes,
            "total_ingredients": len(results)
        })
    
    def _process_discovery_query(self, query: str) -> QueryResult:
        """处理发现查询"""
        query_lower = query.lower()
        
        # 检查是否是热门组合发现查询
        if any(keyword in query_lower for keyword in ['热门', '流行', '趋势']) and any(keyword in query_lower for keyword in ['组合', '搭配', '食材']):
            # 获取热门食材组合
            if self.recommendation_engine:
                combinations = self.recommendation_engine.discover_trending_combinations()
            else:
                # 如果没有推荐引擎，使用图结构直接计算
                combinations = self._discover_trending_combinations_direct()
            
            # 转换为结果格式
            results = []
            for combination, count in combinations:
                # 创建虚拟节点来表示组合
                from graph_models import GraphNode, NodeType
                combination_node = GraphNode(
                    id=f"combination_{'_'.join(combination)}",
                    node_type=NodeType.INGREDIENT,  # 使用INGREDIENT类型
                    name=" + ".join(combination),
                    properties={
                        "type": "ingredient_combination",
                        "ingredients": combination,
                        "cooccurrence_count": count
                    }
                )
                results.append((combination_node, count))
            
            return QueryResult("discovery", results, {
                "discovery_type": "trending_combinations",
                "total_combinations": len(results)
            })
        
        # 其他发现查询类型可以在这里扩展
        else:
            return QueryResult("discovery", [], {"error": "未支持的发现查询类型"})
    
    def _discover_trending_combinations_direct(self, min_cooccurrence: int = 3) -> List[Tuple[List[str], int]]:
        """直接使用图结构发现热门食材组合"""
        from collections import defaultdict
        
        # 统计所有食材对的出现频率
        ingredient_pairs = defaultdict(int)
        
        # 获取所有菜品
        dish_nodes = self.graph.find_nodes_by_type(NodeType.DISH)
        
        for dish in dish_nodes:
            ingredients = self.graph.get_neighbors(dish.id, EdgeType.CONTAINS)
            ingredient_names = [ing.name for ing in ingredients]
            
            # 生成所有可能的食材对
            for i in range(len(ingredient_names)):
                for j in range(i + 1, len(ingredient_names)):
                    pair = tuple(sorted([ingredient_names[i], ingredient_names[j]]))
                    ingredient_pairs[pair] += 1
        
        # 过滤并排序
        trending_combinations = []
        for pair, count in ingredient_pairs.items():
            if count >= min_cooccurrence:
                trending_combinations.append((list(pair), count))
        
        trending_combinations.sort(key=lambda x: x[1], reverse=True)
        return trending_combinations[:20]  # 返回前20个热门组合
    
    def generate_llm_enhanced_answer(self, query: str, result: QueryResult) -> str:
        """
        生成LLM增强的回答
        
        Args:
            query: 原始查询
            result: 查询结果
            
        Returns:
            LLM增强的回答
        """
        if not self.llm_integration:
            return self._generate_simple_answer(query, result)
        
         # 检查是否有图谱信息
        has_graph_info = result.results and len(result.results) > 0
    
        if has_graph_info:
            # 有图谱信息时，使用图谱信息生成回答
            # 构建图上下文
            from llm_integration import GraphContext
        
            # 从结果中提取节点和边信息
            nodes = []
            edges = []
            relationships = []
            
            if result.results:
                for item in result.results:
                    if isinstance(item, tuple) and len(item) >= 1:
                        # 处理 (node, score) 格式
                        node = item[0]
                        if hasattr(node, 'id') and hasattr(node, 'name'):
                            nodes.append(node)
                    elif hasattr(item, 'id') and hasattr(item, 'name'):
                        # 处理单个节点
                        nodes.append(item)
            
            # 构建关系信息
            for node in nodes:
                # 获取节点的邻居关系
                neighbors = self.graph.get_neighbors(node.id)
                for neighbor in neighbors:
                    # 获取边信息
                    node_edges = self.graph.get_edges(node.id, neighbor.id)
                    edges.extend(node_edges)
                    
                    # 构建关系描述
                    for edge in node_edges:
                        relationships.append({
                            'source': node.name,
                            'target': neighbor.name,
                            'type': edge.edge_type.value,
                            'weight': edge.weight
                        })
            
            # 创建图上下文
            graph_context = GraphContext(
                nodes=nodes,
                edges=edges,
                relationships=relationships,
                statistics=result.metadata or {}
            )
        
            # 生成LLM增强回答
            return self.llm_integration.generate_intelligent_answer(query, graph_context)
        else:
            # 没有图谱信息时，使用通用知识生成回答
            return self.llm_integration.generate_fallback_answer(query)
    
    def _generate_simple_answer(self, query: str, result: QueryResult) -> str:
        """
        生成简单回答（当LLM不可用时）
        
        Args:
            query: 原始查询
            result: 查询结果
            
        Returns:
            简单回答
        """
        if not result.results:
            return "抱歉，没有找到相关信息。"
        
        answer_parts = [f"基于您的查询「{query}」，我找到了以下信息：\n"]
        
        if result.query_type == "pairing":
            answer_parts.append("🔗 食材搭配信息：")
            for i, (ingredient, count) in enumerate(result.results[:5], 1):
                answer_parts.append(f"{i}. {ingredient.name} (共同出现 {count} 次)")
        
        elif result.query_type == "recommendation":
            answer_parts.append("💡 推荐结果：")
            for i, (item, score) in enumerate(result.results[:5], 1):
                answer_parts.append(f"{i}. {item.name} (推荐度: {score:.2f})")
        
        elif result.query_type == "similarity":
            answer_parts.append("🔍 相似菜品：")
            for i, (dish, score) in enumerate(result.results[:5], 1):
                answer_parts.append(f"{i}. {dish.name} (相似度: {score:.2f})")
        
        elif result.query_type == "discovery":
            answer_parts.append("🔍 发现结果：")
            for i, (item, score) in enumerate(result.results[:5], 1):
                if hasattr(item, 'properties') and item.properties.get('type') == 'ingredient_combination':
                    ingredients = item.properties.get('ingredients', [])
                    answer_parts.append(f"{i}. {' + '.join(ingredients)} (共同出现 {score} 次)")
                else:
                    answer_parts.append(f"{i}. {item.name} (相关度: {score})")
        
        else:
            answer_parts.append("📋 查询结果：")
            for i, item in enumerate(result.results[:5], 1):
                if hasattr(item, 'name'):
                    answer_parts.append(f"{i}. {item.name}")
                else:
                    answer_parts.append(f"{i}. {item}")
        
        return "\n".join(answer_parts)
    
    def _process_analysis_query(self, query: str) -> QueryResult:
        """处理分析查询"""
        # 提取要分析的对象名称
        target_name = self._extract_target_from_analysis_query(query)
        
        if not target_name:
            return QueryResult("analysis", [], {"error": "未找到分析对象"})
        
        # 尝试分析不同类型的对象
        analysis_results = []
        
        # 1. 尝试作为食材分析
        ingredient_nodes = self.query_engine.search_nodes(target_name, NodeType.INGREDIENT)
        if ingredient_nodes:
            analysis = self.analyze_ingredient_network(target_name)
            analysis_results.append({
                "type": "ingredient",
                "name": target_name,
                "analysis": analysis
            })
        
        # 2. 尝试作为菜品分析
        dish_nodes = self.query_engine.search_nodes(target_name, NodeType.DISH)
        if dish_nodes:
            dish_analysis = self._analyze_dish_network(target_name)
            analysis_results.append({
                "type": "dish",
                "name": target_name,
                "analysis": dish_analysis
            })
        
        # 3. 尝试作为烹饪方法分析
        method_nodes = self.query_engine.search_nodes(target_name, NodeType.COOKING_METHOD)
        if method_nodes:
            method_analysis = self._analyze_cooking_method_network(target_name)
            analysis_results.append({
                "type": "cooking_method",
                "name": target_name,
                "analysis": method_analysis
            })
        
        return QueryResult("analysis", analysis_results, {
            "target_name": target_name,
            "analysis_count": len(analysis_results)
        })
    
    def _process_general_query(self, query: str) -> QueryResult:
        """处理一般查询"""
        # 尝试搜索所有类型的节点
        all_results = []
        
        for node_type in NodeType:
            nodes = self.query_engine.search_nodes(query, node_type, limit=5)
            all_results.extend(nodes)
        
        return QueryResult("general", all_results, {
            "query_text": query,
            "total_results": len(all_results)
        })
    
    def _extract_target_from_analysis_query(self, query: str) -> Optional[str]:
        """从分析查询中提取目标对象名称"""
        # 移除分析关键词
        analysis_keywords = ['分析', '了解', '介绍', '说明', '一下', '的']
        
        target = query
        for keyword in analysis_keywords:
            target = target.replace(keyword, '').strip()
        
        # 移除常见的停用词
        stop_words = ['一下', '的', '这个', '那个', '什么', '如何', '怎样']
        for word in stop_words:
            target = target.replace(word, '').strip()
        
        return target if target else None
    
    def _analyze_dish_network(self, dish_name: str) -> Dict[str, Any]:
        """分析菜品网络"""
        # 查找菜品节点
        dish_nodes = self.query_engine.search_nodes(dish_name, NodeType.DISH)
        if not dish_nodes:
            return {"error": "未找到菜品"}
        
        analysis = {
            "dish": dish_name,
            "total_ingredients": 0,
            "cooking_methods": [],
            "categories": [],
            "similar_dishes": []
        }
        
        for dish in dish_nodes:
            # 获取菜品的食材
            ingredients = self.graph.get_neighbors(dish.id, EdgeType.CONTAINS)
            analysis["total_ingredients"] += len(ingredients)
            
            # 获取烹饪方法
            methods = self.graph.get_neighbors(dish.id, EdgeType.USES_METHOD)
            analysis["cooking_methods"].extend([method.name for method in methods])
            
            # 获取分类
            categories = self.graph.get_neighbors(dish.id, EdgeType.BELONGS_TO)
            analysis["categories"].extend([cat.name for cat in categories])
            
            # 获取相似菜品
            similar_edges = self.graph.get_edges(dish.id, edge_type=EdgeType.SIMILAR_TO)
            for edge in similar_edges:
                similar_dish = self.graph.get_node(edge.target_id)
                if similar_dish:
                    analysis["similar_dishes"].append((similar_dish.name, edge.weight))
        
        # 去重并排序
        analysis["cooking_methods"] = list(set(analysis["cooking_methods"]))
        analysis["categories"] = list(set(analysis["categories"]))
        analysis["similar_dishes"].sort(key=lambda x: x[1], reverse=True)
        
        return analysis
    
    def _analyze_cooking_method_network(self, method_name: str) -> Dict[str, Any]:
        """分析烹饪方法网络"""
        # 查找烹饪方法节点
        method_nodes = self.query_engine.search_nodes(method_name, NodeType.COOKING_METHOD)
        if not method_nodes:
            return {"error": "未找到烹饪方法"}
        
        analysis = {
            "method": method_name,
            "total_dishes": 0,
            "common_ingredients": [],
            "categories": []
        }
        
        for method in method_nodes:
            # 获取使用该方法的菜品
            dishes = self.graph.get_neighbors(method.id, EdgeType.USES_METHOD)
            analysis["total_dishes"] += len(dishes)
            
            # 统计常用食材
            ingredient_counts = Counter()
            for dish in dishes:
                ingredients = self.graph.get_neighbors(dish.id, EdgeType.CONTAINS)
                for ingredient in ingredients:
                    ingredient_counts[ingredient.name] += 1
            
            # 获取前10个常用食材
            analysis["common_ingredients"] = ingredient_counts.most_common(10)
            
            # 获取分类
            for dish in dishes:
                categories = self.graph.get_neighbors(dish.id, EdgeType.BELONGS_TO)
                analysis["categories"].extend([cat.name for cat in categories])
        
        # 去重
        analysis["categories"] = list(set(analysis["categories"]))
        
        return analysis
    
    def _extract_ingredients_from_query(self, query: str) -> List[str]:
        """从查询中提取食材名称"""
        # 简单的关键词提取
        ingredients = []
        
        # 常见的食材关键词
        ingredient_keywords = [
            '鸡', '鸭', '猪', '牛', '羊', '鱼', '虾', '蟹',
            '白菜', '萝卜', '土豆', '西红柿', '黄瓜', '茄子', '豆角', '青椒', '红椒',
            '洋葱', '蒜', '姜', '葱', '韭菜', '菠菜', '芹菜', '花菜', '西兰花',
            '胡萝卜', '冬瓜', '南瓜', '丝瓜', '苦瓜', '豆芽', '蘑菇', '香菇',
            '金针菇', '木耳', '银耳', '鸡蛋', '鸭蛋', '豆腐', '豆干', '豆皮',
            '米', '面', '面条', '挂面', '意面', '饺子', '包子', '馒头', '饼', '饭', '粥'
        ]
        
        for keyword in ingredient_keywords:
            if keyword in query:
                ingredients.append(keyword)
        
        return ingredients
    
    def _extract_dishes_from_query(self, query: str) -> List[str]:
        """从查询中提取菜品名称"""
        dishes = []
        
        # 常见的菜品关键词
        dish_keywords = [
            '炒', '煮', '蒸', '炸', '烤', '炖', '焖', '煎', '拌', '凉拌',
            '红烧', '清炒', '爆炒', '干煸', '水煮', '清蒸', '糖醋',
            '麻辣', '香辣', '酸辣', '蒜蓉', '蚝油', '白灼', '上汤'
        ]
        
        # 方法1: 查找包含烹饪方法的词汇
        for keyword in dish_keywords:
            if keyword in query:
                # 尝试提取完整的菜品名称
                pattern = rf'(\w*{keyword}\w*)'
                matches = re.findall(pattern, query)
                dishes.extend(matches)
        
        # 方法2: 如果查询中包含"和"或"与"，尝试提取"和"前面的菜品名称
        if '和' in query or '与' in query:
            # 提取"和"前面的部分作为菜品名称
            if '和' in query:
                dish_part = query.split('和')[0].strip()
            else:
                dish_part = query.split('与')[0].strip()
            
            # 移除常见的停用词
            stop_words = ['的', '菜', '菜品', '食物']
            for word in stop_words:
                dish_part = dish_part.replace(word, '').strip()
            
            if dish_part and len(dish_part) > 1:
                dishes.append(dish_part)
        
        # 方法2.5: 如果查询中包含"和...相似的"，尝试提取"和"和"相似"之间的菜品名称
        if '和' in query and '相似' in query:
            # 找到"和"的位置
            he_pos = query.find('和')
            # 找到"相似"的位置
            similar_pos = query.find('相似')
            
            if he_pos < similar_pos:
                # 提取"和"和"相似"之间的部分
                dish_part = query[he_pos+1:similar_pos].strip()
                
                # 移除常见的停用词
                stop_words = ['的', '菜', '菜品', '食物']
                for word in stop_words:
                    dish_part = dish_part.replace(word, '').strip()
                
                if dish_part and len(dish_part) > 1:
                    dishes.append(dish_part)
        
        # 方法3: 如果查询中包含"类似"或"像"，尝试提取后面的菜品名称
        if '类似' in query:
            parts = query.split('类似')
            if len(parts) > 1:
                dish_part = parts[1].strip()
                # 移除常见的停用词
                stop_words = ['的', '菜', '菜品', '食物']
                for word in stop_words:
                    dish_part = dish_part.replace(word, '').strip()
                if dish_part and len(dish_part) > 1:
                    dishes.append(dish_part)
        
        if '像' in query:
            parts = query.split('像')
            if len(parts) > 1:
                dish_part = parts[1].strip()
                # 移除常见的停用词
                stop_words = ['的', '菜', '菜品', '食物']
                for word in stop_words:
                    dish_part = dish_part.replace(word, '').strip()
                if dish_part and len(dish_part) > 1:
                    dishes.append(dish_part)
        
        return dishes
    
    def _extract_cooking_methods_from_query(self, query: str) -> List[str]:
        """从查询中提取烹饪方法"""
        methods = []
        
        cooking_methods = [
            '炒', '煮', '蒸', '炸', '烤', '炖', '焖', '煎', '拌', '凉拌',
            '红烧', '清炒', '爆炒', '干煸', '水煮', '清蒸', '糖醋',
            '麻辣', '香辣', '酸辣', '蒜蓉', '蚝油', '白灼', '上汤', '勾芡'
        ]
        
        for method in cooking_methods:
            if method in query:
                methods.append(method)
        
        return methods
    
    def analyze_ingredient_network(self, ingredient_name: str) -> Dict[str, Any]:
        """分析食材网络"""
        # 查找食材节点
        ingredient_nodes = self.query_engine.search_nodes(ingredient_name, NodeType.INGREDIENT)
        if not ingredient_nodes:
            return {"error": "未找到食材"}
        
        analysis = {
            "ingredient": ingredient_name,
            "total_dishes": 0,
            "common_pairings": [],
            "cooking_methods": [],
            "categories": [],
            "substitution_suggestions": []
        }
        
        for ingredient in ingredient_nodes:
            # 统计包含该食材的菜品数量
            dishes = self.graph.get_neighbors(ingredient.id, EdgeType.CONTAINS)
            analysis["total_dishes"] += len(dishes)
            
            # 获取搭配食材
            pairs = self.query_engine.find_ingredient_pairs(ingredient.name)
            analysis["common_pairings"].extend(pairs[:10])  # 前10个
            
            # 获取烹饪方法
            methods = self.query_engine.find_cooking_methods_for_ingredient(ingredient.name)
            analysis["cooking_methods"].extend(methods[:10])  # 前10个
            
            # 获取分类信息
            if ingredient.properties.get('category'):
                analysis["categories"].append(ingredient.properties['category'])
            
            # 获取替代建议
            substitutions = self.query_engine.get_ingredient_substitution_suggestions(ingredient.name)
            analysis["substitution_suggestions"].extend(substitutions[:5])  # 前5个
        
        # 去重并排序
        analysis["common_pairings"] = list(set(analysis["common_pairings"]))
        analysis["cooking_methods"] = list(set(analysis["cooking_methods"]))
        analysis["categories"] = list(set(analysis["categories"]))
        analysis["substitution_suggestions"] = list(set(analysis["substitution_suggestions"]))
        
        return analysis
    
    def find_recipe_paths(self, start_ingredient: str, end_ingredient: str) -> List[List[GraphNode]]:
        """查找食谱路径"""
        return self.query_engine.find_path_between_ingredients(start_ingredient, end_ingredient)
    
    def get_ingredient_compatibility_matrix(self, ingredients: List[str]) -> Dict[str, Dict[str, float]]:
        """获取食材兼容性矩阵"""
        matrix = {}
        
        for i, ingredient1 in enumerate(ingredients):
            matrix[ingredient1] = {}
            pairs1 = self.query_engine.find_ingredient_pairs(ingredient1)
            pair_dict1 = {pair[0].name: pair[1] for pair in pairs1}
            
            for j, ingredient2 in enumerate(ingredients):
                if i == j:
                    matrix[ingredient1][ingredient2] = 1.0
                else:
                    # 计算兼容性分数
                    compatibility = pair_dict1.get(ingredient2, 0) / 10.0  # 归一化
                    matrix[ingredient1][ingredient2] = min(compatibility, 1.0)
        
        return matrix
