"""
Evaluator for KGRL research framework.

Provides comprehensive evaluation capabilities for agents and experiments.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from ..agents.base_agent import BaseAgent
from ..environments.base_env import BaseEnvironment
from ..utils.metrics import MetricsCalculator, EpisodeMetrics


class AgentEvaluator:
    """Comprehensive agent evaluator."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Evaluation parameters
        self.num_episodes = self.config.get("num_episodes", 10)
        self.max_steps_per_episode = self.config.get("max_steps_per_episode", 100)
        self.save_trajectories = self.config.get("save_trajectories", False)
        
        # Results storage
        self.metrics_calculator = MetricsCalculator()
        self.trajectories = []
        
        self.logger.info("Initialized agent evaluator")
    
    def evaluate_agent(
        self,
        agent: BaseAgent,
        environment: BaseEnvironment,
        num_episodes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluate agent performance in environment.
        
        Args:
            agent: Agent to evaluate
            environment: Environment for evaluation
            num_episodes: Number of episodes to run (overrides config)
            
        Returns:
            Evaluation results
        """
        num_episodes = num_episodes or self.num_episodes
        
        self.logger.info(f"Starting evaluation: {num_episodes} episodes")
        
        # Reset metrics
        self.metrics_calculator.reset()
        self.trajectories.clear()
        
        for episode in range(num_episodes):
            episode_result = self._run_episode(agent, environment, episode)
            
            # Create episode metrics
            metrics = EpisodeMetrics(
                episode_id=episode,
                success=episode_result["success"],
                total_reward=episode_result["total_reward"],
                step_count=episode_result["step_count"],
                duration=episode_result["duration"],
                invalid_actions=episode_result["invalid_actions"],
                kg_queries=episode_result.get("kg_queries", 0),
                successful_queries=episode_result.get("successful_queries", 0)
            )
            
            self.metrics_calculator.add_episode(metrics)
            
            if self.save_trajectories:
                self.trajectories.append(episode_result["trajectory"])
            
            # Log progress
            if (episode + 1) % max(1, num_episodes // 10) == 0:
                self.logger.info(f"Completed {episode + 1}/{num_episodes} episodes")
        
        # Calculate final results
        results = self._compile_results()
        
        self.logger.info("Evaluation completed")
        self.logger.info(f"Success rate: {results['success_rate']:.2%}")
        self.logger.info(f"Average reward: {results['avg_reward']:.3f}")
        
        return results
    
    def _run_episode(
        self,
        agent: BaseAgent,
        environment: BaseEnvironment,
        episode_id: int
    ) -> Dict[str, Any]:
        """Run a single evaluation episode."""
        start_time = time.time()
        
        # Reset environment and agent
        observation = environment.reset()
        agent.reset()
        
        # Episode tracking
        trajectory = []
        total_reward = 0.0
        step_count = 0
        invalid_actions = 0
        success = False
        
        while step_count < self.max_steps_per_episode and not environment.is_done():
            # Get available actions
            available_actions = environment.get_available_actions()
            
            # Agent selects action
            action = agent.act(observation, available_actions)
            
            # Validate action
            if not environment.validate_action(action):
                invalid_actions += 1
                # Use first available action as fallback
                action = available_actions[0] if available_actions else "wait"
            
            # Execute action
            next_observation, reward, done, info = environment.step(action)
            
            # Update tracking
            total_reward += reward
            step_count += 1
            
            # Save trajectory step
            if self.save_trajectories:
                trajectory.append({
                    "step": step_count,
                    "observation": observation,
                    "action": action,
                    "reward": reward,
                    "next_observation": next_observation,
                    "done": done,
                    "info": info
                })
            
            # Update for next step
            observation = next_observation
            
            # Check for success (positive reward often indicates success)
            if reward > 0.5:  # Threshold for success
                success = True
        
        # Final success check
        if not success and total_reward > 0:
            success = True
        
        duration = time.time() - start_time
        
        # Get agent statistics
        agent_stats = agent.get_stats()
        
        return {
            "episode_id": episode_id,
            "success": success,
            "total_reward": total_reward,
            "step_count": step_count,
            "duration": duration,
            "invalid_actions": invalid_actions,
            "kg_queries": agent_stats.get("kg_queries", 0),
            "successful_queries": agent_stats.get("kg_queries", 0),  # Assume all successful for now
            "trajectory": trajectory,
            "final_observation": observation
        }
    
    def _compile_results(self) -> Dict[str, Any]:
        """Compile evaluation results."""
        # Get aggregate metrics
        aggregate_metrics = self.metrics_calculator.calculate_aggregate_metrics()
        
        # Get learning curve
        learning_curve = self.metrics_calculator.calculate_learning_curve()
        
        # Compile final results
        results = {
            **aggregate_metrics,
            "learning_curve": learning_curve,
            "evaluation_config": self.config
        }
        
        if self.save_trajectories:
            results["trajectories"] = self.trajectories
        
        return results
    
    def compare_agents(
        self,
        agents: List[Tuple[str, BaseAgent]],
        environment: BaseEnvironment,
        num_episodes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple agents.
        
        Args:
            agents: List of (name, agent) tuples
            environment: Environment for evaluation
            num_episodes: Number of episodes per agent
            
        Returns:
            Comparison results
        """
        self.logger.info(f"Comparing {len(agents)} agents")
        
        agent_results = {}
        
        for agent_name, agent in agents:
            self.logger.info(f"Evaluating agent: {agent_name}")
            
            results = self.evaluate_agent(agent, environment, num_episodes)
            agent_results[agent_name] = results
        
        # Create comparison summary
        comparison = self._create_comparison_summary(agent_results)
        
        return {
            "individual_results": agent_results,
            "comparison": comparison
        }
    
    def _create_comparison_summary(self, agent_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Create comparison summary between agents."""
        if not agent_results:
            return {}
        
        # Extract key metrics for comparison
        comparison_metrics = ["success_rate", "avg_reward", "avg_steps", "avg_duration"]
        
        summary = {}
        
        for metric in comparison_metrics:
            metric_values = {}
            for agent_name, results in agent_results.items():
                if metric in results:
                    metric_values[agent_name] = results[metric]
            
            if metric_values:
                # Find best and worst
                best_agent = max(metric_values, key=metric_values.get)
                worst_agent = min(metric_values, key=metric_values.get)
                
                summary[metric] = {
                    "values": metric_values,
                    "best_agent": best_agent,
                    "best_value": metric_values[best_agent],
                    "worst_agent": worst_agent,
                    "worst_value": metric_values[worst_agent],
                    "range": metric_values[best_agent] - metric_values[worst_agent]
                }
        
        return summary
    
    def save_results(self, results: Dict[str, Any], filepath: str):
        """Save evaluation results to file."""
        try:
            import json
            
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.info(f"Saved evaluation results to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
    
    def load_results(self, filepath: str) -> Dict[str, Any]:
        """Load evaluation results from file."""
        try:
            import json
            
            with open(filepath, 'r') as f:
                results = json.load(f)
            
            self.logger.info(f"Loaded evaluation results from {filepath}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to load results: {e}")
            return {}
    
    def get_summary_report(self, results: Dict[str, Any]) -> str:
        """Generate summary report from results."""
        if not results:
            return "No results available"
        
        report = f"""
=== Agent Evaluation Report ===

Episodes Evaluated: {results.get('total_episodes', 'N/A')}
Success Rate: {results.get('success_rate', 0):.2%}
Average Reward: {results.get('avg_reward', 0):.3f} ± {results.get('std_reward', 0):.3f}
Average Steps: {results.get('avg_steps', 0):.1f} ± {results.get('std_steps', 0):.1f}
Average Duration: {results.get('avg_duration', 0):.2f}s

Performance Metrics:
- Invalid Action Rate: {results.get('invalid_action_rate', 0):.2%}
- KG Query Success Rate: {results.get('kg_query_success_rate', 0):.2%}
- Successful Episodes: {results.get('successful_episodes', 0)}

Success-Specific Metrics:
- Avg Steps (Success): {results.get('successful_avg_steps', 0):.1f}
- Avg Reward (Success): {results.get('successful_avg_reward', 0):.3f}

===============================
"""
        
        return report
