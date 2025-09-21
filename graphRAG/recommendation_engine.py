"""
基于图的推荐算法
实现多种推荐策略，包括协同过滤、内容推荐、混合推荐等
"""

import math
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict, Counter
from dataclasses import dataclass
import random

from graph_models import RecipeGraph, GraphNode, NodeType, EdgeType
from graph_storage import GraphQueryEngine


@dataclass
class Recommendation:
    """推荐结果"""
    item: GraphNode
    score: float
    reason: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class GraphRecommendationEngine:
    """基于图的推荐引擎"""
    
    def __init__(self, query_engine: GraphQueryEngine):
        self.query_engine = query_engine
        self.graph = query_engine.graph
    
    def recommend_dishes_by_ingredients(self, available_ingredients: List[str], 
                                      max_recommendations: int = 10) -> List[Recommendation]:
        """基于可用食材推荐菜品"""
        recommendations = []
        
        # 获取所有包含这些食材的菜品
        dish_candidates = self.query_engine.find_dishes_by_ingredients(available_ingredients)
        
        for dish, match_count in dish_candidates:
            # 计算推荐分数
            score = self._calculate_ingredient_based_score(dish, available_ingredients, match_count)
            
            # 生成推荐理由
            reason = f"包含 {match_count} 种可用食材"
            
            # 获取菜品详细信息
            dish_ingredients = self.graph.get_neighbors(dish.id, EdgeType.CONTAINS)
            missing_ingredients = []
            for ingredient in dish_ingredients:
                if ingredient.name not in available_ingredients:
                    missing_ingredients.append(ingredient.name)
            
            recommendation = Recommendation(
                item=dish,
                score=score,
                reason=reason,
                metadata={
                    "match_count": match_count,
                    "total_ingredients": len(dish_ingredients),
                    "missing_ingredients": missing_ingredients[:5],  # 只显示前5个
                    "completion_rate": match_count / len(dish_ingredients) if dish_ingredients else 0
                }
            )
            recommendations.append(recommendation)
        
        # 按分数排序并限制数量
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:max_recommendations]
    
    def recommend_ingredients_by_dish(self, dish_name: str, 
                                    max_recommendations: int = 10) -> List[Recommendation]:
        """基于菜品推荐搭配食材"""
        recommendations = []
        
        # 查找菜品节点
        dish_nodes = self.query_engine.search_nodes(dish_name, NodeType.DISH)
        if not dish_nodes:
            return recommendations
        
        for dish in dish_nodes:
            # 获取菜品的食材
            dish_ingredients = self.graph.get_neighbors(dish.id, EdgeType.CONTAINS)
            ingredient_names = [ing.name for ing in dish_ingredients]
            
            # 为每个食材查找搭配食材
            for ingredient in dish_ingredients:
                pairs = self.query_engine.find_ingredient_pairs(ingredient.name)
                
                for pair_ingredient, cooccurrence_count in pairs:
                    # 避免推荐已经在菜品中的食材
                    if pair_ingredient.name not in ingredient_names:
                        score = self._calculate_pairing_score(cooccurrence_count, len(dish_ingredients))
                        
                        reason = f"与 {ingredient.name} 搭配，共同出现在 {cooccurrence_count} 个菜品中"
                        
                        recommendation = Recommendation(
                            item=pair_ingredient,
                            score=score,
                            reason=reason,
                            metadata={
                                "base_ingredient": ingredient.name,
                                "cooccurrence_count": cooccurrence_count,
                                "target_dish": dish_name
                            }
                        )
                        recommendations.append(recommendation)
        
        # 去重并排序
        unique_recommendations = {}
        for rec in recommendations:
            if rec.item.name not in unique_recommendations:
                unique_recommendations[rec.item.name] = rec
            else:
                # 保留分数更高的推荐
                if rec.score > unique_recommendations[rec.item.name].score:
                    unique_recommendations[rec.item.name] = rec
        
        final_recommendations = list(unique_recommendations.values())
        final_recommendations.sort(key=lambda x: x.score, reverse=True)
        return final_recommendations[:max_recommendations]
    
    def recommend_similar_dishes(self, dish_name: str, 
                               max_recommendations: int = 10) -> List[Recommendation]:
        """推荐相似菜品"""
        recommendations = []
        
        # 获取相似菜品
        similar_dishes = self.query_engine.find_similar_dishes(dish_name)
        
        for dish, similarity_score in similar_dishes:
            # 计算推荐分数
            score = self._calculate_similarity_score(similarity_score)
            
            # 生成推荐理由
            reason = f"与 {dish_name} 相似度 {similarity_score:.2f}"
            
            # 获取菜品信息
            dish_ingredients = self.graph.get_neighbors(dish.id, EdgeType.CONTAINS)
            cooking_methods = self.graph.get_neighbors(dish.id, EdgeType.USES_METHOD)
            
            recommendation = Recommendation(
                item=dish,
                score=score,
                reason=reason,
                metadata={
                    "similarity_score": similarity_score,
                    "ingredient_count": len(dish_ingredients),
                    "cooking_methods": [method.name for method in cooking_methods[:3]]
                }
            )
            recommendations.append(recommendation)
        
        return recommendations[:max_recommendations]
    
    def recommend_by_cooking_method(self, cooking_method: str, 
                                  max_recommendations: int = 10) -> List[Recommendation]:
        """基于烹饪方法推荐菜品"""
        recommendations = []
        
        # 查找使用该烹饪方法的食材
        ingredients_for_method = self.query_engine.find_ingredients_by_cooking_method(cooking_method)
        
        # 统计食材使用频率
        ingredient_frequency = Counter()
        for ingredient, count in ingredients_for_method:
            ingredient_frequency[ingredient.name] = count
        
        # 查找包含这些食材的菜品
        all_dishes = set()
        for ingredient, _ in ingredients_for_method:
            dishes = self.graph.get_neighbors(ingredient.id, EdgeType.CONTAINS)
            all_dishes.update(dishes)
        
        # 为每个菜品计算推荐分数
        for dish in all_dishes:
            dish_ingredients = self.graph.get_neighbors(dish.id, EdgeType.CONTAINS)
            
            # 计算该菜品中常用食材的比例
            common_ingredient_count = 0
            for ingredient in dish_ingredients:
                if ingredient.name in ingredient_frequency:
                    common_ingredient_count += 1
            
            if common_ingredient_count > 0:
                score = self._calculate_method_based_score(common_ingredient_count, len(dish_ingredients))
                
                reason = f"包含 {common_ingredient_count} 种适合 {cooking_method} 的食材"
                
                recommendation = Recommendation(
                    item=dish,
                    score=score,
                    reason=reason,
                    metadata={
                        "cooking_method": cooking_method,
                        "common_ingredient_count": common_ingredient_count,
                        "total_ingredients": len(dish_ingredients)
                    }
                )
                recommendations.append(recommendation)
        
        # 排序并限制数量
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:max_recommendations]
    
    def recommend_by_category(self, category: str, 
                            max_recommendations: int = 10) -> List[Recommendation]:
        """基于分类推荐菜品"""
        recommendations = []
        
        # 查找该分类下的所有菜品
        category_nodes = self.query_engine.search_nodes(category, NodeType.CATEGORY)
        if not category_nodes:
            return recommendations
        
        category_node = category_nodes[0]
        dishes = self.graph.get_neighbors(category_node.id, EdgeType.BELONGS_TO)
        
        for dish in dishes:
            # 计算推荐分数（基于菜品的复杂度等）
            score = self._calculate_category_based_score(dish)
            
            reason = f"属于 {category} 分类"
            
            # 获取菜品详细信息
            dish_ingredients = self.graph.get_neighbors(dish.id, EdgeType.CONTAINS)
            cooking_methods = self.graph.get_neighbors(dish.id, EdgeType.USES_METHOD)
            
            recommendation = Recommendation(
                item=dish,
                score=score,
                reason=reason,
                metadata={
                    "category": category,
                    "ingredient_count": len(dish_ingredients),
                    "cooking_methods": [method.name for method in cooking_methods[:3]],
                    "difficulty": dish.properties.get('difficulty', '未知')
                }
            )
            recommendations.append(recommendation)
        
        # 排序并限制数量
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:max_recommendations]
    
    def hybrid_recommend(self, user_preferences: Dict[str, Any], 
                        max_recommendations: int = 10) -> List[Recommendation]:
        """混合推荐算法"""
        all_recommendations = []
        
        # 1. 基于食材的推荐
        if 'available_ingredients' in user_preferences:
            ingredient_recs = self.recommend_dishes_by_ingredients(
                user_preferences['available_ingredients'], max_recommendations
            )
            all_recommendations.extend(ingredient_recs)
        
        # 2. 基于烹饪方法的推荐
        if 'preferred_cooking_methods' in user_preferences:
            for method in user_preferences['preferred_cooking_methods']:
                method_recs = self.recommend_by_cooking_method(method, max_recommendations)
                all_recommendations.extend(method_recs)
        
        # 3. 基于分类的推荐
        if 'preferred_categories' in user_preferences:
            for category in user_preferences['preferred_categories']:
                category_recs = self.recommend_by_category(category, max_recommendations)
                all_recommendations.extend(category_recs)
        
        # 4. 基于历史菜品的推荐
        if 'favorite_dishes' in user_preferences:
            for dish in user_preferences['favorite_dishes']:
                similar_recs = self.recommend_similar_dishes(dish, max_recommendations)
                all_recommendations.extend(similar_recs)
        
        # 合并和重新排序
        return self._merge_recommendations(all_recommendations, max_recommendations)
    
    def recommend_ingredient_substitutions(self, original_ingredient: str, 
                                         max_recommendations: int = 5) -> List[Recommendation]:
        """推荐食材替代品"""
        recommendations = []
        
        # 获取替代建议
        substitutions = self.query_engine.get_ingredient_substitution_suggestions(original_ingredient)
        
        for ingredient, substitution_score in substitutions:
            score = self._calculate_substitution_score(substitution_score)
            
            reason = f"与 {original_ingredient} 搭配相似度 {substitution_score:.2f}"
            
            # 获取替代食材的搭配信息
            pairs = self.query_engine.find_ingredient_pairs(ingredient.name)
            
            recommendation = Recommendation(
                item=ingredient,
                score=score,
                reason=reason,
                metadata={
                    "original_ingredient": original_ingredient,
                    "substitution_score": substitution_score,
                    "common_pairings": [pair[0].name for pair in pairs[:5]]
                }
            )
            recommendations.append(recommendation)
        
        return recommendations[:max_recommendations]
    
    def discover_trending_combinations(self, min_cooccurrence: int = 3) -> List[Tuple[List[str], int]]:
        """发现热门食材组合"""
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
    
    def _calculate_ingredient_based_score(self, dish: GraphNode, available_ingredients: List[str], 
                                        match_count: int) -> float:
        """计算基于食材的推荐分数"""
        dish_ingredients = self.graph.get_neighbors(dish.id, EdgeType.CONTAINS)
        total_ingredients = len(dish_ingredients)
        
        if total_ingredients == 0:
            return 0.0
        
        # 基础分数：匹配比例
        base_score = match_count / total_ingredients
        
        # 复杂度调整：食材数量适中得分更高
        complexity_factor = 1.0
        if 3 <= total_ingredients <= 8:
            complexity_factor = 1.2
        elif total_ingredients > 10:
            complexity_factor = 0.8
        
        return base_score * complexity_factor
    
    def _calculate_pairing_score(self, cooccurrence_count: int, total_ingredients: int) -> float:
        """计算搭配分数"""
        # 基于共现频率的对数分数
        log_score = math.log(cooccurrence_count + 1)
        
        # 归一化到0-1范围
        normalized_score = min(log_score / 5.0, 1.0)
        
        return normalized_score
    
    def _calculate_similarity_score(self, similarity: float) -> float:
        """计算相似性分数"""
        return similarity
    
    def _calculate_method_based_score(self, common_ingredient_count: int, total_ingredients: int) -> float:
        """计算基于烹饪方法的分数"""
        if total_ingredients == 0:
            return 0.0
        
        return common_ingredient_count / total_ingredients
    
    def _calculate_category_based_score(self, dish: GraphNode) -> float:
        """计算基于分类的分数"""
        # 基于菜品复杂度评分
        ingredients = self.graph.get_neighbors(dish.id, EdgeType.CONTAINS)
        methods = self.graph.get_neighbors(dish.id, EdgeType.USES_METHOD)
        
        # 适中的复杂度得分更高
        complexity = len(ingredients) + len(methods)
        if 4 <= complexity <= 10:
            return 1.0
        elif complexity < 4:
            return 0.8
        else:
            return 0.6
    
    def _calculate_substitution_score(self, substitution_score: float) -> float:
        """计算替代分数"""
        return substitution_score
    
    def _merge_recommendations(self, recommendations: List[Recommendation], 
                             max_recommendations: int) -> List[Recommendation]:
        """合并推荐结果"""
        # 按菜品名称去重，保留最高分数
        unique_recommendations = {}
        for rec in recommendations:
            if rec.item.name not in unique_recommendations:
                unique_recommendations[rec.item.name] = rec
            else:
                if rec.score > unique_recommendations[rec.item.name].score:
                    unique_recommendations[rec.item.name] = rec
        
        # 排序并返回
        final_recommendations = list(unique_recommendations.values())
        final_recommendations.sort(key=lambda x: x.score, reverse=True)
        return final_recommendations[:max_recommendations]
