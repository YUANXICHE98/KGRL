#!/usr/bin/env python3
"""
修复版本的基线对比实验 - 使用真实KG数据和状态更新
"""

import sys
import json
import time
import random
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.environments.scene_based_env import SceneBasedEnvironment
from src.agents.baseline_agents import LLMBaselineAgent, ReActAgent, RAGAgent
from tools.visualization.visualization import ExperimentVisualizer

class FixedBaselineExperiment:
    """修复版本的基线实验"""
    
    def __init__(self, episodes: int = 12, max_steps: int = 15):
        self.episodes = episodes
        self.max_steps = max_steps
        
        # 初始化环境
        self.env = SceneBasedEnvironment()
        
        # 初始化智能体
        self.agents = {
            'llm_baseline': LLMBaselineAgent(),
            'react': ReActAgent(),
            'rag': RAGAgent()
        }
        
        # 结果存储
        self.results = {agent_name: {
            'rewards': [],
            'steps': [],
            'success': [],
            'actions': [],
            'episode_details': []
        } for agent_name in self.agents.keys()}
        
        print(f"🎯 修复版基线实验 - 真实KG数据")
        print(f"📊 回合数: {episodes}, 最大步数: {max_steps}")
        print(f"🤖 智能体: {list(self.agents.keys())}")
        print(f"🚀 开始修复版基线实验")
        
        # 检查可用场景
        if not self.env.scenes:
            raise ValueError("❌ 没有可用场景！请检查KG数据")
        
        available_scenes = list(self.env.scenes.keys())
        print(f"📊 可用场景: {len(available_scenes)}")
        print(f"🎯 场景列表: {available_scenes[:5]}...")
    
    def run_experiment(self) -> str:
        """运行完整实验"""
        start_time = time.time()
        
        # 选择实验场景
        available_scenes = list(self.env.scenes.keys())
        selected_scenes = random.sample(available_scenes, min(5, len(available_scenes)))
        print(f"🎯 选择的场景: {selected_scenes}")
        
        # 对每个智能体运行实验
        for agent_name, agent in self.agents.items():
            print(f"\n🤖 测试智能体: {agent_name.upper()}")
            
            for episode in range(self.episodes):
                # 随机选择场景
                scene_name = random.choice(selected_scenes)
                
                # 运行单个回合
                episode_result = self._run_episode(agent_name, agent, scene_name, episode + 1)
                
                # 记录结果
                self.results[agent_name]['rewards'].append(episode_result['total_reward'])
                self.results[agent_name]['steps'].append(episode_result['steps'])
                self.results[agent_name]['success'].append(episode_result['success'])
                self.results[agent_name]['actions'].append(episode_result['actions'])
                self.results[agent_name]['episode_details'].append(episode_result)
                
                print(f"  回合 {episode + 1}: 奖励={episode_result['total_reward']:.3f}, "
                      f"步数={episode_result['steps']}, 成功={episode_result['success']}")
        
        # 计算最终分析
        final_analysis = self._analyze_results()
        
        # 保存结果
        results_file = self._save_results(final_analysis, start_time)
        
        # 生成可视化
        self._generate_visualizations(results_file)
        
        return results_file
    
    def _run_episode(self, agent_name: str, agent, scene_name: str, episode_num: int) -> Dict[str, Any]:
        """运行单个回合"""
        # 重置环境和智能体
        observation = self.env.reset(scene_name)
        agent.reset()
        
        total_reward = 0
        actions_taken = []
        step_rewards = []
        
        for step in range(self.max_steps):
            # 智能体选择动作
            action, target = agent.select_action(observation)
            actions_taken.append({'action': action, 'target': target})
            
            # 环境执行动作
            observation, reward, done, info = self.env.step(action, target)
            
            total_reward += reward
            step_rewards.append(reward)
            
            if done:
                break
        
        return {
            'agent': agent_name,
            'scene': scene_name,
            'episode': episode_num,
            'total_reward': total_reward,
            'steps': step + 1,
            'success': done and info.get('task_completed', False),
            'actions': actions_taken,
            'step_rewards': step_rewards,
            'final_info': info
        }
    
    def _analyze_results(self) -> Dict[str, Any]:
        """分析实验结果"""
        analysis = {}
        
        for agent_name, results in self.results.items():
            rewards = results['rewards']
            steps = results['steps']
            success = results['success']
            
            analysis[agent_name] = {
                'avg_reward': sum(rewards) / len(rewards) if rewards else 0,
                'std_reward': self._calculate_std(rewards),
                'success_rate': sum(success) / len(success) if success else 0,
                'avg_steps': sum(steps) / len(steps) if steps else 0,
                'best_reward': max(rewards) if rewards else 0,
                'worst_reward': min(rewards) if rewards else 0,
                'total_episodes': len(rewards)
            }
        
        return analysis
    
    def _calculate_std(self, values: List[float]) -> float:
        """计算标准差"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _save_results(self, final_analysis: Dict[str, Any], start_time: float) -> str:
        """保存实验结果"""
        timestamp = int(time.time())
        
        results_data = {
            'experiment_info': {
                'type': 'fixed_baseline_experiment',
                'timestamp': timestamp,
                'duration': time.time() - start_time,
                'episodes': self.episodes,
                'max_steps': self.max_steps,
                'agents': list(self.agents.keys()),
                'scenes_used': len(self.env.scenes)
            },
            'results': self.results,
            'final_analysis': final_analysis
        }
        
        # 保存到文件
        results_dir = Path("experiments/results/baseline_comparison")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = results_dir / f"fixed_baseline_experiment_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 结果已保存到: {results_file}")
        return str(results_file)
    
    def _generate_visualizations(self, results_file: str):
        """生成可视化图表"""
        print(f"📊 生成实验可视化...")
        
        try:
            visualizer = ExperimentVisualizer()
            
            # 生成基线对比图
            visualizer.plot_baseline_comparison(results_file)
            
            # 生成学习曲线
            visualizer.plot_learning_curves(results_file)
            
            # 生成性能雷达图
            visualizer.plot_performance_radar(results_file)
            
            print(f"📈 可视化图表生成完成")
            
        except Exception as e:
            print(f"⚠️ 可视化生成失败: {e}")
    
    def print_summary(self, final_analysis: Dict[str, Any]):
        """打印实验总结"""
        print(f"\n🎯 修复版实验总结:")
        print("=" * 60)
        
        # 性能排名
        agents_by_reward = sorted(final_analysis.items(), 
                                key=lambda x: x[1]['avg_reward'], reverse=True)
        
        print(f"📈 性能对比:")
        for i, (agent, stats) in enumerate(agents_by_reward, 1):
            print(f"{i}. {agent.upper()}:")
            print(f"   - 平均奖励: {stats['avg_reward']:.3f} ± {stats['std_reward']:.3f}")
            print(f"   - 成功率: {stats['success_rate']:.3f}")
            print(f"   - 平均步数: {stats['avg_steps']:.1f}")
            print(f"   - 最佳奖励: {stats['best_reward']:.3f}")
        
        print(f"\n🏆 性能排名:")
        ranking = " > ".join([f"{agent}({stats['avg_reward']:.3f})" 
                            for agent, stats in agents_by_reward])
        print(f"按平均奖励: {ranking}")

def main():
    """主函数"""
    # 创建实验
    experiment = FixedBaselineExperiment(episodes=12, max_steps=15)
    
    # 运行实验
    results_file = experiment.run_experiment()
    
    # 打印总结
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    experiment.print_summary(data['final_analysis'])
    
    print(f"\n🎉 修复版实验完成! 结果: {results_file}")

if __name__ == "__main__":
    main()
