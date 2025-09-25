#!/usr/bin/env python3
"""
Real Baseline Experiment - NO SIMULATION ALLOWED
Uses real LLM calls and real KG data only
"""

import json
import time
import random
from pathlib import Path
from typing import Dict, Any, List
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.environments.scene_based_env import SceneBasedEnvironment
from src.utils.llm_client import LLMBaselineAgent
from src.agents.baseline_agents import ReActAgent, RAGAgent
from experiments.utils.visualization import ExperimentVisualizer


class RealBaselineExperiment:
    """Real baseline experiment with no simulation"""
    
    def __init__(self, api_key: str, num_episodes: int = 15, max_steps: int = 12):
        self.api_key = api_key
        self.num_episodes = num_episodes
        self.max_steps = max_steps
        
        # Initialize environment
        self.env = SceneBasedEnvironment()
        
        # Initialize three real agents - NO SIMULATION
        self.agents = {
            'llm_baseline': LLMBaselineAgent(api_key),
            'react': ReActAgent(),
            'rag': RAGAgent()
        }
        
        # Results storage
        self.results = {agent_name: {
            'rewards': [],
            'success_rates': [],
            'steps': [],
            'episode_details': []
        } for agent_name in self.agents.keys()}
        
        # Experiment configuration
        self.experiment_config = {
            'num_episodes': num_episodes,
            'max_steps': max_steps,
            'agents': list(self.agents.keys()),
            'timestamp': int(time.time()),
            'api_key_provided': bool(api_key),
            'experiment_type': 'real_baseline_no_simulation'
        }
        
        print(f"🧪 Real Baseline Experiment (NO SIMULATION)")
        print(f"📊 Episodes: {num_episodes}, Max Steps: {max_steps}")
        print(f"🤖 Agents: {', '.join(self.agents.keys())}")
    
    def run_single_episode(self, agent_name: str, agent, scene_name: str = None) -> Dict[str, Any]:
        """Run single episode with real interactions only"""
        print(f"  🎮 Running {agent_name} in scene {scene_name}")
        
        # Reset environment with real KG data
        obs = self.env.reset(scene_name)
        agent.reset(obs)
        
        total_reward = 0
        steps = 0
        done = False
        episode_log = []
        
        print(f"    🔍 Initial observation: {obs.get('visible_entities', [])} entities")
        
        while not done and steps < self.max_steps:
            # Agent selects action - REAL DECISION MAKING ONLY
            try:
                action, target = agent.select_action(obs)
                print(f"    Step {steps+1}: {action} {target or ''}")
            except Exception as e:
                print(f"    ❌ Agent action selection failed: {e}")
                action, target = "wait", None
            
            # Execute action in real environment
            try:
                next_obs, reward, done, info = self.env.step(action, target)
                print(f"    💰 Reward: {reward:.2f}")
            except Exception as e:
                print(f"    ❌ Environment step failed: {e}")
                reward = -0.1
                done = True
                next_obs = obs
                info = {}
            
            # Log step
            step_log = {
                'step': steps,
                'action': action,
                'target': target,
                'reward': reward,
                'done': done,
                'visible_entities': obs.get('visible_entities', []),
                'available_actions': obs.get('available_actions', [])
            }
            episode_log.append(step_log)
            
            # Agent learning/update - REAL LEARNING ONLY
            try:
                agent.update(obs, action, target, reward, next_obs, done)
            except Exception as e:
                print(f"    ⚠️ Agent update failed: {e}")
            
            # Update state
            obs = next_obs
            total_reward += reward
            steps += 1
            
            # Success condition
            if reward > 3:  # Task success
                done = True
                break
        
        # Determine success
        success = info.get('task_completed', False) or total_reward > 2
        
        result = {
            'agent': agent_name,
            'scene': scene_name,
            'total_reward': total_reward,
            'steps': steps,
            'success': success,
            'episode_log': episode_log,
            'final_info': info
        }
        
        print(f"    ✅ Result: Reward={total_reward:.2f}, Steps={steps}, Success={success}")
        return result
    
    def run_experiment(self):
        """Run complete real experiment"""
        print(f"🚀 Starting Real Baseline Experiment")
        
        # Get available scenes from real KG data
        scenes = self.env.get_scene_list()
        if not scenes:
            print("❌ No scenes available, please build knowledge graphs first")
            return
        
        print(f"📊 Available scenes: {len(scenes)}")
        
        # Use all available scenes for comprehensive testing
        selected_scenes = scenes[:5] if len(scenes) > 5 else scenes
        print(f"🎯 Selected scenes: {selected_scenes}")
        
        start_time = time.time()
        
        for episode in range(self.num_episodes):
            # Select scene for this episode
            scene_name = random.choice(selected_scenes)
            
            print(f"\n🎮 Episode {episode + 1}/{self.num_episodes} - Scene: {scene_name}")
            
            # Run each agent on the same scene
            for agent_name, agent in self.agents.items():
                try:
                    result = self.run_single_episode(agent_name, agent, scene_name)
                    
                    # Store results
                    self.results[agent_name]['rewards'].append(result['total_reward'])
                    self.results[agent_name]['success_rates'].append(1 if result['success'] else 0)
                    self.results[agent_name]['steps'].append(result['steps'])
                    self.results[agent_name]['episode_details'].append(result)
                    
                except Exception as e:
                    print(f"  ❌ {agent_name} failed: {e}")
                    # Record failure
                    self.results[agent_name]['rewards'].append(-5)
                    self.results[agent_name]['success_rates'].append(0)
                    self.results[agent_name]['steps'].append(self.max_steps)
            
            # Progress report
            if (episode + 1) % 5 == 0:
                self._report_progress(episode + 1)
        
        # Final analysis
        self._final_analysis()
        
        # Save results
        results_file = self._save_results()
        
        # Generate visualizations
        self._generate_visualizations(results_file)
        
        total_time = time.time() - start_time
        print(f"⏱️ Total experiment time: {total_time:.2f} seconds")
        
        return results_file
    
    def _report_progress(self, episode: int):
        """Report progress"""
        print(f"\n📊 Episode {episode} Progress Report:")
        
        for agent_name in self.agents.keys():
            rewards = self.results[agent_name]['rewards']
            success_rates = self.results[agent_name]['success_rates']
            
            if rewards:
                avg_reward = sum(rewards) / len(rewards)
                success_rate = sum(success_rates) / len(success_rates)
                
                print(f"  {agent_name}: Avg Reward={avg_reward:.3f}, Success Rate={success_rate:.3f}")
    
    def _final_analysis(self):
        """Final analysis"""
        print(f"\n🎯 Final Analysis:")
        
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
                    'reward_std': self._calculate_std(rewards)
                }
        
        # Display results
        print(f"\n📈 Performance Comparison:")
        for agent_name, stats in analysis.items():
            print(f"\n🤖 {agent_name.upper()}:")
            print(f"  - Average Reward: {stats['avg_reward']:.3f} ± {stats['reward_std']:.3f}")
            print(f"  - Success Rate: {stats['success_rate']:.3f}")
            print(f"  - Average Steps: {stats['avg_steps']:.1f}")
            print(f"  - Best Reward: {stats['best_reward']:.3f}")
        
        # Rankings
        reward_ranking = sorted(analysis.items(), key=lambda x: x[1]['avg_reward'], reverse=True)
        success_ranking = sorted(analysis.items(), key=lambda x: x[1]['success_rate'], reverse=True)
        
        print(f"\n🏆 Performance Rankings:")
        reward_str = ' > '.join([f'{name}({stats["avg_reward"]:.3f})' for name, stats in reward_ranking])
        success_str = ' > '.join([f'{name}({stats["success_rate"]:.3f})' for name, stats in success_ranking])
        print(f"📊 By Average Reward: {reward_str}")
        print(f"🎯 By Success Rate: {success_str}")
        
        self.final_analysis = analysis
    
    def _calculate_std(self, values):
        """Calculate standard deviation"""
        if len(values) <= 1:
            return 0
        mean = sum(values) / len(values)
        return (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5
    
    def _save_results(self) -> str:
        """Save experiment results with standardized naming"""
        results_dir = Path("experiments/results/baseline_comparison")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = int(time.time())
        
        # Save detailed results
        detailed_results = {
            'experiment_config': self.experiment_config,
            'results': self.results,
            'final_analysis': getattr(self, 'final_analysis', {}),
            'agent_statistics': {name: agent.get_statistics() for name, agent in self.agents.items()},
            'timestamp': timestamp,
            'experiment_type': 'real_baseline_no_simulation'
        }
        
        results_file = results_dir / f"real_baseline_experiment_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {results_file}")
        return str(results_file)
    
    def _generate_visualizations(self, results_file: str):
        """Generate visualizations with standardized naming"""
        print("📊 Generating experiment visualizations...")
        
        try:
            visualizer = ExperimentVisualizer()
            visualizer.generate_experiment_report(results_file)
        except Exception as e:
            print(f"⚠️ Visualization generation failed: {e}")


def main():
    """Main function"""
    print("🎯 Real Baseline Experiment - NO SIMULATION")
    
    # LLM API configuration
    api_key = "sk-rvwMvUNbWBz9L76KB05650C7Cc464324BdC98dB3FbD4296a"
    
    # Create experiment
    experiment = RealBaselineExperiment(
        api_key=api_key,
        num_episodes=12,  # Reasonable number for thorough testing
        max_steps=15      # Allow more steps for complex interactions
    )
    
    # Run experiment
    results_file = experiment.run_experiment()
    
    print(f"\n🎉 Real Experiment Complete! Results: {results_file}")


if __name__ == "__main__":
    main()
