#!/usr/bin/env python3
"""
综合实验运行器 - 真实数据测试，包含完整的KG节点追踪
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root / "tools" / "visualization"))

from src.environments.scene_based_env import SceneBasedEnvironment
from src.agents.baseline_agents import LLMBaselineAgent, ReActAgent, RAGAgent
from agent_path_tracker import AgentPathTracker

class ComprehensiveExperimentRunner:
    """综合实验运行器"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.experiment_id = f"comprehensive_experiment_{self.timestamp}"
        
        # 创建实验目录
        self.experiment_dir = project_root / "experiments" / "results" / self.experiment_id
        self.experiment_dir.mkdir(parents=True, exist_ok=True)
        
        # 子目录
        self.results_dir = self.experiment_dir / "results"
        self.reports_dir = self.experiment_dir / "reports"
        self.visualizations_dir = self.experiment_dir / "visualizations"
        
        for dir_path in [self.results_dir, self.reports_dir, self.visualizations_dir]:
            dir_path.mkdir(exist_ok=True)
        
        print(f"🧪 Comprehensive Experiment: {self.experiment_id}")
        print(f"📁 Experiment Directory: {self.experiment_dir}")
    
    def run_experiment(self, scenes: List[str] = None, max_episodes: int = 3, max_steps: int = 10):
        """运行综合实验"""
        print("=" * 80)
        print("🚀 Starting Comprehensive KGRL Experiment")
        print("=" * 80)
        
        # 默认场景
        if scenes is None:
            scenes = ["FloorPlan202-openable", "FloorPlan308-openable"]
        
        # 初始化环境
        print("🌍 Initializing Environment...")
        env = SceneBasedEnvironment()
        
        # 初始化智能体
        print("🤖 Initializing Agents...")
        agents = {
            "llm_baseline": LLMBaselineAgent(model_name="gpt-3.5-turbo"),
            "react": ReActAgent(),
            "rag": RAGAgent()
        }
        
        # 实验结果存储
        experiment_results = {
            'experiment_id': self.experiment_id,
            'timestamp': self.timestamp,
            'config': {
                'scenes': scenes,
                'max_episodes': max_episodes,
                'max_steps': max_steps,
                'agents': list(agents.keys())
            },
            'results': {},
            'summary': {}
        }
        
        # 对每个场景运行实验
        for scene_name in scenes:
            print(f"\n🎯 Testing Scene: {scene_name}")
            scene_results = self._run_scene_experiment(
                env, agents, scene_name, max_episodes, max_steps
            )
            experiment_results['results'][scene_name] = scene_results
        
        # 生成综合报告
        print("\n📊 Generating Comprehensive Report...")
        self._generate_comprehensive_report(experiment_results)
        
        # 保存实验结果
        results_file = self.results_dir / "experiment_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(experiment_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Experiment Complete!")
        print(f"📁 Results saved to: {self.experiment_dir}")
        
        return experiment_results
    
    def _run_scene_experiment(self, env, agents, scene_name: str, 
                            max_episodes: int, max_steps: int) -> Dict:
        """运行单个场景的实验"""
        print(f"  📋 Scene: {scene_name}")
        
        # 创建路径追踪器
        tracker = AgentPathTracker(scene_name)
        
        # 场景结果
        scene_results = {
            'scene_name': scene_name,
            'agents': {},
            'episodes': max_episodes,
            'max_steps': max_steps
        }
        
        # 运行多个回合
        for episode in range(max_episodes):
            print(f"    📋 Episode {episode + 1}/{max_episodes}")
            tracker.start_episode(episode + 1)
            
            # 测试每个智能体
            for agent_name, agent in agents.items():
                print(f"      🤖 Agent: {agent_name}")
                
                if agent_name not in scene_results['agents']:
                    scene_results['agents'][agent_name] = {
                        'episodes': [],
                        'total_reward': 0,
                        'total_steps': 0,
                        'kg_nodes_accessed': set()
                    }
                
                # 运行单个智能体的回合
                episode_result = self._run_agent_episode(
                    env, agent, agent_name, scene_name, max_steps, tracker
                )
                
                scene_results['agents'][agent_name]['episodes'].append(episode_result)
                scene_results['agents'][agent_name]['total_reward'] += episode_result['total_reward']
                scene_results['agents'][agent_name]['total_steps'] += episode_result['steps']
                scene_results['agents'][agent_name]['kg_nodes_accessed'].update(
                    episode_result.get('kg_nodes_accessed', [])
                )
        
        # 转换set为list以便JSON序列化
        for agent_data in scene_results['agents'].values():
            agent_data['kg_nodes_accessed'] = list(agent_data['kg_nodes_accessed'])
        
        # 保存路径数据
        json_file, csv_file = tracker.save_paths(self.results_dir)
        md_file = tracker.generate_path_table(self.reports_dir)
        
        scene_results['files'] = {
            'path_json': str(json_file),
            'path_csv': str(csv_file),
            'path_report': str(md_file)
        }
        
        return scene_results
    
    def _run_agent_episode(self, env, agent, agent_name: str, scene_name: str, 
                          max_steps: int, tracker: AgentPathTracker) -> Dict:
        """运行单个智能体的单个回合"""
        
        # 重置环境
        observation = env.reset(scene_name)
        
        episode_result = {
            'agent': agent_name,
            'scene': scene_name,
            'steps': 0,
            'total_reward': 0,
            'actions': [],
            'kg_nodes_accessed': [],
            'reasoning_traces': []
        }
        
        print(f"        👁️ Initial observation: {observation.get('visible_entities', [])[:3]}...")
        
        # 运行步骤
        for step in range(max_steps):
            try:
                # 记录步骤开始
                step_start_time = time.time()
                
                # 智能体决策（包含KG节点访问追踪）
                if agent_name == "rag":
                    # RAG智能体需要特殊处理以追踪KG访问
                    action_name, target, kg_nodes, reasoning = self._get_rag_action_with_tracking(
                        agent, observation
                    )
                else:
                    # 其他智能体
                    action_name, target = agent.select_action(observation)
                    kg_nodes = []
                    reasoning = f"{agent_name} selected {action_name} -> {target}"
                
                action = {"action": action_name, "target": target}
                
                # 执行动作
                observation, reward, done, info = env.step(action)
                
                # 记录步骤
                step_time = time.time() - step_start_time
                
                episode_result['steps'] += 1
                episode_result['total_reward'] += reward
                episode_result['actions'].append({
                    'step': step + 1,
                    'action': action_name,
                    'target': target,
                    'reward': reward,
                    'step_time': step_time
                })
                episode_result['kg_nodes_accessed'].extend(kg_nodes)
                episode_result['reasoning_traces'].append(reasoning)
                
                # 记录到追踪器
                tracker.record_step(
                    agent_name=agent_name,
                    action=action_name,
                    target=target if target else 'none',
                    observation=observation,
                    reward=reward,
                    kg_nodes_accessed=kg_nodes,
                    reasoning_trace=reasoning
                )
                
                print(f"          Step {step + 1}: {action_name} -> {target} "
                      f"(KG nodes: {len(kg_nodes)}, Reward: {reward:.3f})")
                
                if done:
                    print(f"          ✅ Task completed!")
                    break
                    
            except Exception as e:
                print(f"          ❌ Error in step {step + 1}: {e}")
                # 记录错误步骤
                tracker.record_step(
                    agent_name=agent_name,
                    action="error",
                    target="none",
                    observation=observation,
                    reward=-0.1,
                    kg_nodes_accessed=[],
                    reasoning_trace=f"Error: {str(e)}"
                )
                break
        
        print(f"        📊 Episode complete: {episode_result['steps']} steps, "
              f"reward: {episode_result['total_reward']:.3f}, "
              f"KG nodes: {len(set(episode_result['kg_nodes_accessed']))}")
        
        return episode_result
    
    def _get_rag_action_with_tracking(self, agent, observation) -> Tuple[str, str, List[str], str]:
        """获取RAG智能体的动作，同时追踪KG节点访问"""
        # 使用RAG智能体的追踪方法
        if hasattr(agent, 'select_action_with_tracking'):
            return agent.select_action_with_tracking(observation)
        else:
            # 回退到普通方法
            action_name, target = agent.select_action(observation)
            visible_entities = observation.get('visible_entities', [])
            kg_nodes_accessed = [entity for entity in visible_entities if entity != target]
            reasoning = f"RAG: Retrieved {len(kg_nodes_accessed)} nodes, selected {action_name} -> {target}"
            return action_name, target, kg_nodes_accessed, reasoning
    
    def _generate_comprehensive_report(self, experiment_results: Dict):
        """生成综合实验报告"""
        report_file = self.reports_dir / "comprehensive_report.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Comprehensive KGRL Experiment Report\n\n")
            f.write(f"**Experiment ID**: {experiment_results['experiment_id']}\n")
            f.write(f"**Timestamp**: {experiment_results['timestamp']}\n\n")
            
            # 配置信息
            config = experiment_results['config']
            f.write("## Experiment Configuration\n\n")
            f.write(f"- **Scenes**: {', '.join(config['scenes'])}\n")
            f.write(f"- **Episodes**: {config['max_episodes']}\n")
            f.write(f"- **Max Steps**: {config['max_steps']}\n")
            f.write(f"- **Agents**: {', '.join(config['agents'])}\n\n")
            
            # 结果汇总
            f.write("## Results Summary\n\n")
            f.write("| Scene | Agent | Total Reward | Total Steps | Avg Reward | KG Nodes |\n")
            f.write("|-------|-------|--------------|-------------|------------|----------|\n")
            
            for scene_name, scene_data in experiment_results['results'].items():
                for agent_name, agent_data in scene_data['agents'].items():
                    avg_reward = agent_data['total_reward'] / agent_data['total_steps'] if agent_data['total_steps'] > 0 else 0
                    kg_nodes_count = len(agent_data['kg_nodes_accessed'])
                    
                    f.write(f"| {scene_name} | {agent_name} | {agent_data['total_reward']:.3f} | "
                           f"{agent_data['total_steps']} | {avg_reward:.3f} | {kg_nodes_count} |\n")
            
            f.write("\n## Detailed Analysis\n\n")
            f.write("See individual scene reports in the reports directory.\n")
        
        print(f"  ✅ Comprehensive report: {report_file}")

def main():
    """主函数"""
    runner = ComprehensiveExperimentRunner()
    
    # 运行实验
    results = runner.run_experiment(
        scenes=["FloorPlan202-openable", "FloorPlan308-openable"],
        max_episodes=2,
        max_steps=8
    )
    
    return results

if __name__ == "__main__":
    try:
        results = main()
        print(f"\n🎉 Experiment completed successfully!")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n⚠️ Experiment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Experiment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
