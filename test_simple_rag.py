#!/usr/bin/env python3
"""
测试简化RAG Agent
快速验证修复效果
"""

import sys
sys.path.append('.')

def test_simple_rag_agent():
    print("🧠 测试简化RAG Agent")
    print("=" * 50)
    
    try:
        # 1. 创建知识图谱
        from src.knowledge.kg_builder import KnowledgeGraphBuilder
        from src.knowledge.kg_retriever import KnowledgeGraphRetriever
        
        kg = KnowledgeGraphBuilder('test_simple_kg')
        kg.add_fact('key', 'location', 'kitchen')
        kg.add_fact('chest', 'location', 'bedroom')
        kg.add_fact('key', 'opens', 'chest')
        
        retriever = KnowledgeGraphRetriever(kg, 'test_simple_retriever')
        print(f"✅ 知识图谱创建: {len(kg.facts)} 个事实")
        
        # 2. 创建简化RAG Agent
        from src.agents.simple_rag_agent import SimpleRAGAgent
        
        simple_rag = SimpleRAGAgent('test_simple_rag', {
            'model_name': 'gpt-4o',
            'use_local_model': False,
            'use_knowledge_graph': True,
            'temperature': 0.7,
            'max_tokens': 50,
            'max_kg_facts': 2,
            'kg_retrieval_method': 'keywords'
        })
        
        simple_rag.set_knowledge_retriever(retriever)
        print("✅ 简化RAG Agent创建成功")
        
        # 3. 测试知识检索
        observation = "You are in a kitchen. There is a key here."
        knowledge = simple_rag.retrieve_relevant_knowledge(observation)
        print(f"✅ 知识检索测试: 找到 {len(knowledge)} 个相关事实")
        for fact in knowledge:
            print(f"   - {fact}")
        
        # 4. 测试prompt构建
        actions = ['take key', 'go north', 'look']
        prompt = simple_rag.build_simple_prompt(observation, actions, knowledge)
        print(f"\\n✅ 简化Prompt构建成功 (长度: {len(prompt)} 字符)")
        print("Prompt预览:")
        print("-" * 40)
        print(prompt)
        print("-" * 40)
        
        # 5. 对比复杂RAG的prompt
        from src.agents.rag_agent import RAGAgent
        complex_rag = RAGAgent('test_complex_rag', {
            'model_name': 'gpt-4o',
            'use_knowledge_graph': True,
            'use_react_reasoning': True,
            'max_kg_facts': 3
        })
        
        knowledge_dicts = [{'subject': 'key', 'predicate': 'location', 'object': 'kitchen', 'confidence': 1.0}]
        complex_prompt = complex_rag.build_enhanced_prompt(observation, actions, knowledge_dicts)
        
        print(f"\\n📊 Prompt长度对比:")
        print(f"  简化RAG: {len(prompt)} 字符")
        print(f"  复杂RAG: {len(complex_prompt)} 字符")
        print(f"  简化程度: {(1 - len(prompt)/len(complex_prompt)):.1%}")
        
        print("\\n🎉 简化RAG Agent测试通过！")
        print("主要改进:")
        print("  ✅ 去除复杂的ReAct推理格式")
        print("  ✅ 简化知识图谱信息展示")
        print("  ✅ 减少prompt长度和复杂性")
        print("  ✅ 使用更可靠的关键词检索")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_prompts():
    """对比不同Agent的prompt复杂度"""
    print("\\n📊 Prompt复杂度对比")
    print("=" * 50)
    
    observation = "You are in a kitchen. There is a key here. Goal: Find the key and open the chest in the bedroom."
    actions = ['take key', 'go north', 'look', 'inventory']
    
    # Baseline prompt (简单)
    baseline_prompt = f"""You are playing a text adventure game. Your goal is to find the key and open the chest in the bedroom.

Current situation: {observation}

Available actions: {actions}

Choose the best action to progress towards your goal. Respond with only the action name."""
    
    # Simple RAG prompt
    knowledge = ['key location kitchen', 'key opens chest']
    simple_rag_prompt = f"""You are playing a text adventure game. Your goal is to find the key and open the chest in the bedroom.

Current situation: {observation}

Relevant facts: {', '.join(knowledge)}

Available actions: {actions}

Choose the best action to progress towards your goal. Respond with only the action name."""
    
    # Complex RAG prompt (ReAct)
    complex_rag_prompt = f"""You are an intelligent agent playing a text-based adventure game.
Your goal is to complete the given task by taking appropriate actions.

Current situation:
Observation: {observation}

Relevant knowledge from your knowledge base:
1. key location kitchen
2. key opens chest

Available actions: {actions}

Please think step by step and choose the best action:

1. THOUGHT: Analyze the current situation and consider the relevant knowledge
2. ACTION: Choose one action from the available actions
3. REASON: Explain why this action is the best choice

Format your response as:
THOUGHT: [your analysis]
ACTION: [chosen action]
REASON: [your reasoning]"""
    
    print(f"Baseline Prompt: {len(baseline_prompt)} 字符")
    print(f"Simple RAG Prompt: {len(simple_rag_prompt)} 字符")
    print(f"Complex RAG Prompt: {len(complex_rag_prompt)} 字符")
    
    print(f"\\n复杂度增加:")
    print(f"  Simple RAG vs Baseline: +{len(simple_rag_prompt) - len(baseline_prompt)} 字符 ({(len(simple_rag_prompt)/len(baseline_prompt) - 1):.1%})")
    print(f"  Complex RAG vs Baseline: +{len(complex_rag_prompt) - len(baseline_prompt)} 字符 ({(len(complex_rag_prompt)/len(baseline_prompt) - 1):.1%})")

if __name__ == "__main__":
    success = test_simple_rag_agent()
    if success:
        compare_prompts()
        print("\\n✅ 简化RAG Agent准备就绪，可以进行对比实验！")
    else:
        print("\\n❌ 还有问题需要修复")
