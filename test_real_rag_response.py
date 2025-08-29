#!/usr/bin/env python3
"""
测试真实RAG Agent的API响应
看看LLM实际返回什么
"""

import sys
import time
sys.path.append('.')

def test_real_rag_api_response():
    print("🔍 测试真实RAG Agent API响应")
    print("=" * 60)
    
    # 1. 创建知识图谱
    from src.knowledge.kg_builder import KnowledgeGraphBuilder
    from src.knowledge.kg_retriever import KnowledgeGraphRetriever
    
    kg = KnowledgeGraphBuilder('real_test_kg')
    kg.add_fact('kitchen', 'contains', 'key')
    kg.add_fact('key', 'opens', 'chest')
    kg.add_fact('chest', 'location', 'bedroom')
    
    retriever = KnowledgeGraphRetriever(kg, 'real_test_retriever')
    print(f"📚 知识图谱: {len(kg.facts)} 个事实")
    
    # 2. 创建环境
    from src.environments.textworld_env import TextWorldEnvironment
    env = TextWorldEnvironment('real_test_env', {'difficulty': 'easy'})
    observation = env.reset()
    available_actions = env.get_available_actions()
    
    print(f"🌍 环境观察: {observation}")
    print(f"🎮 可用动作: {available_actions}")
    
    # 3. 创建RAG Agent
    from src.agents.rag_agent import RAGAgent
    rag_agent = RAGAgent('real_test_rag', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'use_knowledge_graph': True,
        'use_react_reasoning': True,
        'temperature': 0.7,
        'max_tokens': 150,
        'max_kg_facts': 2
    })
    rag_agent.set_knowledge_retriever(retriever)
    
    # 4. 执行一步真实决策
    print(f"\n🤖 执行真实RAG决策...")
    print(f"⏱️  这将调用真实GPT-4o API，请等待...")
    
    start_time = time.time()
    
    try:
        # 调用真实的act方法
        chosen_action = rag_agent.act(observation, available_actions)
        api_time = time.time() - start_time
        
        print(f"✅ RAG Agent决策完成!")
        print(f"   选择的动作: '{chosen_action}'")
        print(f"   API响应时间: {api_time:.2f}秒")
        print(f"   动作是否有效: {chosen_action in available_actions}")
        
        # 获取统计信息
        stats = rag_agent.get_stats()
        print(f"   KG查询: {stats['kg_queries']}")
        print(f"   KG命中: {stats['kg_hits']}")
        print(f"   KG命中率: {stats['kg_hit_rate']:.2%}")
        
        # 5. 对比Baseline Agent
        print(f"\n📊 对比Baseline Agent...")
        from src.agents.baseline_agent import BaselineAgent
        
        baseline_agent = BaselineAgent('real_test_baseline', {
            'model_name': 'gpt-4o',
            'temperature': 0.7,
            'max_tokens': 50
        })
        
        baseline_start = time.time()
        baseline_action = baseline_agent.act(observation, available_actions)
        baseline_time = time.time() - baseline_start
        
        print(f"✅ Baseline Agent决策完成!")
        print(f"   选择的动作: '{baseline_action}'")
        print(f"   API响应时间: {baseline_time:.2f}秒")
        print(f"   动作是否有效: {baseline_action in available_actions}")
        
        # 6. 结果对比
        print(f"\n🔍 决策对比分析:")
        print(f"   RAG动作: '{chosen_action}' ({api_time:.2f}s)")
        print(f"   Baseline动作: '{baseline_action}' ({baseline_time:.2f}s)")
        print(f"   动作是否相同: {chosen_action == baseline_action}")
        print(f"   RAG是否更慢: {api_time > baseline_time} ({api_time - baseline_time:+.2f}s)")
        
        # 7. 执行动作看结果
        print(f"\n🎯 执行RAG Agent选择的动作...")
        next_obs, reward, done, info = env.step(chosen_action)
        print(f"   执行结果: 奖励={reward}, 完成={done}")
        print(f"   新观察: {next_obs}")
        
        if reward > 0:
            print(f"   🎉 RAG Agent做出了正确决策!")
        elif reward == 0:
            print(f"   ⚪ RAG Agent做出了中性决策")
        else:
            print(f"   ❌ RAG Agent做出了错误决策")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG Agent决策失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prompt_effectiveness():
    """测试不同prompt的有效性"""
    print(f"\n📝 测试Prompt有效性")
    print("=" * 60)
    
    from src.agents.rag_agent import RAGAgent
    
    # 创建RAG Agent但不调用API
    rag_agent = RAGAgent('prompt_test', {
        'model_name': 'gpt-4o',
        'use_knowledge_graph': True,
        'use_react_reasoning': True,
        'max_kg_facts': 2
    })
    
    observation = "You are in a kitchen. There is a key here. Goal: Find the key and open the chest in the bedroom."
    actions = ['take key', 'go north', 'look']
    knowledge = [
        {'subject': 'kitchen', 'predicate': 'contains', 'object': 'key', 'confidence': 1.0},
        {'subject': 'key', 'predicate': 'opens', 'object': 'chest', 'confidence': 1.0}
    ]
    
    # 构建prompt
    prompt = rag_agent.build_enhanced_prompt(observation, actions, knowledge)
    
    print(f"RAG Prompt分析:")
    print(f"   长度: {len(prompt)} 字符")
    lines = prompt.split('\n')
    print(f"   行数: {len(lines)} 行")
    print(f"   包含ReAct格式: {'THOUGHT:' in prompt}")
    print(f"   包含知识图谱: {'knowledge base' in prompt}")

    # 分析可能的问题
    print(f"\n🔍 潜在问题分析:")
    if len(prompt) > 800:
        print(f"   ⚠️  Prompt过长 ({len(prompt)} 字符)，可能影响LLM理解")
    if len(lines) > 20:
        print(f"   ⚠️  Prompt结构复杂 ({len(lines)} 行)")
    if 'THOUGHT:' in prompt and 'ACTION:' in prompt and 'REASON:' in prompt:
        print(f"   ⚠️  ReAct格式要求复杂，可能导致解析错误")
    
    print(f"\n💡 建议:")
    print(f"   1. 简化prompt结构")
    print(f"   2. 减少ReAct复杂性")
    print(f"   3. 专注于核心任务信息")

if __name__ == "__main__":
    print("🚀 真实RAG Agent测试")
    print("这将调用真实的GPT-4o API")
    
    confirm = input("\\n确认开始测试? (y/N): ").strip().lower()
    if confirm == 'y':
        success = test_real_rag_api_response()
        if success:
            test_prompt_effectiveness()
    else:
        print("测试取消")
        test_prompt_effectiveness()  # 只分析prompt，不调用API
