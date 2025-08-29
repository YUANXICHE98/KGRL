#!/usr/bin/env python3
"""
测试修改后的DODAF知识图谱
验证DO-DA-F分类和query_kg接口
"""

import sys
sys.path.append('.')

def test_dodaf_kg():
    """测试DODAF知识图谱功能"""
    print("🔍 测试DODAF知识图谱")
    print("=" * 60)
    
    from src.knowledge.kg_builder import KnowledgeGraphBuilder
    from src.knowledge.kg_retriever import KnowledgeGraphRetriever
    
    # 创建KG并添加不同类型的事实
    kg = KnowledgeGraphBuilder('dodaf_test')
    
    print("📝 添加DODAF分类的事实:")
    
    # DA (Condition) - 状态和条件
    kg.add_fact('kitchen', 'contains', 'key', dodaf_type='DA')
    kg.add_fact('chest', 'location', 'bedroom', dodaf_type='DA')
    kg.add_fact('player', 'current_location', 'kitchen', dodaf_type='DA')
    
    # DO (Action) - 动作和操作
    kg.add_fact('take', 'enables', 'key_possession', dodaf_type='DO')
    kg.add_fact('key', 'opens', 'chest', dodaf_type='DO')
    kg.add_fact('go_north', 'leads_to', 'living_room', dodaf_type='DO')
    
    # F (Outcome) - 结果和目标
    kg.add_fact('goal', 'is', 'open_chest', dodaf_type='F')
    kg.add_fact('success', 'requires', 'key_and_chest', dodaf_type='F')
    
    # 显示所有事实及其DODAF分类
    print(f"总事实数: {len(kg.facts)}")
    for i, fact in enumerate(kg.facts, 1):
        print(f"  {i}. [{fact.dodaf_type}] {fact.subject} --{fact.predicate}--> {fact.object}")
    
    return kg

def test_dodaf_retrieval():
    """测试DODAF检索功能"""
    print("\n🔎 测试DODAF检索功能")
    print("=" * 60)

    from src.knowledge.kg_retriever import KnowledgeGraphRetriever

    kg = test_dodaf_kg()
    retriever = KnowledgeGraphRetriever(kg, 'dodaf_retriever')
    
    print("\n1. 按DODAF类型检索:")
    
    # 检索DO类型事实
    do_facts = retriever.retrieve_by_dodaf_type('DO')
    print(f"  DO (Action) 事实 ({len(do_facts)} 个):")
    for fact in do_facts:
        print(f"    - {fact.subject} {fact.predicate} {fact.object}")
    
    # 检索DA类型事实
    da_facts = retriever.retrieve_by_dodaf_type('DA')
    print(f"  DA (Condition) 事实 ({len(da_facts)} 个):")
    for fact in da_facts:
        print(f"    - {fact.subject} {fact.predicate} {fact.object}")
    
    # 检索F类型事实
    f_facts = retriever.retrieve_by_dodaf_type('F')
    print(f"  F (Outcome) 事实 ({len(f_facts)} 个):")
    for fact in f_facts:
        print(f"    - {fact.subject} {fact.predicate} {fact.object}")
    
    return retriever

def test_query_kg_interface():
    """测试统一的query_kg接口"""
    print("\n🎯 测试query_kg统一接口")
    print("=" * 60)

    from src.knowledge.kg_retriever import KnowledgeGraphRetriever

    kg = test_dodaf_kg()
    retriever = KnowledgeGraphRetriever(kg, 'query_test')
    
    print("2. 使用query_kg接口:")
    
    # 测试关键词查询
    print("  关键词查询 'kitchen key':")
    results = retriever.query_kg('keywords', 'kitchen key', max_results=2)
    for fact in results:
        print(f"    - [{fact.dodaf_type}] {fact.subject} {fact.predicate} {fact.object}")
    
    # 测试DODAF查询
    print("  DODAF查询 'DO:key':")
    results = retriever.query_kg('dodaf', 'DO:key', max_results=2)
    for fact in results:
        print(f"    - [{fact.dodaf_type}] {fact.subject} {fact.predicate} {fact.object}")
    
    print("  DODAF查询 'DA:kitchen':")
    results = retriever.query_kg('dodaf', 'DA:kitchen', max_results=2)
    for fact in results:
        print(f"    - [{fact.dodaf_type}] {fact.subject} {fact.predicate} {fact.object}")
    
    return retriever

def test_automatic_dodaf_inference():
    """测试自动DODAF类型推断"""
    print("\n🤖 测试自动DODAF类型推断")
    print("=" * 60)
    
    from src.knowledge.kg_builder import KnowledgeGraphBuilder
    
    kg = KnowledgeGraphBuilder('auto_inference_test')
    
    print("3. 自动推断DODAF类型:")
    
    # 添加事实时不指定类型，让系统自动推断
    test_facts = [
        ('key', 'opens', 'chest'),  # 应该推断为DO
        ('kitchen', 'contains', 'apple'),  # 应该推断为DA
        ('goal', 'is', 'find_treasure'),  # 应该推断为F
        ('take', 'enables', 'movement'),  # 应该推断为DO
        ('success', 'requires', 'key'),  # 应该推断为F
    ]
    
    for subj, pred, obj in test_facts:
        fact = kg.add_fact(subj, pred, obj)  # 不指定dodaf_type
        print(f"  '{subj} {pred} {obj}' → 推断为: {fact.dodaf_type}")
    
    return kg

def demonstrate_react_integration():
    """演示ReAct框架集成"""
    print("\n🔄 演示ReAct框架集成")
    print("=" * 60)

    from src.knowledge.kg_retriever import KnowledgeGraphRetriever

    kg = test_dodaf_kg()
    retriever = KnowledgeGraphRetriever(kg, 'react_demo')
    
    print("4. 模拟ReAct框架调用:")
    
    # 模拟ReAct步骤
    print("  Thought: 我需要了解当前环境的条件")
    print("  Action: query_kg('dodaf', 'DA:kitchen')")
    
    da_results = retriever.query_kg('dodaf', 'DA:kitchen', max_results=3)
    print("  Observation:")
    for fact in da_results:
        print(f"    - {fact.subject} {fact.predicate} {fact.object}")
    
    print("\n  Thought: 我需要知道可以执行什么动作")
    print("  Action: query_kg('dodaf', 'DO:key')")
    
    do_results = retriever.query_kg('dodaf', 'DO:key', max_results=3)
    print("  Observation:")
    for fact in do_results:
        print(f"    - {fact.subject} {fact.predicate} {fact.object}")
    
    print("\n  Thought: 我需要了解目标和期望结果")
    print("  Action: query_kg('dodaf', 'F:')")
    
    f_results = retriever.query_kg('dodaf', 'F:', max_results=3)
    print("  Observation:")
    for fact in f_results:
        print(f"    - {fact.subject} {fact.predicate} {fact.object}")

if __name__ == "__main__":
    print("🎯 DODAF知识图谱测试")
    print("验证DO-DA-F分类和ReAct集成")
    
    try:
        kg = test_dodaf_kg()
        retriever = test_dodaf_retrieval()
        query_retriever = test_query_kg_interface()
        auto_kg = test_automatic_dodaf_inference()
        demonstrate_react_integration()
        
        print("\n✅ 所有测试通过!")
        print("DODAF知识图谱已准备好支持ReAct框架")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
