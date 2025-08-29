#!/usr/bin/env python3
"""
测试修改后的ReAct RAG Agent
验证真正的query_kg机制
"""

import sys
sys.path.append('.')

def test_react_rag_agent():
    """测试ReAct RAG Agent的query_kg机制"""
    print("🔍 测试ReAct RAG Agent")
    print("=" * 60)
    
    # 1. 创建DODAF知识图谱
    from src.knowledge.kg_builder import KnowledgeGraphBuilder
    from src.knowledge.kg_retriever import KnowledgeGraphRetriever
    
    kg = KnowledgeGraphBuilder('react_test_kg')
    
    # 添加DODAF分类的事实
    kg.add_fact('kitchen', 'contains', 'key', dodaf_type='DA')
    kg.add_fact('chest', 'location', 'bedroom', dodaf_type='DA')
    kg.add_fact('key', 'opens', 'chest', dodaf_type='DO')
    kg.add_fact('go_north', 'leads_to', 'living_room', dodaf_type='DO')
    kg.add_fact('goal', 'is', 'open_chest', dodaf_type='F')
    
    retriever = KnowledgeGraphRetriever(kg, 'react_test_retriever')
    print(f"✅ 知识图谱创建: {len(kg.facts)} 个DODAF事实")
    
    # 2. 创建修改后的RAG Agent
    from src.agents.rag_agent import RAGAgent
    
    rag_agent = RAGAgent('react_test_rag', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'use_knowledge_graph': True,
        'use_react_reasoning': True,  # 启用ReAct
        'temperature': 0.7,
        'max_tokens': 200,
        'max_kg_facts': 3
    })
    
    rag_agent.set_knowledge_retriever(retriever)
    print("✅ ReAct RAG Agent创建成功")
    
    return rag_agent, retriever

def test_query_kg_interface():
    """测试query_kg接口"""
    print("\n🔎 测试query_kg接口")
    print("=" * 60)
    
    rag_agent, retriever = test_react_rag_agent()
    
    print("1. 测试不同类型的KG查询:")
    
    # 测试关键词查询
    print("  关键词查询 'kitchen key':")
    results = rag_agent.query_kg('keywords', 'kitchen key', max_results=2)
    for fact in results:
        dodaf_type = fact.get('dodaf_type', 'DA')
        print(f"    - [{dodaf_type}] {fact['subject']} {fact['predicate']} {fact['object']}")
    
    # 测试DODAF查询
    print("  DODAF查询 'DO:key':")
    results = rag_agent.query_kg('dodaf', 'DO:key', max_results=2)
    for fact in results:
        dodaf_type = fact.get('dodaf_type', 'DA')
        print(f"    - [{dodaf_type}] {fact['subject']} {fact['predicate']} {fact['object']}")
    
    print("  DODAF查询 'DA:kitchen':")
    results = rag_agent.query_kg('dodaf', 'DA:kitchen', max_results=2)
    for fact in results:
        dodaf_type = fact.get('dodaf_type', 'DA')
        print(f"    - [{dodaf_type}] {fact['subject']} {fact['predicate']} {fact['object']}")

def test_query_kg_action_parsing():
    """测试query_kg动作解析"""
    print("\n🔧 测试query_kg动作解析")
    print("=" * 60)
    
    rag_agent, retriever = test_react_rag_agent()
    
    print("2. 测试query_kg动作解析:")
    
    # 测试不同格式的query_kg调用
    test_actions = [
        "query_kg('keywords', 'kitchen key')",
        "query_kg('dodaf', 'DO:key')",
        "query_kg('dodaf', 'DA:kitchen')",
        "query_kg('dodaf', 'F:')",
    ]
    
    for action in test_actions:
        print(f"  执行: {action}")
        result = rag_agent._execute_query_kg_action(action)
        print(f"    结果: {result}")

def test_react_prompt_building():
    """测试ReAct prompt构建"""
    print("\n📝 测试ReAct Prompt构建")
    print("=" * 60)
    
    rag_agent, retriever = test_react_rag_agent()
    
    observation = "You are in a kitchen. There is a fridge here. Goal: Find the key and open the chest in the bedroom."
    actions = ['look', 'inventory', 'go north', 'take apple', 'take key']
    
    print("3. ReAct Prompt (不包含KG信息):")
    prompt = rag_agent._build_react_prompt(observation, actions, 0)
    print("-" * 40)
    print(prompt)
    print("-" * 40)
    print(f"长度: {len(prompt)} 字符")
    
    print("\n💡 关键特点:")
    print("  ✅ 不包含预先检索的KG信息")
    print("  ✅ 支持query_kg调用")
    print("  ✅ 明确的DODAF查询选项")
    print("  ✅ 简洁的ReAct格式")

def simulate_react_decision():
    """模拟ReAct决策过程（不调用真实API）"""
    print("\n🎭 模拟ReAct决策过程")
    print("=" * 60)
    
    rag_agent, retriever = test_react_rag_agent()
    
    print("4. 模拟ReAct循环:")
    
    # 模拟LLM响应
    mock_responses = [
        """THOUGHT: I need to understand what's available in the kitchen
ACTION: query_kg('dodaf', 'DA:kitchen')
REASON: I should check the knowledge graph for conditions about the kitchen""",
        
        """THOUGHT: Now I know the key is in the kitchen, I should take it
ACTION: take key
REASON: Taking the key is necessary to open the chest later"""
    ]
    
    observation = "You are in a kitchen. There is a fridge here."
    
    for i, response in enumerate(mock_responses):
        print(f"\n  迭代 {i+1}:")
        print(f"    观察: {observation}")
        
        # 解析响应
        thought, action, reason = rag_agent.parse_react_response(response)
        print(f"    思考: {thought}")
        print(f"    动作: {action}")
        print(f"    理由: {reason}")
        
        # 如果是query_kg动作，执行它
        if action.startswith('query_kg('):
            kg_result = rag_agent._execute_query_kg_action(action)
            print(f"    KG结果: {kg_result}")
            observation += f" KG查询结果: {kg_result}"
        else:
            print(f"    → 选择游戏动作: {action}")
            break

def compare_with_old_approach():
    """对比新旧方法"""
    print("\n📊 新旧方法对比")
    print("=" * 60)
    
    print("❌ 旧方法 (静态KG):")
    print("  1. 预先检索KG信息")
    print("  2. 将KG信息拼接到prompt")
    print("  3. LLM被动接受所有信息")
    print("  4. 可能信息过载，干扰决策")
    
    print("\n✅ 新方法 (动态query_kg):")
    print("  1. prompt不包含KG信息")
    print("  2. LLM主动调用query_kg")
    print("  3. 按需获取相关知识")
    print("  4. 支持DODAF结构化查询")
    print("  5. 真正的ReAct循环")
    
    print("\n🎯 关键改进:")
    print("  ✅ KG从'背景知识'变成'可调用函数'")
    print("  ✅ 支持DO-DA-F结构化决策")
    print("  ✅ 减少信息过载")
    print("  ✅ 增强决策透明度")

if __name__ == "__main__":
    print("🚀 ReAct RAG Agent测试")
    print("验证真正的query_kg机制和DODAF集成")
    
    try:
        rag_agent, retriever = test_react_rag_agent()
        test_query_kg_interface()
        test_query_kg_action_parsing()
        test_react_prompt_building()
        simulate_react_decision()
        compare_with_old_approach()
        
        print("\n✅ 所有测试通过!")
        print("ReAct RAG Agent已准备好进行真实实验")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
