#!/usr/bin/env python3
"""
完整的基线对比实验
包含真正的LLM调用、ReAct、RAG三条线
"""

import json
import time
import random
from pathlib import Path
from typing import Dict, Any, List
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.environments.scene_based_env import SceneBasedEnvironment
from src.utils.llm_client import LLMBaselineAgent
from src.agents.baseline_agents import ReActAgent, RAGAgent
from experiments.utils.visualization import ExperimentVisualizer


class CompleteBaselineExperiment:
    """完整的基线对比实验"""
    
    def __init__(self, api_key: str, num_episodes: int = 20, max_steps: int = 15):
        self.api_key = api_key
        self.num_episodes = num_episodes
        self.max_steps = max_steps
        
        # 初始化环境
        self.env = SceneBasedEnvironment()
        
        # 初始化三个智能体
        self.agents = {
            'llm_baseline': LLMBaselineAgent(api_key),
            'react': ReActAgent(),
            'rag': RAGAgent()
        }
        
        # 结果记录
        self.results = {agent_name: {
            'rewards': [],
            'success_rates': [],
            'steps': [],
            'episode_details': []
        } for agent_name in self.agents.keys()}
        
        # 实验配置
        self.experiment_config = {
            'num_episodes': num_episodes,
            'max_steps': max_steps,
            'agents': list(self.agents.keys()),
            'timestamp': int(time.time()),
            'api_key_provided': bool(api_key)
        }
        
        print(f"🧪 初始化完整基线实验 (episodes: {num_episodes}, max_steps: {max_steps})")
    
    def run_single_episode(self, agent_name: str, agent, scene_name: str = None) -> Dict[str, Any]:
        """运行单个episode"""
        print(f"  🎮 运行 {agent_name} 在场景 {scene_name}")
        
        # 重置环境
        obs = self.env.reset(scene_name)
        agent.reset(obs)
        
        total_reward = 0
        steps = 0
        done = False
        episode_log = []
        
        while not done and steps < self.max_steps:
            # 智能体选择动作
            try:
                action, target = agent.select_action(obs)
                print(f"    步骤 {steps+1}: {action} {target or ''}")
            except Exception as e:
                print(f"    ❌ 智能体选择动作失败: {e}")
                action, target = "wait", None
            
            # 执行动作
            try:
                next_obs, reward, done, info = self.env.step(action, target)
            except Exception as e:
                print(f"    ❌ 环境执行动作失败: {e}")
                reward = -0.1
                done = True
                next_obs = obs
                info = {}
            
            # 记录步骤
            step_log = {
                'step': steps,
                'action': action,
                'target': target,
                'reward': reward,
                'done': done
            }
            episode_log.append(step_log)
            
            # 智能体学习/更新
            try:
                agent.update(obs, action, target, reward, next_obs, done)
            except Exception as e:
                print(f"    ⚠️  智能体更新失败: {e}")
            
            # 更新状态
            obs = next_obs
            total_reward += reward
            steps += 1
            
            # 早停条件
            if reward > 5:  # 任务成功
                done = True
                break
        
        # 判断成功
        success = info.get('task_completed', False) or total_reward > 3
        
        result = {
            'agent': agent_name,
            'scene': scene_name,
            'total_reward': total_reward,
            'steps': steps,
            'success': success,
            'episode_log': episode_log,
            'final_info': info
        }
        
        print(f"    结果: 奖励={total_reward:.2f}, 步数={steps}, 成功={success}")
        return result
    
    def run_experiment(self):
        """运行完整实验"""
        print(f"🚀 开始完整基线对比实验")
        
        # 获取可用场景
        scenes = self.env.get_scene_list()
        if not scenes:
            print("❌ 没有可用场景，请先构建知识图谱")
            return
        
        print(f"📊 可用场景: {len(scenes)} 个")
        
        # 限制场景数量以加快实验
        if len(scenes) > 5:
            scenes = random.sample(scenes, 5)
            print(f"🎯 随机选择 {len(scenes)} 个场景进行实验")
        
        start_time = time.time()
        
        for episode in range(self.num_episodes):
            # 随机选择场景
            scene_name = random.choice(scenes)
            
            print(f"\n🎮 Episode {episode + 1}/{self.num_episodes} - 场景: {scene_name}")
            
            # 为每个智能体运行episode
            for agent_name, agent in self.agents.items():
                try:
                    result = self.run_single_episode(agent_name, agent, scene_name)
                    
                    # 记录结果
                    self.results[agent_name]['rewards'].append(result['total_reward'])
                    self.results[agent_name]['success_rates'].append(1 if result['success'] else 0)
                    self.results[agent_name]['steps'].append(result['steps'])
                    self.results[agent_name]['episode_details'].append(result)
                    
                except Exception as e:
                    print(f"  ❌ {agent_name} 执行失败: {e}")
                    # 记录失败结果
                    self.results[agent_name]['rewards'].append(-5)
                    self.results[agent_name]['success_rates'].append(0)
                    self.results[agent_name]['steps'].append(self.max_steps)
            
            # 定期报告进度
            if (episode + 1) % 5 == 0:
                self._report_progress(episode + 1)
        
        # 最终分析
        self._final_analysis()
        
        # 保存结果
        results_file = self._save_results()
        
        # 生成可视化
        self._generate_visualizations(results_file)
        
        total_time = time.time() - start_time
        print(f"⏱️  总实验时间: {total_time:.2f} 秒")
        
        return results_file
    
    def _report_progress(self, episode: int):
        """报告进度"""
        print(f"\n📊 Episode {episode} 进度报告:")
        
        for agent_name in self.agents.keys():
            rewards = self.results[agent_name]['rewards']
            success_rates = self.results[agent_name]['success_rates']
            
            if rewards:
                avg_reward = sum(rewards) / len(rewards)
                success_rate = sum(success_rates) / len(success_rates)
                
                print(f"  {agent_name}: 平均奖励={avg_reward:.3f}, 成功率={success_rate:.3f}")
    
    def _final_analysis(self):
        """最终分析"""
        print(f"\n🎯 最终分析结果:")
        
        analysis = {}
        
        for agent_name in self.agents.keys():
            rewards = self.results[agent_name]['rewards']
            success_rates = self.results[agent_name]['success_rates']
            steps = self.results[agent_name]['steps']
            
            if rewards:
                analysis[agent_name] = {
                    'avg_reward': sum(rewards) / len(rewards),
                    'success_rate': sum(success_rates) / len(success_rates),
                    'avg_steps': sum(steps) / len(steps),
                    'total_episodes': len(rewards),
                    'best_reward': max(rewards),
                    'worst_reward': min(rewards),
                    'reward_std': np.std(rewards) if len(rewards) > 1 else 0
                }
        
        # 显示结果
        print(f"\n📈 性能对比:")
        for agent_name, stats in analysis.items():
            print(f"\n🤖 {agent_name.upper()}:")
            print(f"  - 平均奖励: {stats['avg_reward']:.3f} ± {stats['reward_std']:.3f}")
            print(f"  - 成功率: {stats['success_rate']:.3f}")
            print(f"  - 平均步数: {stats['avg_steps']:.1f}")
            print(f"  - 最佳奖励: {stats['best_reward']:.3f}")
        
        # 排名
        reward_ranking = sorted(analysis.items(), key=lambda x: x[1]['avg_reward'], reverse=True)
        success_ranking = sorted(analysis.items(), key=lambda x: x[1]['success_rate'], reverse=True)
        
        print(f"\n🏆 性能排名:")
        reward_str = ' > '.join([f'{name}({stats["avg_reward"]:.3f})' for name, stats in reward_ranking])
        success_str = ' > '.join([f'{name}({stats["success_rate"]:.3f})' for name, stats in success_ranking])
        print(f"📊 按平均奖励: {reward_str}")
        print(f"🎯 按成功率: {success_str}")
        
        self.final_analysis = analysis
    
    def _save_results(self) -> str:
        """保存实验结果"""
        results_dir = Path("experiments/results/baseline_comparison")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = int(time.time())
        
        # 保存详细结果
        detailed_results = {
            'experiment_config': self.experiment_config,
            'results': self.results,
            'final_analysis': getattr(self, 'final_analysis', {}),
            'agent_statistics': {name: agent.get_statistics() for name, agent in self.agents.items()},
            'timestamp': timestamp
        }
        
        results_file = results_dir / f"complete_baseline_experiment_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 详细结果保存到: {results_file}")
        return str(results_file)
    
    def _generate_visualizations(self, results_file: str):
        """生成可视化"""
        print("📊 生成实验可视化...")
        
        try:
            visualizer = ExperimentVisualizer()
            visualizer.generate_experiment_report(results_file)
        except Exception as e:
            print(f"⚠️  可视化生成失败: {e}")


def main():
    """主函数"""
    print("🎯 完整基线对比实验")
    
    # LLM API配置
    api_key = "sk-rvwMvUNbWBz9L76KB05650C7Cc464324BdC98dB3FbD4296a"
    
    # 创建实验
    experiment = CompleteBaselineExperiment(
        api_key=api_key,
        num_episodes=10,  # 减少episode数量以加快测试
        max_steps=10      # 减少步数以加快测试
    )
    
    # 运行实验
    results_file = experiment.run_experiment()
    
    print(f"\n🎉 实验完成! 结果文件: {results_file}")


if __name__ == "__main__":
    # 导入numpy用于统计计算
    try:
        import numpy as np
    except ImportError:
        print("⚠️  numpy未安装，使用简化统计")
        class np:
            @staticmethod
            def std(x):
                if len(x) <= 1:
                    return 0
                mean = sum(x) / len(x)
                return (sum((xi - mean) ** 2 for xi in x) / len(x)) ** 0.5
    
    main()
