"""
评估指标模块
提供各种评估指标的计算功能
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

@dataclass
class EpisodeMetrics:
    """单个episode的指标"""
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
    """指标计算器"""
    
    def __init__(self):
        self.episode_metrics: List[EpisodeMetrics] = []
    
    def add_episode(self, metrics: EpisodeMetrics):
        """添加episode指标"""
        self.episode_metrics.append(metrics)
    
    def calculate_aggregate_metrics(self) -> Dict[str, Any]:
        """计算聚合指标"""
        if not self.episode_metrics:
            return {}
        
        # 基础统计
        total_episodes = len(self.episode_metrics)
        successful_episodes = sum(1 for m in self.episode_metrics if m.success)
        
        # 成功率
        success_rate = successful_episodes / total_episodes
        
        # 步数统计
        step_counts = [m.step_count for m in self.episode_metrics]
        avg_steps = np.mean(step_counts)
        std_steps = np.std(step_counts)
        
        # 奖励统计
        rewards = [m.total_reward for m in self.episode_metrics]
        avg_reward = np.mean(rewards)
        std_reward = np.std(rewards)
        
        # 时间统计
        durations = [m.duration for m in self.episode_metrics]
        avg_duration = np.mean(durations)
        
        # 无效动作统计
        invalid_actions = [m.invalid_actions for m in self.episode_metrics]
        avg_invalid_actions = np.mean(invalid_actions)
        invalid_action_rate = avg_invalid_actions / avg_steps if avg_steps > 0 else 0
        
        # 知识图谱查询统计
        kg_queries = [m.kg_queries for m in self.episode_metrics]
        successful_queries = [m.successful_queries for m in self.episode_metrics]
        
        total_kg_queries = sum(kg_queries)
        total_successful_queries = sum(successful_queries)
        kg_query_success_rate = total_successful_queries / max(1, total_kg_queries)
        
        # 成功episode的特殊统计
        successful_metrics = [m for m in self.episode_metrics if m.success]
        if successful_metrics:
            successful_avg_steps = np.mean([m.step_count for m in successful_metrics])
            successful_avg_reward = np.mean([m.total_reward for m in successful_metrics])
        else:
            successful_avg_steps = 0
            successful_avg_reward = 0
        
        return {
            # 基础指标
            "total_episodes": total_episodes,
            "successful_episodes": successful_episodes,
            "success_rate": success_rate,
            
            # 步数指标
            "average_steps": avg_steps,
            "std_steps": std_steps,
            "min_steps": min(step_counts),
            "max_steps": max(step_counts),
            
            # 奖励指标
            "average_reward": avg_reward,
            "std_reward": std_reward,
            "min_reward": min(rewards),
            "max_reward": max(rewards),
            
            # 效率指标
            "average_duration": avg_duration,
            "steps_per_second": avg_steps / avg_duration if avg_duration > 0 else 0,
            
            # 动作质量指标
            "average_invalid_actions": avg_invalid_actions,
            "invalid_action_rate": invalid_action_rate,
            
            # 知识图谱指标
            "total_kg_queries": total_kg_queries,
            "average_kg_queries_per_episode": np.mean(kg_queries),
            "kg_query_success_rate": kg_query_success_rate,
            
            # 成功episode指标
            "successful_average_steps": successful_avg_steps,
            "successful_average_reward": successful_avg_reward,
        }
    
    def calculate_learning_curve(self, window_size: int = 10) -> List[Dict[str, Any]]:
        """计算学习曲线（滑动窗口平均）"""
        if len(self.episode_metrics) < window_size:
            return []
        
        learning_curve = []
        
        for i in range(window_size - 1, len(self.episode_metrics)):
            window_metrics = self.episode_metrics[i - window_size + 1:i + 1]
            
            window_success_rate = sum(1 for m in window_metrics if m.success) / window_size
            window_avg_reward = np.mean([m.total_reward for m in window_metrics])
            window_avg_steps = np.mean([m.step_count for m in window_metrics])
            
            learning_curve.append({
                "episode": i + 1,
                "window_success_rate": window_success_rate,
                "window_avg_reward": window_avg_reward,
                "window_avg_steps": window_avg_steps
            })
        
        return learning_curve
    
    def compare_agents(self, other: 'MetricsCalculator', 
                      agent1_name: str = "Agent1", 
                      agent2_name: str = "Agent2") -> Dict[str, Any]:
        """比较两个Agent的性能"""
        metrics1 = self.calculate_aggregate_metrics()
        metrics2 = other.calculate_aggregate_metrics()
        
        comparison = {
            "agents": [agent1_name, agent2_name],
            "comparison": {}
        }
        
        # 比较关键指标
        key_metrics = [
            "success_rate", "average_steps", "average_reward", 
            "invalid_action_rate", "kg_query_success_rate"
        ]
        
        for metric in key_metrics:
            if metric in metrics1 and metric in metrics2:
                value1 = metrics1[metric]
                value2 = metrics2[metric]
                
                # 计算改进百分比
                if value1 != 0:
                    improvement = ((value2 - value1) / abs(value1)) * 100
                else:
                    improvement = float('inf') if value2 > 0 else 0
                
                comparison["comparison"][metric] = {
                    agent1_name: value1,
                    agent2_name: value2,
                    "improvement_pct": improvement,
                    "better_agent": agent2_name if value2 > value1 else agent1_name
                }
        
        return comparison
    
    def get_episode_details(self, episode_id: int) -> Optional[Dict[str, Any]]:
        """获取特定episode的详细信息"""
        for metrics in self.episode_metrics:
            if metrics.episode_id == episode_id:
                return metrics.to_dict()
        return None
    
    def get_top_episodes(self, n: int = 5, metric: str = "total_reward") -> List[Dict[str, Any]]:
        """获取表现最好的n个episodes"""
        if not self.episode_metrics:
            return []
        
        # 根据指定指标排序
        sorted_metrics = sorted(
            self.episode_metrics, 
            key=lambda m: getattr(m, metric, 0), 
            reverse=True
        )
        
        return [m.to_dict() for m in sorted_metrics[:n]]
    
    def get_worst_episodes(self, n: int = 5, metric: str = "total_reward") -> List[Dict[str, Any]]:
        """获取表现最差的n个episodes"""
        if not self.episode_metrics:
            return []
        
        # 根据指定指标排序（升序）
        sorted_metrics = sorted(
            self.episode_metrics, 
            key=lambda m: getattr(m, metric, 0), 
            reverse=False
        )
        
        return [m.to_dict() for m in sorted_metrics[:n]]
    
    def export_metrics(self, filepath: str):
        """导出指标到文件"""
        export_data = {
            "aggregate_metrics": self.calculate_aggregate_metrics(),
            "episode_metrics": [m.to_dict() for m in self.episode_metrics],
            "learning_curve": self.calculate_learning_curve(),
            "top_episodes": self.get_top_episodes(),
            "worst_episodes": self.get_worst_episodes()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
    
    def reset(self):
        """重置所有指标"""
        self.episode_metrics.clear()
    
    def __len__(self) -> int:
        return len(self.episode_metrics)
    
    def __str__(self) -> str:
        metrics = self.calculate_aggregate_metrics()
        return (f"MetricsCalculator(episodes={len(self.episode_metrics)}, "
                f"success_rate={metrics.get('success_rate', 0):.2%})")

def calculate_statistical_significance(metrics1: List[float], 
                                     metrics2: List[float], 
                                     alpha: float = 0.05) -> Dict[str, Any]:
    """计算两组指标的统计显著性"""
    try:
        from scipy import stats
        
        # 进行t检验
        t_stat, p_value = stats.ttest_ind(metrics1, metrics2)
        
        # 计算效应大小 (Cohen's d)
        pooled_std = np.sqrt(((len(metrics1) - 1) * np.var(metrics1, ddof=1) + 
                             (len(metrics2) - 1) * np.var(metrics2, ddof=1)) / 
                            (len(metrics1) + len(metrics2) - 2))
        
        cohens_d = (np.mean(metrics2) - np.mean(metrics1)) / pooled_std if pooled_std > 0 else 0
        
        return {
            "t_statistic": t_stat,
            "p_value": p_value,
            "significant": p_value < alpha,
            "cohens_d": cohens_d,
            "effect_size": "small" if abs(cohens_d) < 0.5 else "medium" if abs(cohens_d) < 0.8 else "large"
        }
        
    except ImportError:
        return {
            "error": "scipy not available for statistical tests",
            "mean_difference": np.mean(metrics2) - np.mean(metrics1)
        }
