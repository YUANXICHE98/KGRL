#!/usr/bin/env python3
"""
深度调试RAG Agent
打印所有中间步骤，找出失败原因
"""

import sys
sys.path.append('.')

def debug_rag_step_by_step():
    print("🔍 RAG Agent 深度调试")
    print("=" * 60)
    
    # 1. 创建知识图谱
    from src.knowledge.kg_builder import KnowledgeGraphBuilder
    from src.knowledge.kg_retriever import KnowledgeGraphRetriever
    
    kg = KnowledgeGraphBuilder('debug_kg')
    kg.add_fact('kitchen', 'contains', 'key')
    kg.add_fact('key', 'opens', 'chest')
    kg.add_fact('chest', 'location', 'bedroom')
    kg.add_fact('bedroom', 'entrance', 'from living room')
    kg.add_fact('goal', 'is', 'find key and open chest')
    
    retriever = KnowledgeGraphRetriever(kg, 'debug_retriever')
    print(f"📚 知识图谱创建: {len(kg.facts)} 个事实")
    for fact in kg.facts:
        print(f"   - {fact.subject} {fact.predicate} {fact.object}")
    
    # 2. 创建环境
    from src.environments.textworld_env import TextWorldEnvironment
    env = TextWorldEnvironment('debug_env', {'difficulty': 'easy'})
    observation = env.reset()
    available_actions = env.get_available_actions()
    
    print(f"\n🌍 环境状态:")
    print(f"   观察: {observation}")
    print(f"   可用动作: {available_actions}")
    
    # 3. 创建RAG Agent
    from src.agents.rag_agent import RAGAgent
    rag_agent = RAGAgent('debug_rag', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'use_knowledge_graph': True,
        'use_react_reasoning': True,
        'temperature': 0.7,
        'max_tokens': 200,
        'max_kg_facts': 3
    })
    rag_agent.set_knowledge_retriever(retriever)
    
    print(f"\n🤖 RAG Agent配置:")
    print(f"   模型: {rag_agent.model_name}")
    print(f"   使用KG: {rag_agent.use_knowledge_graph}")
    print(f"   使用ReAct: {rag_agent.use_react_reasoning}")
    print(f"   最大KG事实: {rag_agent.max_kg_facts}")
    
    # 4. 调试知识检索过程
    print(f"\n🔍 调试知识检索过程:")
    
    # 4.1 提取关键词
    keywords = rag_agent._extract_keywords(observation)
    print(f"   提取的关键词: '{keywords}'")
    
    # 4.2 执行检索
    print(f"   执行知识检索...")
    knowledge_facts = rag_agent.retrieve_knowledge(keywords)
    print(f"   检索结果: {len(knowledge_facts)} 个事实")
    for i, fact in enumerate(knowledge_facts):
        print(f"     {i+1}. {fact}")
    
    # 4.3 检查检索器直接调用
    print(f"\n   直接调用检索器测试:")
    try:
        if rag_agent.kg_retrieval_method == 'semantic':
            direct_results = retriever.retrieve_by_similarity(keywords, max_results=3)
            print(f"     语义检索结果: {len(direct_results)} 个")
            for fact, score in direct_results:
                print(f"       - {fact.subject} {fact.predicate} {fact.object} (分数: {score:.3f})")
        else:
            direct_results = retriever.retrieve_by_keywords(keywords)
            print(f"     关键词检索结果: {len(direct_results)} 个")
            for fact in direct_results:
                print(f"       - {fact.subject} {fact.predicate} {fact.object}")
    except Exception as e:
        print(f"     ❌ 直接检索失败: {e}")
    
    # 5. 调试Prompt构建
    print(f"\n📝 调试Prompt构建:")
    prompt = rag_agent.build_enhanced_prompt(observation, available_actions, knowledge_facts)
    print(f"   Prompt长度: {len(prompt)} 字符")
    print(f"   Prompt内容:")
    print("   " + "="*50)
    print("   " + prompt.replace('\n', '\n   '))
    print("   " + "="*50)
    
    # 6. 模拟LLM响应解析
    print(f"\n🧠 测试ReAct响应解析:")
    
    # 模拟一个典型的ReAct响应
    mock_response = """THOUGHT: I need to find the key first. I can see there's a key in the kitchen according to my knowledge.
ACTION: take key
REASON: Taking the key is the first step towards opening the chest in the bedroom."""
    
    thought, action, reason = rag_agent.parse_react_response(mock_response)
    print(f"   模拟响应解析:")
    print(f"     THOUGHT: {thought}")
    print(f"     ACTION: {action}")
    print(f"     REASON: {reason}")
    
    # 7. 检查动作验证
    print(f"\n✅ 动作验证测试:")
    test_action = "take key"
    is_valid = test_action in available_actions
    print(f"   测试动作: '{test_action}'")
    print(f"   是否有效: {is_valid}")
    print(f"   可用动作: {available_actions}")
    
    # 8. 完整决策过程测试（不调用真实API）
    print(f"\n🎯 完整决策过程测试:")
    print(f"   注意: 这里不会调用真实API，只测试到prompt构建")
    
    try:
        # 重置统计
        rag_agent.reset()
        
        # 模拟act方法的前半部分
        start_time = time.time()
        
        # 1. 知识检索
        query_keywords = rag_agent._extract_keywords(observation)
        knowledge_facts = rag_agent.retrieve_knowledge(query_keywords)
        
        # 2. 构建prompt
        prompt = rag_agent.build_enhanced_prompt(observation, available_actions, knowledge_facts)
        
        print(f"   ✅ 知识检索: {len(knowledge_facts)} 个事实")
        print(f"   ✅ Prompt构建: {len(prompt)} 字符")
        print(f"   ✅ KG统计: 查询={rag_agent.kg_queries}, 命中={rag_agent.kg_hits}")
        
        if rag_agent.kg_queries > 0:
            hit_rate = rag_agent.kg_hits / rag_agent.kg_queries
            print(f"   ✅ KG命中率: {hit_rate:.2%}")
        
    except Exception as e:
        print(f"   ❌ 决策过程失败: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 RAG Agent调试完成!")
    return True

def compare_with_baseline():
    """对比Baseline Agent的prompt"""
    print(f"\n📊 与Baseline Agent对比:")
    print("=" * 60)
    
    from src.agents.baseline_agent import BaselineAgent
    
    baseline_agent = BaselineAgent('debug_baseline', {
        'model_name': 'gpt-4o',
        'temperature': 0.7,
        'max_tokens': 100
    })
    
    observation = "You are in a kitchen. There is a key here. Goal: Find the key and open the chest in the bedroom."
    available_actions = ['take key', 'go north', 'look', 'inventory']
    
    # Baseline prompt
    baseline_prompt = baseline_agent._build_prompt(observation, available_actions)
    
    print(f"Baseline Prompt ({len(baseline_prompt)} 字符):")
    print("-" * 40)
    print(baseline_prompt)
    print("-" * 40)
    
    print(f"\n💡 关键差异分析:")
    print(f"   Baseline特点: 简洁直接，只有基本信息")
    print(f"   RAG特点: 包含知识图谱信息和ReAct推理格式")
    print(f"   可能问题: RAG的复杂性可能让LLM困惑")

if __name__ == "__main__":
    import time
    
    success = debug_rag_step_by_step()
    if success:
        compare_with_baseline()
        
        print(f"\n🔍 调试总结:")
        print(f"   1. 检查知识图谱是否正确检索")
        print(f"   2. 检查Prompt是否过于复杂")
        print(f"   3. 检查ReAct解析是否正确")
        print(f"   4. 对比Baseline的简洁性")
    else:
        print(f"\n❌ 调试过程中发现错误")
