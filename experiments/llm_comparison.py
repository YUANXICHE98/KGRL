"""
LLM比较实验
比较不同语言模型在KGRL任务上的性能
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.baseline_agent import BaselineAgent
from src.environments.textworld_env import TextWorldEnvironment
from src.knowledge.kg_builder import KnowledgeGraphBuilder
from src.utils.metrics import MetricsCalculator, EpisodeMetrics
from src.utils.visualization import ExperimentVisualizer
from src.utils.logger import create_experiment_logger, setup_logging
from config.base_config import config
from config.llm_config import get_available_llms, get_recommended_llms_for_comparison, llm_manager

class LLMComparisonExperiment:
    """LLM比较实验"""
    
    def __init__(self, num_episodes: int = 20, max_steps: int = 30):
        self.num_episodes = num_episodes
        self.max_steps = max_steps
        self.logger = create_experiment_logger("llm_comparison")
        self.results_dir = config.RESULTS_DIR / "llm_comparison"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # 可视化器
        self.visualizer = ExperimentVisualizer(str(self.results_dir / "plots"))
        
        self.logger.info(f"Initialized LLM comparison with {num_episodes} episodes")
    
    def setup_environment(self):
        """设置实验环境"""
        env_config = {
            "max_episode_steps": self.max_steps,
            "difficulty": "easy",  # 使用简单难度确保公平比较
            "nb_objects": 5,
            "nb_rooms": 3,
            "quest_length": 3
        }
        
        environment = TextWorldEnvironment("llm_comparison_env", env_config)
        self.logger.info("LLM comparison environment created")
        return environment
    
    def create_agent_for_llm(self, llm_key: str) -> BaselineAgent:
        """为指定LLM创建Agent"""
        llm_config = llm_manager.get_config(llm_key)
        if not llm_config:
            raise ValueError(f"LLM {llm_key} not found or not available")
        
        agent_config = {
            "model_name": llm_config.model_id,
            "use_local_model": llm_config.provider in ["huggingface", "local"],
            "max_tokens": min(llm_config.max_tokens, 512),  # 限制token数量
            "temperature": llm_config.temperature,
            "max_retries": 2,  # 减少重试次数以加快实验
            "system_prompt": self._get_optimized_prompt()
        }
        
        return BaselineAgent(f"agent_{llm_key}", agent_config)
    
    def _get_optimized_prompt(self) -> str:
        """获取优化的系统提示词"""
        return """You are playing a text adventure game. Your goal is to complete the task efficiently.

Rules:
1. Read the observation carefully
2. Choose ONE action that helps progress toward the goal
3. Respond with only the action command, nothing else
4. Common actions: look, go [direction], take [item], open [container], use [item]

Example:
Observation: "You are in a kitchen. There is a key on the table."
Response: take key

Be concise and direct."""
    
    def run_single_llm_evaluation(self, llm_key: str, environment) -> Dict[str, Any]:
        """运行单个LLM的评估"""
        self.logger.info(f"Evaluating LLM: {llm_key}")
        
        # 创建Agent
        try:
            agent = self.create_agent_for_llm(llm_key)
        except Exception as e:
            self.logger.error(f"Failed to create agent for {llm_key}: {e}")
            return {"error": str(e)}
        
        # 运行episodes
        metrics_calc = MetricsCalculator()
        episode_results = []
        total_cost = 0.0
        
        for episode_id in range(1, self.num_episodes + 1):
            try:
                # 重置环境和Agent
                observation = environment.reset()
                agent.reset()
                
                episode_start_time = time.time()
                episode_reward = 0.0
                invalid_actions = 0
                total_tokens_used = 0
                
                for step in range(self.max_steps):
                    # Agent选择动作
                    available_actions = environment.get_available_actions()
                    action = agent.act(observation, available_actions)
                    
                    # 估算token使用量（粗略估计）
                    estimated_tokens = len(observation.split()) + len(action.split()) + 100
                    total_tokens_used += estimated_tokens
                    
                    # 检查无效动作
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
                success = episode_reward > 0
                
                # 估算成本
                from config.llm_config import estimate_cost
                episode_cost = estimate_cost(llm_key, total_tokens_used)
                total_cost += episode_cost
                
                # 创建episode指标
                episode_metrics = EpisodeMetrics(
                    episode_id=episode_id,
                    success=success,
                    total_reward=episode_reward,
                    step_count=step + 1,
                    duration=episode_duration,
                    invalid_actions=invalid_actions
                )
                
                metrics_calc.add_episode(episode_metrics)
                
                # 添加额外信息
                episode_data = episode_metrics.to_dict()
                episode_data.update({
                    "tokens_used": total_tokens_used,
                    "estimated_cost": episode_cost
                })
                episode_results.append(episode_data)
                
                if episode_id % 5 == 0:
                    self.logger.info(f"{llm_key} - Episode {episode_id}/{self.num_episodes}")
                
            except Exception as e:
                self.logger.error(f"Error in episode {episode_id} for {llm_key}: {e}")
                continue
        
        # 计算聚合指标
        aggregate_metrics = metrics_calc.calculate_aggregate_metrics()
        
        # 添加LLM特定指标
        llm_config = llm_manager.get_config(llm_key)
        aggregate_metrics.update({
            "llm_name": llm_config.name,
            "llm_provider": llm_config.provider,
            "total_estimated_cost": total_cost,
            "avg_cost_per_episode": total_cost / len(episode_results) if episode_results else 0,
            "cost_per_success": total_cost / max(1, aggregate_metrics.get("successful_episodes", 0))
        })
        
        results = {
            "llm_key": llm_key,
            "llm_config": {
                "name": llm_config.name,
                "provider": llm_config.provider,
                "model_id": llm_config.model_id,
                "cost_per_1k_tokens": llm_config.cost_per_1k_tokens
            },
            "aggregate_metrics": aggregate_metrics,
            "episode_results": episode_results
        }
        
        self.logger.info(f"{llm_key} evaluation completed - Success: {aggregate_metrics.get('success_rate', 0):.2%}, Cost: ${total_cost:.4f}")
        return results
    
    def run_comparison(self, llm_keys: List[str] = None) -> Dict[str, Any]:
        """运行LLM比较实验"""
        if llm_keys is None:
            llm_keys = get_recommended_llms_for_comparison()
        
        self.logger.info(f"Starting LLM comparison with models: {llm_keys}")
        
        # 设置环境
        environment = self.setup_environment()
        
        # 比较结果
        comparison_results = {
            "experiment_config": {
                "num_episodes": self.num_episodes,
                "max_steps": self.max_steps,
                "llm_models": llm_keys,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "llm_results": {},
            "comparison_summary": {}
        }
        
        # 评估每个LLM
        all_results = {}
        for llm_key in llm_keys:
            try:
                result = self.run_single_llm_evaluation(llm_key, environment)
                if "error" not in result:
                    all_results[llm_key] = result
                    comparison_results["llm_results"][llm_key] = result["aggregate_metrics"]
                else:
                    self.logger.error(f"Skipping {llm_key} due to error: {result['error']}")
            except Exception as e:
                self.logger.error(f"Failed to evaluate {llm_key}: {e}")
                continue
        
        # 生成比较摘要
        if len(all_results) > 1:
            comparison_results["comparison_summary"] = self._generate_comparison_summary(all_results)
        
        # 生成可视化
        self.logger.info("Generating comparison visualizations...")
        plots = self._create_comparison_plots(comparison_results)
        comparison_results["generated_plots"] = plots
        
        # 保存详细结果
        results_file = self.results_dir / "llm_comparison_results.json"
        with open(results_file, 'w') as f:
            json.dump(comparison_results, f, indent=2, default=str)
        
        # 清理资源
        environment.close()
        
        self.logger.info("LLM comparison completed!")
        return comparison_results
    
    def _generate_comparison_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成比较摘要"""
        summary = {
            "best_performance": {},
            "best_efficiency": {},
            "cost_analysis": {},
            "recommendations": []
        }
        
        # 找出各项最佳
        metrics_to_compare = ["success_rate", "average_steps", "average_reward", "invalid_action_rate"]
        
        for metric in metrics_to_compare:
            values = {llm: result["aggregate_metrics"].get(metric, 0) 
                     for llm, result in results.items()}
            
            if metric == "invalid_action_rate":  # 越低越好
                best_llm = min(values.keys(), key=lambda k: values[k])
            else:  # 越高越好
                best_llm = max(values.keys(), key=lambda k: values[k])
            
            summary["best_performance"][metric] = {
                "llm": best_llm,
                "value": values[best_llm]
            }
        
        # 成本分析
        costs = {llm: result["aggregate_metrics"].get("total_estimated_cost", 0) 
                for llm, result in results.items()}
        
        if any(cost > 0 for cost in costs.values()):
            cheapest_llm = min(costs.keys(), key=lambda k: costs[k])
            summary["cost_analysis"] = {
                "cheapest": cheapest_llm,
                "cost": costs[cheapest_llm],
                "most_expensive": max(costs.keys(), key=lambda k: costs[k]),
                "total_range": f"${min(costs.values()):.4f} - ${max(costs.values()):.4f}"
            }
        
        return summary
    
    def _create_comparison_plots(self, results: Dict[str, Any]) -> List[str]:
        """创建比较图表"""
        plots = []
        
        if "llm_results" in results and len(results["llm_results"]) > 1:
            # 成功率比较
            success_plot = self.visualizer.plot_success_rate_comparison(
                results["llm_results"],
                title="LLM Performance Comparison - Success Rate",
                save_name="llm_success_comparison.png"
            )
            plots.append(success_plot)
            
            # 多指标比较
            metrics_plot = self.visualizer.plot_metrics_comparison(
                results["llm_results"],
                metrics=["success_rate", "average_steps", "average_reward", "invalid_action_rate"],
                title="LLM Performance Comparison - Multiple Metrics",
                save_name="llm_metrics_comparison.png"
            )
            plots.append(metrics_plot)
        
        return plots

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM Comparison Experiment")
    parser.add_argument("--episodes", type=int, default=20, help="Number of episodes per LLM")
    parser.add_argument("--max-steps", type=int, default=30, help="Max steps per episode")
    parser.add_argument("--models", nargs="+", help="Specific LLMs to compare")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(log_level=args.log_level)
    
    # 显示可用模型
    available_llms = get_available_llms()
    print("Available LLMs:")
    for key, config in available_llms.items():
        print(f"  - {key}: {config.name} ({config.provider})")
    
    # 运行比较
    experiment = LLMComparisonExperiment(args.episodes, args.max_steps)
    
    try:
        results = experiment.run_comparison(args.models)
        
        # 打印结果摘要
        print("\n" + "="*60)
        print("LLM COMPARISON RESULTS")
        print("="*60)
        
        for llm_key, metrics in results["llm_results"].items():
            print(f"\n{metrics['llm_name']} ({metrics['llm_provider']}):")
            print(f"  Success Rate: {metrics.get('success_rate', 0):.2%}")
            print(f"  Avg Steps: {metrics.get('average_steps', 0):.1f}")
            print(f"  Avg Reward: {metrics.get('average_reward', 0):.3f}")
            print(f"  Cost: ${metrics.get('total_estimated_cost', 0):.4f}")
        
        if "comparison_summary" in results:
            summary = results["comparison_summary"]
            if "best_performance" in summary:
                print(f"\nBest Success Rate: {summary['best_performance']['success_rate']['llm']}")
                print(f"Best Efficiency: {summary['best_performance']['average_steps']['llm']}")
        
        print("="*60)
        
    except KeyboardInterrupt:
        print("\nComparison interrupted by user")
    except Exception as e:
        print(f"Comparison failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
