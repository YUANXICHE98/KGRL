"""
结果分析脚本
用于分析实验结果，生成科研级别的报告和图表
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import argparse

sys.path.append(str(Path(__file__).parent.parent))

def load_experiment_results(results_dir: str):
    """加载实验结果"""
    results_path = Path(results_dir)
    
    # 查找最新的结果文件
    json_files = list(results_path.glob("**/data/results_*.json"))
    if not json_files:
        raise FileNotFoundError(f"No result files found in {results_dir}")
    
    latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    return pd.DataFrame(data), latest_file

def statistical_analysis(df: pd.DataFrame):
    """进行统计分析"""
    print("📊 统计分析结果")
    print("=" * 60)
    
    # 基本统计
    print("\n1. 基本统计信息")
    print(f"总Episodes: {len(df)}")
    print(f"Agent类型: {df['agent_type'].unique()}")
    print(f"实验时间跨度: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
    
    # 按Agent类型分组分析
    print("\n2. 按Agent类型分组分析")
    for agent_type in df['agent_type'].unique():
        agent_df = df[df['agent_type'] == agent_type]
        
        print(f"\n{agent_type}:")
        print(f"  Episodes: {len(agent_df)}")
        print(f"  成功率: {agent_df['success'].mean():.2%} ± {agent_df['success'].std():.3f}")
        print(f"  平均步数: {agent_df['total_steps'].mean():.1f} ± {agent_df['total_steps'].std():.1f}")
        print(f"  平均奖励: {agent_df['total_reward'].mean():.3f} ± {agent_df['total_reward'].std():.3f}")
        print(f"  平均完成时间: {agent_df['completion_time'].mean():.1f}s ± {agent_df['completion_time'].std():.1f}s")
        
        # 无效动作率
        total_actions = agent_df['total_steps'].sum()
        total_invalid = agent_df['invalid_actions'].sum()
        invalid_rate = total_invalid / total_actions if total_actions > 0 else 0
        print(f"  无效动作率: {invalid_rate:.2%}")
        
        # API性能
        if agent_df['api_response_times'].iloc[0]:
            all_api_times = []
            for times in agent_df['api_response_times']:
                all_api_times.extend(times)
            if all_api_times:
                print(f"  平均API响应时间: {np.mean(all_api_times):.2f}s ± {np.std(all_api_times):.2f}s")
        
        # 知识图谱使用情况
        kg_episodes = agent_df[agent_df['use_knowledge_graph'] == True]
        if not kg_episodes.empty:
            total_queries = kg_episodes['kg_queries'].sum()
            total_hits = kg_episodes['kg_hits'].sum()
            hit_rate = total_hits / total_queries if total_queries > 0 else 0
            print(f"  KG查询命中率: {hit_rate:.2%} ({total_hits}/{total_queries})")
    
    # 统计显著性检验
    if len(df['agent_type'].unique()) >= 2:
        print("\n3. 统计显著性检验")
        agent_types = df['agent_type'].unique()
        
        for i, agent1 in enumerate(agent_types):
            for agent2 in agent_types[i+1:]:
                group1 = df[df['agent_type'] == agent1]['success']
                group2 = df[df['agent_type'] == agent2]['success']
                
                # 卡方检验 (成功率)
                contingency = pd.crosstab(
                    df['agent_type'].isin([agent1, agent2]),
                    df['success']
                )
                chi2, p_value = stats.chi2_contingency(contingency)[:2]
                
                print(f"\n{agent1} vs {agent2}:")
                print(f"  成功率差异显著性: p = {p_value:.4f} {'***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else 'ns'}")
                
                # t检验 (步数)
                steps1 = df[df['agent_type'] == agent1]['total_steps']
                steps2 = df[df['agent_type'] == agent2]['total_steps']
                t_stat, t_p = stats.ttest_ind(steps1, steps2)
                print(f"  步数差异显著性: p = {t_p:.4f} {'***' if t_p < 0.001 else '**' if t_p < 0.01 else '*' if t_p < 0.05 else 'ns'}")

def generate_scientific_plots(df: pd.DataFrame, output_dir: str):
    """生成科研级别的图表"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 设置科研图表样式
    plt.style.use('seaborn-v0_8-whitegrid')
    sns.set_palette("husl")
    
    # 1. 主要性能指标对比
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Agent Performance Comparison', fontsize=16, fontweight='bold')
    
    # 成功率对比 (带误差棒)
    success_stats = df.groupby('agent_type')['success'].agg(['mean', 'std', 'count']).reset_index()
    success_stats['se'] = success_stats['std'] / np.sqrt(success_stats['count'])  # 标准误
    
    bars1 = axes[0, 0].bar(success_stats['agent_type'], success_stats['mean'], 
                          yerr=success_stats['se'], capsize=5, alpha=0.8)
    axes[0, 0].set_title('Success Rate Comparison')
    axes[0, 0].set_ylabel('Success Rate')
    axes[0, 0].set_ylim(0, 1)
    
    # 添加数值标签
    for i, (bar, mean, se) in enumerate(zip(bars1, success_stats['mean'], success_stats['se'])):
        axes[0, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + se + 0.02,
                       f'{mean:.2%}', ha='center', va='bottom', fontweight='bold')
    
    # 平均步数对比
    steps_stats = df.groupby('agent_type')['total_steps'].agg(['mean', 'std', 'count']).reset_index()
    steps_stats['se'] = steps_stats['std'] / np.sqrt(steps_stats['count'])
    
    bars2 = axes[0, 1].bar(steps_stats['agent_type'], steps_stats['mean'],
                          yerr=steps_stats['se'], capsize=5, alpha=0.8)
    axes[0, 1].set_title('Average Steps to Completion')
    axes[0, 1].set_ylabel('Steps')
    
    for i, (bar, mean, se) in enumerate(zip(bars2, steps_stats['mean'], steps_stats['se'])):
        axes[0, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + se + 0.5,
                       f'{mean:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # 奖励分布箱线图
    sns.boxplot(data=df, x='agent_type', y='total_reward', ax=axes[1, 0])
    axes[1, 0].set_title('Reward Distribution')
    axes[1, 0].set_ylabel('Total Reward')
    
    # 完成时间对比
    sns.violinplot(data=df, x='agent_type', y='completion_time', ax=axes[1, 1])
    axes[1, 1].set_title('Completion Time Distribution')
    axes[1, 1].set_ylabel('Time (seconds)')
    
    plt.tight_layout()
    plt.savefig(output_path / 'performance_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. 学习曲线和趋势分析
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 按时间顺序的成功率趋势
    df_sorted = df.sort_values('timestamp')
    window_size = max(5, len(df) // 20)
    
    for agent_type in df['agent_type'].unique():
        agent_df = df_sorted[df_sorted['agent_type'] == agent_type].reset_index(drop=True)
        if len(agent_df) >= window_size:
            rolling_success = agent_df['success'].rolling(window=window_size, center=True).mean()
            axes[0].plot(range(len(agent_df)), rolling_success, 
                        label=f'{agent_type} (window={window_size})', linewidth=2)
    
    axes[0].set_title('Learning Curve (Rolling Average Success Rate)')
    axes[0].set_xlabel('Episode')
    axes[0].set_ylabel('Success Rate')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 步数vs成功率散点图
    for agent_type in df['agent_type'].unique():
        agent_df = df[df['agent_type'] == agent_type]
        axes[1].scatter(agent_df['total_steps'], agent_df['success'], 
                       alpha=0.6, label=agent_type, s=50)
    
    axes[1].set_title('Steps vs Success Rate')
    axes[1].set_xlabel('Total Steps')
    axes[1].set_ylabel('Success (1=Success, 0=Failure)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path / 'learning_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"📊 科研图表已保存到: {output_path}")

def generate_latex_table(df: pd.DataFrame, output_dir: str):
    """生成LaTeX格式的结果表格"""
    output_path = Path(output_dir)
    
    # 计算统计数据
    stats_data = []
    for agent_type in df['agent_type'].unique():
        agent_df = df[df['agent_type'] == agent_type]
        
        success_rate = agent_df['success'].mean()
        success_std = agent_df['success'].std()
        
        avg_steps = agent_df['total_steps'].mean()
        steps_std = agent_df['total_steps'].std()
        
        avg_reward = agent_df['total_reward'].mean()
        reward_std = agent_df['total_reward'].std()
        
        total_actions = agent_df['total_steps'].sum()
        total_invalid = agent_df['invalid_actions'].sum()
        invalid_rate = total_invalid / total_actions if total_actions > 0 else 0
        
        stats_data.append({
            'Agent': agent_type.replace('_', ' '),
            'Episodes': len(agent_df),
            'Success Rate': f"{success_rate:.3f} ± {success_std:.3f}",
            'Avg Steps': f"{avg_steps:.1f} ± {steps_std:.1f}",
            'Avg Reward': f"{avg_reward:.3f} ± {reward_std:.3f}",
            'Invalid Rate': f"{invalid_rate:.3f}"
        })
    
    # 生成LaTeX表格
    latex_table = """
\\begin{table}[htbp]
\\centering
\\caption{Agent Performance Comparison}
\\label{tab:agent_comparison}
\\begin{tabular}{lcccccc}
\\toprule
Agent & Episodes & Success Rate & Avg Steps & Avg Reward & Invalid Rate \\\\
\\midrule
"""
    
    for row in stats_data:
        latex_table += f"{row['Agent']} & {row['Episodes']} & {row['Success Rate']} & {row['Avg Steps']} & {row['Avg Reward']} & {row['Invalid Rate']} \\\\\n"
    
    latex_table += """\\bottomrule
\\end{tabular}
\\end{table}
"""
    
    # 保存LaTeX表格
    with open(output_path / 'results_table.tex', 'w') as f:
        f.write(latex_table)
    
    print(f"📄 LaTeX表格已保存到: {output_path / 'results_table.tex'}")

def main():
    parser = argparse.ArgumentParser(description='分析KGRL实验结果')
    parser.add_argument('--results_dir', default='results', help='结果目录路径')
    parser.add_argument('--output_dir', default='results/analysis', help='输出目录路径')
    
    args = parser.parse_args()
    
    try:
        # 加载数据
        df, source_file = load_experiment_results(args.results_dir)
        print(f"📁 加载结果文件: {source_file}")
        print(f"📊 数据概览: {len(df)} episodes, {len(df['agent_type'].unique())} agent types")
        
        # 统计分析
        statistical_analysis(df)
        
        # 生成图表
        generate_scientific_plots(df, args.output_dir)
        
        # 生成LaTeX表格
        generate_latex_table(df, args.output_dir)
        
        print(f"\n✅ 分析完成! 结果保存在: {args.output_dir}")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
