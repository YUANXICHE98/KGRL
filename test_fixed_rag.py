#!/usr/bin/env python3
"""
测试修复后的RAG Agent
"""

import sys
sys.path.append('.')

def test_rag_agent():
    print("🧠 测试修复后的RAG Agent")
    print("=" * 50)
    
    try:
        # 1. 创建知识图谱
        from src.knowledge.kg_builder import KnowledgeGraphBuilder
        from src.knowledge.kg_retriever import KnowledgeGraphRetriever
        
        kg = KnowledgeGraphBuilder('test_kg')
        kg.add_fact('kitchen', 'contains', 'key')
        kg.add_fact('key', 'opens', 'chest')
        kg.add_fact('chest', 'location', 'bedroom')
        
        retriever = KnowledgeGraphRetriever(kg, 'test_retriever')
        print(f"✅ 知识图谱创建: {len(kg.facts)} 个事实")
        
        # 2. 创建RAG Agent
        from src.agents.rag_agent import RAGAgent
        
        rag_agent = RAGAgent('test_rag', {
            'model_name': 'gpt-4o',
            'use_local_model': False,
            'use_knowledge_graph': True,
            'use_react_reasoning': True,
            'temperature': 0.7,
            'max_tokens': 100,
            'max_kg_facts': 3
        })
        
        # 3. 设置知识检索器
        rag_agent.set_knowledge_retriever(retriever)
        print("✅ RAG Agent创建成功")
        
        # 4. 测试知识检索
        knowledge = rag_agent.retrieve_knowledge('kitchen key')
        print(f"✅ 知识检索测试: 找到 {len(knowledge)} 个相关事实")
        for fact in knowledge:
            print(f"   - {fact['subject']} {fact['predicate']} {fact['object']}")
        
        # 5. 测试prompt构建
        from src.environments.textworld_env import TextWorldEnvironment
        env = TextWorldEnvironment('test_env', {'difficulty': 'easy'})
        obs = env.reset()
        actions = env.get_available_actions()
        
        prompt = rag_agent.build_enhanced_prompt(obs, actions, knowledge)
        print(f"\\n✅ 增强Prompt构建成功 (长度: {len(prompt)} 字符)")
        print("Prompt预览:")
        print("-" * 40)
        print(prompt[:300] + "...")
        print("-" * 40)
        
        print("\\n🎉 所有测试通过！RAG Agent修复成功")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_agent()
    if success:
        print("\\n✅ RAG Agent已修复，可以运行真实实验了！")
    else:
        print("\\n❌ 还有问题需要修复")
