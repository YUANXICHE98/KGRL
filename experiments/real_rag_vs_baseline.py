"""
真实RAG vs Baseline对比实验
使用真实的RAG Agent和知识图谱进行对比实验
"""

import sys
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.baseline_agent import BaselineAgent
from src.agents.rag_agent import RAGAgent
from src.environments.textworld_env import TextWorldEnvironment
from src.knowledge.kg_builder import KnowledgeGraphBuilder
from src.knowledge.kg_retriever import KnowledgeGraphRetriever
from src.utils.experiment_logger import ExperimentLogger
from src.utils.logger import get_logger

def create_game_knowledge_graph():
    """创建游戏相关的知识图谱"""
    kg = KnowledgeGraphBuilder('game_knowledge')
    
    # 房间和物品关系
    kg.add_fact('kitchen', 'contains', 'fridge')
    kg.add_fact('kitchen', 'contains', 'table')
    kg.add_fact('kitchen', 'has_exit', 'north')
    
    kg.add_fact('fridge', 'contains', 'apple')
    kg.add_fact('fridge', 'contains', 'milk')
    kg.add_fact('fridge', 'can_be', 'opened')
    
    kg.add_fact('bedroom', 'contains', 'chest')
    kg.add_fact('bedroom', 'contains', 'bed')
    kg.add_fact('bedroom', 'has_exit', 'south')
    
    kg.add_fact('chest', 'requires', 'key')
    kg.add_fact('chest', 'contains', 'treasure')
    kg.add_fact('chest', 'can_be', 'opened')
    
    kg.add_fact('key', 'opens', 'chest')
    kg.add_fact('key', 'location', 'kitchen')
    kg.add_fact('key', 'can_be', 'taken')
    
    # 动作相关知识
    kg.add_fact('take', 'works_with', 'key')
    kg.add_fact('take', 'works_with', 'apple')
    kg.add_fact('open', 'works_with', 'chest')
    kg.add_fact('open', 'works_with', 'fridge')
    kg.add_fact('go', 'works_with', 'north')
    kg.add_fact('go', 'works_with', 'south')
    
    # 目标相关知识
    kg.add_fact('goal', 'requires', 'key')
    kg.add_fact('goal', 'requires', 'chest')
    kg.add_fact('goal', 'action', 'open_chest')
    
    return kg

def run_agent_experiment(agent, env, exp_logger, agent_type, num_episodes=10):
    """运行单个Agent的实验"""
    logger = get_logger(f"{agent_type}Experiment")
    
    for episode in range(num_episodes):
        logger.info(f"开始 {agent_type} Episode {episode + 1}/{num_episodes}")
        
        # 开始记录episode
        episode_id = exp_logger.start_episode(
            agent_type=agent_type,
            model_name=getattr(agent, 'model_name', 'gpt-4o'),
            environment="TextWorld_Simulated",
            difficulty="easy",
            config={
                'use_knowledge_graph': getattr(agent, 'use_knowledge_graph', False),
                'use_react_reasoning': getattr(agent, 'use_react_reasoning', False),
                'temperature': getattr(agent, 'temperature', 0.7),
                'max_tokens': getattr(agent, 'max_tokens', 150)
            }
        )
        
        # 重置环境和Agent
        observation = env.reset()
        agent.reset()
        
        total_reward = 0
        done = False
        step_count = 0
        max_steps = 30
        
        logger.debug(f"初始观察: {observation}")
        
        while not done and step_count < max_steps:
            # 获取可用动作
            available_actions = env.get_available_actions()
            logger.debug(f"可用动作: {available_actions}")
            
            # Agent决策
            start_time = time.time()
            try:
                action = agent.act(observation, available_actions)
                api_time = time.time() - start_time
                is_valid = action in available_actions
                
                logger.debug(f"Agent选择: {action} (有效: {is_valid})")
                
            except Exception as e:
                logger.error(f"Agent决策失败: {e}")
                action = available_actions[0] if available_actions else "look"
                api_time = time.time() - start_time
                is_valid = False
            
            # 记录动作
            exp_logger.log_action(action, is_valid, api_time)
            
            # 如果是RAG Agent，记录KG查询
            if hasattr(agent, 'kg_queries') and hasattr(agent, 'kg_hits'):
                if step_count == 0:  # 记录初始状态
                    initial_kg_queries = agent.kg_queries
                    initial_kg_hits = agent.kg_hits
                else:
                    # 记录新的KG查询
                    new_queries = agent.kg_queries - getattr(agent, '_last_kg_queries', 0)
                    new_hits = agent.kg_hits - getattr(agent, '_last_kg_hits', 0)
                    if new_queries > 0:
                        exp_logger.log_kg_query(f"step_{step_count}", new_hits)
                
                agent._last_kg_queries = agent.kg_queries
                agent._last_kg_hits = agent.kg_hits
            
            # 执行动作
            observation, reward, done, info = env.step(action)
            total_reward += reward
            step_count += 1
            
            logger.debug(f"Step {step_count}: 奖励={reward}, 完成={done}, 新观察={observation[:100]}...")
            
            # 检查是否达到目标
            if done and reward > 0:
                logger.info(f"🎉 {agent_type} 成功完成任务！")
                break
        
        # 判断成功
        success = done and total_reward > 0
        
        # 结束episode记录
        result = exp_logger.end_episode(success, total_reward)
        
        logger.info(f"{agent_type} Episode {episode + 1} 完成: "
                   f"成功={success}, 步数={result.total_steps}, 奖励={total_reward:.3f}")
        
        # 如果是RAG Agent，显示KG使用统计
        if hasattr(agent, 'get_stats'):
            stats = agent.get_stats()
            if stats.get('kg_queries', 0) > 0:
                logger.info(f"  KG查询: {stats['kg_queries']}, 命中: {stats['kg_hits']}, "
                           f"命中率: {stats['kg_hit_rate']:.2%}")

def run_real_rag_vs_baseline_experiment(baseline_episodes=10, rag_episodes=10):
    """运行真实的RAG vs Baseline对比实验"""
    logger = get_logger("RealRAGExperiment")
    
    print("🧪 开始真实RAG vs Baseline对比实验")
    print("=" * 60)
    
    # 创建实验记录器
    exp_logger = ExperimentLogger("real_rag_vs_baseline")
    
    # 创建环境
    env = TextWorldEnvironment('real_rag_exp', {
        'difficulty': 'easy',
        'max_episode_steps': 30
    })
    
    # 创建知识图谱
    print("📚 构建游戏知识图谱...")
    kg = create_game_knowledge_graph()
    retriever = KnowledgeGraphRetriever(kg, 'game_retriever')
    print(f"✅ 知识图谱构建完成: {len(kg.facts)} 个事实")
    
    # 创建Baseline Agent
    print("🤖 创建Baseline Agent...")
    baseline_agent = BaselineAgent('baseline_real', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'temperature': 0.7,
        'max_tokens': 150
    })
    
    # 创建RAG Agent
    print("🧠 创建RAG Agent...")
    rag_agent = RAGAgent('rag_real', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'use_knowledge_graph': True,
        'use_react_reasoning': True,
        'temperature': 0.7,
        'max_tokens': 200,
        'max_kg_facts': 5,
        'kg_retrieval_method': 'semantic'
    })
    
    # 设置RAG Agent的知识检索器
    rag_agent.set_knowledge_retriever(retriever)
    print("✅ RAG Agent知识检索器设置完成")
    
    # 运行Baseline实验
    print(f"\n🔬 运行Baseline Agent实验 ({baseline_episodes} episodes)...")
    run_agent_experiment(baseline_agent, env, exp_logger, "Baseline_LLM_Real", baseline_episodes)
    
    # 运行RAG实验
    print(f"\n🔬 运行RAG Agent实验 ({rag_episodes} episodes)...")
    run_agent_experiment(rag_agent, env, exp_logger, "RAG_LLM_Real", rag_episodes)
    
    # 保存结果
    print("\n📊 保存实验结果...")
    json_file, csv_file = exp_logger.save_results()
    
    # 生成报告和图表
    print("📈 生成分析报告...")
    summary_report = exp_logger.generate_summary_report()
    comparison_plot = exp_logger.generate_comparison_plots()
    detailed_plot = exp_logger.generate_detailed_analysis()
    
    print("\n" + "="*60)
    print("🎉 真实RAG vs Baseline实验完成!")
    print("="*60)
    print(summary_report)
    
    print(f"\n📁 结果文件:")
    print(f"  数据: {json_file}")
    print(f"  CSV: {csv_file}")
    print(f"  对比图: {comparison_plot}")
    print(f"  详细分析: {detailed_plot}")
    
    return exp_logger

if __name__ == "__main__":
    print("🚀 真实RAG Agent实验")
    print("这将使用真实的:")
    print("  ✅ GPT-4o API调用")
    print("  ✅ 知识图谱检索")
    print("  ✅ ReAct推理框架")
    print("  ✅ 完整的RAG管道")
    
    confirm = input("\n确认开始实验? (y/N): ").strip().lower()
    if confirm == 'y':
        run_real_rag_vs_baseline_experiment(baseline_episodes=8, rag_episodes=8)
    else:
        print("实验取消")
