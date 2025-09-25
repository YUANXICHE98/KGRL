#!/usr/bin/env python3
"""
实验结果可视化工具
"""

import json
import time
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置英文字体和样式
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['axes.unicode_minus'] = False

# 设置样式
sns.set_style("whitegrid")
plt.style.use('seaborn-v0_8')


class ExperimentVisualizer:
    """实验结果可视化器"""
    
    def __init__(self, results_dir: str = "experiments/results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建图表保存目录
        self.plots_dir = self.results_dir / "plots"
        self.plots_dir.mkdir(exist_ok=True)
        
        print(f"📊 初始化实验可视化器 (结果目录: {results_dir})")
    
    def plot_baseline_comparison(self, results_file: str) -> None:
        """Plot baseline comparison charts"""
        # Load results
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        results = data['results']
        final_analysis = data.get('final_analysis', {})

        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Baseline Agent Comparison Results', fontsize=16, fontweight='bold')
        
        # 1. Average Reward Comparison
        agents = list(final_analysis.keys())
        avg_rewards = [final_analysis[agent]['avg_reward'] for agent in agents]

        axes[0, 0].bar(agents, avg_rewards, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        axes[0, 0].set_title('Average Reward Comparison')
        axes[0, 0].set_ylabel('Average Reward')
        axes[0, 0].tick_params(axis='x', rotation=45)

        # Add value labels
        for i, v in enumerate(avg_rewards):
            axes[0, 0].text(i, v + 0.01, f'{v:.3f}', ha='center', va='bottom')

        # 2. Success Rate Comparison
        success_rates = [final_analysis[agent]['success_rate'] for agent in agents]

        axes[0, 1].bar(agents, success_rates, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        axes[0, 1].set_title('Success Rate Comparison')
        axes[0, 1].set_ylabel('Success Rate')
        axes[0, 1].tick_params(axis='x', rotation=45)
        axes[0, 1].set_ylim(0, 1)

        # Add value labels
        for i, v in enumerate(success_rates):
            axes[0, 1].text(i, v + 0.01, f'{v:.3f}', ha='center', va='bottom')

        # 3. Average Steps Comparison
        avg_steps = [final_analysis[agent]['avg_steps'] for agent in agents]

        axes[1, 0].bar(agents, avg_steps, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        axes[1, 0].set_title('Average Steps Comparison (Lower is Better)')
        axes[1, 0].set_ylabel('Average Steps')
        axes[1, 0].tick_params(axis='x', rotation=45)

        # Add value labels
        for i, v in enumerate(avg_steps):
            axes[1, 0].text(i, v + 0.5, f'{v:.1f}', ha='center', va='bottom')

        # 4. Reward Distribution Box Plot
        reward_data = []
        agent_labels = []

        for agent in agents:
            rewards = results[agent]['rewards']
            reward_data.extend(rewards)
            agent_labels.extend([agent] * len(rewards))

        df = pd.DataFrame({'Agent': agent_labels, 'Reward': reward_data})
        sns.boxplot(data=df, x='Agent', y='Reward', ax=axes[1, 1])
        axes[1, 1].set_title('Reward Distribution')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()

        # Save chart with standardized naming
        timestamp = int(time.time())
        plot_file = self.plots_dir / f"baseline_comparison_{timestamp}.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"📊 Baseline comparison chart saved to: {plot_file}")

        plt.close()  # Close instead of show for batch processing
    
    def plot_learning_curves(self, results_file: str) -> None:
        """Plot learning curves with English labels"""
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        results = data['results']

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('Learning Curves', fontsize=16, fontweight='bold')
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        for i, (agent, agent_results) in enumerate(results.items()):
            episodes = range(1, len(agent_results['rewards']) + 1)
            
            # 1. 奖励曲线
            axes[0].plot(episodes, agent_results['rewards'], 
                        label=agent, color=colors[i % len(colors)], alpha=0.7)
            
            # 添加移动平均
            if len(agent_results['rewards']) > 5:
                window = min(5, len(agent_results['rewards']) // 4)
                moving_avg = pd.Series(agent_results['rewards']).rolling(window=window).mean()
                axes[0].plot(episodes, moving_avg, 
                           color=colors[i % len(colors)], linewidth=2)
            
            # 2. 成功率曲线
            axes[1].plot(episodes, agent_results['success_rates'], 
                        label=agent, color=colors[i % len(colors)], alpha=0.7)
            
            # 3. 步数曲线
            axes[2].plot(episodes, agent_results['steps'], 
                        label=agent, color=colors[i % len(colors)], alpha=0.7)
        
        axes[0].set_title('Reward Progress')
        axes[0].set_xlabel('Episode')
        axes[0].set_ylabel('Reward')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        axes[1].set_title('Success Rate Progress')
        axes[1].set_xlabel('Episode')
        axes[1].set_ylabel('Success Rate')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        axes[2].set_title('Steps Progress')
        axes[2].set_xlabel('Episode')
        axes[2].set_ylabel('Steps')
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)

        plt.tight_layout()

        # Save chart with standardized naming
        timestamp = int(time.time())
        plot_file = self.plots_dir / f"learning_curves_{timestamp}.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"📈 Learning curves saved to: {plot_file}")

        plt.close()  # Close instead of show
    
    def plot_performance_radar(self, results_file: str) -> None:
        """绘制性能雷达图"""
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        final_analysis = data.get('final_analysis', {})
        
        if not final_analysis:
            print("❌ 没有找到最终分析数据")
            return
        
        # 准备数据
        agents = list(final_analysis.keys())
        metrics = ['avg_reward', 'success_rate', 'efficiency']  # efficiency = 1 / avg_steps
        
        # 标准化数据到0-1范围
        values = []
        for agent in agents:
            agent_data = final_analysis[agent]
            efficiency = 1.0 / max(agent_data['avg_steps'], 1)  # 步数越少效率越高
            
            agent_values = [
                agent_data['avg_reward'] / 10.0,  # 假设最大奖励为10
                agent_data['success_rate'],
                efficiency * 10  # 调整效率比例
            ]
            values.append(agent_values)
        
        # 创建雷达图
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]  # 闭合图形
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        for i, (agent, agent_values) in enumerate(zip(agents, values)):
            agent_values += agent_values[:1]  # 闭合数据
            ax.plot(angles, agent_values, 'o-', linewidth=2, 
                   label=agent, color=colors[i % len(colors)])
            ax.fill(angles, agent_values, alpha=0.25, color=colors[i % len(colors)])
        
        # 设置标签
        metric_labels = ['平均奖励', '成功率', '效率']
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metric_labels)
        ax.set_ylim(0, 1)
        ax.set_title('智能体性能雷达图', size=16, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
        
        plt.tight_layout()
        
        # 保存图表
        plot_file = self.plots_dir / "performance_radar.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"🎯 性能雷达图保存到: {plot_file}")
        
        plt.show()
    
    def generate_experiment_report(self, results_file: str) -> str:
        """生成实验报告"""
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 生成所有图表
        print("📊 生成实验图表...")
        self.plot_baseline_comparison(results_file)
        self.plot_learning_curves(results_file)
        self.plot_performance_radar(results_file)
        
        # 生成报告
        report_file = self.results_dir / "experiment_report.md"
        
        final_analysis = data.get('final_analysis', {})
        config = data.get('experiment_config', {})
        
        report_content = f"""# 基线智能体对比实验报告

## 实验配置
- **Episodes**: {config.get('num_episodes', 'N/A')}
- **最大步数**: {config.get('max_steps', 'N/A')}
- **智能体类型**: {', '.join(data['results'].keys())}

## 实验结果

### 性能对比
"""
        
        if final_analysis:
            for agent, stats in final_analysis.items():
                report_content += f"""
#### {agent.upper()}
- 平均奖励: {stats['avg_reward']:.3f}
- 成功率: {stats['success_rate']:.3f}
- 平均步数: {stats['avg_steps']:.1f}
- 最佳奖励: {stats['best_reward']:.3f}
"""
        
        report_content += f"""
## 可视化结果

### 图表文件
- 基线对比图: `plots/baseline_comparison.png`
- 学习曲线: `plots/learning_curves.png`
- 性能雷达图: `plots/performance_radar.png`

## 结论

基于实验结果，我们可以得出以下结论：

1. **性能排名**: 根据平均奖励排序
2. **学习效率**: 分析学习曲线的收敛速度
3. **稳定性**: 基于奖励方差评估稳定性

## 下一步工作

1. 增加更多场景测试
2. 优化智能体策略
3. 引入知识图谱增强
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📋 实验报告保存到: {report_file}")
        return str(report_file)


if __name__ == "__main__":
    # 测试可视化工具
    print("🧪 测试实验可视化工具")
    
    visualizer = ExperimentVisualizer()
    
    # 查找最新的结果文件
    results_dir = Path("experiments/results/baseline_comparison")
    if results_dir.exists():
        result_files = list(results_dir.glob("baseline_comparison_*.json"))
        if result_files:
            latest_file = max(result_files, key=lambda x: x.stat().st_mtime)
            print(f"📊 处理结果文件: {latest_file}")
            
            # 生成完整报告
            visualizer.generate_experiment_report(str(latest_file))
        else:
            print("❌ 没有找到结果文件")
    else:
        print("❌ 结果目录不存在")
    
    print("✅ 测试完成")
