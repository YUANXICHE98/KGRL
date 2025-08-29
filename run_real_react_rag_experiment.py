#!/usr/bin/env python3
"""
真实ReAct RAG Agent vs Baseline实验
使用真实GPT-4o API和完整的query_kg机制
"""

import sys
import time
import json
from pathlib import Path
sys.path.append('.')

from src.agents.baseline_agent import BaselineAgent
from src.agents.rag_agent import RAGAgent
from src.environments.textworld_env import TextWorldEnvironment
from src.knowledge.kg_builder import KnowledgeGraphBuilder
from src.knowledge.kg_retriever import KnowledgeGraphRetriever
from src.utils.logger import get_logger

def create_comprehensive_dodaf_kg():
    """创建全面的DODAF知识图谱"""
    kg = KnowledgeGraphBuilder('real_react_kg')
    
    print("📚 构建DODAF知识图谱...")
    
    # DA (Condition) - 状态和条件
    kg.add_fact('kitchen', 'contains', 'key', dodaf_type='DA')
    kg.add_fact('kitchen', 'contains', 'apple', dodaf_type='DA')
    kg.add_fact('kitchen', 'contains', 'fridge', dodaf_type='DA')
    kg.add_fact('chest', 'location', 'bedroom', dodaf_type='DA')
    kg.add_fact('living_room', 'connects', 'kitchen_and_bedroom', dodaf_type='DA')
    kg.add_fact('player', 'starts_in', 'kitchen', dodaf_type='DA')
    
    # DO (Action) - 动作和操作
    kg.add_fact('take', 'enables', 'key_possession', dodaf_type='DO')
    kg.add_fact('key', 'opens', 'chest', dodaf_type='DO')
    kg.add_fact('go_north', 'leads_to', 'living_room', dodaf_type='DO')
    kg.add_fact('go_east', 'leads_to', 'bedroom', dodaf_type='DO')
    kg.add_fact('open', 'works_with', 'chest', dodaf_type='DO')
    kg.add_fact('inventory', 'shows', 'carried_items', dodaf_type='DO')
    
    # F (Outcome) - 结果和目标
    kg.add_fact('goal', 'is', 'open_chest_in_bedroom', dodaf_type='F')
    kg.add_fact('success', 'requires', 'key_and_chest_access', dodaf_type='F')
    kg.add_fact('treasure', 'obtained_by', 'opening_chest', dodaf_type='F')
    kg.add_fact('mission_complete', 'when', 'chest_opened', dodaf_type='F')
    
    print(f"✅ DODAF知识图谱完成: {len(kg.facts)} 个事实")
    print("  DO (Action): 6个动作事实")
    print("  DA (Condition): 6个条件事实") 
    print("  F (Outcome): 4个结果事实")
    
    return kg

def run_single_real_episode(agent, env, agent_name, episode_num, max_steps=25):
    """运行单个真实episode"""
    logger = get_logger(f"{agent_name}_Real")
    
    print(f"\n🎮 {agent_name} Episode {episode_num} 开始")
    print("-" * 50)
    
    # 重置环境和Agent
    observation = env.reset()
    if hasattr(agent, 'reset'):
        agent.reset()
    
    episode_data = {
        'episode_id': episode_num,
        'agent_type': agent_name,
        'actions_taken': [],
        'kg_queries': 0,
        'kg_hits': 0,
        'api_calls': 0,
        'api_response_times': [],
        'start_time': time.time()
    }
    
    total_reward = 0
    done = False
    step_count = 0
    
    print(f"初始观察: {observation}")
    
    while not done and step_count < max_steps:
        available_actions = env.get_available_actions()
        
        print(f"\nStep {step_count + 1}:")
        print(f"  可用动作: {available_actions}")
        
        # Agent决策（真实API调用）
        start_time = time.time()
        try:
            action = agent.act(observation, available_actions)
            api_time = time.time() - start_time
            
            print(f"  Agent选择: '{action}' ({api_time:.2f}s)")
            
            episode_data['actions_taken'].append(action)
            episode_data['api_response_times'].append(api_time)
            
        except Exception as e:
            print(f"  ❌ Agent决策失败: {e}")
            action = available_actions[0] if available_actions else "look"
            api_time = time.time() - start_time
        
        # 执行动作
        observation, reward, done, info = env.step(action)
        total_reward += reward
        step_count += 1
        
        print(f"  执行结果: 奖励={reward}, 完成={done}")
        print(f"  新观察: {observation}")
        
        if done and reward > 0:
            print(f"  🎉 {agent_name} 成功完成任务！")
            break
        elif reward < 0:
            print(f"  ⚠️ 负奖励，可能是错误动作")
    
    # 收集统计信息
    success = done and total_reward > 0
    completion_time = time.time() - episode_data['start_time']
    
    if hasattr(agent, 'get_stats'):
        stats = agent.get_stats()
        episode_data['kg_queries'] = stats.get('kg_queries', 0)
        episode_data['kg_hits'] = stats.get('kg_hits', 0)
        episode_data['api_calls'] = stats.get('api_calls', 0)
    
    episode_data.update({
        'success': success,
        'total_steps': step_count,
        'total_reward': total_reward,
        'completion_time': completion_time,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })
    
    print(f"\n📊 Episode {episode_num} 结果:")
    print(f"  成功: {success}")
    print(f"  总步数: {step_count}")
    print(f"  总奖励: {total_reward:.3f}")
    print(f"  完成时间: {completion_time:.1f}s")
    
    if episode_data['kg_queries'] > 0:
        hit_rate = episode_data['kg_hits'] / episode_data['kg_queries']
        print(f"  KG使用: {episode_data['kg_queries']}查询, {hit_rate:.2%}命中率")
    
    return episode_data

def run_real_react_rag_experiment():
    """运行真实ReAct RAG实验"""
    print("🚀 真实ReAct RAG vs Baseline实验")
    print("=" * 60)
    print("使用真实GPT-4o API和完整query_kg机制")
    
    # 创建环境
    env = TextWorldEnvironment('real_react_exp', {
        'difficulty': 'easy',
        'max_episode_steps': 25
    })
    
    # 创建DODAF知识图谱
    kg = create_comprehensive_dodaf_kg()
    retriever = KnowledgeGraphRetriever(kg, 'real_react_retriever')
    
    # 创建Agents
    print(f"\n🤖 创建对比Agents...")
    
    # 1. Baseline Agent
    baseline_agent = BaselineAgent('real_baseline', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'temperature': 0.7,
        'max_tokens': 100
    })
    print("✅ Baseline Agent创建")
    
    # 2. ReAct RAG Agent
    react_rag_agent = RAGAgent('real_react_rag', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'use_knowledge_graph': True,
        'use_react_reasoning': True,  # 启用真正的ReAct
        'temperature': 0.7,
        'max_tokens': 250,  # 增加token以支持ReAct推理
        'max_kg_facts': 3
    })
    react_rag_agent.set_knowledge_retriever(retriever)
    print("✅ ReAct RAG Agent创建")
    
    # 运行对比实验
    all_results = []
    episodes_per_agent = 4  # 每种Agent运行4个episodes
    
    agents = [
        (baseline_agent, "Baseline_Real"),
        (react_rag_agent, "ReAct_RAG_Real")
    ]
    
    for agent, agent_name in agents:
        print(f"\n{'='*60}")
        print(f"🔬 运行 {agent_name} 实验 ({episodes_per_agent} episodes)")
        print(f"{'='*60}")
        
        for episode in range(episodes_per_agent):
            result = run_single_real_episode(agent, env, agent_name, episode + 1)
            all_results.append(result)
            
            # 短暂休息避免API限制
            if episode < episodes_per_agent - 1:
                print("⏳ 短暂休息...")
                time.sleep(2)
    
    # 保存结果
    print(f"\n💾 保存实验结果...")
    output_dir = Path("results/real_react_rag_experiment")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    json_file = output_dir / f"react_rag_results_{timestamp}.json"
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # 生成对比报告
    print(f"\n📊 真实实验结果对比:")
    print("=" * 60)
    
    for agent, agent_name in agents:
        agent_results = [r for r in all_results if r['agent_type'] == agent_name]
        
        if agent_results:
            success_rate = sum(1 for r in agent_results if r['success']) / len(agent_results)
            avg_steps = sum(r['total_steps'] for r in agent_results) / len(agent_results)
            avg_reward = sum(r['total_reward'] for r in agent_results) / len(agent_results)
            avg_time = sum(r['completion_time'] for r in agent_results) / len(agent_results)
            avg_api_time = sum(sum(r['api_response_times']) for r in agent_results) / len(agent_results)
            
            print(f"\n{agent_name}:")
            print(f"  Episodes: {len(agent_results)}")
            print(f"  成功率: {success_rate:.1%}")
            print(f"  平均步数: {avg_steps:.1f}")
            print(f"  平均奖励: {avg_reward:.3f}")
            print(f"  平均完成时间: {avg_time:.1f}s")
            print(f"  平均API时间: {avg_api_time:.1f}s")
            
            # ReAct RAG特定统计
            if 'ReAct_RAG' in agent_name:
                total_kg_queries = sum(r['kg_queries'] for r in agent_results)
                total_kg_hits = sum(r['kg_hits'] for r in agent_results)
                if total_kg_queries > 0:
                    kg_hit_rate = total_kg_hits / total_kg_queries
                    print(f"  KG查询统计: {total_kg_queries}次查询, {kg_hit_rate:.2%}命中率")
                
                # 显示成功案例的动作序列
                successful = [r for r in agent_results if r['success']]
                if successful:
                    print(f"  成功案例动作序列:")
                    for i, r in enumerate(successful):
                        print(f"    Episode {r['episode_id']}: {r['actions_taken']}")
    
    print(f"\n✅ 真实ReAct RAG实验完成!")
    print(f"📁 结果文件: {json_file}")
    
    return json_file

if __name__ == "__main__":
    print("🎯 真实ReAct RAG Agent实验")
    print("这将使用:")
    print("  ✅ 真实GPT-4o API调用")
    print("  ✅ 真正的ReAct循环 (Thought → Action(query_kg) → Observation)")
    print("  ✅ DODAF结构化知识图谱")
    print("  ✅ 动态query_kg机制")
    print("  ✅ 与Baseline Agent对比")
    
    confirm = input("\n确认开始真实实验? (y/N): ").strip().lower()
    if confirm == 'y':
        run_real_react_rag_experiment()
    else:
        print("实验取消")
