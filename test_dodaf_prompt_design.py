#!/usr/bin/env python3
"""
测试基于DODAF框架的Prompt设计
展示如何将知识图谱作为决策指南而非数据列表
"""

def show_current_bad_prompt():
    """显示当前有问题的RAG prompt"""
    print("❌ 当前有问题的RAG Prompt:")
    print("=" * 60)
    
    bad_prompt = """You are an intelligent agent playing a text-based adventure game.
Your goal is to complete the given task by taking appropriate actions.

Current situation:
Observation: You are in a kitchen. There is a fridge here. Goal: Find the key and open the chest in the bedroom.

Relevant knowledge from your knowledge base:
1. kitchen contains key
2. key opens chest  
3. chest location bedroom

Available actions: ['look', 'inventory', 'go north', 'take apple', 'take key']

Please think step by step and choose the best action:

1. THOUGHT: Analyze the current situation and consider the relevant knowledge
2. ACTION: Choose one action from the available actions
3. REASON: Explain why this action is the best choice

Format your response as:
THOUGHT: [your analysis]
ACTION: [chosen action]
REASON: [your reasoning]"""

    print(bad_prompt)
    print("=" * 60)
    print(f"问题分析:")
    print("  ❌ 知识图谱以'数据库查询结果'形式展示")
    print("  ❌ 要求复杂的三段式推理格式")
    print("  ❌ 没有清晰的决策指导结构")
    print("  ❌ LLM需要'考虑相关知识'但不知道如何考虑")

def show_dodaf_good_prompt():
    """显示基于DODAF框架的良好prompt"""
    print("\n✅ 基于DODAF框架的良好Prompt:")
    print("=" * 60)
    
    # 这里展示如何将知识图谱转换为DODAF结构
    good_prompt = """Mission: Find the key and open the chest in the bedroom.

Situation Analysis (DA):
- Current: You are in kitchen with fridge
- Condition: Key is available here (take key → enables chest opening)
- Path: kitchen → go north → living room → go east → bedroom
- Target: Chest in bedroom (requires key to open)

Available Actions (DO): ['look', 'inventory', 'go north', 'take apple', 'take key']

Decision Framework (F):
- Priority 1: Secure key (prerequisite for mission)
- Priority 2: Navigate to bedroom  
- Priority 3: Open chest with key

Action:"""

    print(good_prompt)
    print("=" * 60)
    print(f"优势分析:")
    print("  ✅ 知识图谱转换为'决策指导'")
    print("  ✅ 清晰的DO-DA-F结构")
    print("  ✅ 优先级明确，减少决策困惑")
    print("  ✅ 简单的输出格式")

def show_dodaf_structure_mapping():
    """展示DODAF结构在游戏场景中的映射"""
    print("\n🎯 DODAF结构在游戏场景中的映射:")
    print("=" * 60)
    
    print("DO (Action) - 具体可执行的动作:")
    print("  • take key")
    print("  • go north") 
    print("  • go east")
    print("  • open chest")
    
    print("\nDA (Condition/Analysis) - 条件分析:")
    print("  • 当前位置状态: kitchen/living room/bedroom")
    print("  • 物品可用性: key available in kitchen")
    print("  • 路径条件: north leads to living room")
    print("  • 前置条件: need key to open chest")
    
    print("\nF (Outcome/Feedback) - 结果反馈:")
    print("  • 成功条件: chest opened with treasure")
    print("  • 失败条件: timeout without completing goal")
    print("  • 中间反馈: key obtained, location changed")

def show_knowledge_graph_to_dodaf_conversion():
    """展示如何将知识图谱转换为DODAF结构"""
    print("\n🔄 知识图谱 → DODAF 转换示例:")
    print("=" * 60)
    
    print("原始知识图谱事实:")
    kg_facts = [
        "kitchen contains key",
        "key opens chest", 
        "chest location bedroom",
        "go north leads to living room",
        "go east leads to bedroom"
    ]
    
    for fact in kg_facts:
        print(f"  • {fact}")
    
    print("\n转换为DODAF决策指导:")
    print("DA (分析): 你在kitchen，key在这里。路径是kitchen→north→living room→east→bedroom")
    print("DO (动作): 优先拿key，然后导航到bedroom")  
    print("F (反馈): 拿到key后去bedroom，用key开chest获得treasure")
    
    print("\n关键转换原则:")
    print("  1. 将事实转换为条件判断")
    print("  2. 将关系转换为行动指导") 
    print("  3. 将目标转换为优先级框架")

def design_minimal_dodaf_prompt():
    """设计最简化的DODAF prompt"""
    print("\n🎯 最简化DODAF Prompt设计:")
    print("=" * 60)
    
    minimal_prompt = """Goal: Find key, open chest in bedroom.
Status: Kitchen. Key here. Path: north→living room→east→bedroom.
Actions: ['look', 'inventory', 'go north', 'take apple', 'take key']
Next:"""

    print(minimal_prompt)
    print("=" * 60)
    print(f"长度: {len(minimal_prompt)} 字符 (vs 原来的808字符)")
    lines = minimal_prompt.split('\n')
    print(f"行数: {len(lines)} 行 (vs 原来的23行)")
    
    print("\n极简设计原则:")
    print("  ✅ 一句话说明目标 (DO)")
    print("  ✅ 一句话分析现状 (DA)")  
    print("  ✅ 直接列出选项 (F)")
    print("  ✅ 简单输出格式")

def compare_llm_cognitive_load():
    """对比不同prompt的认知负担"""
    print("\n🧠 LLM认知负担对比:")
    print("=" * 60)
    
    print("❌ 原始RAG Prompt认知负担:")
    print("  1. 理解复杂的ReAct格式要求")
    print("  2. 处理'knowledge base'抽象概念")
    print("  3. 生成THOUGHT/ACTION/REASON三部分")
    print("  4. 在知识列表中找到相关信息")
    print("  5. 将知识与当前情况关联")
    print("  → 总计: 5个认知步骤")
    
    print("\n✅ DODAF Prompt认知负担:")
    print("  1. 理解当前状态和目标")
    print("  2. 从给定选项中选择动作")
    print("  → 总计: 2个认知步骤")
    
    print("\n💡 认知负担减少: 60%")
    print("这解释了为什么RAG Agent陷入'look'循环!")

if __name__ == "__main__":
    print("🎯 基于DODAF框架的RAG Prompt重新设计")
    print("将知识图谱从'数据列表'转换为'决策指南'")
    
    show_current_bad_prompt()
    show_dodaf_good_prompt()
    show_dodaf_structure_mapping()
    show_knowledge_graph_to_dodaf_conversion()
    design_minimal_dodaf_prompt()
    compare_llm_cognitive_load()
    
    print("\n🎉 设计完成!")
    print("现在我们有了真正基于DODAF框架的RAG设计方案。")
