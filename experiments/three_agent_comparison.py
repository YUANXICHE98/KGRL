"""
三种Agent对比实验
Baseline vs Complex RAG vs Simple RAG
"""

import sys
import time
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.baseline_agent import BaselineAgent
from src.agents.rag_agent import RAGAgent
from src.agents.simple_rag_agent import SimpleRAGAgent
from src.environments.textworld_env import TextWorldEnvironment
from src.knowledge.kg_builder import KnowledgeGraphBuilder
from src.knowledge.kg_retriever import KnowledgeGraphRetriever
from src.utils.logger import get_logger

def create_focused_knowledge_graph():
    """创建专注于任务的知识图谱"""
    kg = KnowledgeGraphBuilder('focused_game_knowledge')
    
    # 核心任务知识
    kg.add_fact('goal', 'is', 'find key and open chest')
    kg.add_fact('key', 'location', 'kitchen')
    kg.add_fact('chest', 'location', 'bedroom')
    kg.add_fact('key', 'opens', 'chest')
    
    # 房间连接
    kg.add_fact('kitchen', 'exit', 'north')
    kg.add_fact('bedroom', 'entrance', 'from living room')
    kg.add_fact('living room', 'connects', 'kitchen and bedroom')
    
    # 关键动作
    kg.add_fact('take', 'works_with', 'key')
    kg.add_fact('open', 'works_with', 'chest')
    kg.add_fact('go', 'directions', 'north south east west')
    
    return kg

def run_single_episode(agent, env, agent_name, episode_num):
    """运行单个episode"""
    logger = get_logger(f"{agent_name}_Episode")
    
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
        'api_response_times': [],
        'start_time': time.time()
    }
    
    total_reward = 0
    done = False
    step_count = 0
    max_steps = 30
    
    logger.info(f"开始 {agent_name} Episode {episode_num}")
    logger.debug(f"初始观察: {observation}")
    
    while not done and step_count < max_steps:
        available_actions = env.get_available_actions()
        
        # Agent决策
        start_time = time.time()
        try:
            action = agent.act(observation, available_actions)
            api_time = time.time() - start_time
            
            episode_data['actions_taken'].append(action)
            episode_data['api_response_times'].append(api_time)
            
            logger.debug(f"Step {step_count + 1}: {action} ({api_time:.2f}s)")
            
        except Exception as e:
            logger.error(f"Agent决策失败: {e}")
            action = available_actions[0] if available_actions else "look"
            api_time = time.time() - start_time
        
        # 执行动作
        observation, reward, done, info = env.step(action)
        total_reward += reward
        step_count += 1
        
        if done and reward > 0:
            logger.info(f"🎉 {agent_name} Episode {episode_num} 成功完成！")
            break
    
    # 记录结果
    success = done and total_reward > 0
    completion_time = time.time() - episode_data['start_time']
    
    # 获取Agent统计
    if hasattr(agent, 'get_stats'):
        stats = agent.get_stats()
        episode_data['kg_queries'] = stats.get('kg_queries', 0)
        episode_data['kg_hits'] = stats.get('kg_hits', 0)
    
    episode_data.update({
        'success': success,
        'total_steps': step_count,
        'total_reward': total_reward,
        'completion_time': completion_time,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })
    
    logger.info(f"{agent_name} Episode {episode_num} 完成: "
               f"成功={success}, 步数={step_count}, 奖励={total_reward:.3f}")
    
    if episode_data['kg_queries'] > 0:
        hit_rate = episode_data['kg_hits'] / episode_data['kg_queries']
        logger.info(f"  KG使用: 查询={episode_data['kg_queries']}, 命中率={hit_rate:.2%}")
    
    return episode_data

def run_three_agent_comparison(episodes_per_agent=4):
    """运行三种Agent的对比实验"""
    print("🔬 三种Agent对比实验")
    print("=" * 60)
    print("对比: Baseline vs Complex RAG vs Simple RAG")
    
    # 创建环境
    env = TextWorldEnvironment('three_agent_comparison', {
        'difficulty': 'easy',
        'max_episode_steps': 30
    })
    
    # 创建知识图谱
    print("\n📚 构建专注的知识图谱...")
    kg = create_focused_knowledge_graph()
    retriever = KnowledgeGraphRetriever(kg, 'focused_retriever')
    print(f"✅ 知识图谱构建完成: {len(kg.facts)} 个事实")
    
    # 创建三种Agent
    print("\n🤖 创建三种Agent...")
    
    # 1. Baseline Agent
    baseline_agent = BaselineAgent('baseline_comparison', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'temperature': 0.7,
        'max_tokens': 100
    })
    
    # 2. Complex RAG Agent
    complex_rag_agent = RAGAgent('complex_rag_comparison', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'use_knowledge_graph': True,
        'use_react_reasoning': True,
        'temperature': 0.7,
        'max_tokens': 200,
        'max_kg_facts': 5
    })
    complex_rag_agent.set_knowledge_retriever(retriever)
    
    # 3. Simple RAG Agent
    simple_rag_agent = SimpleRAGAgent('simple_rag_comparison', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'use_knowledge_graph': True,
        'temperature': 0.7,
        'max_tokens': 100,
        'max_kg_facts': 3,
        'kg_retrieval_method': 'keywords'
    })
    simple_rag_agent.set_knowledge_retriever(retriever)
    
    print("✅ 三种Agent创建完成")
    
    # 运行实验
    all_results = []
    
    agents = [
        (baseline_agent, "Baseline_LLM"),
        (simple_rag_agent, "Simple_RAG_LLM"),
        (complex_rag_agent, "Complex_RAG_LLM")
    ]
    
    for agent, agent_name in agents:
        print(f"\n🔬 运行 {agent_name} 实验 ({episodes_per_agent} episodes)...")
        
        for episode in range(episodes_per_agent):
            result = run_single_episode(agent, env, agent_name, episode)
            all_results.append(result)
    
    # 保存结果
    print("\n💾 保存实验结果...")
    output_dir = Path("results/three_agent_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    json_file = output_dir / f"three_agent_results_{timestamp}.json"
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # 生成对比报告
    print("\n📊 实验结果对比:")
    print("=" * 60)
    
    for agent, agent_name in agents:
        agent_results = [r for r in all_results if r['agent_type'] == agent_name]
        
        if agent_results:
            success_rate = sum(1 for r in agent_results if r['success']) / len(agent_results)
            avg_steps = sum(r['total_steps'] for r in agent_results) / len(agent_results)
            avg_reward = sum(r['total_reward'] for r in agent_results) / len(agent_results)
            avg_time = sum(r['completion_time'] for r in agent_results) / len(agent_results)
            
            print(f"\n{agent_name}:")
            print(f"  Episodes: {len(agent_results)}")
            print(f"  成功率: {success_rate:.1%}")
            print(f"  平均步数: {avg_steps:.1f}")
            print(f"  平均奖励: {avg_reward:.3f}")
            print(f"  平均时间: {avg_time:.1f}s")
            
            # KG统计
            total_kg_queries = sum(r['kg_queries'] for r in agent_results)
            total_kg_hits = sum(r['kg_hits'] for r in agent_results)
            if total_kg_queries > 0:
                kg_hit_rate = total_kg_hits / total_kg_queries
                print(f"  KG命中率: {kg_hit_rate:.2%} ({total_kg_hits}/{total_kg_queries})")
    
    print(f"\n✅ 三种Agent对比实验完成!")
    print(f"📁 结果文件: {json_file}")
    
    return json_file

if __name__ == "__main__":
    print("🚀 三种Agent对比实验")
    print("这将对比:")
    print("  1. Baseline LLM (无知识图谱)")
    print("  2. Simple RAG LLM (简化知识图谱)")
    print("  3. Complex RAG LLM (完整ReAct推理)")
    
    confirm = input("\n确认开始对比实验? (y/N): ").strip().lower()
    if confirm == 'y':
        run_three_agent_comparison(episodes_per_agent=4)
    else:
        print("实验取消")
