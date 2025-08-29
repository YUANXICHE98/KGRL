"""
测试修复的RAG Agent
对比 Baseline vs Fixed RAG vs Original RAG
"""

import sys
import time
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.baseline_agent import BaselineAgent
from src.agents.rag_agent import RAGAgent
from src.agents.fixed_rag_agent import FixedRAGAgent
from src.environments.textworld_env import TextWorldEnvironment
from src.knowledge.kg_builder import KnowledgeGraphBuilder
from src.knowledge.kg_retriever import KnowledgeGraphRetriever
from src.utils.logger import get_logger

def create_enhanced_knowledge_graph():
    """创建增强的知识图谱，包含导航信息"""
    kg = KnowledgeGraphBuilder('enhanced_game_knowledge')
    
    # 核心任务知识
    kg.add_fact('goal', 'is', 'find key and open chest')
    kg.add_fact('key', 'location', 'kitchen')
    kg.add_fact('chest', 'location', 'bedroom')
    kg.add_fact('key', 'opens', 'chest')
    
    # 导航知识（关键！）
    kg.add_fact('kitchen', 'exit', 'north')
    kg.add_fact('go north', 'leads to', 'living room')
    kg.add_fact('living room', 'exit east', 'bedroom')
    kg.add_fact('go east', 'leads to', 'bedroom')
    kg.add_fact('bedroom', 'contains', 'chest')
    
    # 动作知识
    kg.add_fact('take', 'works with', 'key')
    kg.add_fact('open', 'works with', 'chest')
    kg.add_fact('after taking key', 'next step', 'go to bedroom')
    kg.add_fact('path to bedroom', 'is', 'north then east')
    
    # 策略知识
    kg.add_fact('strategy step 1', 'take', 'key')
    kg.add_fact('strategy step 2', 'go', 'north')
    kg.add_fact('strategy step 3', 'go', 'east')
    kg.add_fact('strategy step 4', 'open', 'chest')
    
    return kg

def run_single_episode_debug(agent, env, agent_name, episode_num, max_steps=15):
    """运行单个episode并打印详细调试信息"""
    logger = get_logger(f"{agent_name}_Debug")
    
    print(f"\n🔬 {agent_name} Episode {episode_num} 开始")
    print("-" * 50)
    
    # 重置环境和Agent
    observation = env.reset()
    if hasattr(agent, 'reset'):
        agent.reset()
    
    total_reward = 0
    done = False
    step_count = 0
    actions_taken = []
    
    print(f"初始观察: {observation}")
    print(f"目标: Find the key and open the chest in the bedroom")
    
    while not done and step_count < max_steps:
        available_actions = env.get_available_actions()
        print(f"\n--- Step {step_count + 1} ---")
        print(f"可用动作: {available_actions}")
        
        # Agent决策
        start_time = time.time()
        try:
            action = agent.act(observation, available_actions)
            api_time = time.time() - start_time
            
            print(f"Agent选择: '{action}' ({api_time:.2f}s)")
            print(f"动作有效: {action in available_actions}")
            
            # 显示RAG Agent的知识使用情况
            if hasattr(agent, 'get_stats'):
                stats = agent.get_stats()
                if stats.get('kg_queries', 0) > 0:
                    print(f"KG使用: {stats['kg_queries']}查询, {stats['kg_hits']}命中")
            
        except Exception as e:
            print(f"❌ Agent决策失败: {e}")
            action = available_actions[0] if available_actions else "look"
            api_time = time.time() - start_time
        
        actions_taken.append(action)
        
        # 执行动作
        observation, reward, done, info = env.step(action)
        total_reward += reward
        step_count += 1
        
        print(f"执行结果: 奖励={reward}, 完成={done}")
        print(f"新观察: {observation}")
        
        if done and reward > 0:
            print(f"🎉 {agent_name} 成功完成任务！")
            break
        elif reward < 0:
            print(f"⚠️ 负奖励，可能是错误动作")
    
    success = done and total_reward > 0
    
    print(f"\n📊 Episode {episode_num} 结果:")
    print(f"  成功: {success}")
    print(f"  总步数: {step_count}")
    print(f"  总奖励: {total_reward}")
    print(f"  动作序列: {actions_taken}")
    
    # 分析动作模式
    unique_actions = len(set(actions_taken))
    print(f"  动作多样性: {unique_actions}/{len(actions_taken)} ({unique_actions/len(actions_taken):.1%})")
    
    if len(actions_taken) > 5:
        last_5 = actions_taken[-5:]
        most_common = max(set(last_5), key=last_5.count)
        count = last_5.count(most_common)
        if count > 3:
            print(f"  ⚠️ 可能陷入循环: '{most_common}' 在最后5步中出现{count}次")
    
    return {
        'success': success,
        'total_steps': step_count,
        'total_reward': total_reward,
        'actions_taken': actions_taken,
        'agent_type': agent_name
    }

def test_three_agents():
    """测试三种Agent的表现"""
    print("🔬 三种Agent对比测试")
    print("=" * 60)
    print("对比: Baseline vs Fixed RAG vs Original RAG")
    
    # 创建环境
    env = TextWorldEnvironment('agent_comparison', {
        'difficulty': 'easy',
        'max_episode_steps': 15  # 减少步数，专注于效率
    })
    
    # 创建增强知识图谱
    print("\n📚 构建增强知识图谱...")
    kg = create_enhanced_knowledge_graph()
    retriever = KnowledgeGraphRetriever(kg, 'enhanced_retriever')
    print(f"✅ 知识图谱构建完成: {len(kg.facts)} 个事实")
    
    # 显示关键知识
    print("关键知识:")
    key_facts = [
        'key location kitchen',
        'go north leads to living room', 
        'go east leads to bedroom',
        'path to bedroom is north then east'
    ]
    for fact in key_facts:
        print(f"  - {fact}")
    
    # 创建三种Agent
    print("\n🤖 创建三种Agent...")
    
    # 1. Baseline Agent
    baseline_agent = BaselineAgent('baseline_test', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'temperature': 0.7,
        'max_tokens': 50
    })
    
    # 2. Fixed RAG Agent
    fixed_rag_agent = FixedRAGAgent('fixed_rag_test', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'use_knowledge_graph': True,
        'temperature': 0.7,
        'max_tokens': 80,
        'max_kg_facts': 2
    })
    fixed_rag_agent.set_knowledge_retriever(retriever)
    
    # 3. Original RAG Agent (for comparison)
    original_rag_agent = RAGAgent('original_rag_test', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'use_knowledge_graph': True,
        'use_react_reasoning': True,
        'temperature': 0.7,
        'max_tokens': 150,
        'max_kg_facts': 3
    })
    original_rag_agent.set_knowledge_retriever(retriever)
    
    print("✅ 三种Agent创建完成")
    
    # 运行测试
    agents = [
        (baseline_agent, "Baseline"),
        (fixed_rag_agent, "Fixed_RAG"),
        (original_rag_agent, "Original_RAG")
    ]
    
    all_results = []
    
    for agent, agent_name in agents:
        print(f"\n{'='*60}")
        print(f"🔬 测试 {agent_name}")
        print(f"{'='*60}")
        
        # 运行2个episodes
        for episode in range(2):
            result = run_single_episode_debug(agent, env, agent_name, episode + 1)
            all_results.append(result)
    
    # 生成对比报告
    print(f"\n{'='*60}")
    print("📊 最终对比结果")
    print(f"{'='*60}")
    
    for agent, agent_name in agents:
        agent_results = [r for r in all_results if r['agent_type'] == agent_name]
        
        if agent_results:
            success_rate = sum(1 for r in agent_results if r['success']) / len(agent_results)
            avg_steps = sum(r['total_steps'] for r in agent_results) / len(agent_results)
            avg_reward = sum(r['total_reward'] for r in agent_results) / len(agent_results)
            
            print(f"\n{agent_name}:")
            print(f"  Episodes: {len(agent_results)}")
            print(f"  成功率: {success_rate:.1%}")
            print(f"  平均步数: {avg_steps:.1f}")
            print(f"  平均奖励: {avg_reward:.3f}")
            
            # 显示成功的episodes
            successful = [r for r in agent_results if r['success']]
            if successful:
                print(f"  成功案例动作序列:")
                for i, r in enumerate(successful):
                    print(f"    Episode {i+1}: {r['actions_taken']}")
    
    return all_results

if __name__ == "__main__":
    print("🚀 修复RAG Agent测试")
    print("这将测试修复后的RAG Agent是否能超越Baseline")
    
    confirm = input("\n确认开始测试? (y/N): ").strip().lower()
    if confirm == 'y':
        results = test_three_agents()
        print(f"\n✅ 测试完成！")
    else:
        print("测试取消")
