#!/usr/bin/env python3
"""
基于场景的强化学习训练脚本
Scene-based Reinforcement Learning Training Script
"""

import json
import time
import random
from pathlib import Path
from typing import Dict, Any, List
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.environments.scene_based_env import SceneBasedEnvironment
from src.agents.rl_kg_agent import RLKGAgent
from src.utils.config_manager import get_config


class SceneBasedTrainer:
    """基于场景的RL训练器"""
    
    def __init__(self, config_path: str = None):
        self.config = get_config('agents') if config_path is None else self._load_config(config_path)
        
        # 初始化环境和智能体
        self.env = SceneBasedEnvironment()
        self.agent = RLKGAgent(use_kg=True)
        self.baseline_agent = RLKGAgent(use_kg=False)  # 对比基线
        
        # 训练设置
        self.episodes = self.config.get('training', {}).get('episodes', 100)
        self.max_steps = self.config.get('training', {}).get('max_steps_per_episode', 50)
        self.eval_frequency = self.config.get('training', {}).get('evaluation', {}).get('frequency', 20)
        
        # 结果记录
        self.training_results = {
            'kg_agent': {'rewards': [], 'success_rates': [], 'steps': []},
            'baseline_agent': {'rewards': [], 'success_rates': [], 'steps': []}
        }
        
        print(f"🏋️ 初始化场景训练器 (episodes: {self.episodes})")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            import yaml
            return yaml.safe_load(f)
    
    def train_single_episode(self, agent, scene_name: str = None) -> Dict[str, Any]:
        """训练单个episode"""
        # 重置环境
        obs = self.env.reset(scene_name)
        agent.reset(obs)
        
        total_reward = 0
        steps = 0
        done = False
        
        while not done and steps < self.max_steps:
            # 智能体选择动作
            action, target = agent.select_action(obs)
            
            # 执行动作
            next_obs, reward, done, info = self.env.step(action, target)
            
            # 智能体学习
            agent.update(obs, action, target, reward, next_obs, done)
            
            # 更新状态
            obs = next_obs
            total_reward += reward
            steps += 1
        
        # 计算成功率
        success = info.get('task_completed', False) or total_reward > 5
        
        return {
            'total_reward': total_reward,
            'steps': steps,
            'success': success,
            'scene': obs['scene']
        }
    
    def evaluate_agent(self, agent, num_episodes: int = 10) -> Dict[str, float]:
        """评估智能体性能"""
        results = []
        
        for _ in range(num_episodes):
            result = self.train_single_episode(agent)
            results.append(result)
        
        # 计算统计指标
        total_rewards = [r['total_reward'] for r in results]
        success_count = sum(1 for r in results if r['success'])
        total_steps = [r['steps'] for r in results]
        
        return {
            'avg_reward': sum(total_rewards) / len(total_rewards),
            'success_rate': success_count / len(results),
            'avg_steps': sum(total_steps) / len(total_steps),
            'episodes': len(results)
        }
    
    def train(self):
        """主训练循环"""
        print(f"🚀 开始训练 {self.episodes} episodes")
        
        # 获取可用场景
        scenes = self.env.get_scene_list()
        print(f"📊 可用场景: {len(scenes)} 个")
        
        if not scenes:
            print("❌ 没有可用场景，请先构建知识图谱")
            return
        
        start_time = time.time()
        
        for episode in range(self.episodes):
            # 随机选择场景
            scene_name = random.choice(scenes)
            
            # 训练KG增强智能体
            kg_result = self.train_single_episode(self.agent, scene_name)
            
            # 训练基线智能体
            baseline_result = self.train_single_episode(self.baseline_agent, scene_name)
            
            # 记录结果
            self.training_results['kg_agent']['rewards'].append(kg_result['total_reward'])
            self.training_results['kg_agent']['success_rates'].append(1 if kg_result['success'] else 0)
            self.training_results['kg_agent']['steps'].append(kg_result['steps'])
            
            self.training_results['baseline_agent']['rewards'].append(baseline_result['total_reward'])
            self.training_results['baseline_agent']['success_rates'].append(1 if baseline_result['success'] else 0)
            self.training_results['baseline_agent']['steps'].append(baseline_result['steps'])
            
            # 定期评估和报告
            if (episode + 1) % self.eval_frequency == 0:
                self._report_progress(episode + 1)
        
        # 最终评估
        print(f"\n🎯 最终评估:")
        self._final_evaluation()
        
        # 保存结果
        self._save_results()
        
        training_time = time.time() - start_time
        print(f"⏱️  总训练时间: {training_time:.2f} 秒")
    
    def _report_progress(self, episode: int):
        """报告训练进度"""
        print(f"\n📊 Episode {episode} 进度报告:")
        
        # 计算最近的性能
        recent_episodes = min(self.eval_frequency, len(self.training_results['kg_agent']['rewards']))
        
        # KG智能体性能
        kg_recent_rewards = self.training_results['kg_agent']['rewards'][-recent_episodes:]
        kg_recent_success = self.training_results['kg_agent']['success_rates'][-recent_episodes:]
        kg_recent_steps = self.training_results['kg_agent']['steps'][-recent_episodes:]
        
        kg_avg_reward = sum(kg_recent_rewards) / len(kg_recent_rewards)
        kg_success_rate = sum(kg_recent_success) / len(kg_recent_success)
        kg_avg_steps = sum(kg_recent_steps) / len(kg_recent_steps)
        
        # 基线智能体性能
        baseline_recent_rewards = self.training_results['baseline_agent']['rewards'][-recent_episodes:]
        baseline_recent_success = self.training_results['baseline_agent']['success_rates'][-recent_episodes:]
        baseline_recent_steps = self.training_results['baseline_agent']['steps'][-recent_episodes:]
        
        baseline_avg_reward = sum(baseline_recent_rewards) / len(baseline_recent_rewards)
        baseline_success_rate = sum(baseline_recent_success) / len(baseline_recent_success)
        baseline_avg_steps = sum(baseline_recent_steps) / len(baseline_recent_steps)
        
        print(f"🧠 KG智能体 - 平均奖励: {kg_avg_reward:.3f}, 成功率: {kg_success_rate:.3f}, 平均步数: {kg_avg_steps:.1f}")
        print(f"📋 基线智能体 - 平均奖励: {baseline_avg_reward:.3f}, 成功率: {baseline_success_rate:.3f}, 平均步数: {baseline_avg_steps:.1f}")
        
        # 性能对比
        reward_improvement = ((kg_avg_reward - baseline_avg_reward) / max(abs(baseline_avg_reward), 0.001)) * 100
        success_improvement = (kg_success_rate - baseline_success_rate) * 100
        
        print(f"📈 KG增强效果 - 奖励提升: {reward_improvement:+.1f}%, 成功率提升: {success_improvement:+.1f}%")
    
    def _final_evaluation(self):
        """最终评估"""
        print("🔍 进行最终详细评估...")
        
        # 详细评估两个智能体
        kg_eval = self.evaluate_agent(self.agent, num_episodes=20)
        baseline_eval = self.evaluate_agent(self.baseline_agent, num_episodes=20)
        
        print(f"\n🧠 KG增强智能体最终性能:")
        print(f"   - 平均奖励: {kg_eval['avg_reward']:.3f}")
        print(f"   - 成功率: {kg_eval['success_rate']:.3f}")
        print(f"   - 平均步数: {kg_eval['avg_steps']:.1f}")
        
        print(f"\n📋 基线智能体最终性能:")
        print(f"   - 平均奖励: {baseline_eval['avg_reward']:.3f}")
        print(f"   - 成功率: {baseline_eval['success_rate']:.3f}")
        print(f"   - 平均步数: {baseline_eval['avg_steps']:.1f}")
        
        # 计算改进
        reward_improvement = ((kg_eval['avg_reward'] - baseline_eval['avg_reward']) / max(abs(baseline_eval['avg_reward']), 0.001)) * 100
        success_improvement = (kg_eval['success_rate'] - baseline_eval['success_rate']) * 100
        step_efficiency = ((baseline_eval['avg_steps'] - kg_eval['avg_steps']) / max(baseline_eval['avg_steps'], 1)) * 100
        
        print(f"\n🎯 KG增强总体效果:")
        print(f"   - 奖励改进: {reward_improvement:+.1f}%")
        print(f"   - 成功率改进: {success_improvement:+.1f}%")
        print(f"   - 步数效率改进: {step_efficiency:+.1f}%")
        
        # 保存评估结果
        self.final_evaluation = {
            'kg_agent': kg_eval,
            'baseline_agent': baseline_eval,
            'improvements': {
                'reward': reward_improvement,
                'success_rate': success_improvement,
                'step_efficiency': step_efficiency
            }
        }
    
    def _save_results(self):
        """保存训练结果"""
        results_dir = Path("results/training")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存训练历史
        training_file = results_dir / f"scene_training_{int(time.time())}.json"
        
        results_data = {
            'config': {
                'episodes': self.episodes,
                'max_steps': self.max_steps,
                'eval_frequency': self.eval_frequency
            },
            'training_results': self.training_results,
            'final_evaluation': getattr(self, 'final_evaluation', {}),
            'agent_stats': {
                'kg_agent': self.agent.get_statistics(),
                'baseline_agent': self.baseline_agent.get_statistics()
            },
            'scenes_used': self.env.get_scene_list()
        }
        
        with open(training_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 训练结果保存到: {training_file}")
        
        # 保存智能体状态
        agent_dir = Path("checkpoints/agents")
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        kg_agent_file = agent_dir / f"kg_agent_{int(time.time())}.json"
        baseline_agent_file = agent_dir / f"baseline_agent_{int(time.time())}.json"
        
        self.agent.save_agent(str(kg_agent_file))
        self.baseline_agent.save_agent(str(baseline_agent_file))
    
    def create_training_report(self) -> str:
        """创建训练报告"""
        if not hasattr(self, 'final_evaluation'):
            return "训练尚未完成，无法生成报告"
        
        report = f"""
# 场景强化学习训练报告

## 训练配置
- 总Episodes: {self.episodes}
- 最大步数/Episode: {self.max_steps}
- 评估频率: {self.eval_frequency}
- 场景数量: {len(self.env.get_scene_list())}

## 最终性能对比

### KG增强智能体
- 平均奖励: {self.final_evaluation['kg_agent']['avg_reward']:.3f}
- 成功率: {self.final_evaluation['kg_agent']['success_rate']:.3f}
- 平均步数: {self.final_evaluation['kg_agent']['avg_steps']:.1f}

### 基线智能体
- 平均奖励: {self.final_evaluation['baseline_agent']['avg_reward']:.3f}
- 成功率: {self.final_evaluation['baseline_agent']['success_rate']:.3f}
- 平均步数: {self.final_evaluation['baseline_agent']['avg_steps']:.1f}

## KG增强效果
- 奖励改进: {self.final_evaluation['improvements']['reward']:+.1f}%
- 成功率改进: {self.final_evaluation['improvements']['success_rate']:+.1f}%
- 步数效率改进: {self.final_evaluation['improvements']['step_efficiency']:+.1f}%

## 结论
{'KG增强显著提升了智能体性能' if self.final_evaluation['improvements']['reward'] > 5 else 'KG增强效果有限，需要进一步优化'}
        """
        
        return report.strip()


def main():
    """主函数"""
    print("🎯 场景强化学习训练")
    
    # 创建训练器
    trainer = SceneBasedTrainer()
    
    # 开始训练
    trainer.train()
    
    # 生成报告
    report = trainer.create_training_report()
    print(f"\n📋 训练报告:\n{report}")
    
    print("\n🎉 训练完成!")


if __name__ == "__main__":
    main()
