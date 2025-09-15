"""
Metrics utilities for KGRL research framework.

Provides evaluation metrics calculation and tracking.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
import logging


@dataclass
class EpisodeMetrics:
    """Metrics for a single episode."""
    episode_id: int
    success: bool
    total_reward: float
    step_count: int
    duration: float
    invalid_actions: int = 0
    kg_queries: int = 0
    successful_queries: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "success": self.success,
            "total_reward": self.total_reward,
            "step_count": self.step_count,
            "duration": self.duration,
            "invalid_actions": self.invalid_actions,
            "kg_queries": self.kg_queries,
            "successful_queries": self.successful_queries,
            "query_success_rate": self.successful_queries / max(1, self.kg_queries)
        }


class MetricsCalculator:
    """Metrics calculator for experiment evaluation."""
    
    def __init__(self):
        self.episode_metrics: List[EpisodeMetrics] = []
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def add_episode(self, metrics: EpisodeMetrics):
        """Add episode metrics."""
        self.episode_metrics.append(metrics)
        self.logger.debug(f"Added metrics for episode {metrics.episode_id}")
    
    def calculate_aggregate_metrics(self) -> Dict[str, Any]:
        """Calculate aggregate metrics across all episodes."""
        if not self.episode_metrics:
            return {}
        
        # Basic statistics
        total_episodes = len(self.episode_metrics)
        successful_episodes = sum(1 for m in self.episode_metrics if m.success)
        
        # Success rate
        success_rate = successful_episodes / total_episodes
        
        # Step statistics
        step_counts = [m.step_count for m in self.episode_metrics]
        avg_steps = np.mean(step_counts)
        std_steps = np.std(step_counts)
        
        # Reward statistics
        rewards = [m.total_reward for m in self.episode_metrics]
        avg_reward = np.mean(rewards)
        std_reward = np.std(rewards)
        
        # Duration statistics
        durations = [m.duration for m in self.episode_metrics]
        avg_duration = np.mean(durations)
        
        # Invalid action statistics
        invalid_actions = [m.invalid_actions for m in self.episode_metrics]
        avg_invalid_actions = np.mean(invalid_actions)
        invalid_action_rate = avg_invalid_actions / avg_steps if avg_steps > 0 else 0
        
        # Knowledge graph query statistics
        kg_queries = [m.kg_queries for m in self.episode_metrics]
        successful_queries = [m.successful_queries for m in self.episode_metrics]
        
        total_kg_queries = sum(kg_queries)
        total_successful_queries = sum(successful_queries)
        kg_query_success_rate = total_successful_queries / max(1, total_kg_queries)
        
        # Statistics for successful episodes only
        successful_metrics = [m for m in self.episode_metrics if m.success]
        if successful_metrics:
            successful_avg_steps = np.mean([m.step_count for m in successful_metrics])
            successful_avg_reward = np.mean([m.total_reward for m in successful_metrics])
        else:
            successful_avg_steps = 0
            successful_avg_reward = 0
        
        return {
            # Basic metrics
            "total_episodes": total_episodes,
            "successful_episodes": successful_episodes,
            "success_rate": success_rate,
            
            # Step metrics
            "avg_steps": avg_steps,
            "std_steps": std_steps,
            "min_steps": min(step_counts),
            "max_steps": max(step_counts),
            
            # Reward metrics
            "avg_reward": avg_reward,
            "std_reward": std_reward,
            "min_reward": min(rewards),
            "max_reward": max(rewards),
            
            # Duration metrics
            "avg_duration": avg_duration,
            "total_duration": sum(durations),
            
            # Action quality metrics
            "avg_invalid_actions": avg_invalid_actions,
            "invalid_action_rate": invalid_action_rate,
            
            # Knowledge graph metrics
            "total_kg_queries": total_kg_queries,
            "avg_kg_queries_per_episode": total_kg_queries / total_episodes,
            "kg_query_success_rate": kg_query_success_rate,
            
            # Success-specific metrics
            "successful_avg_steps": successful_avg_steps,
            "successful_avg_reward": successful_avg_reward,
        }
    
    def calculate_learning_curve(self, window_size: int = 10) -> Dict[str, List[float]]:
        """Calculate learning curve with moving averages."""
        if len(self.episode_metrics) < window_size:
            return {}
        
        success_rates = []
        avg_rewards = []
        avg_steps = []
        
        for i in range(window_size - 1, len(self.episode_metrics)):
            window_metrics = self.episode_metrics[i - window_size + 1:i + 1]
            
            # Success rate in window
            window_success_rate = sum(1 for m in window_metrics if m.success) / window_size
            success_rates.append(window_success_rate)
            
            # Average reward in window
            window_avg_reward = np.mean([m.total_reward for m in window_metrics])
            avg_rewards.append(window_avg_reward)
            
            # Average steps in window
            window_avg_steps = np.mean([m.step_count for m in window_metrics])
            avg_steps.append(window_avg_steps)
        
        return {
            "success_rates": success_rates,
            "avg_rewards": avg_rewards,
            "avg_steps": avg_steps,
            "window_size": window_size
        }
    
    def compare_with_baseline(self, baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current metrics with baseline."""
        current_metrics = self.calculate_aggregate_metrics()
        
        if not current_metrics or not baseline_metrics:
            return {}
        
        comparison = {}
        
        for key in ["success_rate", "avg_reward", "avg_steps", "kg_query_success_rate"]:
            if key in current_metrics and key in baseline_metrics:
                current_val = current_metrics[key]
                baseline_val = baseline_metrics[key]
                
                if baseline_val != 0:
                    improvement = (current_val - baseline_val) / baseline_val * 100
                else:
                    improvement = float('inf') if current_val > 0 else 0
                
                comparison[f"{key}_improvement"] = improvement
                comparison[f"{key}_current"] = current_val
                comparison[f"{key}_baseline"] = baseline_val
        
        return comparison
    
    def get_episode_data(self) -> List[Dict[str, Any]]:
        """Get all episode data as list of dictionaries."""
        return [m.to_dict() for m in self.episode_metrics]
    
    def save_metrics(self, filepath: str):
        """Save metrics to JSON file."""
        try:
            data = {
                "aggregate_metrics": self.calculate_aggregate_metrics(),
                "episode_data": self.get_episode_data(),
                "learning_curve": self.calculate_learning_curve()
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved metrics to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")
    
    def load_metrics(self, filepath: str):
        """Load metrics from JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Reconstruct episode metrics
            self.episode_metrics = []
            for episode_data in data.get("episode_data", []):
                metrics = EpisodeMetrics(
                    episode_id=episode_data["episode_id"],
                    success=episode_data["success"],
                    total_reward=episode_data["total_reward"],
                    step_count=episode_data["step_count"],
                    duration=episode_data["duration"],
                    invalid_actions=episode_data.get("invalid_actions", 0),
                    kg_queries=episode_data.get("kg_queries", 0),
                    successful_queries=episode_data.get("successful_queries", 0)
                )
                self.episode_metrics.append(metrics)
            
            self.logger.info(f"Loaded metrics from {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to load metrics: {e}")
    
    def reset(self):
        """Reset all metrics."""
        self.episode_metrics.clear()
        self.logger.info("Reset all metrics")
    
    def get_summary_stats(self) -> str:
        """Get summary statistics as formatted string."""
        metrics = self.calculate_aggregate_metrics()
        
        if not metrics:
            return "No metrics available"
        
        summary = f"""
=== Experiment Summary ===
Total Episodes: {metrics['total_episodes']}
Success Rate: {metrics['success_rate']:.2%}
Average Reward: {metrics['avg_reward']:.3f} ± {metrics['std_reward']:.3f}
Average Steps: {metrics['avg_steps']:.1f} ± {metrics['std_steps']:.1f}
Invalid Action Rate: {metrics['invalid_action_rate']:.2%}
KG Query Success Rate: {metrics['kg_query_success_rate']:.2%}
========================
"""
        return summary
