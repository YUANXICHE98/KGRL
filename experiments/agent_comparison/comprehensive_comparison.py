"""
完整的真实RAG vs Baseline实验
确保数据正确保存到results/real_rag_vs_baseline/data/
"""

import sys
import time
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.agents.baseline_agent import BaselineAgent
from src.agents.react_agent import ReactAgent
from src.environments.textworld_env import TextWorldEnvironment
from src.knowledge.kg_builder import KnowledgeGraphBuilder
from src.knowledge.kg_retriever import KnowledgeGraphRetriever
from src.utils.experiment_logger import ExperimentLogger
from src.utils.logger import get_logger

def create_comprehensive_knowledge_graph():
    """创建全面的游戏知识图谱"""
    kg = KnowledgeGraphBuilder('comprehensive_game_knowledge')
    
    # 房间结构
    kg.add_fact('kitchen', 'type', 'room')
    kg.add_fact('bedroom', 'type', 'room')
    kg.add_fact('kitchen', 'connects_to', 'bedroom')
    kg.add_fact('bedroom', 'connects_to', 'kitchen')
    
    # 房间内容
    kg.add_fact('kitchen', 'contains', 'fridge')
    kg.add_fact('kitchen', 'contains', 'table')
    kg.add_fact('kitchen', 'contains', 'key')
    kg.add_fact('bedroom', 'contains', 'chest')
    kg.add_fact('bedroom', 'contains', 'bed')
    
    # 物品属性
    kg.add_fact('fridge', 'type', 'container')
    kg.add_fact('fridge', 'contains', 'apple')
    kg.add_fact('fridge', 'can_be', 'opened')
    kg.add_fact('chest', 'type', 'container')
    kg.add_fact('chest', 'contains', 'treasure')
    kg.add_fact('chest', 'requires', 'key')
    kg.add_fact('key', 'type', 'item')
    kg.add_fact('key', 'opens', 'chest')
    kg.add_fact('apple', 'type', 'food')
    
    # 动作知识
    kg.add_fact('take', 'works_with', 'key')
    kg.add_fact('take', 'works_with', 'apple')
    kg.add_fact('open', 'works_with', 'chest')
    kg.add_fact('open', 'works_with', 'fridge')
    kg.add_fact('go', 'direction', 'north')
    kg.add_fact('go', 'direction', 'south')
    
    # 策略知识
    kg.add_fact('strategy', 'first_step', 'find_key')
    kg.add_fact('strategy', 'second_step', 'go_to_bedroom')
    kg.add_fact('strategy', 'final_step', 'open_chest')
    kg.add_fact('goal', 'requires', 'key_and_chest')
    
    return kg

def run_single_agent_episodes(agent, env, agent_type, num_episodes=8):
    """运行单个Agent的episodes并返回结果数据"""
    logger = get_logger(f"{agent_type}_Experiment")
    results = []
    
    for episode in range(num_episodes):
        logger.info(f"开始 {agent_type} Episode {episode + 1}/{num_episodes}")
        
        # 记录episode开始时间
        episode_start_time = time.time()
        
        # 重置环境和Agent
        observation = env.reset()
        if hasattr(agent, 'reset'):
            agent.reset()
        
        # Episode数据
        episode_data = {
            'episode_id': episode,
            'agent_type': agent_type,
            'model_name': getattr(agent, 'model_name', 'gpt-4o'),
            'environment': 'TextWorld_Simulated',
            'difficulty': 'easy',
            'use_knowledge_graph': getattr(agent, 'use_knowledge_graph', False),
            'use_react_reasoning': getattr(agent, 'use_react_reasoning', False),
            'temperature': getattr(agent, 'temperature', 0.7),
            'max_tokens': getattr(agent, 'max_tokens', 150),
            'actions_taken': [],
            'invalid_actions': 0,
            'kg_queries': 0,
            'kg_hits': 0,
            'api_calls': 0,
            'api_response_times': [],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        total_reward = 0
        done = False
        step_count = 0
        max_steps = 30
        
        logger.debug(f"初始观察: {observation}")
        
        while not done and step_count < max_steps:
            # 获取可用动作
            available_actions = env.get_available_actions()
            
            # Agent决策
            start_time = time.time()
            try:
                action = agent.act(observation, available_actions)
                api_time = time.time() - start_time
                is_valid = action in available_actions
                
                # 记录API调用
                episode_data['api_calls'] += 1
                episode_data['api_response_times'].append(api_time)
                episode_data['actions_taken'].append(action)
                
                if not is_valid:
                    episode_data['invalid_actions'] += 1
                
                logger.debug(f"Agent选择: {action} (有效: {is_valid}, 时间: {api_time:.2f}s)")
                
            except Exception as e:
                logger.error(f"Agent决策失败: {e}")
                action = available_actions[0] if available_actions else "look"
                api_time = time.time() - start_time
                is_valid = False
                episode_data['invalid_actions'] += 1
            
            # 记录RAG Agent的KG使用情况
            if hasattr(agent, 'kg_queries') and hasattr(agent, 'kg_hits'):
                episode_data['kg_queries'] = agent.kg_queries
                episode_data['kg_hits'] = agent.kg_hits
            
            # 执行动作
            observation, reward, done, info = env.step(action)
            total_reward += reward
            step_count += 1
            
            logger.debug(f"Step {step_count}: 奖励={reward}, 完成={done}")
            
            if done and reward > 0:
                logger.info(f"🎉 {agent_type} Episode {episode + 1} 成功完成任务！")
                break
        
        # 完成episode
        episode_end_time = time.time()
        success = done and total_reward > 0
        
        episode_data.update({
            'success': success,
            'total_steps': step_count,
            'total_reward': total_reward,
            'completion_time': episode_end_time - episode_start_time
        })
        
        results.append(episode_data)
        
        logger.info(f"{agent_type} Episode {episode + 1} 完成: "
                   f"成功={success}, 步数={step_count}, 奖励={total_reward:.3f}")
        
        # 显示RAG统计
        if hasattr(agent, 'get_stats'):
            stats = agent.get_stats()
            if stats.get('kg_queries', 0) > 0:
                logger.info(f"  KG使用: 查询={stats['kg_queries']}, "
                           f"命中={stats['kg_hits']}, 命中率={stats['kg_hit_rate']:.2%}")
    
    return results

def save_experiment_data(baseline_results, rag_results, output_dir="results/real_rag_vs_baseline"):
    """保存实验数据"""
    output_path = Path(output_dir)
    
    # 创建目录结构
    data_dir = output_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 合并所有结果
    all_results = baseline_results + rag_results
    
    # 生成时间戳
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    
    # 保存JSON格式
    json_file = data_dir / f"real_experiment_results_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # 保存CSV格式
    import pandas as pd
    csv_file = data_dir / f"real_experiment_results_{timestamp}.csv"
    df = pd.DataFrame(all_results)
    df.to_csv(csv_file, index=False)
    
    print(f"✅ 实验数据已保存:")
    print(f"  JSON: {json_file}")
    print(f"  CSV: {csv_file}")
    
    return json_file, csv_file, all_results

def run_complete_real_experiment():
    """运行完整的真实实验"""
    print("🚀 完整真实RAG vs Baseline实验")
    print("=" * 60)
    print("这将使用:")
    print("  ✅ 真实GPT-4o API调用")
    print("  ✅ 真实知识图谱检索")
    print("  ✅ 真实ReAct推理")
    print("  ✅ 完整数据保存")
    
    # 创建环境
    env = TextWorldEnvironment('complete_real_exp', {
        'difficulty': 'easy',
        'max_episode_steps': 30
    })
    
    # 创建知识图谱
    print("\n📚 构建知识图谱...")
    kg = create_comprehensive_knowledge_graph()
    retriever = KnowledgeGraphRetriever(kg, 'complete_retriever')
    print(f"✅ 知识图谱构建完成: {len(kg.facts)} 个事实")
    
    # 创建Baseline Agent
    print("\n🤖 创建Baseline Agent...")
    baseline_agent = BaselineAgent('baseline_complete', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'temperature': 0.7,
        'max_tokens': 150
    })
    
    # 创建React Agent
    print("🧠 创建React Agent...")
    react_agent = ReactAgent('react_complete', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'use_knowledge_graph': True,
        'use_react_reasoning': True,
        'temperature': 0.7,
        'max_tokens': 200,
        'max_kg_facts': 5
    })
    react_agent.set_knowledge_retriever(retriever)

    # 运行实验
    print("\n🔬 运行Baseline Agent实验...")
    baseline_results = run_single_agent_episodes(baseline_agent, env, "Baseline_LLM_Real", 6)

    print("\n🔬 运行React Agent实验...")
    react_results = run_single_agent_episodes(react_agent, env, "React_LLM_Real", 6)
    
    # 保存数据
    print("\n💾 保存实验数据...")
    json_file, csv_file, all_results = save_experiment_data(baseline_results, react_results)
    
    # 生成摘要
    print("\n📊 实验结果摘要:")
    baseline_success = sum(1 for r in baseline_results if r['success']) / len(baseline_results)
    react_success = sum(1 for r in react_results if r['success']) / len(react_results)

    print(f"  Baseline Agent: {baseline_success:.1%} 成功率")
    print(f"  React Agent: {react_success:.1%} 成功率")
    print(f"  改进: {(react_success - baseline_success):.1%}")
    
    return json_file, csv_file

if __name__ == "__main__":
    confirm = input("确认运行完整真实实验? (y/N): ").strip().lower()
    if confirm == 'y':
        run_complete_real_experiment()
    else:
        print("实验取消")
