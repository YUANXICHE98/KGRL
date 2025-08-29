#!/usr/bin/env python3
"""
显示各种Agent的实际Prompt
看看知识图谱是如何被整合的
"""

import sys
sys.path.append('.')

def show_baseline_prompt():
    """显示Baseline Agent的prompt"""
    from src.agents.baseline_agent import BaselineAgent
    
    baseline = BaselineAgent('demo', {'model_name': 'gpt-4o'})
    
    observation = "You are in a kitchen. There is a fridge here. Goal: Find the key and open the chest in the bedroom."
    actions = ['look', 'inventory', 'go north', 'take apple', 'take key']
    
    prompt = baseline._build_prompt(observation, actions)
    
    print("🔵 BASELINE AGENT PROMPT")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    print(f"长度: {len(prompt)} 字符")
    lines = prompt.split('\n')
    print(f"行数: {len(lines)} 行")
    return prompt

def show_original_rag_prompt():
    """显示原始RAG Agent的prompt"""
    from src.agents.rag_agent import RAGAgent
    
    rag = RAGAgent('demo', {
        'model_name': 'gpt-4o',
        'use_knowledge_graph': True,
        'use_react_reasoning': True,
        'max_kg_facts': 3
    })
    
    observation = "You are in a kitchen. There is a fridge here. Goal: Find the key and open the chest in the bedroom."
    actions = ['look', 'inventory', 'go north', 'take apple', 'take key']
    
    # 模拟知识图谱检索结果
    knowledge_facts = [
        {'subject': 'kitchen', 'predicate': 'contains', 'object': 'key', 'confidence': 1.0},
        {'subject': 'key', 'predicate': 'opens', 'object': 'chest', 'confidence': 1.0},
        {'subject': 'chest', 'predicate': 'location', 'object': 'bedroom', 'confidence': 1.0}
    ]
    
    prompt = rag.build_enhanced_prompt(observation, actions, knowledge_facts)
    
    print("\\n🔴 ORIGINAL RAG AGENT PROMPT (with ReAct)")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    print(f"长度: {len(prompt)} 字符")
    lines = prompt.split('\n')
    print(f"行数: {len(lines)} 行")
    return prompt

def show_fixed_rag_prompt():
    """显示修复RAG Agent的prompt"""
    from src.agents.fixed_rag_agent import FixedRAGAgent
    
    fixed_rag = FixedRAGAgent('demo', {
        'model_name': 'gpt-4o',
        'use_knowledge_graph': True,
        'max_kg_facts': 2
    })
    
    observation = "You are in a kitchen. There is a fridge here. Goal: Find the key and open the chest in the bedroom."
    actions = ['look', 'inventory', 'go north', 'take apple', 'take key']
    
    # 模拟知识图谱检索结果
    knowledge = [
        'kitchen contains key',
        'key opens chest'
    ]
    
    prompt = fixed_rag._build_enhanced_prompt(observation, actions, knowledge)
    
    print("\\n🟡 FIXED RAG AGENT PROMPT (simplified)")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    print(f"长度: {len(prompt)} 字符")
    lines = prompt.split('\n')
    print(f"行数: {len(lines)} 行")
    return prompt

def analyze_prompt_differences():
    """分析不同prompt的差异"""
    print("\\n📊 PROMPT 对比分析")
    print("=" * 80)
    
    baseline_prompt = show_baseline_prompt()
    original_rag_prompt = show_original_rag_prompt()
    fixed_rag_prompt = show_fixed_rag_prompt()
    
    print("\\n📈 统计对比:")
    baseline_lines = len(baseline_prompt.split('\n'))
    original_lines = len(original_rag_prompt.split('\n'))
    fixed_lines = len(fixed_rag_prompt.split('\n'))
    print(f"Baseline:     {len(baseline_prompt):4d} 字符, {baseline_lines:2d} 行")
    print(f"Original RAG: {len(original_rag_prompt):4d} 字符, {original_lines:2d} 行")
    print(f"Fixed RAG:    {len(fixed_rag_prompt):4d} 字符, {fixed_lines:2d} 行")
    
    print("\\n🔍 关键差异:")
    print("1. Baseline: 简洁直接，专注任务")
    print("2. Original RAG: 复杂ReAct格式 + 详细知识信息")
    print("3. Fixed RAG: 简化格式但仍有知识信息")
    
    print("\\n💡 问题分析:")
    if 'THOUGHT:' in original_rag_prompt:
        print("❌ Original RAG要求复杂的THOUGHT/ACTION/REASON格式")
    if 'knowledge base' in original_rag_prompt.lower():
        print("❌ Original RAG包含'knowledge base'等复杂描述")
    if len(original_rag_prompt) > len(baseline_prompt) * 1.5:
        print(f"❌ Original RAG比Baseline长{len(original_rag_prompt)/len(baseline_prompt):.1f}倍")
    
    print("\\n🎯 DODAF框架对比:")
    print("理想的DO-DA-F结构应该是:")
    print("  DO (Action): 明确的动作指令")
    print("  DA (Analysis): 简洁的情况分析")
    print("  F (Feedback): 清晰的期望输出")
    
    print("\\n当前prompt问题:")
    print("  ❌ 知识信息过于详细，干扰决策")
    print("  ❌ ReAct格式增加认知负担")
    print("  ❌ 缺乏清晰的DO-DA-F结构")

def design_ideal_rag_prompt():
    """设计理想的RAG prompt（基于DODAF框架）"""
    print("\\n🎯 理想的RAG PROMPT设计 (基于DODAF)")
    print("=" * 80)
    
    # DO: 明确的任务和动作
    do_section = """DO (Action): Find the key and open the chest in the bedroom."""
    
    # DA: 简洁的情况分析
    da_section = """DA (Analysis): You are in a kitchen. Key is here. Path: kitchen → north → living room → east → bedroom."""
    
    # F: 清晰的期望输出
    f_section = """F (Feedback): Choose one action: ['look', 'inventory', 'go north', 'take apple', 'take key']"""
    
    ideal_prompt = f"""{do_section}
{da_section}
{f_section}

Action:"""
    
    print(ideal_prompt)
    print("=" * 80)
    print(f"长度: {len(ideal_prompt)} 字符")
    ideal_lines = ideal_prompt.split('\n')
    print(f"行数: {len(ideal_lines)} 行")
    
    print("\\n✅ 理想prompt特点:")
    print("  ✅ 遵循DODAF框架")
    print("  ✅ 知识图谱信息简洁明确")
    print("  ✅ 无复杂推理要求")
    print("  ✅ 输出格式简单")
    
    return ideal_prompt

if __name__ == "__main__":
    print("🔍 RAG Agent Prompt 深度分析")
    print("查看知识图谱是如何被整合到prompt中的")
    
    try:
        analyze_prompt_differences()
        design_ideal_rag_prompt()
        
        print("\\n🎉 分析完成！")
        print("现在你可以看到知识图谱整合的具体问题了。")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
