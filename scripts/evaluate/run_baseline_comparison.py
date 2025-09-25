#!/usr/bin/env python3
"""
基线对比实验脚本
运行LLM基线、ReAct、RAG三条线的对比实验
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
from src.agents.baseline_agents import LLMBaselineAgent, ReActAgent, RAGAgent
from src.knowledge.scene_kg_builder import SceneKGBuilder


class BaselineComparison:
    """基线对比实验"""
    
    def __init__(self, num_episodes: int = 50, max_steps: int = 30):
        self.num_episodes = num_episodes
        self.max_steps = max_steps
        
        # 初始化环境
        self.env = SceneBasedEnvironment()
        
        # 初始化三个智能体
        self.agents = {
            'llm_baseline': LLMBaselineAgent(),
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
        
        print(f"🏁 初始化基线对比实验 (episodes: {num_episodes}, max_steps: {max_steps})")
    
    def run_single_episode(self, agent_name: str, agent, scene_name: str = None) -> Dict[str, Any]:
        """运行单个episode"""
        # 重置环境
        obs = self.env.reset(scene_name)
        agent.reset(obs)
        
        total_reward = 0
        steps = 0
        done = False
        episode_log = []
        
        while not done and steps < self.max_steps:
            # 智能体选择动作
            action, target = agent.select_action(obs)
            
            # 执行动作
            next_obs, reward, done, info = self.env.step(action, target)
            
            # 记录步骤
            step_log = {
                'step': steps,
                'action': action,
                'target': target,
                'reward': reward,
                'observation': obs['description'],
                'next_observation': next_obs['description']
            }
            episode_log.append(step_log)
            
            # 智能体学习/更新
            agent.update(obs, action, target, reward, next_obs, done)
            
            # 更新状态
            obs = next_obs
            total_reward += reward
            steps += 1
        
        # 判断成功
        success = info.get('task_completed', False) or total_reward > 3
        
        return {
            'agent': agent_name,
            'scene': obs['scene'],
            'total_reward': total_reward,
            'steps': steps,
            'success': success,
            'episode_log': episode_log,
            'final_info': info
        }
    
    def run_comparison(self):
        """运行完整对比实验"""
        print(f"🚀 开始基线对比实验")
        
        # 获取可用场景
        scenes = self.env.get_scene_list()
        if not scenes:
            print("❌ 没有可用场景，请先构建知识图谱")
            return
        
        print(f"📊 可用场景: {len(scenes)} 个")
        
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
                    
                    # 显示结果
                    success_icon = "✅" if result['success'] else "❌"
                    print(f"  {success_icon} {agent_name}: 奖励={result['total_reward']:.2f}, 步数={result['steps']}")
                    
                except Exception as e:
                    print(f"  ❌ {agent_name} 执行失败: {e}")
                    # 记录失败结果
                    self.results[agent_name]['rewards'].append(-10)
                    self.results[agent_name]['success_rates'].append(0)
                    self.results[agent_name]['steps'].append(self.max_steps)
            
            # 定期报告进度
            if (episode + 1) % 10 == 0:
                self._report_progress(episode + 1)
        
        # 最终分析
        self._final_analysis()
        
        # 保存结果
        self._save_results()
        
        total_time = time.time() - start_time
        print(f"⏱️  总实验时间: {total_time:.2f} 秒")
    
    def _report_progress(self, episode: int):
        """报告进度"""
        print(f"\n📊 Episode {episode} 进度报告:")
        
        for agent_name in self.agents.keys():
            rewards = self.results[agent_name]['rewards']
            success_rates = self.results[agent_name]['success_rates']
            steps = self.results[agent_name]['steps']
            
            if rewards:
                avg_reward = sum(rewards) / len(rewards)
                success_rate = sum(success_rates) / len(success_rates)
                avg_steps = sum(steps) / len(steps)
                
                print(f"  {agent_name}: 平均奖励={avg_reward:.3f}, 成功率={success_rate:.3f}, 平均步数={avg_steps:.1f}")
    
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
                    'worst_reward': min(rewards)
                }
        
        # 显示结果
        print(f"\n📈 性能对比:")
        for agent_name, stats in analysis.items():
            print(f"\n🤖 {agent_name.upper()}:")
            print(f"  - 平均奖励: {stats['avg_reward']:.3f}")
            print(f"  - 成功率: {stats['success_rate']:.3f}")
            print(f"  - 平均步数: {stats['avg_steps']:.1f}")
            print(f"  - 最佳奖励: {stats['best_reward']:.3f}")
            print(f"  - 最差奖励: {stats['worst_reward']:.3f}")
        
        # 排名
        print(f"\n🏆 性能排名:")
        
        # 按平均奖励排名
        reward_ranking = sorted(analysis.items(), key=lambda x: x[1]['avg_reward'], reverse=True)
        print(f"📊 按平均奖励排名:")
        for i, (agent_name, stats) in enumerate(reward_ranking):
            print(f"  {i+1}. {agent_name}: {stats['avg_reward']:.3f}")
        
        # 按成功率排名
        success_ranking = sorted(analysis.items(), key=lambda x: x[1]['success_rate'], reverse=True)
        print(f"🎯 按成功率排名:")
        for i, (agent_name, stats) in enumerate(success_ranking):
            print(f"  {i+1}. {agent_name}: {stats['success_rate']:.3f}")
        
        # 按效率排名（步数越少越好）
        efficiency_ranking = sorted(analysis.items(), key=lambda x: x[1]['avg_steps'])
        print(f"⚡ 按效率排名:")
        for i, (agent_name, stats) in enumerate(efficiency_ranking):
            print(f"  {i+1}. {agent_name}: {stats['avg_steps']:.1f} 步")
        
        self.final_analysis = analysis
        self.rankings = {
            'reward': reward_ranking,
            'success': success_ranking,
            'efficiency': efficiency_ranking
        }
    
    def _save_results(self):
        """保存实验结果"""
        results_dir = Path("experiments/results/baseline_comparison")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = int(time.time())
        
        # 保存详细结果
        detailed_results = {
            'experiment_config': {
                'num_episodes': self.num_episodes,
                'max_steps': self.max_steps,
                'agents': list(self.agents.keys()),
                'timestamp': timestamp
            },
            'results': self.results,
            'final_analysis': getattr(self, 'final_analysis', {}),
            'rankings': getattr(self, 'rankings', {}),
            'agent_statistics': {name: agent.get_statistics() for name, agent in self.agents.items()}
        }
        
        results_file = results_dir / f"baseline_comparison_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 详细结果保存到: {results_file}")
        
        # 保存简化报告
        report = self._generate_report()
        report_file = results_dir / f"comparison_report_{timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📋 实验报告保存到: {report_file}")
    
    def _generate_report(self) -> str:
        """生成实验报告"""
        if not hasattr(self, 'final_analysis'):
            return "实验尚未完成"
        
        report = f"""# 基线智能体对比实验报告

## 实验配置
- 总Episodes: {self.num_episodes}
- 最大步数/Episode: {self.max_steps}
- 智能体类型: {', '.join(self.agents.keys())}
- 场景数量: {len(self.env.get_scene_list())}

## 性能对比

"""
        
        for agent_name, stats in self.final_analysis.items():
            report += f"""### {agent_name.upper()}
- 平均奖励: {stats['avg_reward']:.3f}
- 成功率: {stats['success_rate']:.3f}
- 平均步数: {stats['avg_steps']:.1f}
- 最佳奖励: {stats['best_reward']:.3f}

"""
        
        report += f"""## 排名结果

### 按平均奖励排名
"""
        for i, (agent_name, stats) in enumerate(self.rankings['reward']):
            report += f"{i+1}. **{agent_name}**: {stats['avg_reward']:.3f}\n"
        
        report += f"""
### 按成功率排名
"""
        for i, (agent_name, stats) in enumerate(self.rankings['success']):
            report += f"{i+1}. **{agent_name}**: {stats['success_rate']:.3f}\n"
        
        report += f"""
### 按效率排名
"""
        for i, (agent_name, stats) in enumerate(self.rankings['efficiency']):
            report += f"{i+1}. **{agent_name}**: {stats['avg_steps']:.1f} 步\n"
        
        # 分析结论
        best_reward_agent = self.rankings['reward'][0][0]
        best_success_agent = self.rankings['success'][0][0]
        best_efficiency_agent = self.rankings['efficiency'][0][0]
        
        report += f"""
## 结论

- **最佳奖励**: {best_reward_agent}
- **最高成功率**: {best_success_agent}  
- **最高效率**: {best_efficiency_agent}

"""
        
        if best_reward_agent == best_success_agent == best_efficiency_agent:
            report += f"🏆 **{best_reward_agent}** 在所有指标上都表现最佳！"
        else:
            report += "各智能体在不同指标上有不同优势，需要根据具体任务需求选择。"
        
        return report


def main():
    """主函数"""
    print("🎯 基线智能体对比实验")
    
    # 首先构建增强的场景KG
    print("🏗️ 构建增强场景KG...")
    kg_builder = SceneKGBuilder()
    scene_kgs = kg_builder.build_all_scene_kgs(max_scenes=10)
    
    if scene_kgs:
        # 保存增强的场景KG
        output_dir = Path("data/knowledge_graphs/enhanced_scenes")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for scene_name, scene_kg in scene_kgs.items():
            json_file = output_dir / f"{scene_name}_enhanced_kg.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(scene_kg, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 保存了 {len(scene_kgs)} 个增强场景KG")
    
    # 运行对比实验
    comparison = BaselineComparison(num_episodes=30, max_steps=25)
    comparison.run_comparison()
    
    print("\n🎉 基线对比实验完成!")


if __name__ == "__main__":
    main()
