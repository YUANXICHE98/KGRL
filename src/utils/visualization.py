"""
可视化工具模块
提供实验结果和数据的可视化功能
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json

# 设置中文字体和样式
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
sns.set_palette("husl")

class ExperimentVisualizer:
    """实验结果可视化器"""
    
    def __init__(self, save_dir: str = "results/plots"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置图表样式
        self.figsize = (10, 6)
        self.dpi = 300
        
    def plot_success_rate_comparison(self, 
                                   results: Dict[str, Dict[str, Any]], 
                                   title: str = "Agent Success Rate Comparison",
                                   save_name: str = "success_rate_comparison.png") -> str:
        """绘制Agent成功率对比图"""
        
        agents = list(results.keys())
        success_rates = [results[agent].get('success_rate', 0) for agent in agents]
        
        plt.figure(figsize=self.figsize)
        bars = plt.bar(agents, success_rates, alpha=0.8)
        
        # 添加数值标签
        for bar, rate in zip(bars, success_rates):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{rate:.1%}', ha='center', va='bottom', fontweight='bold')
        
        plt.title(title, fontsize=14, fontweight='bold')
        plt.ylabel('Success Rate', fontsize=12)
        plt.xlabel('Agent Type', fontsize=12)
        plt.ylim(0, 1.1)
        plt.grid(axis='y', alpha=0.3)
        
        # 保存图片
        save_path = self.save_dir / save_name
        plt.tight_layout()
        plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(save_path)
    
    def plot_learning_curve(self, 
                           learning_data: List[Dict[str, Any]], 
                           metrics: List[str] = None,
                           title: str = "Learning Curve",
                           save_name: str = "learning_curve.png") -> str:
        """绘制学习曲线"""
        
        if not learning_data:
            return ""
        
        if metrics is None:
            metrics = ['window_success_rate', 'window_avg_reward']
        
        episodes = [d['episode'] for d in learning_data]
        
        fig, axes = plt.subplots(len(metrics), 1, figsize=(self.figsize[0], self.figsize[1] * len(metrics)))
        if len(metrics) == 1:
            axes = [axes]
        
        for i, metric in enumerate(metrics):
            values = [d.get(metric, 0) for d in learning_data]
            
            axes[i].plot(episodes, values, linewidth=2, marker='o', markersize=3)
            axes[i].set_title(f'{metric.replace("_", " ").title()}', fontsize=12)
            axes[i].set_xlabel('Episode' if i == len(metrics) - 1 else '')
            axes[i].grid(True, alpha=0.3)
            
            # 添加趋势线
            if len(episodes) > 5:
                z = np.polyfit(episodes, values, 1)
                p = np.poly1d(z)
                axes[i].plot(episodes, p(episodes), "--", alpha=0.7, color='red')
        
        plt.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        save_path = self.save_dir / save_name
        plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(save_path)
    
    def plot_metrics_comparison(self, 
                              results: Dict[str, Dict[str, Any]], 
                              metrics: List[str] = None,
                              title: str = "Metrics Comparison",
                              save_name: str = "metrics_comparison.png") -> str:
        """绘制多个指标的对比图"""
        
        if metrics is None:
            metrics = ['success_rate', 'average_steps', 'average_reward', 'invalid_action_rate']
        
        # 准备数据
        agents = list(results.keys())
        data = []
        
        for agent in agents:
            for metric in metrics:
                value = results[agent].get(metric, 0)
                data.append({
                    'Agent': agent,
                    'Metric': metric.replace('_', ' ').title(),
                    'Value': value
                })
        
        df = pd.DataFrame(data)
        
        # 创建子图
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()
        
        for i, metric in enumerate(metrics[:4]):  # 最多显示4个指标
            metric_title = metric.replace('_', ' ').title()
            metric_data = df[df['Metric'] == metric_title]
            
            sns.barplot(data=metric_data, x='Agent', y='Value', ax=axes[i])
            axes[i].set_title(metric_title, fontsize=12, fontweight='bold')
            axes[i].set_xlabel('')
            
            # 添加数值标签
            for container in axes[i].containers:
                axes[i].bar_label(container, fmt='%.3f')
        
        plt.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        save_path = self.save_dir / save_name
        plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(save_path)
    
    def plot_episode_distribution(self, 
                                episodes_data: List[Dict[str, Any]], 
                                metric: str = 'total_reward',
                                title: str = "Episode Performance Distribution",
                                save_name: str = "episode_distribution.png") -> str:
        """绘制episode性能分布图"""
        
        values = [ep.get(metric, 0) for ep in episodes_data]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 直方图
        ax1.hist(values, bins=20, alpha=0.7, edgecolor='black')
        ax1.set_title(f'{metric.replace("_", " ").title()} Distribution')
        ax1.set_xlabel(metric.replace("_", " ").title())
        ax1.set_ylabel('Frequency')
        ax1.grid(True, alpha=0.3)
        
        # 箱线图
        ax2.boxplot(values, vert=True)
        ax2.set_title(f'{metric.replace("_", " ").title()} Box Plot')
        ax2.set_ylabel(metric.replace("_", " ").title())
        ax2.grid(True, alpha=0.3)
        
        plt.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        save_path = self.save_dir / save_name
        plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(save_path)
    
    def plot_knowledge_graph_usage(self, 
                                  episodes_data: List[Dict[str, Any]], 
                                  title: str = "Knowledge Graph Usage Analysis",
                                  save_name: str = "kg_usage.png") -> str:
        """绘制知识图谱使用情况分析"""
        
        kg_queries = [ep.get('kg_queries', 0) for ep in episodes_data]
        successful_queries = [ep.get('successful_queries', 0) for ep in episodes_data]
        success_flags = [ep.get('success', False) for ep in episodes_data]
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # KG查询次数分布
        axes[0, 0].hist(kg_queries, bins=15, alpha=0.7, edgecolor='black')
        axes[0, 0].set_title('KG Queries per Episode')
        axes[0, 0].set_xlabel('Number of Queries')
        axes[0, 0].set_ylabel('Frequency')
        
        # 成功查询率分布
        query_success_rates = [s/max(1, q) for q, s in zip(kg_queries, successful_queries)]
        axes[0, 1].hist(query_success_rates, bins=15, alpha=0.7, edgecolor='black')
        axes[0, 1].set_title('Query Success Rate Distribution')
        axes[0, 1].set_xlabel('Success Rate')
        axes[0, 1].set_ylabel('Frequency')
        
        # 成功vs失败episode的KG使用对比
        successful_episodes = [i for i, success in enumerate(success_flags) if success]
        failed_episodes = [i for i, success in enumerate(success_flags) if not success]
        
        successful_queries_count = [kg_queries[i] for i in successful_episodes]
        failed_queries_count = [kg_queries[i] for i in failed_episodes]
        
        axes[1, 0].boxplot([successful_queries_count, failed_queries_count], 
                          labels=['Successful', 'Failed'])
        axes[1, 0].set_title('KG Queries: Success vs Failure')
        axes[1, 0].set_ylabel('Number of Queries')
        
        # KG查询与奖励的关系
        rewards = [ep.get('total_reward', 0) for ep in episodes_data]
        axes[1, 1].scatter(kg_queries, rewards, alpha=0.6)
        axes[1, 1].set_title('KG Queries vs Reward')
        axes[1, 1].set_xlabel('Number of KG Queries')
        axes[1, 1].set_ylabel('Total Reward')
        
        # 添加趋势线
        if len(kg_queries) > 5:
            z = np.polyfit(kg_queries, rewards, 1)
            p = np.poly1d(z)
            axes[1, 1].plot(kg_queries, p(kg_queries), "r--", alpha=0.8)
        
        plt.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        save_path = self.save_dir / save_name
        plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(save_path)
    
    def create_experiment_report(self, 
                               results: Dict[str, Any], 
                               title: str = "Experiment Report") -> str:
        """创建完整的实验报告可视化"""
        
        report_plots = []
        
        # 1. 成功率对比
        if 'agents' in results:
            success_plot = self.plot_success_rate_comparison(
                results['agents'], 
                title=f"{title} - Success Rate Comparison"
            )
            report_plots.append(success_plot)
        
        # 2. 学习曲线
        if 'learning_curve' in results:
            learning_plot = self.plot_learning_curve(
                results['learning_curve'], 
                title=f"{title} - Learning Curve"
            )
            report_plots.append(learning_plot)
        
        # 3. 指标对比
        if 'agents' in results:
            metrics_plot = self.plot_metrics_comparison(
                results['agents'], 
                title=f"{title} - Metrics Comparison"
            )
            report_plots.append(metrics_plot)
        
        # 4. Episode分布
        if 'episode_metrics' in results:
            dist_plot = self.plot_episode_distribution(
                results['episode_metrics'], 
                title=f"{title} - Episode Distribution"
            )
            report_plots.append(dist_plot)
        
        return report_plots
    
    def save_summary_table(self, 
                          results: Dict[str, Dict[str, Any]], 
                          filename: str = "results_summary.csv") -> str:
        """保存结果摘要表格"""
        
        # 转换为DataFrame
        df_data = []
        for agent_name, metrics in results.items():
            row = {'Agent': agent_name}
            row.update(metrics)
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        
        # 保存CSV
        save_path = self.save_dir / filename
        df.to_csv(save_path, index=False, float_format='%.4f')
        
        return str(save_path)
