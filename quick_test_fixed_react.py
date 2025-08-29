#!/usr/bin/env python3
"""
快速测试修复后的ReAct RAG Agent
验证是否还会陷入look循环
"""

import sys
sys.path.append('.')

def quick_test_react_agent():
    """快速测试ReAct Agent"""
    print("🔍 快速测试修复后的ReAct RAG Agent")
    print("=" * 60)
    
    # 创建知识图谱
    from src.knowledge.kg_builder import KnowledgeGraphBuilder
    from src.knowledge.kg_retriever import KnowledgeGraphRetriever
    
    kg = KnowledgeGraphBuilder('quick_test')
    kg.add_fact('kitchen', 'contains', 'key', dodaf_type='DA')
    kg.add_fact('key', 'opens', 'chest', dodaf_type='DO')
    kg.add_fact('chest', 'location', 'bedroom', dodaf_type='DA')
    
    retriever = KnowledgeGraphRetriever(kg, 'quick_test')
    print(f"✅ KG创建: {len(kg.facts)} 个事实")
    
    # 创建环境
    from src.environments.textworld_env import TextWorldEnvironment
    env = TextWorldEnvironment('quick_test', {'difficulty': 'easy'})
    observation = env.reset()
    available_actions = env.get_available_actions()
    
    print(f"🌍 环境: {observation}")
    print(f"🎮 动作: {available_actions}")
    
    # 创建ReAct RAG Agent
    from src.agents.rag_agent import RAGAgent
    
    agent = RAGAgent('quick_test_react', {
        'model_name': 'gpt-4o',
        'use_knowledge_graph': True,
        'use_react_reasoning': True,  # 启用ReAct
        'temperature': 0.7,
        'max_tokens': 200
    })
    agent.set_knowledge_retriever(retriever)
    
    print("✅ ReAct RAG Agent创建")
    
    # 测试一步决策
    print("\n🤖 测试ReAct决策...")
    print("⏱️ 调用真实GPT-4o API...")
    
    try:
        action = agent.act(observation, available_actions)
        print(f"✅ Agent选择: '{action}'")
        print(f"✅ 动作有效: {action in available_actions}")
        
        # 获取统计
        stats = agent.get_stats()
        print(f"📊 统计: KG查询={stats['kg_queries']}, 命中={stats['kg_hits']}")
        
        # 检查是否还是选择look
        if action == "look":
            print("⚠️ 警告: 仍然选择了'look'，可能还有问题")
        else:
            print("🎉 成功: 没有陷入'look'循环！")
            
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 快速测试修复后的ReAct Agent")
    
    confirm = input("确认测试? (y/N): ").strip().lower()
    if confirm == 'y':
        quick_test_react_agent()
    else:
        print("测试取消")
