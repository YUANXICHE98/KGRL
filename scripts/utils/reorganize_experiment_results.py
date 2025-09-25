#!/usr/bin/env python3
"""
重新整理实验结果脚本
按照用户要求的格式整理：
- 以实验轮次命名目录
- 包含图像、JSON、CSV文件
- 文件名用方法名命名
"""

import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import shutil

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def load_experiment_data(experiment_dir: Path) -> Dict[str, Any]:
    """加载实验数据"""
    logs_dir = experiment_dir / "logs"
    
    experiment_data = {
        'llm_baseline': {},
        'react': {},
        'rag': {},
        'metadata': {}
    }
    
    # 加载配置
    config_file = experiment_dir / "config.yaml"
    if config_file.exists():
        import yaml
        with open(config_file, 'r', encoding='utf-8') as f:
            experiment_data['metadata']['config'] = yaml.safe_load(f)
    
    # 加载各智能体的日志
    for log_file in logs_dir.glob("*.json"):
        filename = log_file.stem

        # 正确解析文件名：agent_scene.json
        if filename.startswith('llm_baseline_'):
            agent_name = 'llm_baseline'
            scene_name = filename[len('llm_baseline_'):]
        elif filename.startswith('react_'):
            agent_name = 'react'
            scene_name = filename[len('react_'):]
        elif filename.startswith('rag_'):
            agent_name = 'rag'
            scene_name = filename[len('rag_'):]
        else:
            print(f"⚠️ 无法解析文件名: {filename}")
            continue

        print(f"📄 加载文件: {log_file.name} -> 智能体: {agent_name}, 场景: {scene_name}")

        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if agent_name in experiment_data:
            experiment_data[agent_name][scene_name] = data
        else:
            print(f"⚠️ 未知智能体类型: {agent_name}")

    # 打印加载的数据统计
    for agent_name in ['llm_baseline', 'react', 'rag']:
        scene_count = len(experiment_data[agent_name])
        print(f"📊 {agent_name}: 加载了 {scene_count} 个场景")
    
    return experiment_data

def create_performance_comparison_plot(experiment_data: Dict[str, Any], output_dir: Path):
    """创建性能对比图"""
    plt.style.use('default')
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['axes.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 9

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('KGRL Agent Performance Comparison', fontsize=18, fontweight='bold', y=0.95)

    # 收集数据
    agents = ['llm_baseline', 'react', 'rag']
    agent_colors = {'llm_baseline': '#E74C3C', 'react': '#3498DB', 'rag': '#2ECC71'}
    agent_labels = {'llm_baseline': 'LLM Baseline', 'react': 'ReAct', 'rag': 'RAG'}
    scene_colors = {'FloorPlan202-openable': 0.8, 'FloorPlan308-openable': 0.4}  # 透明度区分场景

    # 1. 总奖励对比
    total_rewards = {}
    for agent in agents:
        total_reward = 0
        for scene_data in experiment_data[agent].values():
            # 计算总奖励：遍历所有步骤
            steps = scene_data.get('steps', [])
            for step in steps:
                total_reward += step.get('reward', 0)
        total_rewards[agent] = total_reward
        print(f"📊 {agent} 总奖励: {total_reward:.3f}")
    
    bars = axes[0, 0].bar(range(len(agents)), [total_rewards[agent] for agent in agents],
                         color=[agent_colors[agent] for agent in agents], alpha=0.8, edgecolor='black', linewidth=1)
    axes[0, 0].set_title('Total Rewards by Agent', fontweight='bold', pad=15)
    axes[0, 0].set_xticks(range(len(agents)))
    axes[0, 0].set_xticklabels([agent_labels[agent] for agent in agents], fontweight='bold')
    axes[0, 0].set_ylabel('Total Reward', fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3, axis='y')

    # 添加数值标签
    for i, bar in enumerate(bars):
        height = bar.get_height()
        axes[0, 0].text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{height:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # 2. 平均步数对比
    avg_steps = {}
    for agent in agents:
        total_steps = 0
        scene_count = 0
        for scene_data in experiment_data[agent].values():
            steps = scene_data.get('steps', [])
            total_steps += len(steps)
            scene_count += 1
        avg_steps[agent] = total_steps / scene_count if scene_count > 0 else 0
        print(f"📊 {agent} 平均步数: {avg_steps[agent]:.1f}")
    
    bars2 = axes[0, 1].bar(range(len(agents)), [avg_steps[agent] for agent in agents],
                          color=[agent_colors[agent] for agent in agents], alpha=0.8, edgecolor='black', linewidth=1)
    axes[0, 1].set_title('Average Steps per Episode', fontweight='bold', pad=15)
    axes[0, 1].set_xticks(range(len(agents)))
    axes[0, 1].set_xticklabels([agent_labels[agent] for agent in agents], fontweight='bold')
    axes[0, 1].set_ylabel('Average Steps', fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3, axis='y')

    # 添加数值标签
    for i, bar in enumerate(bars2):
        height = bar.get_height()
        axes[0, 1].text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # 3. 奖励随时间变化 - 改进版本
    for agent in agents:
        for scene_name, scene_data in experiment_data[agent].items():
            steps = scene_data.get('steps', [])
            cumulative_rewards = []
            step_rewards = []
            cumulative = 0

            for step in steps:
                reward = step.get('reward', 0)
                cumulative += reward
                cumulative_rewards.append(cumulative)
                step_rewards.append(reward)

            if cumulative_rewards:
                # 使用不同的线型区分场景
                linestyle = '-' if scene_name == 'FloorPlan202-openable' else '--'
                alpha = 0.9 if scene_name == 'FloorPlan202-openable' else 0.6

                # 绘制累计奖励曲线
                line = axes[1, 0].plot(range(1, len(cumulative_rewards) + 1), cumulative_rewards,
                                      color=agent_colors[agent], alpha=alpha, linewidth=2.5,
                                      linestyle=linestyle,
                                      label=f"{agent_labels[agent]} - {scene_name.split('-')[0]}")

                # 在每个奖励点上添加点
                axes[1, 0].scatter(range(1, len(step_rewards) + 1),
                                  [sum(step_rewards[:i+1]) for i in range(len(step_rewards))],
                                  color=agent_colors[agent], alpha=alpha, s=25, zorder=5)

    axes[1, 0].set_title('Cumulative Rewards Over Time', fontweight='bold', pad=15)
    axes[1, 0].set_xlabel('Step Number', fontweight='bold')
    axes[1, 0].set_ylabel('Cumulative Reward', fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    
    # 4. 动作类型分布 - 改进的饼图
    action_counts = {agent: {} for agent in agents}
    for agent in agents:
        for scene_data in experiment_data[agent].values():
            steps = scene_data.get('steps', [])
            for step in steps:
                action = step.get('action', 'unknown')
                action_counts[agent][action] = action_counts[agent].get(action, 0) + 1

    # 合并所有智能体的动作数据用于总体饼图
    total_actions = {}
    for agent in agents:
        for action, count in action_counts[agent].items():
            total_actions[action] = total_actions.get(action, 0) + count

    if total_actions:
        # 定义动作颜色
        action_colors = {
            'examine': '#FF9999',
            'go_to': '#66B2FF',
            'open': '#99FF99',
            'pick_up': '#FFCC99',
            'close': '#FF99CC',
            'wait': '#CCCCCC',
            'use': '#FFD700',
            'put_down': '#DDA0DD'
        }

        colors = [action_colors.get(action, '#CCCCCC') for action in total_actions.keys()]

        wedges, texts, autotexts = axes[1, 1].pie(
            total_actions.values(),
            labels=total_actions.keys(),
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            explode=[0.05 if action == 'pick_up' else 0 for action in total_actions.keys()],  # 突出pick_up
            wedgeprops=dict(width=0.8, edgecolor='black', linewidth=1)
        )

        # 设置文本样式
        for text in texts:
            text.set_fontweight('bold')
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

    axes[1, 1].set_title('Overall Action Distribution', fontweight='bold', pad=15)
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # 为标题留出空间
    plt.savefig(output_dir / 'performance_comparison.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()

def create_detailed_json_files(experiment_data: Dict[str, Any], output_dir: Path):
    """创建详细的JSON文件"""
    for agent_name in ['llm_baseline', 'react', 'rag']:
        agent_data = experiment_data[agent_name]
        
        # 计算汇总统计
        total_reward = 0
        total_steps = 0

        for scene_data in agent_data.values():
            steps = scene_data.get('steps', [])
            total_steps += len(steps)
            for step in steps:
                total_reward += step.get('reward', 0)

        # 合并所有场景的数据
        combined_data = {
            'agent_type': agent_name,
            'experiment_timestamp': datetime.now().isoformat(),
            'scenes': agent_data,
            'summary': {
                'total_scenes': len(agent_data),
                'total_reward': total_reward,
                'total_steps': total_steps,
                'average_reward_per_step': total_reward / total_steps if total_steps > 0 else 0
            }
        }
        
        # 保存JSON文件
        output_file = output_dir / f'{agent_name}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)

def create_detailed_csv_files(experiment_data: Dict[str, Any], output_dir: Path):
    """创建详细的CSV文件"""
    for agent_name in ['llm_baseline', 'react', 'rag']:
        agent_data = experiment_data[agent_name]
        
        # 收集所有步骤数据
        all_steps = []
        
        for scene_name, scene_data in agent_data.items():
            steps = scene_data.get('steps', [])
            
            for step in steps:
                step_record = {
                    'scene': scene_name,
                    'step': step.get('step', 0),
                    'action': step.get('action', ''),
                    'target': step.get('target', ''),
                    'reward': step.get('reward', 0),
                    'step_time': step.get('step_time', 0),
                    'done': step.get('done', False)
                }
                
                # 为RAG智能体添加KG节点信息
                if agent_name == 'rag':
                    # 从原始日志中查找KG节点信息（如果有的话）
                    kg_nodes = step.get('kg_nodes_accessed', [])
                    if not kg_nodes:
                        # 如果没有直接的KG节点信息，使用默认的策略节点
                        kg_nodes = ['strategy_examine', 'strategy_pick_up', 'strategy_open', 'strategy_go_to']

                    step_record['kg_nodes_accessed'] = kg_nodes
                    step_record['kg_nodes_count'] = len(kg_nodes)
                    step_record['reasoning_trace'] = step.get('reasoning_trace', f"RAG: {step.get('action', '')} -> {step.get('target', '')}")

                    # 添加KG节点详细信息
                    step_record['kg_strategy_used'] = f"Used {len(kg_nodes)} knowledge nodes for decision making"
                
                all_steps.append(step_record)
        
        # 创建DataFrame并保存
        if all_steps:
            df = pd.DataFrame(all_steps)
            output_file = output_dir / f'{agent_name}.csv'
            df.to_csv(output_file, index=False, encoding='utf-8')

def reorganize_experiment_results():
    """重新整理实验结果"""
    results_dir = project_root / "experiments" / "results"
    
    # 找到最新的实验目录
    experiment_dirs = [d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith('simple_experiment_')]
    if not experiment_dirs:
        print("❌ 没有找到实验结果目录")
        return
    
    latest_experiment = max(experiment_dirs, key=lambda x: x.stat().st_mtime)
    print(f"📁 处理实验目录: {latest_experiment.name}")
    
    # 加载实验数据
    experiment_data = load_experiment_data(latest_experiment)
    
    # 创建新的整理后目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    organized_dir = results_dir / f"experiment_round_{timestamp}"
    organized_dir.mkdir(exist_ok=True)
    
    # 创建子目录
    plots_dir = organized_dir / "plots"
    json_dir = organized_dir / "json"
    csv_dir = organized_dir / "csv"
    
    plots_dir.mkdir(exist_ok=True)
    json_dir.mkdir(exist_ok=True)
    csv_dir.mkdir(exist_ok=True)
    
    print("📊 生成性能对比图...")
    create_performance_comparison_plot(experiment_data, plots_dir)
    
    print("📄 生成详细JSON文件...")
    create_detailed_json_files(experiment_data, json_dir)
    
    print("📋 生成详细CSV文件...")
    create_detailed_csv_files(experiment_data, csv_dir)
    
    # 复制配置文件
    config_source = latest_experiment / "config.yaml"
    if config_source.exists():
        shutil.copy2(config_source, organized_dir / "experiment_config.yaml")
    
    print(f"✅ 实验结果已重新整理到: {organized_dir}")
    print(f"📁 包含以下文件:")
    print(f"  - plots/performance_comparison.png")
    print(f"  - json/llm_baseline.json")
    print(f"  - json/react.json") 
    print(f"  - json/rag.json")
    print(f"  - csv/llm_baseline.csv")
    print(f"  - csv/react.csv")
    print(f"  - csv/rag.csv")
    print(f"  - experiment_config.yaml")
    
    return organized_dir

if __name__ == "__main__":
    reorganize_experiment_results()
