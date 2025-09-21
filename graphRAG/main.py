"""
GraphRAG主程序
基于图结构的食谱知识图谱系统
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# 添加模块路径
sys.path.append(str(Path(__file__).parent))

from graph_models import RecipeGraph, NodeType, EdgeType
from graph_builder import RecipeGraphBuilder
from graph_storage import GraphStorage, GraphQueryEngine
from complex_queries import ComplexQueryProcessor
from recommendation_engine import GraphRecommendationEngine
from llm_integration import GraphLLMIntegration
from config import GraphRAGConfig, DEFAULT_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GraphRAGSystem:
    """基于图结构的RAG系统"""
    
    def __init__(self, config: GraphRAGConfig = None):
        """
        初始化GraphRAG系统
        
        Args:
            config: 系统配置
        """
        self.config = config or DEFAULT_CONFIG
        self.data_path = Path(self.config.data_path)
        self.storage_dir = self.config.storage_dir
        
        # 初始化组件
        self.graph: Optional[RecipeGraph] = None
        self.storage: Optional[GraphStorage] = None
        self.query_engine: Optional[GraphQueryEngine] = None
        self.query_processor: Optional[ComplexQueryProcessor] = None
        self.recommendation_engine: Optional[GraphRecommendationEngine] = None
        self.llm_integration: Optional[GraphLLMIntegration] = None
        
        # 检查数据路径
        if not self.data_path.exists():
            raise FileNotFoundError(f"数据路径不存在: {self.data_path}")
        
        # 检查API密钥（如果启用LLM）
        if self.config.enable_llm and not os.getenv("MOONSHOT_API_KEY"):
            raise ValueError("请设置 MOONSHOT_API_KEY 环境变量")
    
    def initialize_system(self, rebuild_graph: bool = False):
        """初始化系统"""
        print("🚀 正在初始化GraphRAG系统...")
        
        # 初始化存储管理器
        self.storage = GraphStorage(self.storage_dir)
        
        # 尝试加载已保存的图
        if not rebuild_graph:
            self.graph = self.storage.load_graph()
        
        if self.graph is None:
            print("未找到已保存的图谱，开始构建新图谱...")
            self._build_graph()
        else:
            print("✅ 成功加载已保存的图谱！")
        
        # 初始化查询引擎
        self.query_engine = GraphQueryEngine(self.graph, self.storage)
        
        # 初始化推荐引擎
        self.recommendation_engine = GraphRecommendationEngine(self.query_engine)
        
        # 初始化LLM集成（如果启用）
        if self.config.enable_llm:
            print("🤖 初始化LLM集成...")
            self.llm_integration = GraphLLMIntegration(
                model_name=self.config.llm_model,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens
            )
        else:
            print("⚠️ LLM功能已禁用")
            self.llm_integration = None
        
        # 初始化复杂查询处理器
        self.query_processor = ComplexQueryProcessor(
            self.query_engine, 
            self.recommendation_engine,
            self.llm_integration
        )
        
        print("✅ GraphRAG系统初始化完成！")
        self._show_statistics()
    
    def _build_graph(self):
        """构建知识图谱"""
        print("开始构建知识图谱...")
        
        # 创建图构建器
        builder = RecipeGraphBuilder(self.data_path)
        
        # 构建图谱
        self.graph = builder.build_graph()
        
        # 保存图谱
        self.storage.save_graph(self.graph)
        
        print("✅ 知识图谱构建完成！")
    
    def _show_statistics(self):
        """显示系统统计信息"""
        if not self.graph:
            return
        
        stats = self.graph.get_statistics()
        print(f"\n📊 知识图谱统计:")
        print(f"   总节点数: {stats['total_nodes']}")
        print(f"   总边数: {stats['total_edges']}")
        print(f"\n   节点类型分布:")
        for node_type, count in stats['nodes_by_type'].items():
            print(f"     {node_type}: {count}")
        print(f"\n   边类型分布:")
        for edge_type, count in stats['edges_by_type'].items():
            print(f"     {edge_type}: {count}")
    
    def process_query(self, query: str, use_llm: bool = None) -> Dict[str, Any]:
        """
        处理用户查询
        
        Args:
            query: 用户查询
            use_llm: 是否使用LLM增强（None表示使用配置中的设置）
            
        Returns:
            查询结果
        """
        if not self.query_processor:
            raise ValueError("系统未初始化")
        
        print(f"\n❓ 用户查询: {query}")
        
        # 使用复杂查询处理器处理查询
        result = self.query_processor.process_natural_language_query(query)
        
        # 生成回答
        if use_llm is None:
            use_llm = self.config.enable_llm and self.llm_integration is not None
        
        if use_llm and self.llm_integration:
            print("🤖 使用LLM生成智能回答...")
            answer = self.query_processor.generate_llm_enhanced_answer(query, result)
        else:
            answer = self.query_processor._generate_simple_answer(query, result)
        
        return {
            "query": query,
            "query_type": result.query_type,
            "results": result.results,
            "metadata": result.metadata,
            "answer": answer,
            "llm_enhanced": use_llm
        }
    
    def get_ingredient_pairs(self, ingredient_name: str) -> List[Dict[str, Any]]:
        """获取食材搭配"""
        if not self.query_engine:
            raise ValueError("系统未初始化")
        
        pairs = self.query_engine.find_ingredient_pairs(ingredient_name)
        
        return [
            {
                "ingredient": pair[0].name,
                "cooccurrence_count": pair[1],
                "category": pair[0].properties.get('category', '未知')
            }
            for pair in pairs
        ]
    
    def recommend_dishes(self, available_ingredients: List[str], 
                        max_recommendations: int = 10) -> List[Dict[str, Any]]:
        """推荐菜品"""
        if not self.recommendation_engine:
            raise ValueError("系统未初始化")
        
        recommendations = self.recommendation_engine.recommend_dishes_by_ingredients(
            available_ingredients, max_recommendations
        )
        
        return [
            {
                "dish": rec.item.name,
                "score": rec.score,
                "reason": rec.reason,
                "completion_rate": rec.metadata.get('completion_rate', 0),
                "missing_ingredients": rec.metadata.get('missing_ingredients', [])
            }
            for rec in recommendations
        ]
    
    def recommend_ingredients(self, dish_name: str, 
                            max_recommendations: int = 10) -> List[Dict[str, Any]]:
        """推荐搭配食材"""
        if not self.recommendation_engine:
            raise ValueError("系统未初始化")
        
        recommendations = self.recommendation_engine.recommend_ingredients_by_dish(
            dish_name, max_recommendations
        )
        
        return [
            {
                "ingredient": rec.item.name,
                "score": rec.score,
                "reason": rec.reason,
                "base_ingredient": rec.metadata.get('base_ingredient', ''),
                "cooccurrence_count": rec.metadata.get('cooccurrence_count', 0)
            }
            for rec in recommendations
        ]
    
    def find_similar_dishes(self, dish_name: str, 
                          max_recommendations: int = 5) -> List[Dict[str, Any]]:
        """查找相似菜品"""
        if not self.recommendation_engine:
            raise ValueError("系统未初始化")
        
        recommendations = self.recommendation_engine.recommend_similar_dishes(
            dish_name, max_recommendations
        )
        
        return [
            {
                "dish": rec.item.name,
                "similarity_score": rec.score,
                "reason": rec.reason,
                "ingredient_count": rec.metadata.get('ingredient_count', 0),
                "cooking_methods": rec.metadata.get('cooking_methods', [])
            }
            for rec in recommendations
        ]
    
    def get_ingredient_analysis(self, ingredient_name: str) -> Dict[str, Any]:
        """获取食材分析"""
        if not self.query_processor:
            raise ValueError("系统未初始化")
        
        return self.query_processor.analyze_ingredient_network(ingredient_name)
    
    def discover_trending_combinations(self, min_cooccurrence: int = 3) -> List[Dict[str, Any]]:
        """发现热门食材组合"""
        if not self.recommendation_engine:
            raise ValueError("系统未初始化")
        
        combinations = self.recommendation_engine.discover_trending_combinations(min_cooccurrence)
        
        return [
            {
                "ingredients": combination[0],
                "cooccurrence_count": combination[1]
            }
            for combination in combinations
        ]
    
    def run_interactive(self):
        """运行交互式查询"""
        print("=" * 60)
        print("🍽️  GraphRAG食谱知识图谱系统  🍽️")
        print("=" * 60)
        print("💡 基于图结构的智能食谱推荐和查询系统")
        print("💡 支持复杂关系查询、食材搭配分析、智能推荐等功能")
        
        # 初始化系统
        self.initialize_system()
        
        print("\n🎯 智能查询功能:")
        print("=" * 50)
        
        print("🥘 食材搭配与推荐:")
        print("  • 食材搭配: '和鸡肉搭配的食材有哪些'")
        print("  • 菜品推荐: '推荐一些用西红柿做的菜'")
        print("  • 相似菜品: '和西红柿炒鸡蛋相似的菜'")
        print("  • 替代建议: '鸡蛋的替代品有哪些'")
        
        print("\n📊 深度分析:")
        print("  • 食材分析: '分析一下鸡蛋' / '了解西红柿'")
        print("  • 菜品分析: '分析一下西红柿炒鸡蛋'")
        print("  • 烹饪方法: '炒的常用食材有哪些' / '分析一下炒'")
        
        print("\n🔍 发现与趋势:")
        print("  • 热门组合: '发现热门食材组合' / '热门食材搭配'")
        print("  • 流行趋势: '流行食材组合' / '食材搭配趋势'")
        
        print("\n💡 使用提示:")
        print("  • 支持自然语言查询，直接说出你的需求")
        print("  • 可以询问食材、菜品、烹饪方法的相关信息")
        print("  • 系统会基于知识图谱提供智能回答")
        if self.config.enable_llm and self.llm_integration:
            print("  • 🤖 已启用AI智能回答，提供更详细的解释和建议")
        else:
            print("  • 💡 当前为基础模式，如需AI增强请配置LLM")
        
        print("\n交互式查询 (输入'退出'结束):")
        
        while True:
            try:
                user_input = input("\n您的问题: ").strip()
                if user_input.lower() in ['退出', 'quit', 'exit', '']:
                    break
                
                # 处理查询
                result = self.process_query(user_input)
                
                # 显示结果
                self._display_query_result(result)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"处理查询时出错: {e}")
                logger.error(f"查询处理错误: {e}")
        
        print("\n感谢使用GraphRAG食谱知识图谱系统！")
    
    def _display_query_result(self, result: Dict[str, Any]):
        """显示查询结果"""
        query_type = result["query_type"]
        results = result["results"]
        metadata = result["metadata"]
        answer = result.get("answer", "")
        llm_enhanced = result.get("llm_enhanced", False)
        
        print(f"\n🎯 查询类型: {query_type}")
        
        # 显示是否找到相关结果
        if results:
            print(f"✅ 找到 {len(results)} 个相关结果")
        else:
            print("❌ 未找到相关结果")
        
        # 显示LLM增强的回答（无论是否有图谱信息）
        if answer:
            print("\n{} 智能回答:".format("AI" if llm_enhanced else "系统"))
            print("{}".format(answer))
        
        # 如果有图谱结果，也显示出来
        if results:
            print("\n图谱查询结果:")
        else:
            return

        if query_type == "pairing":
            print(f"🔗 找到 {len(results)} 个搭配食材:")
            for i, (ingredient, count) in enumerate(results[:10], 1):
                print(f"   {i}. {ingredient.name} (共同出现 {count} 次)")
        
        elif query_type == "recommendation":
            print(f"💡 推荐 {len(results)} 个菜品:")
            for i, (item, score) in enumerate(results[:10], 1):
                print(f"   {i}. {item.name} (推荐度: {score:.2f})")
        
        elif query_type == "similarity":
            print(f"🔍 找到 {len(results)} 个相似菜品:")
            for i, (dish, score) in enumerate(results[:10], 1):
                print(f"   {i}. {dish.name} (相似度: {score:.2f})")
        
        elif query_type == "substitution":
            print(f"🔄 找到 {len(results)} 个替代建议:")
            for i, (ingredient, score) in enumerate(results[:10], 1):
                print(f"   {i}. {ingredient.name} (替代度: {score:.2f})")
        
        elif query_type == "cooking_method":
            print(f"👨‍🍳 找到 {len(results)} 个相关结果:")
            for i, (item, count) in enumerate(results[:10], 1):
                print(f"   {i}. {item.name} (使用次数: {count})")
        
        elif query_type == "ingredient":
            print(f"🥬 找到 {len(results)} 个食材:")
            for i, (ingredient, count) in enumerate(results[:10], 1):
                print(f"   {i}. {ingredient.name} (出现次数: {count})")
        
        elif query_type == "discovery":
            print(f"🔍 发现结果:")
            for i, (item, score) in enumerate(results, 1):
                if hasattr(item, 'properties') and item.properties.get('type') == 'ingredient_combination':
                    ingredients = item.properties.get('ingredients', [])
                    print(f"   {i}. {' + '.join(ingredients)} (共同出现 {score} 次)")
                else:
                    print(f"   {i}. {item.name} (相关度: {score})")
        
        elif query_type == "analysis":
            print(f"📊 分析结果:")
            for i, analysis_item in enumerate(results, 1):
                analysis_type = analysis_item["type"]
                name = analysis_item["name"]
                analysis_data = analysis_item["analysis"]
                
                print(f"\n   {i}. {name} ({analysis_type}):")
                
                if analysis_type == "ingredient":
                    if "error" not in analysis_data:
                        print(f"     总菜品数: {analysis_data.get('total_dishes', 0)}")
                        print(f"     常见搭配: {len(analysis_data.get('common_pairings', []))} 个")
                        print(f"     烹饪方法: {len(analysis_data.get('cooking_methods', []))} 种")
                        print(f"     分类: {', '.join(analysis_data.get('categories', []))}")
                        
                        if analysis_data.get('common_pairings'):
                            print("     热门搭配:")
                            for j, (ingredient, count) in enumerate(analysis_data['common_pairings'][:5], 1):
                                print(f"       {j}. {ingredient.name} (共同出现 {count} 次)")
                    else:
                        print(f"     {analysis_data['error']}")
                
                elif analysis_type == "dish":
                    if "error" not in analysis_data:
                        print(f"     食材数量: {analysis_data.get('total_ingredients', 0)}")
                        print(f"     烹饪方法: {', '.join(analysis_data.get('cooking_methods', []))}")
                        print(f"     分类: {', '.join(analysis_data.get('categories', []))}")
                        
                        if analysis_data.get('similar_dishes'):
                            print("     相似菜品:")
                            for j, (dish_name, similarity) in enumerate(analysis_data['similar_dishes'][:3], 1):
                                print(f"       {j}. {dish_name} (相似度: {similarity:.2f})")
                    else:
                        print(f"     {analysis_data['error']}")
                
                elif analysis_type == "cooking_method":
                    if "error" not in analysis_data:
                        print(f"     使用菜品数: {analysis_data.get('total_dishes', 0)}")
                        print(f"     常用食材: {len(analysis_data.get('common_ingredients', []))} 种")
                        print(f"     适用分类: {', '.join(analysis_data.get('categories', []))}")
                        
                        if analysis_data.get('common_ingredients'):
                            print("     常用食材:")
                            for j, (ingredient, count) in enumerate(analysis_data['common_ingredients'][:5], 1):
                                print(f"       {j}. {ingredient} (使用 {count} 次)")
                    else:
                        print(f"     {analysis_data['error']}")
        
        else:
            print(f"📋 找到 {len(results)} 个结果:")
            for i, item in enumerate(results[:10], 1):
                if hasattr(item, 'name'):
                    print(f"   {i}. {item.name} ({item.node_type.value})")
                else:
                    print(f"   {i}. {item}")
        
        # 显示LLM增强的回答
        if answer:
            print(f"\n{'🤖' if llm_enhanced else '💡'} 智能回答:")
            print(f"{answer}")


def main():
    """主函数"""
    try:
        # 创建配置
        config = GraphRAGConfig()
        
        # 创建GraphRAG系统
        graph_rag = GraphRAGSystem(config)
        
        # 运行交互式查询
        graph_rag.run_interactive()
        
    except Exception as e:
        logger.error(f"系统运行出错: {e}")
        print(f"系统错误: {e}")


if __name__ == "__main__":
    main()
