#!/usr/bin/env python3
"""
修复图表标签为英文版本
直接基于现有数据重新生成清晰的英文图表
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import json

def load_data():
    """加载实验数据"""
    data_file = Path("results/rag_vs_baseline_comparison/data/results_20250828_190733.json")
    with open(data_file, 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data)

def create_comparison_plot(df):
    """创建对比图表"""
    plt.style.use('default')  # 使用默认样式避免字体问题
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('RAG vs Baseline - Performance Comparison', fontsize=16, fontweight='bold')
    
    # 1. 成功率对比
    success_stats = df.groupby('agent_type')['success'].agg(['mean', 'std', 'count']).reset_index()
    success_stats['se'] = success_stats['std'] / np.sqrt(success_stats['count'])
    
    bars1 = axes[0, 0].bar(success_stats['agent_type'], success_stats['mean'], 
                          yerr=success_stats['se'], capsize=5, alpha=0.8, 
                          color=['#1f77b4', '#ff7f0e'])
    axes[0, 0].set_title('Success Rate Comparison', fontweight='bold', fontsize=14)
    axes[0, 0].set_ylabel('Success Rate', fontsize=12)
    axes[0, 0].set_ylim(0, 1)
    axes[0, 0].grid(True, alpha=0.3)
    
    # 添加数值标签
    for i, (bar, mean, se) in enumerate(zip(bars1, success_stats['mean'], success_stats['se'])):
        axes[0, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + se + 0.02,
                       f'{mean:.1%}', ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # 2. 平均步数对比
    steps_stats = df.groupby('agent_type')['total_steps'].agg(['mean', 'std', 'count']).reset_index()
    steps_stats['se'] = steps_stats['std'] / np.sqrt(steps_stats['count'])
    
    bars2 = axes[0, 1].bar(steps_stats['agent_type'], steps_stats['mean'],
                          yerr=steps_stats['se'], capsize=5, alpha=0.8,
                          color=['#1f77b4', '#ff7f0e'])
    axes[0, 1].set_title('Average Steps Comparison', fontweight='bold', fontsize=14)
    axes[0, 1].set_ylabel('Average Steps', fontsize=12)
    axes[0, 1].grid(True, alpha=0.3)
    
    for i, (bar, mean, se) in enumerate(zip(bars2, steps_stats['mean'], steps_stats['se'])):
        axes[0, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + se + 0.5,
                       f'{mean:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # 3. 奖励分布箱线图
    reward_data = []
    for agent_type in df['agent_type'].unique():
        agent_rewards = df[df['agent_type'] == agent_type]['total_reward'].tolist()
        reward_data.append(agent_rewards)
    
    bp = axes[1, 0].boxplot(reward_data, labels=df['agent_type'].unique(), patch_artist=True)
    axes[1, 0].set_title('Reward Distribution', fontweight='bold', fontsize=14)
    axes[1, 0].set_ylabel('Total Reward', fontsize=12)
    axes[1, 0].grid(True, alpha=0.3)
    
    # 设置箱线图颜色
    colors = ['#1f77b4', '#ff7f0e']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # 4. API响应时间对比
    api_data = []
    labels = []
    for _, row in df.iterrows():
        if row['api_response_times']:
            api_data.extend(row['api_response_times'])
            labels.extend([row['agent_type']] * len(row['api_response_times']))
    
    # 分组API时间数据
    baseline_times = [time for time, label in zip(api_data, labels) if 'Baseline' in label]
    rag_times = [time for time, label in zip(api_data, labels) if 'RAG' in label]
    
    bp2 = axes[1, 1].boxplot([baseline_times, rag_times], 
                            labels=['Baseline_LLM', 'RAG_Enhanced_LLM'], 
                            patch_artist=True)
    axes[1, 1].set_title('API Response Time Distribution', fontweight='bold', fontsize=14)
    axes[1, 1].set_ylabel('Response Time (seconds)', fontsize=12)
    axes[1, 1].grid(True, alpha=0.3)
    
    # 设置箱线图颜色
    for patch, color in zip(bp2['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    plt.tight_layout()
    return fig

def create_detailed_plot(df):
    """创建详细分析图表"""
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle('RAG vs Baseline - Detailed Performance Analysis', fontsize=16, fontweight='bold')
    
    # 1. 成功率随时间变化
    df_sorted = df.sort_values('timestamp')
    window_size = 5
    
    for agent_type in df['agent_type'].unique():
        agent_df = df_sorted[df_sorted['agent_type'] == agent_type].reset_index(drop=True)
        if len(agent_df) >= window_size:
            rolling_success = agent_df['success'].rolling(window=window_size, center=True).mean()
            axes[0, 0].plot(range(len(agent_df)), rolling_success, 
                           label=f'{agent_type}', linewidth=2, marker='o', markersize=4)
    
    axes[0, 0].set_title('Learning Curve (Rolling Average)', fontweight='bold', fontsize=14)
    axes[0, 0].set_xlabel('Episode', fontsize=12)
    axes[0, 0].set_ylabel('Success Rate', fontsize=12)
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 步数 vs 成功率散点图（改进版）
    colors = ['#1f77b4', '#ff7f0e']
    markers = ['o', 's']

    for i, agent_type in enumerate(df['agent_type'].unique()):
        agent_df = df[df['agent_type'] == agent_type]

        # 分别绘制成功和失败的点
        success_df = agent_df[agent_df['success'] == True]
        failure_df = agent_df[agent_df['success'] == False]

        if not success_df.empty:
            axes[0, 1].scatter(success_df['total_steps'], [1.02 + i*0.04]*len(success_df),
                             alpha=0.8, label=f'{agent_type} (Success)', s=80,
                             color=colors[i], marker=markers[i], edgecolors='black', linewidth=0.5)

        if not failure_df.empty:
            axes[0, 1].scatter(failure_df['total_steps'], [-0.02 - i*0.04]*len(failure_df),
                             alpha=0.8, label=f'{agent_type} (Failure)', s=100,
                             color=colors[i], marker='x')

    axes[0, 1].set_title('Steps vs Success/Failure', fontweight='bold', fontsize=14)
    axes[0, 1].set_xlabel('Total Steps', fontsize=12)
    axes[0, 1].set_ylabel('Outcome', fontsize=12)
    axes[0, 1].set_ylim(-0.2, 1.2)
    axes[0, 1].set_yticks([0, 1])
    axes[0, 1].set_yticklabels(['Failure', 'Success'])
    axes[0, 1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. 平均API响应时间对比（更有意义的指标）
    api_time_stats = []
    for agent_type in df['agent_type'].unique():
        agent_df = df[df['agent_type'] == agent_type]
        all_times = []
        for times in agent_df['api_response_times']:
            all_times.extend(times)
        if all_times:
            api_time_stats.append({
                'agent': agent_type,
                'mean_time': sum(all_times) / len(all_times),
                'std_time': (sum([(t - sum(all_times)/len(all_times))**2 for t in all_times]) / len(all_times))**0.5
            })

    if api_time_stats:
        agents = [stat['agent'] for stat in api_time_stats]
        means = [stat['mean_time'] for stat in api_time_stats]
        stds = [stat['std_time'] for stat in api_time_stats]

        bars = axes[0, 2].bar(agents, means, yerr=stds, capsize=5, alpha=0.8, color=colors[:len(agents)])
        axes[0, 2].set_title('Average API Response Time', fontweight='bold', fontsize=14)
        axes[0, 2].set_ylabel('Response Time (seconds)', fontsize=12)
        axes[0, 2].grid(True, alpha=0.3)

        # 添加数值标签
        for bar, mean in zip(bars, means):
            axes[0, 2].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                           f'{mean:.2f}s', ha='center', va='bottom', fontweight='bold')
    else:
        axes[0, 2].text(0.5, 0.5, 'No API Time Data', ha='center', va='center', transform=axes[0, 2].transAxes)
        axes[0, 2].set_title('API Response Time', fontweight='bold', fontsize=14)
    
    # 4. 性能指标雷达图（简化为柱状图）
    metrics = []
    for agent_type in df['agent_type'].unique():
        agent_df = df[df['agent_type'] == agent_type]
        metrics.append({
            'Agent': agent_type,
            'Success Rate': agent_df['success'].mean(),
            'Efficiency': 1 / (agent_df['total_steps'].mean() / 10),  # 归一化
            'Speed': 1 / (agent_df['completion_time'].mean() / 20),   # 归一化
            'Consistency': 1 - agent_df['success'].std()  # 一致性
        })
    
    metrics_df = pd.DataFrame(metrics)
    x = np.arange(len(metrics_df))
    width = 0.2
    
    axes[1, 0].bar(x - width, metrics_df['Success Rate'], width, label='Success Rate', alpha=0.8)
    axes[1, 0].bar(x, metrics_df['Efficiency'], width, label='Efficiency', alpha=0.8)
    axes[1, 0].bar(x + width, metrics_df['Consistency'], width, label='Consistency', alpha=0.8)
    
    axes[1, 0].set_title('Performance Metrics Comparison', fontweight='bold', fontsize=14)
    axes[1, 0].set_ylabel('Normalized Score', fontsize=12)
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(metrics_df['Agent'], rotation=45)
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 5. 奖励累积曲线
    for agent_type in df['agent_type'].unique():
        agent_df = df_sorted[df_sorted['agent_type'] == agent_type].reset_index(drop=True)
        cumulative_reward = agent_df['total_reward'].cumsum()
        axes[1, 1].plot(range(len(agent_df)), cumulative_reward, 
                       label=f'{agent_type}', linewidth=2, marker='s', markersize=4)
    
    axes[1, 1].set_title('Cumulative Reward Over Time', fontweight='bold', fontsize=14)
    axes[1, 1].set_xlabel('Episode', fontsize=12)
    axes[1, 1].set_ylabel('Cumulative Reward', fontsize=12)
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    # 6. 统计摘要表格（文本形式）
    axes[1, 2].axis('off')
    summary_text = "Performance Summary:\n\n"
    
    for agent_type in df['agent_type'].unique():
        agent_df = df[df['agent_type'] == agent_type]
        summary_text += f"{agent_type}:\n"
        summary_text += f"  Episodes: {len(agent_df)}\n"
        summary_text += f"  Success Rate: {agent_df['success'].mean():.1%}\n"
        summary_text += f"  Avg Steps: {agent_df['total_steps'].mean():.1f}\n"
        summary_text += f"  Avg Reward: {agent_df['total_reward'].mean():.3f}\n"
        summary_text += f"  Avg Time: {agent_df['completion_time'].mean():.1f}s\n\n"
    
    axes[1, 2].text(0.1, 0.9, summary_text, transform=axes[1, 2].transAxes, 
                   fontsize=12, verticalalignment='top', fontfamily='monospace')
    axes[1, 2].set_title('Statistical Summary', fontweight='bold', fontsize=14)
    
    plt.tight_layout()
    return fig

def main():
    print("🎨 生成英文标签图表")
    print("=" * 50)
    
    # 加载数据
    df = load_data()
    print(f"📊 数据加载完成: {len(df)} episodes")
    
    # 创建输出目录
    output_dir = Path("results/rag_vs_baseline_comparison/plots_english")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成对比图表
    print("📈 生成对比图表...")
    fig1 = create_comparison_plot(df)
    comparison_file = output_dir / "comparison_english.png"
    fig1.savefig(comparison_file, dpi=300, bbox_inches='tight')
    plt.close(fig1)
    print(f"✅ 对比图表已保存: {comparison_file}")
    
    # 生成详细分析图表
    print("📊 生成详细分析图表...")
    fig2 = create_detailed_plot(df)
    detailed_file = output_dir / "detailed_analysis_english.png"
    fig2.savefig(detailed_file, dpi=300, bbox_inches='tight')
    plt.close(fig2)
    print(f"✅ 详细分析图表已保存: {detailed_file}")
    
    print(f"\n🎉 英文标签图表生成完成！")
    print(f"📁 保存位置: {output_dir}")
    
    # 显示数据摘要
    print(f"\n📋 实验结果摘要:")
    for agent_type in df['agent_type'].unique():
        agent_df = df[df['agent_type'] == agent_type]
        print(f"  {agent_type}:")
        print(f"    Success Rate: {agent_df['success'].mean():.1%}")
        print(f"    Average Steps: {agent_df['total_steps'].mean():.1f}")
        print(f"    Average Reward: {agent_df['total_reward'].mean():.3f}")

if __name__ == "__main__":
    main()
