#!/usr/bin/env python3
"""
检查当前知识图谱的实际结构
分析是否需要修改KG来支持DODAF框架
"""

import sys
sys.path.append('.')

def inspect_kg_structure():
    """检查KG的数据结构"""
    print("🔍 检查当前知识图谱结构")
    print("=" * 60)
    
    from src.knowledge.kg_builder import KnowledgeGraphBuilder
    from src.knowledge.kg_retriever import KnowledgeGraphRetriever
    
    # 创建一个示例KG
    kg = KnowledgeGraphBuilder('inspect_kg')
    
    # 添加一些事实
    kg.add_fact('kitchen', 'contains', 'key')
    kg.add_fact('key', 'opens', 'chest')
    kg.add_fact('chest', 'location', 'bedroom')
    kg.add_fact('go north', 'leads to', 'living room')
    kg.add_fact('go east', 'leads to', 'bedroom')
    
    print("📊 KG基本信息:")
    print(f"  总事实数: {len(kg.facts)}")
    print(f"  KG类型: {type(kg)}")
    
    print("\n📋 事实列表:")
    for i, fact in enumerate(kg.facts, 1):
        print(f"  {i}. {fact}")
        print(f"     类型: {type(fact)}")
        if hasattr(fact, 'subject'):
            print(f"     Subject: '{fact.subject}' (类型: {type(fact.subject)})")
            print(f"     Predicate: '{fact.predicate}' (类型: {type(fact.predicate)})")
            print(f"     Object: '{fact.object}' (类型: {type(fact.object)})")
            if hasattr(fact, 'confidence'):
                print(f"     Confidence: {fact.confidence}")
        print()
    
    return kg

def inspect_kg_retrieval():
    """检查KG检索机制"""
    print("🔍 检查KG检索机制")
    print("=" * 60)
    
    from src.knowledge.kg_builder import KnowledgeGraphBuilder
    from src.knowledge.kg_retriever import KnowledgeGraphRetriever
    
    # 创建KG和检索器
    kg = KnowledgeGraphBuilder('retrieval_test')
    kg.add_fact('kitchen', 'contains', 'key')
    kg.add_fact('key', 'opens', 'chest')
    kg.add_fact('chest', 'location', 'bedroom')
    kg.add_fact('bedroom', 'accessible via', 'living room')
    kg.add_fact('living room', 'accessible via', 'kitchen')
    
    retriever = KnowledgeGraphRetriever(kg, 'test_retriever')
    
    print("🔎 测试不同检索方法:")
    
    # 测试关键词检索
    print("\n1. 关键词检索 'kitchen key':")
    keyword_results = retriever.retrieve_by_keywords('kitchen key')
    for result in keyword_results:
        print(f"   - {result.subject} {result.predicate} {result.object}")
    
    # 测试语义检索
    print("\n2. 语义检索 'kitchen key':")
    try:
        semantic_results = retriever.retrieve_by_similarity('kitchen key', max_results=3)
        for result, score in semantic_results:
            print(f"   - {result.subject} {result.predicate} {result.object} (分数: {score:.3f})")
    except Exception as e:
        print(f"   语义检索失败: {e}")
    
    return retriever

def analyze_kg_for_dodaf():
    """分析当前KG是否适合DODAF框架"""
    print("🎯 分析KG对DODAF框架的适配性")
    print("=" * 60)
    
    from src.knowledge.kg_builder import KnowledgeGraphBuilder
    
    # 当前KG结构
    current_kg = KnowledgeGraphBuilder('current_analysis')
    current_kg.add_fact('kitchen', 'contains', 'key')
    current_kg.add_fact('key', 'opens', 'chest')
    current_kg.add_fact('chest', 'location', 'bedroom')
    
    print("📊 当前KG事实分析:")
    for fact in current_kg.facts:
        subj, pred, obj = fact.subject, fact.predicate, fact.object
        print(f"  '{subj}' --{pred}--> '{obj}'")
        
        # 分析DODAF映射
        dodaf_type = "未分类"
        if 'contains' in pred or 'location' in pred:
            dodaf_type = "DA (Condition) - 状态/位置信息"
        elif 'opens' in pred or 'leads to' in pred:
            dodaf_type = "DO (Action) - 动作关系"
        elif 'goal' in subj.lower() or 'target' in subj.lower():
            dodaf_type = "F (Outcome) - 目标结果"
        
        print(f"    → DODAF映射: {dodaf_type}")
    
    print("\n✅ 结论: 当前KG结构分析")
    print("  ✅ 三元组结构 (subject-predicate-object) 完全适合DODAF")
    print("  ✅ 事实类型可以映射到DO-DA-F")
    print("  ✅ 不需要改变KG存储结构")
    print("  ✅ 只需要改变KG信息的'使用方式'")

def show_kg_usage_transformation():
    """展示KG使用方式的转换"""
    print("\n🔄 KG使用方式转换示例")
    print("=" * 60)
    
    # 模拟当前KG事实
    kg_facts = [
        ('kitchen', 'contains', 'key'),
        ('key', 'opens', 'chest'),
        ('chest', 'location', 'bedroom'),
        ('go north', 'leads to', 'living room'),
        ('go east', 'leads to', 'bedroom')
    ]
    
    print("原始KG事实:")
    for subj, pred, obj in kg_facts:
        print(f"  • {subj} {pred} {obj}")
    
    print("\n❌ 当前错误的使用方式 (列表展示):")
    print("Relevant knowledge from your knowledge base:")
    for i, (subj, pred, obj) in enumerate(kg_facts, 1):
        print(f"{i}. {subj} {pred} {obj}")
    
    print("\n✅ DODAF框架的正确使用方式 (决策指导):")
    
    # 将KG事实转换为DODAF决策指导
    def convert_facts_to_dodaf_guidance(facts, current_location="kitchen"):
        guidance = {}
        
        # 分析当前状态 (DA)
        status_info = []
        for subj, pred, obj in facts:
            if current_location in subj and 'contains' in pred:
                status_info.append(f"{obj} available here")
            elif 'location' in pred and obj != current_location:
                status_info.append(f"{subj} in {obj}")
        
        # 分析路径 (DA)
        path_info = []
        for subj, pred, obj in facts:
            if 'leads to' in pred:
                path_info.append(f"{subj}→{obj}")
        
        # 构建指导
        if status_info:
            guidance['status'] = f"Current: {current_location}. " + ". ".join(status_info)
        if path_info:
            guidance['path'] = f"Path: {' → '.join(path_info)}"
        
        return guidance
    
    guidance = convert_facts_to_dodaf_guidance(kg_facts)
    print(f"Status: {guidance.get('status', '')}")
    print(f"Path: {guidance.get('path', '')}")
    
    print("\n💡 关键洞察:")
    print("  ✅ KG结构不需要改变")
    print("  ✅ 只需要改变'信息提取和组织'的方式")
    print("  ✅ 从'事实列表'转换为'决策指导'")

def recommend_kg_strategy():
    """推荐KG使用策略"""
    print("\n📋 推荐的KG使用策略")
    print("=" * 60)
    
    print("🎯 策略1: 保持现有KG结构")
    print("  ✅ 优点: 无需修改现有代码")
    print("  ✅ 优点: 三元组结构灵活通用")
    print("  ✅ 优点: 检索机制已经工作")
    
    print("\n🔄 策略2: 改进信息转换层")
    print("  ✅ 在RAG Agent中添加'KG→DODAF转换器'")
    print("  ✅ 将检索到的事实转换为决策指导")
    print("  ✅ 根据当前情况动态组织信息")
    
    print("\n📝 具体实现建议:")
    print("  1. 保持KG存储格式不变")
    print("  2. 在RAG Agent中添加convert_kg_to_dodaf()方法")
    print("  3. 根据当前观察智能组织KG信息")
    print("  4. 生成简洁的DODAF格式prompt")
    
    print("\n✅ 结论: 不需要改KG，只需要改'使用方式'")

if __name__ == "__main__":
    print("🔍 当前知识图谱结构分析")
    print("评估是否需要修改KG来支持DODAF框架")
    
    kg = inspect_kg_structure()
    retriever = inspect_kg_retrieval()
    analyze_kg_for_dodaf()
    show_kg_usage_transformation()
    recommend_kg_strategy()
    
    print("\n🎉 分析完成!")
    print("结论: 当前KG结构完全适合，只需要改进'使用方式'！")
