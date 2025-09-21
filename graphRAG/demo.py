"""
GraphRAG系统演示脚本
展示各种查询和推荐功能
"""

import sys
from pathlib import Path

# 添加模块路径
sys.path.append(str(Path(__file__).parent))

from main import GraphRAGSystem


def demo_basic_queries():
    """演示基础查询功能"""
    print("=" * 60)
    print("🎯 GraphRAG智能查询功能演示")
    print("=" * 60)
    print("💡 本演示将展示GraphRAG系统的核心查询能力")
    print("💡 支持自然语言查询，理解复杂的烹饪关系")
    
    # 初始化系统
    graph_rag = GraphRAGSystem()
    graph_rag.initialize_system()
    
    # 分类测试查询
    print("\n🥘 食材搭配与推荐演示:")
    pairing_queries = [
        "和鸡肉搭配的食材有哪些",
        "推荐一些用西红柿做的菜",
        "和西红柿炒鸡蛋相似的菜",
        "鸡蛋的替代品有哪些"
    ]
    
    print("\n📊 深度分析演示:")
    analysis_queries = [
        "炒的常用食材有哪些",
        "分析一下鸡蛋"
    ]
    
    # 演示食材搭配与推荐
    for query in pairing_queries:
        print(f"\n🔍 查询: {query}")
        result = graph_rag.process_query(query)
        
        # 显示结果
        results = result["results"]
        if results:
            print(f"✅ 找到 {len(results)} 个结果:")
            for i, item in enumerate(results[:5], 1):
                if hasattr(item, 'name'):
                    print(f"  {i}. {item.name}")
                else:
                    print(f"  {i}. {item}")
        else:
            print("❌ 未找到相关结果")
    
    # 演示深度分析
    for query in analysis_queries:
        print(f"\n🔍 查询: {query}")
        result = graph_rag.process_query(query)
        
        # 显示结果
        results = result["results"]
        if results:
            print(f"✅ 找到 {len(results)} 个结果:")
            for i, item in enumerate(results[:5], 1):
                if hasattr(item, 'name'):
                    print(f"  {i}. {item.name}")
                else:
                    print(f"  {i}. {item}")
        else:
            print("❌ 未找到相关结果")


def demo_recommendation_system():
    """演示推荐系统功能"""
    print("\n" + "=" * 60)
    print("🤖 智能推荐系统演示")
    print("=" * 60)
    print("💡 基于图结构的智能推荐算法，提供个性化建议")
    
    # 初始化系统
    graph_rag = GraphRAGSystem()
    graph_rag.initialize_system()
    
    # 测试食材推荐
    print("\n🥬 场景1: 我有这些食材，能做什么菜？")
    available_ingredients = ["西红柿", "鸡蛋", "葱"]
    print(f"   可用食材: {', '.join(available_ingredients)}")
    recommendations = graph_rag.recommend_dishes(available_ingredients, max_recommendations=5)
    
    print("   推荐菜品:")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec['dish']} (完成度: {rec['completion_rate']:.1%})")
        if rec['missing_ingredients']:
            print(f"      缺少食材: {', '.join(rec['missing_ingredients'][:3])}")
    
    # 测试菜品推荐搭配食材
    print("\n🔗 场景2: 我想做这道菜，还需要什么食材？")
    target_dish = "西红柿炒鸡蛋"
    print(f"   目标菜品: {target_dish}")
    ingredient_recs = graph_rag.recommend_ingredients(target_dish, max_recommendations=5)
    
    print("   推荐搭配食材:")
    for i, rec in enumerate(ingredient_recs, 1):
        print(f"   {i}. {rec['ingredient']} (推荐度: {rec['score']:.2f})")
        print(f"      理由: {rec['reason']}")
    
    # 测试相似菜品推荐
    print("\n🔍 场景3: 我喜欢这道菜，有什么类似的推荐？")
    similar_dish = "西红柿炒鸡蛋"
    print(f"   参考菜品: {similar_dish}")
    similar_dishes = graph_rag.find_similar_dishes("西红柿炒鸡蛋", max_recommendations=5)
    
    for i, rec in enumerate(similar_dishes, 1):
        print(f"  {i}. {rec['dish']} (相似度: {rec['similarity_score']:.2f})")


def demo_ingredient_analysis():
    """演示食材分析功能"""
    print("\n" + "=" * 60)
    print("📊 深度分析功能演示")
    print("=" * 60)
    print("💡 基于图结构的多维度分析，深入了解食材特性")
    
    # 初始化系统
    graph_rag = GraphRAGSystem()
    graph_rag.initialize_system()
    
    # 分析鸡蛋
    print("\n🥚 食材深度分析: '鸡蛋'")
    analysis = graph_rag.get_ingredient_analysis("鸡蛋")
    
    if "error" not in analysis:
        print(f"  📈 使用统计:")
        print(f"    • 出现在 {analysis['total_dishes']} 道菜品中")
        print(f"    • 有 {len(analysis['common_pairings'])} 个常见搭配")
        print(f"    • 适用 {len(analysis['cooking_methods'])} 种烹饪方法")
        print(f"    • 属于分类: {', '.join(analysis['categories'])}")
        
        if analysis['common_pairings']:
            print(f"  🔗 热门搭配食材:")
            for i, (ingredient, count) in enumerate(analysis['common_pairings'][:5], 1):
                print(f"    {i}. {ingredient.name} (共同出现 {count} 次)")
    else:
        print(f"  ❌ 分析失败: {analysis['error']}")


def demo_trending_combinations():
    """演示热门组合发现功能"""
    print("\n" + "=" * 60)
    print("🔍 趋势发现功能演示")
    print("=" * 60)
    print("💡 基于大数据分析，发现流行的食材搭配趋势")
    
    # 初始化系统
    graph_rag = GraphRAGSystem()
    graph_rag.initialize_system()
    
    print("\n🔥 热门食材搭配趋势:")
    print("   基于共现分析，发现最受欢迎的食材组合")
    combinations = graph_rag.discover_trending_combinations(min_cooccurrence=3)
    
    print("   📊 热门搭配排行榜:")
    for i, combo in enumerate(combinations[:10], 1):
        ingredients = combo['ingredients']
        count = combo['cooccurrence_count']
        print(f"   {i:2d}. {' + '.join(ingredients):<20} (共同出现 {count:2d} 次)")
    
    if combinations:
        print(f"\n   💡 共发现 {len(combinations)} 个热门搭配组合")
    else:
        print("   ❌ 未发现符合条件的组合")


def demo_ingredient_pairs():
    """演示食材搭配查询"""
    print("\n" + "=" * 60)
    print("🔗 食材搭配查询演示")
    print("=" * 60)
    
    # 初始化系统
    graph_rag = GraphRAGSystem()
    graph_rag.initialize_system()
    
    # 测试食材搭配
    test_ingredients = ["鸡肉", "西红柿", "鸡蛋", "土豆"]
    
    for ingredient in test_ingredients:
        print(f"\n🥬 '{ingredient}' 的搭配食材:")
        pairs = graph_rag.get_ingredient_pairs(ingredient)
        
        if pairs:
            for i, pair in enumerate(pairs[:5], 1):
                print(f"  {i}. {pair['ingredient']} (共同出现 {pair['cooccurrence_count']} 次)")
        else:
            print("  未找到搭配信息")


def main():
    """主演示函数"""
    print("🍽️  GraphRAG智能食谱知识图谱系统演示  🍽️")
    print("=" * 60)
    print("💡 本演示将全面展示GraphRAG系统的核心功能")
    print("💡 包括智能查询、推荐算法、深度分析和趋势发现")
    print("=" * 60)
    
    try:
        # 运行各种演示
        demo_basic_queries()
        demo_recommendation_system()
        demo_ingredient_analysis()
        demo_trending_combinations()
        demo_ingredient_pairs()
        
        print("\n" + "=" * 60)
        print("🎉 演示完成！")
        print("=" * 60)
        print("💡 接下来您可以:")
        print("   • 运行 'python main.py' 进入交互式查询模式")
        print("   • 尝试各种自然语言查询")
        print("   • 体验基于图结构的智能推荐")
        print("   • 探索食材搭配的奥秘")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
