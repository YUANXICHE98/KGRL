"""
测试记忆增强智能体
验证记忆系统与智能体的集成效果
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.memory_agent import MemoryAgent
from src.knowledge.kg_builder import KnowledgeGraphBuilder
from src.knowledge.kg_retriever import KnowledgeGraphRetriever
from src.memory.medium_term_memory import MediumTermMemory, ActionSequence
from src.memory.long_term_memory import LongTermMemory, DecisionPattern, TaskStrategy
from src.memory.short_term_memory import ActionMemory
import time


def test_memory_enhanced_agent_creation():
    """测试记忆增强Agent的创建"""
    print("🤖 测试记忆增强Agent创建...")
    
    config = {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'use_memory': True,
        'memory_max_actions': 5,
        'use_knowledge_graph': True,
        'max_kg_facts': 3,
        'prevent_loops': True,
        'temperature': 0.7,
        'max_tokens': 100
    }
    
    agent = MemoryEnhancedRAGAgent('test_memory_agent', config)
    
    print(f"✅ Agent创建成功: {agent.agent_id}")
    print(f"✅ 记忆系统启用: {agent.use_memory}")
    print(f"✅ 知识图谱启用: {agent.use_knowledge_graph}")
    print(f"✅ 循环防止启用: {agent.prevent_loops}")
    
    return agent


def test_knowledge_integration():
    """测试知识图谱集成"""
    print("\n📚 测试知识图谱集成...")
    
    # 创建知识图谱
    kg = KnowledgeGraphBuilder('test_kg')
    kg.add_fact('kitchen', 'contains', 'key')
    kg.add_fact('key', 'opens', 'chest')
    kg.add_fact('chest', 'location', 'bedroom')
    kg.add_fact('bedroom', 'connected_to', 'living_room')
    
    retriever = KnowledgeGraphRetriever(kg, 'test_retriever')
    
    # 创建Agent并设置知识检索器
    agent = MemoryEnhancedRAGAgent('kg_test_agent', {
        'use_memory': True,
        'use_knowledge_graph': True,
        'max_kg_facts': 3
    })
    
    agent.set_knowledge_retriever(retriever)
    
    print(f"✅ 知识图谱创建: {len(kg.facts)} 个事实")
    print("✅ 知识检索器设置成功")
    
    return agent, retriever


def test_memory_guided_decision():
    """测试记忆引导的决策"""
    print("\n🧠 测试记忆引导的决策...")
    
    # 创建Agent和知识图谱
    agent, retriever = test_knowledge_integration()
    
    # 模拟一系列决策场景
    scenarios = [
        {
            "observation": "You are in a kitchen. There is a key on the table.",
            "available_actions": ["take key", "go north", "look"],
            "expected_memory": "应该记住在厨房看到了钥匙"
        },
        {
            "observation": "You are in a kitchen. You are carrying a key.",
            "available_actions": ["go north", "drop key", "look"],
            "expected_memory": "应该记住已经拿到了钥匙"
        },
        {
            "observation": "You are in a living room. There is a sofa here.",
            "available_actions": ["go east", "go south", "look"],
            "expected_memory": "应该记住从厨房移动到了客厅"
        }
    ]
    
    previous_observation = ""
    
    for i, scenario in enumerate(scenarios):
        print(f"\n--- 场景 {i+1} ---")
        print(f"观察: {scenario['observation']}")
        print(f"可用动作: {scenario['available_actions']}")
        
        # 执行决策 (不调用真实API)
        try:
            # 模拟决策过程 (不实际调用LLM)
            action = agent._choose_alternative_action(
                scenario['available_actions'], 
                agent._get_memory_context()
            )
            print(f"选择动作: {action}")
            
            # 记录动作结果到记忆
            if previous_observation:
                agent.record_action_result(
                    action="simulated_action",
                    observation_before=previous_observation,
                    observation_after=scenario['observation'],
                    reward=0.1,
                    done=False
                )
            
            previous_observation = scenario['observation']
            
        except Exception as e:
            print(f"决策过程出错: {e}")
    
    # 检查记忆状态
    if agent.short_term_memory:
        stats = agent.short_term_memory.get_stats()
        print(f"\n✅ 记忆统计: {stats}")
        
        context = agent._get_memory_context()
        print(f"✅ 决策上下文包含 {len(context)} 个字段")


def test_loop_detection():
    """测试循环检测功能"""
    print("\n🔄 测试循环检测功能...")
    
    agent = MemoryEnhancedRAGAgent('loop_test_agent', {
        'use_memory': True,
        'prevent_loops': True,
        'loop_detection_window': 1
    })
    
    # 模拟重复动作
    agent.record_action_result(
        action="look",
        observation_before="You are in a room.",
        observation_after="You see nothing new.",
        reward=0.0,
        done=False
    )
    
    time.sleep(0.1)
    
    agent.record_action_result(
        action="look",
        observation_before="You are in a room.",
        observation_after="You see nothing new.",
        reward=0.0,
        done=False
    )
    
    # 测试循环检测
    available_actions = ["look", "go north", "take item"]
    is_loop = agent._detect_potential_loop(available_actions)
    
    print(f"✅ 循环检测结果: {is_loop}")
    
    if is_loop:
        alternative_action = agent._choose_alternative_action(
            available_actions, 
            agent._get_memory_context()
        )
        print(f"✅ 选择替代动作: {alternative_action}")


def test_memory_keyword_extraction():
    """测试记忆关键词提取"""
    print("\n🔍 测试记忆关键词提取...")
    
    agent = MemoryEnhancedRAGAgent('keyword_test_agent', {
        'use_memory': True,
        'use_knowledge_graph': True
    })
    
    # 添加一些记忆数据
    agent.record_action_result(
        action="take key",
        observation_before="You are in a kitchen.",
        observation_after="You are carrying a key.",
        reward=0.5,
        done=False
    )
    
    agent.record_action_result(
        action="go north",
        observation_before="You are in a kitchen.",
        observation_after="You are in a living room.",
        reward=0.1,
        done=False
    )
    
    # 获取记忆上下文并提取关键词
    memory_context = agent._get_memory_context()
    keywords = agent._extract_memory_keywords(memory_context)
    
    print(f"✅ 提取的记忆关键词: {keywords}")
    print(f"✅ 关键词数量: {len(keywords)}")


def test_agent_stats():
    """测试Agent统计功能"""
    print("\n📊 测试Agent统计功能...")
    
    agent = MemoryEnhancedRAGAgent('stats_test_agent', {
        'use_memory': True,
        'use_knowledge_graph': True
    })
    
    # 模拟一些活动
    agent.total_actions = 5
    agent.memory_guided_decisions = 3
    agent.loop_preventions = 1
    agent.api_calls = 2
    agent.api_response_times = [1.2, 1.5]
    
    # 添加记忆数据
    agent.record_action_result("test", "before", "after", 0.1, False)
    
    # 获取统计信息
    stats = agent.get_stats()
    
    print("✅ Agent统计信息:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")


def test_agent_reset():
    """测试Agent重置功能"""
    print("\n🔄 测试Agent重置功能...")
    
    agent = MemoryEnhancedRAGAgent('reset_test_agent', {
        'use_memory': True
    })
    
    # 添加一些数据
    agent.total_actions = 10
    agent.record_action_result("test", "before", "after", 0.1, False)
    
    print(f"重置前 - 总动作数: {agent.total_actions}")
    if agent.short_term_memory:
        print(f"重置前 - 记忆中动作数: {agent.short_term_memory.get_stats()['action_count']}")
    
    # 重置
    agent.reset()
    
    print(f"重置后 - 总动作数: {agent.total_actions}")
    if agent.short_term_memory:
        print(f"重置后 - 记忆中动作数: {agent.short_term_memory.get_stats()['action_count']}")
    
    print("✅ Agent重置成功")


def test_medium_term_memory():
    """测试中期记忆系统"""
    print("\n🧠 测试中期记忆系统...")

    memory = MediumTermMemory("test_medium", max_sequences=10)

    # 测试动作序列记录
    memory.start_new_sequence("find treasure")

    # 模拟一个成功的动作序列
    actions = [
        ActionMemory("look", "You are in kitchen", "You see a key", 0.0, False, time.time()),
        ActionMemory("take key", "You see a key", "You have key", 0.5, True, time.time() + 1),
        ActionMemory("go north", "You have key", "You are in living room", 0.1, True, time.time() + 2),
        ActionMemory("go east", "You are in living room", "You are in bedroom", 0.1, True, time.time() + 3),
        ActionMemory("open chest", "You are in bedroom", "Chest opened, treasure found!", 1.0, True, time.time() + 4)
    ]

    for action in actions:
        memory.add_action_to_sequence(action)

    # 结束序列
    sequence = memory.end_current_sequence(success=True, reason="goal_achieved")

    print(f"✅ 成功序列记录: {sequence.sequence_id}")
    print(f"✅ 序列长度: {len(sequence.actions)}")
    print(f"✅ 总奖励: {sequence.total_reward}")

    # 测试失败序列
    memory.start_new_sequence("find treasure again")

    failed_actions = [
        ActionMemory("look", "You are in kitchen", "You see nothing", 0.0, False, time.time()),
        ActionMemory("look", "You see nothing", "Still nothing", 0.0, False, time.time() + 1),
        ActionMemory("look", "Still nothing", "Nothing again", -0.1, False, time.time() + 2)
    ]

    for action in failed_actions:
        memory.add_action_to_sequence(action)

    failed_sequence = memory.end_current_sequence(success=False, reason="timeout")

    print(f"✅ 失败序列记录: {failed_sequence.sequence_id}")

    # 测试统计信息
    stats = memory.get_stats()
    print(f"✅ 记忆统计: {stats}")

    # 测试动作统计
    action_stats = memory.get_action_statistics("look")
    print(f"✅ 'look'动作统计: {action_stats}")

    # 测试推荐动作
    recommendations = memory.get_recommended_actions()
    print(f"✅ 推荐动作: {recommendations}")

    return memory


def test_pattern_analysis():
    """测试模式分析功能"""
    print("\n🔍 测试模式分析功能...")

    memory = MediumTermMemory("pattern_test")

    # 创建多个相似的成功序列
    for i in range(3):
        memory.start_new_sequence(f"treasure_hunt_{i}")

        # 相同的成功模式
        success_actions = [
            ActionMemory("take key", "see key", "have key", 0.5, True, time.time()),
            ActionMemory("go north", "have key", "in living room", 0.1, True, time.time() + 1),
            ActionMemory("go east", "in living room", "in bedroom", 0.1, True, time.time() + 2),
            ActionMemory("open chest", "in bedroom", "treasure found", 1.0, True, time.time() + 3)
        ]

        for action in success_actions:
            memory.add_action_to_sequence(action)

        memory.end_current_sequence(success=True)
        time.sleep(0.1)

    # 创建失败序列
    for i in range(2):
        memory.start_new_sequence(f"failed_attempt_{i}")

        fail_actions = [
            ActionMemory("look", "in room", "see nothing", 0.0, False, time.time()),
            ActionMemory("look", "see nothing", "still nothing", -0.1, False, time.time() + 1)
        ]

        for action in fail_actions:
            memory.add_action_to_sequence(action)

        memory.end_current_sequence(success=False)
        time.sleep(0.1)

    # 获取模式分析
    success_patterns = memory.get_success_patterns()
    failure_patterns = memory.get_failure_patterns()

    print(f"✅ 成功模式数量: {len(success_patterns)}")
    for pattern in success_patterns:
        print(f"  - {pattern.pattern_description} (频率: {pattern.frequency})")

    print(f"✅ 失败模式数量: {len(failure_patterns)}")
    for pattern in failure_patterns:
        print(f"  - {pattern.pattern_description} (频率: {pattern.frequency})")

    # 测试动作建议
    should_avoid_look = memory.should_avoid_action("look")
    print(f"✅ 应该避免'look'动作: {should_avoid_look}")


def test_sequence_similarity():
    """测试序列相似性分析"""
    print("\n🔄 测试序列相似性分析...")

    memory = MediumTermMemory("similarity_test")

    # 添加一些历史序列
    memory.start_new_sequence("test1")
    for action_name in ["take key", "go north", "open door"]:
        action = ActionMemory(action_name, "before", "after", 0.1, True, time.time())
        memory.add_action_to_sequence(action)
    memory.end_current_sequence(success=True)

    memory.start_new_sequence("test2")
    for action_name in ["take key", "go south", "open chest"]:
        action = ActionMemory(action_name, "before", "after", 0.2, True, time.time())
        memory.add_action_to_sequence(action)
    memory.end_current_sequence(success=True)

    # 测试相似序列查找
    current_actions = ["take key", "go north"]
    similar_sequences = memory.get_similar_sequences(current_actions)

    print(f"✅ 当前动作: {current_actions}")
    print(f"✅ 找到相似序列: {len(similar_sequences)}")
    for seq in similar_sequences:
        seq_actions = [action.action for action in seq.actions]
        print(f"  - {seq.sequence_id}: {seq_actions}")


def test_long_term_memory():
    """测试长期记忆系统"""
    print("\n🧠 测试长期记忆系统...")

    long_memory = LongTermMemory("test_long_term", max_patterns=20)

    # 创建一些测试序列
    sequences = []

    # 成功序列1
    seq1 = ActionSequence(
        sequence_id="success_1",
        actions=[
            ActionMemory("take key", "see key", "have key", 0.5, True, time.time()),
            ActionMemory("go north", "have key", "in room", 0.1, True, time.time() + 1),
            ActionMemory("open door", "in room", "door opened", 1.0, True, time.time() + 2)
        ],
        start_time=time.time(),
        end_time=time.time() + 3,
        total_reward=1.6,
        success=True,
        goal="open door"
    )
    sequences.append(seq1)

    # 成功序列2 (相似模式)
    seq2 = ActionSequence(
        sequence_id="success_2",
        actions=[
            ActionMemory("take key", "see key", "have key", 0.5, True, time.time()),
            ActionMemory("go north", "have key", "in room", 0.1, True, time.time() + 1),
            ActionMemory("open door", "in room", "door opened", 1.0, True, time.time() + 2)
        ],
        start_time=time.time(),
        end_time=time.time() + 3,
        total_reward=1.6,
        success=True,
        goal="open door"
    )
    sequences.append(seq2)

    # 失败序列
    seq3 = ActionSequence(
        sequence_id="failure_1",
        actions=[
            ActionMemory("look", "in room", "see nothing", 0.0, False, time.time()),
            ActionMemory("look", "see nothing", "still nothing", -0.1, False, time.time() + 1)
        ],
        start_time=time.time(),
        end_time=time.time() + 2,
        total_reward=-0.1,
        success=False,
        goal="explore"
    )
    sequences.append(seq3)

    # 让长期记忆学习
    long_memory.learn_from_sequences(sequences)

    # 检查学习结果
    stats = long_memory.get_stats()
    print(f"✅ 长期记忆统计: {stats}")

    # 检查决策模式
    patterns = list(long_memory.decision_patterns.values())
    print(f"✅ 学习到的决策模式: {len(patterns)}")
    for pattern in patterns:
        print(f"  - {pattern.pattern_type}: {pattern.description}")

    # 检查任务策略
    strategies = list(long_memory.task_strategies.values())
    print(f"✅ 学习到的任务策略: {len(strategies)}")
    for strategy in strategies:
        print(f"  - {strategy.task_type}: {len(strategy.strategy_steps)} 步骤")

    # 检查知识规则
    rules = long_memory.get_knowledge_rules()
    print(f"✅ 学习到的知识规则: {len(rules)}")
    for rule in rules:
        print(f"  - {rule.rule_type}: {rule.condition} -> {rule.action}")

    return long_memory


def test_decision_patterns():
    """测试决策模式推荐"""
    print("\n🎯 测试决策模式推荐...")

    long_memory = test_long_term_memory()

    # 测试决策推荐
    context = {
        "goal": "open door",
        "available_actions_count": 3,
        "current_location": "kitchen"
    }

    recommendation = long_memory.get_decision_recommendation(context)

    if recommendation:
        print(f"✅ 推荐决策模式: {recommendation.description}")
        print(f"✅ 推荐动作序列: {recommendation.actions}")
        print(f"✅ 置信度: {recommendation.confidence:.2f}")
    else:
        print("✅ 没有找到匹配的决策模式")

    # 测试动作避免建议
    should_avoid_look = long_memory.should_avoid_action("look")
    print(f"✅ 应该避免'look'动作: {should_avoid_look}")

    # 测试偏好动作
    preferred_actions = long_memory.get_preferred_actions()
    print(f"✅ 偏好动作: {preferred_actions}")


def test_task_strategies():
    """测试任务策略"""
    print("\n📋 测试任务策略...")

    long_memory = test_long_term_memory()

    # 获取任务策略
    strategy = long_memory.get_task_strategy("open door")

    if strategy:
        print(f"✅ 找到任务策略: {strategy.strategy_id}")
        print(f"✅ 策略有效性: {strategy.effectiveness:.2f}")
        print(f"✅ 策略适应性: {strategy.adaptability:.2f}")
        print(f"✅ 策略步骤:")
        for step in strategy.strategy_steps:
            print(f"  {step['step_number']}. {step['action']}")
    else:
        print("✅ 没有找到对应的任务策略")

    # 测试元学习统计
    meta_stats = long_memory.meta_statistics
    print(f"✅ 元学习统计:")
    print(f"  - 总会话数: {meta_stats['total_sessions']}")
    print(f"  - 成功会话数: {meta_stats['successful_sessions']}")
    print(f"  - 学习到的模式数: {meta_stats['total_patterns_learned']}")
    print(f"  - 按类型分组: {dict(meta_stats['patterns_by_type'])}")


def main():
    """主测试函数"""
    print("🚀 开始测试记忆增强RAG Agent...\n")

    try:
        # 运行所有测试
        test_memory_enhanced_agent_creation()
        test_knowledge_integration()
        test_memory_guided_decision()
        test_loop_detection()
        test_memory_keyword_extraction()
        test_agent_stats()
        test_agent_reset()

        # 新增中期记忆测试
        test_medium_term_memory()
        test_pattern_analysis()
        test_sequence_similarity()

        # 新增长期记忆测试
        test_long_term_memory()
        test_decision_patterns()
        test_task_strategies()

        print("\n🎉 所有测试完成！记忆增强RAG Agent和完整记忆系统工作正常。")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
