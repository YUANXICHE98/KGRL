#!/usr/bin/env python3
"""
KGRL评估脚本
用于运行和比较不同Agent的性能
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.baseline_agent import BaselineAgent
from src.environments.textworld_env import TextWorldEnvironment
from src.knowledge.kg_builder import KnowledgeGraphBuilder
from src.knowledge.kg_retriever import KnowledgeGraphRetriever
from src.utils.metrics import MetricsCalculator, EpisodeMetrics
from src.utils.visualization import ExperimentVisualizer
from src.utils.logger import create_experiment_logger, setup_logging
from config.base_config import config
from config.agent_config import agent_configs
from config.env_config import env_config

class EvaluationRunner:
    """评估运行器"""
    
    def __init__(self, num_episodes: int = 50, max_steps: int = 50):
        self.num_episodes = num_episodes
        self.max_steps = max_steps
        self.logger = create_experiment_logger("evaluation")
        
        # 结果存储
        self.results = {}
        self.metrics_calculators = {}
        
        # 可视化器
        self.visualizer = ExperimentVisualizer()
        
        self.logger.info(f"Initialized evaluation with {num_episodes} episodes, {max_steps} max steps")
    
    def setup_environment(self) -> TextWorldEnvironment:
        """设置评估环境"""
        env_config_dict = {
            "max_episode_steps": self.max_steps,
            "difficulty": "medium",
            "nb_objects": 8,
            "nb_rooms": 4,
            "quest_length": 4
        }
        
        environment = TextWorldEnvironment("eval_env", env_config_dict)
        self.logger.info("Evaluation environment created")
        return environment
    
    def setup_knowledge_graph(self) -> KnowledgeGraphBuilder:
        """设置知识图谱"""
        kg_builder = KnowledgeGraphBuilder("eval_kg")
        
        # 加载示例知识图谱
        kg_file = config.KG_DIR / "example_basic_kg.json"
        if kg_file.exists():
            kg_builder.load_from_file(kg_file)
            self.logger.info(f"Loaded knowledge graph from {kg_file}")
        else:
            # 创建基础知识图谱
            basic_facts = [
                ("kitchen", "connected_to", "living_room"),
                ("living_room", "connected_to", "bedroom"),
                ("bedroom", "connected_to", "bathroom"),
                ("fridge", "located_in", "kitchen"),
                ("chest", "located_in", "bedroom"),
                ("key", "located_in", "kitchen"),
                ("treasure", "hidden_in", "chest"),
                ("key", "opens", "chest"),
                ("chest", "requires", "key"),
            ]
            
            for subject, predicate, obj in basic_facts:
                kg_builder.add_fact(subject, predicate, obj)
            
            self.logger.info("Created basic knowledge graph")
        
        return kg_builder
    
    def create_baseline_agent(self, agent_id: str) -> BaselineAgent:
        """创建基线Agent"""
        baseline_config = agent_configs.baseline
        agent_config_dict = {
            "model_name": baseline_config.model_name,
            "use_local_model": baseline_config.use_local_model,
            "max_tokens": baseline_config.max_tokens,
            "temperature": baseline_config.temperature,
            "system_prompt": baseline_config.system_prompt,
            "max_retries": baseline_config.max_retries
        }
        
        return BaselineAgent(agent_id, agent_config_dict)
    
    def evaluate_agent(self, agent, environment, agent_name: str) -> Dict[str, Any]:
        """评估单个Agent"""
        self.logger.info(f"Evaluating {agent_name}...")
        
        metrics_calc = MetricsCalculator()
        episode_results = []
        
        for episode_id in range(1, self.num_episodes + 1):
            try:
                # 重置环境和Agent
                observation = environment.reset()
                agent.reset()
                
                episode_start_time = time.time()
                episode_reward = 0.0
                invalid_actions = 0
                kg_queries = 0
                successful_queries = 0
                
                for step in range(self.max_steps):
                    # Agent选择动作
                    available_actions = environment.get_available_actions()
                    action = agent.act(observation, available_actions)
                    
                    # 检查是否为无效动作
                    if not environment.validate_action(action):
                        invalid_actions += 1
                    
                    # 执行动作
                    new_observation, reward, done, info = environment.step(action)
                    agent.update(action, new_observation, reward, done, info)
                    
                    episode_reward += reward
                    observation = new_observation
                    
                    if done:
                        break
                
                episode_duration = time.time() - episode_start_time
                success = episode_reward > 0  # 简单的成功判断
                
                # 创建episode指标
                episode_metrics = EpisodeMetrics(
                    episode_id=episode_id,
                    success=success,
                    total_reward=episode_reward,
                    step_count=step + 1,
                    duration=episode_duration,
                    invalid_actions=invalid_actions,
                    kg_queries=kg_queries,
                    successful_queries=successful_queries
                )
                
                metrics_calc.add_episode(episode_metrics)
                episode_results.append(episode_metrics.to_dict())
                
                if episode_id % 10 == 0:
                    self.logger.info(f"{agent_name} - Episode {episode_id}/{self.num_episodes} completed")
                
            except Exception as e:
                self.logger.error(f"Error in episode {episode_id} for {agent_name}: {e}")
                continue
        
        # 计算聚合指标
        aggregate_metrics = metrics_calc.calculate_aggregate_metrics()
        learning_curve = metrics_calc.calculate_learning_curve()
        
        results = {
            "agent_name": agent_name,
            "aggregate_metrics": aggregate_metrics,
            "episode_results": episode_results,
            "learning_curve": learning_curve,
            "agent_config": agent.get_config()
        }
        
        self.metrics_calculators[agent_name] = metrics_calc
        self.logger.info(f"{agent_name} evaluation completed - Success rate: {aggregate_metrics.get('success_rate', 0):.2%}")
        
        return results
    
    def run_comparison(self, agent_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """运行多个Agent的对比评估"""
        self.logger.info("Starting agent comparison evaluation...")
        
        # 设置环境和知识图谱
        environment = self.setup_environment()
        kg_builder = self.setup_knowledge_graph()
        
        comparison_results = {
            "evaluation_config": {
                "num_episodes": self.num_episodes,
                "max_steps": self.max_steps,
                "environment": "TextWorld",
                "knowledge_graph": kg_builder.get_stats()
            },
            "agents": {}
        }
        
        # 评估每个Agent
        for agent_config in agent_configs:
            agent_name = agent_config["name"]
            agent_type = agent_config["type"]
            
            if agent_type == "baseline":
                agent = self.create_baseline_agent(f"eval_{agent_name}")
            else:
                self.logger.warning(f"Agent type {agent_type} not implemented yet")
                continue
            
            # 运行评估
            agent_results = self.evaluate_agent(agent, environment, agent_name)
            comparison_results["agents"][agent_name] = agent_results["aggregate_metrics"]
            
            # 保存详细结果
            detailed_results_file = config.RESULTS_DIR / f"{agent_name}_detailed_results.json"
            with open(detailed_results_file, 'w') as f:
                json.dump(agent_results, f, indent=2, default=str)
        
        # 生成对比分析
        if len(comparison_results["agents"]) > 1:
            agent_names = list(comparison_results["agents"].keys())
            if len(agent_names) >= 2:
                calc1 = self.metrics_calculators[agent_names[0]]
                calc2 = self.metrics_calculators[agent_names[1]]
                comparison_analysis = calc1.compare_agents(calc2, agent_names[0], agent_names[1])
                comparison_results["comparison_analysis"] = comparison_analysis
        
        # 生成可视化
        self.logger.info("Generating visualizations...")
        plots = self.visualizer.create_experiment_report(
            comparison_results, 
            title="Agent Comparison Evaluation"
        )
        comparison_results["generated_plots"] = plots
        
        # 保存摘要表格
        summary_table = self.visualizer.save_summary_table(
            comparison_results["agents"], 
            "evaluation_summary.csv"
        )
        comparison_results["summary_table"] = summary_table
        
        # 清理资源
        environment.close()
        
        self.logger.info("Agent comparison evaluation completed!")
        return comparison_results

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="KGRL Agent Evaluation")
    parser.add_argument("--episodes", type=int, default=50, help="Number of episodes to run")
    parser.add_argument("--max-steps", type=int, default=50, help="Maximum steps per episode")
    parser.add_argument("--agents", nargs="+", default=["baseline"], help="Agents to evaluate")
    parser.add_argument("--output", default="evaluation_results.json", help="Output file name")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(log_level=args.log_level)
    
    # 准备Agent配置
    agent_configs = []
    for agent_name in args.agents:
        if agent_name == "baseline":
            agent_configs.append({"name": "Baseline_LLM", "type": "baseline"})
        # 可以添加更多Agent类型
    
    # 运行评估
    evaluator = EvaluationRunner(args.episodes, args.max_steps)
    
    try:
        results = evaluator.run_comparison(agent_configs)
        
        # 保存结果
        output_file = config.RESULTS_DIR / args.output
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # 打印摘要
        print("\n" + "="*60)
        print("EVALUATION RESULTS SUMMARY")
        print("="*60)
        
        for agent_name, metrics in results["agents"].items():
            print(f"\n{agent_name}:")
            print(f"  Success Rate: {metrics.get('success_rate', 0):.2%}")
            print(f"  Average Steps: {metrics.get('average_steps', 0):.1f}")
            print(f"  Average Reward: {metrics.get('average_reward', 0):.3f}")
            print(f"  Invalid Action Rate: {metrics.get('invalid_action_rate', 0):.2%}")
        
        print(f"\nDetailed results saved to: {output_file}")
        print(f"Plots saved to: {config.RESULTS_DIR / 'plots'}")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\nEvaluation interrupted by user")
    except Exception as e:
        print(f"Evaluation failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import time
    sys.exit(main())
