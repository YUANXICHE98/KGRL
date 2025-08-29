"""
实验结果记录器
用于科研级别的实验数据收集和分析
"""

import json
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from .logger import get_logger

@dataclass
class EpisodeResult:
    """单个episode的结果"""
    episode_id: int
    agent_type: str
    model_name: str
    environment: str
    difficulty: str
    
    # 性能指标
    success: bool
    total_steps: int
    total_reward: float
    completion_time: float
    
    # 详细数据
    actions_taken: List[str]
    invalid_actions: int
    kg_queries: int
    kg_hits: int
    api_calls: int
    api_response_times: List[float]
    
    # 实验配置
    use_knowledge_graph: bool
    use_react_reasoning: bool
    temperature: float
    max_tokens: int
    
    # 时间戳
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)

class ExperimentLogger:
    """科研实验记录器"""
    
    def __init__(self, experiment_name: str, base_dir: str = "results"):
        self.experiment_name = experiment_name
        self.base_dir = Path(base_dir)
        self.logger = get_logger(f"ExperimentLogger_{experiment_name}")
        
        # 创建实验目录结构
        self.experiment_dir = self.base_dir / experiment_name
        self.data_dir = self.experiment_dir / "data"
        self.plots_dir = self.experiment_dir / "plots"
        self.reports_dir = self.experiment_dir / "reports"
        
        for dir_path in [self.data_dir, self.plots_dir, self.reports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 结果存储
        self.episodes: List[EpisodeResult] = []
        self.current_episode: Optional[Dict] = None
        
        self.logger.info(f"Initialized experiment logger: {experiment_name}")
    
    def start_episode(self, agent_type: str, model_name: str, environment: str, 
                     difficulty: str, config: Dict[str, Any]) -> int:
        """开始新的episode记录"""
        episode_id = len(self.episodes)
        
        self.current_episode = {
            'episode_id': episode_id,
            'agent_type': agent_type,
            'model_name': model_name,
            'environment': environment,
            'difficulty': difficulty,
            'start_time': time.time(),
            'actions_taken': [],
            'invalid_actions': 0,
            'kg_queries': 0,
            'kg_hits': 0,
            'api_calls': 0,
            'api_response_times': [],
            'use_knowledge_graph': config.get('use_knowledge_graph', False),
            'use_react_reasoning': config.get('use_react_reasoning', False),
            'temperature': config.get('temperature', 0.7),
            'max_tokens': config.get('max_tokens', 150),
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Started episode {episode_id}: {agent_type} on {environment}")
        return episode_id
    
    def log_action(self, action: str, is_valid: bool, api_time: Optional[float] = None):
        """记录单个动作"""
        if self.current_episode is None:
            return
        
        self.current_episode['actions_taken'].append(action)
        if not is_valid:
            self.current_episode['invalid_actions'] += 1
        
        if api_time is not None:
            self.current_episode['api_calls'] += 1
            self.current_episode['api_response_times'].append(api_time)
    
    def log_kg_query(self, query: str, results_count: int):
        """记录知识图谱查询"""
        if self.current_episode is None:
            return
        
        self.current_episode['kg_queries'] += 1
        if results_count > 0:
            self.current_episode['kg_hits'] += 1
    
    def end_episode(self, success: bool, total_reward: float) -> EpisodeResult:
        """结束episode记录"""
        if self.current_episode is None:
            raise ValueError("No active episode to end")
        
        end_time = time.time()
        completion_time = end_time - self.current_episode['start_time']
        
        episode_result = EpisodeResult(
            episode_id=self.current_episode['episode_id'],
            agent_type=self.current_episode['agent_type'],
            model_name=self.current_episode['model_name'],
            environment=self.current_episode['environment'],
            difficulty=self.current_episode['difficulty'],
            success=success,
            total_steps=len(self.current_episode['actions_taken']),
            total_reward=total_reward,
            completion_time=completion_time,
            actions_taken=self.current_episode['actions_taken'],
            invalid_actions=self.current_episode['invalid_actions'],
            kg_queries=self.current_episode['kg_queries'],
            kg_hits=self.current_episode['kg_hits'],
            api_calls=self.current_episode['api_calls'],
            api_response_times=self.current_episode['api_response_times'],
            use_knowledge_graph=self.current_episode['use_knowledge_graph'],
            use_react_reasoning=self.current_episode['use_react_reasoning'],
            temperature=self.current_episode['temperature'],
            max_tokens=self.current_episode['max_tokens'],
            timestamp=self.current_episode['timestamp']
        )
        
        self.episodes.append(episode_result)
        self.current_episode = None
        
        self.logger.info(f"Completed episode {episode_result.episode_id}: "
                        f"Success={success}, Steps={episode_result.total_steps}")
        
        return episode_result
    
    def save_results(self):
        """保存实验结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON格式（完整数据）
        json_file = self.data_dir / f"results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump([ep.to_dict() for ep in self.episodes], f, indent=2)
        
        # 保存CSV格式（表格数据）
        csv_file = self.data_dir / f"results_{timestamp}.csv"
        df = pd.DataFrame([ep.to_dict() for ep in self.episodes])
        df.to_csv(csv_file, index=False)
        
        self.logger.info(f"Saved {len(self.episodes)} episodes to {json_file} and {csv_file}")
        
        return json_file, csv_file
    
    def generate_summary_report(self) -> str:
        """生成实验总结报告"""
        if not self.episodes:
            return "No episodes recorded yet."
        
        df = pd.DataFrame([ep.to_dict() for ep in self.episodes])
        
        # 按Agent类型分组统计
        summary = []
        summary.append(f"# {self.experiment_name} 实验报告")
        summary.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"总Episode数: {len(self.episodes)}")
        summary.append("")
        
        # 整体统计
        overall_success_rate = df['success'].mean()
        overall_avg_steps = df['total_steps'].mean()
        overall_avg_reward = df['total_reward'].mean()
        
        summary.append("## 整体性能")
        summary.append(f"- 成功率: {overall_success_rate:.2%}")
        summary.append(f"- 平均步数: {overall_avg_steps:.1f}")
        summary.append(f"- 平均奖励: {overall_avg_reward:.3f}")
        summary.append("")
        
        # 按Agent类型分组
        summary.append("## 按Agent类型分组")
        for agent_type in df['agent_type'].unique():
            agent_df = df[df['agent_type'] == agent_type]
            success_rate = agent_df['success'].mean()
            avg_steps = agent_df['total_steps'].mean()
            avg_reward = agent_df['total_reward'].mean()
            invalid_rate = agent_df['invalid_actions'].sum() / agent_df['total_steps'].sum()
            
            summary.append(f"### {agent_type}")
            summary.append(f"- Episodes: {len(agent_df)}")
            summary.append(f"- 成功率: {success_rate:.2%}")
            summary.append(f"- 平均步数: {avg_steps:.1f}")
            summary.append(f"- 平均奖励: {avg_reward:.3f}")
            summary.append(f"- 无效动作率: {invalid_rate:.2%}")
            
            if agent_df['api_response_times'].iloc[0]:  # 如果有API时间数据
                avg_api_time = sum(sum(times) for times in agent_df['api_response_times']) / sum(len(times) for times in agent_df['api_response_times'])
                summary.append(f"- 平均API响应时间: {avg_api_time:.2f}s")
            
            summary.append("")
        
        report_text = "\n".join(summary)
        
        # 保存报告
        report_file = self.reports_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        self.logger.info(f"Generated summary report: {report_file}")
        return report_text

    def generate_comparison_plots(self):
        """生成对比图表 (英文标签)"""
        if not self.episodes:
            self.logger.warning("No episodes to plot")
            return

        df = pd.DataFrame([ep.to_dict() for ep in self.episodes])

        # 设置图表样式
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'{self.experiment_name} - Performance Comparison', fontsize=16)

        # 1. 成功率对比
        success_by_agent = df.groupby('agent_type')['success'].agg(['mean', 'count']).reset_index()
        axes[0, 0].bar(success_by_agent['agent_type'], success_by_agent['mean'])
        axes[0, 0].set_title('Success Rate Comparison')
        axes[0, 0].set_ylabel('Success Rate')
        axes[0, 0].set_ylim(0, 1)
        for i, v in enumerate(success_by_agent['mean']):
            axes[0, 0].text(i, v + 0.01, f'{v:.2%}', ha='center')

        # 2. 平均步数对比
        steps_by_agent = df.groupby('agent_type')['total_steps'].mean()
        axes[0, 1].bar(steps_by_agent.index, steps_by_agent.values)
        axes[0, 1].set_title('Average Steps Comparison')
        axes[0, 1].set_ylabel('Average Steps')
        for i, v in enumerate(steps_by_agent.values):
            axes[0, 1].text(i, v + 0.5, f'{v:.1f}', ha='center')

        # 3. 奖励分布
        for agent_type in df['agent_type'].unique():
            agent_rewards = df[df['agent_type'] == agent_type]['total_reward']
            axes[1, 0].hist(agent_rewards, alpha=0.7, label=agent_type, bins=10)
        axes[1, 0].set_title('Reward Distribution')
        axes[1, 0].set_xlabel('Total Reward')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].legend()

        # 4. 无效动作率对比
        df['invalid_rate'] = df['invalid_actions'] / df['total_steps']
        invalid_by_agent = df.groupby('agent_type')['invalid_rate'].mean()
        axes[1, 1].bar(invalid_by_agent.index, invalid_by_agent.values)
        axes[1, 1].set_title('Invalid Action Rate Comparison')
        axes[1, 1].set_ylabel('Invalid Action Rate')
        for i, v in enumerate(invalid_by_agent.values):
            axes[1, 1].text(i, v + 0.005, f'{v:.2%}', ha='center')

        plt.tight_layout()

        # 保存图表
        plot_file = self.plots_dir / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()

        self.logger.info(f"Generated comparison plots: {plot_file}")
        return plot_file

    def generate_detailed_analysis(self):
        """生成详细分析图表"""
        if not self.episodes:
            return

        df = pd.DataFrame([ep.to_dict() for ep in self.episodes])

        # 创建详细分析图表
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle(f'{self.experiment_name} - Detailed Performance Analysis', fontsize=16)

        # 1. 成功率 vs 难度
        if 'difficulty' in df.columns:
            success_by_difficulty = df.groupby(['agent_type', 'difficulty'])['success'].mean().unstack()
            success_by_difficulty.plot(kind='bar', ax=axes[0, 0])
            axes[0, 0].set_title('Success Rate vs Difficulty')
            axes[0, 0].set_ylabel('Success Rate')
            axes[0, 0].legend(title='Difficulty')

        # 2. 步数 vs 成功率散点图
        for agent_type in df['agent_type'].unique():
            agent_df = df[df['agent_type'] == agent_type]
            axes[0, 1].scatter(agent_df['total_steps'], agent_df['success'],
                             alpha=0.6, label=agent_type)
        axes[0, 1].set_title('Steps vs Success Rate')
        axes[0, 1].set_xlabel('Total Steps')
        axes[0, 1].set_ylabel('Success (1) / Failure (0)')
        axes[0, 1].legend()

        # 3. API响应时间分布
        api_times = []
        agent_labels = []
        for _, row in df.iterrows():
            if row['api_response_times']:
                api_times.extend(row['api_response_times'])
                agent_labels.extend([row['agent_type']] * len(row['api_response_times']))

        if api_times:
            api_df = pd.DataFrame({'time': api_times, 'agent': agent_labels})
            for agent_type in api_df['agent'].unique():
                agent_times = api_df[api_df['agent'] == agent_type]['time']
                axes[0, 2].hist(agent_times, alpha=0.7, label=agent_type, bins=20)
            axes[0, 2].set_title('API Response Time Distribution')
            axes[0, 2].set_xlabel('Response Time (seconds)')
            axes[0, 2].set_ylabel('Frequency')
            axes[0, 2].legend()

        # 4. 知识图谱使用效果 (如果有KG数据)
        kg_df = df[df['use_knowledge_graph'] == True]
        if not kg_df.empty:
            kg_df['kg_hit_rate'] = kg_df['kg_hits'] / kg_df['kg_queries'].replace(0, 1)
            axes[1, 0].scatter(kg_df['kg_hit_rate'], kg_df['success'], alpha=0.6)
            axes[1, 0].set_title('KG Hit Rate vs Success Rate')
            axes[1, 0].set_xlabel('KG Hit Rate')
            axes[1, 0].set_ylabel('Success Rate')

        # 5. 学习曲线 (按时间顺序的成功率)
        df_sorted = df.sort_values('timestamp')
        window_size = max(5, len(df) // 10)  # 滑动窗口大小
        for agent_type in df['agent_type'].unique():
            agent_df = df_sorted[df_sorted['agent_type'] == agent_type]
            if len(agent_df) >= window_size:
                rolling_success = agent_df['success'].rolling(window=window_size).mean()
                axes[1, 1].plot(range(len(rolling_success)), rolling_success,
                               label=f'{agent_type} (window={window_size})')
        axes[1, 1].set_title('Learning Curve (Rolling Average Success Rate)')
        axes[1, 1].set_xlabel('Episode')
        axes[1, 1].set_ylabel('Success Rate')
        axes[1, 1].legend()

        # 6. 配置参数影响分析
        if df['temperature'].nunique() > 1:
            temp_success = df.groupby('temperature')['success'].mean()
            axes[1, 2].plot(temp_success.index, temp_success.values, 'o-')
            axes[1, 2].set_title('Temperature vs Success Rate')
            axes[1, 2].set_xlabel('Temperature')
            axes[1, 2].set_ylabel('Success Rate')

        plt.tight_layout()

        # 保存详细分析图表
        detail_plot_file = self.plots_dir / f"detailed_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(detail_plot_file, dpi=300, bbox_inches='tight')
        plt.close()

        self.logger.info(f"Generated detailed analysis plots: {detail_plot_file}")
        return detail_plot_file
