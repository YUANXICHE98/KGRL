"""
Week 1 实验：环境搭建与基线确立
运行Baseline Agent (Agent 1)并建立性能基线
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from pathlib import Path
from typing import Dict, Any, List

from src.agents.baseline_agent import BaselineAgent
from src.environments.textworld_env import TextWorldEnvironment
from src.knowledge.kg_builder import KnowledgeGraphBuilder
from src.utils.logger import create_experiment_logger, setup_logging
from config.base_config import config
from config.agent_config import agent_configs
from config.env_config import env_config

class Week1Experiment:
    """Week 1 基线实验"""
    
    def __init__(self):
        self.logger = create_experiment_logger("week1_baseline")
        self.results_dir = config.RESULTS_DIR / "week1"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # 实验配置
        self.num_episodes = 20
        self.max_steps_per_episode = 50
        
        # 初始化组件
        self.agent = None
        self.environment = None
        self.kg_builder = None
        
        self.logger.info("Initialized Week 1 Experiment")
    
    def setup_environment(self):
        """设置实验环境"""
        self.logger.info("Setting up TextWorld environment...")
        
        # 创建TextWorld环境
        env_config_dict = {
            "max_episode_steps": self.max_steps_per_episode,
            "nb_objects": 5,
            "nb_rooms": 3,
            "quest_length": 3,
            "difficulty": "easy"
        }
        
        self.environment = TextWorldEnvironment("week1_env", env_config_dict)
        self.logger.info("TextWorld environment created")
    
    def setup_knowledge_graph(self):
        """设置微型知识图谱"""
        self.logger.info("Building micro knowledge graph...")
        
        self.kg_builder = KnowledgeGraphBuilder("week1_kg")
        
        # 添加基础游戏知识
        basic_facts = [
            # 房间和位置关系
            ("kitchen", "connected_to", "living_room"),
            ("living_room", "connected_to", "bedroom"),
            ("bedroom", "connected_to", "bathroom"),
            
            # 物品和容器关系
            ("fridge", "located_in", "kitchen"),
            ("table", "located_in", "kitchen"),
            ("sofa", "located_in", "living_room"),
            ("bed", "located_in", "bedroom"),
            ("chest", "located_in", "bedroom"),
            
            # 物品属性
            ("fridge", "can_be", "opened"),
            ("chest", "can_be", "opened"),
            ("key", "can_be", "taken"),
            ("apple", "can_be", "taken"),
            ("book", "can_be", "taken"),
            
            # 动作规则
            ("open_container", "requires", "key"),
            ("take_item", "requires", "free_hands"),
            ("go_direction", "changes", "location"),
        ]
        
        for subject, predicate, obj in basic_facts:
            self.kg_builder.add_fact(subject, predicate, obj, source="manual")
        
        # 保存知识图谱
        kg_path = config.KG_DIR / "week1_basic_kg.json"
        self.kg_builder.save_to_file(kg_path)
        
        self.logger.info(f"Built knowledge graph with {len(basic_facts)} facts")
    
    def setup_agent(self):
        """设置Baseline Agent"""
        self.logger.info("Setting up Baseline Agent...")
        
        # 获取Agent配置
        baseline_config = agent_configs.baseline
        agent_config_dict = {
            "model_name": baseline_config.model_name,
            "use_local_model": baseline_config.use_local_model,
            "max_tokens": baseline_config.max_tokens,
            "temperature": baseline_config.temperature,
            "system_prompt": baseline_config.system_prompt,
            "max_retries": baseline_config.max_retries
        }
        
        self.agent = BaselineAgent("baseline_week1", agent_config_dict)
        self.logger.info("Baseline Agent created")
    
    def run_single_episode(self, episode_id: int) -> Dict[str, Any]:
        """运行单个episode"""
        self.logger.info(f"Starting episode {episode_id}")
        
        # 重置环境和Agent
        observation = self.environment.reset()
        self.agent.reset()
        
        episode_data = {
            "episode_id": episode_id,
            "steps": [],
            "total_reward": 0.0,
            "success": False,
            "step_count": 0,
            "start_time": time.time()
        }
        
        for step in range(self.max_steps_per_episode):
            # Agent选择动作
            available_actions = self.environment.get_available_actions()
            action = self.agent.act(observation, available_actions)
            
            # 执行动作
            new_observation, reward, done, info = self.environment.step(action)
            
            # 更新Agent
            self.agent.update(action, new_observation, reward, done, info)
            
            # 记录步骤
            step_data = {
                "step": step + 1,
                "observation": observation,
                "action": action,
                "reward": reward,
                "new_observation": new_observation,
                "done": done,
                "info": info
            }
            episode_data["steps"].append(step_data)
            episode_data["total_reward"] += reward
            episode_data["step_count"] = step + 1
            
            self.logger.debug(f"Step {step + 1}: {action} -> reward: {reward}")
            
            # 更新观测
            observation = new_observation
            
            # 检查是否结束
            if done:
                episode_data["success"] = reward > 0  # 简单的成功判断
                break
        
        episode_data["end_time"] = time.time()
        episode_data["duration"] = episode_data["end_time"] - episode_data["start_time"]
        
        self.logger.info(f"Episode {episode_id} completed: "
                        f"steps={episode_data['step_count']}, "
                        f"reward={episode_data['total_reward']:.2f}, "
                        f"success={episode_data['success']}")
        
        return episode_data
    
    def run_experiment(self) -> Dict[str, Any]:
        """运行完整实验"""
        self.logger.info(f"Starting Week 1 experiment with {self.num_episodes} episodes")
        
        # 设置所有组件
        self.setup_environment()
        self.setup_knowledge_graph()
        self.setup_agent()
        
        # 运行episodes
        all_episodes = []
        successful_episodes = 0
        total_steps = 0
        total_reward = 0.0
        
        for episode_id in range(1, self.num_episodes + 1):
            try:
                episode_data = self.run_single_episode(episode_id)
                all_episodes.append(episode_data)
                
                if episode_data["success"]:
                    successful_episodes += 1
                
                total_steps += episode_data["step_count"]
                total_reward += episode_data["total_reward"]
                
            except Exception as e:
                self.logger.error(f"Error in episode {episode_id}: {e}")
                continue
        
        # 计算统计信息
        experiment_results = {
            "experiment_name": "week1_baseline",
            "agent_type": "BaselineAgent",
            "environment_type": "TextWorld",
            "num_episodes": len(all_episodes),
            "successful_episodes": successful_episodes,
            "success_rate": successful_episodes / len(all_episodes) if all_episodes else 0,
            "average_steps": total_steps / len(all_episodes) if all_episodes else 0,
            "average_reward": total_reward / len(all_episodes) if all_episodes else 0,
            "total_steps": total_steps,
            "total_reward": total_reward,
            "episodes": all_episodes,
            "agent_stats": self.agent.get_stats(),
            "environment_stats": self.environment.get_stats()
        }
        
        # 保存结果
        results_file = self.results_dir / "baseline_results.json"
        with open(results_file, 'w') as f:
            json.dump(experiment_results, f, indent=2, default=str)
        
        self.logger.info("Week 1 experiment completed!")
        self.logger.info(f"Success rate: {experiment_results['success_rate']:.2%}")
        self.logger.info(f"Average steps: {experiment_results['average_steps']:.1f}")
        self.logger.info(f"Average reward: {experiment_results['average_reward']:.2f}")
        self.logger.info(f"Results saved to: {results_file}")
        
        return experiment_results
    
    def cleanup(self):
        """清理资源"""
        if self.environment:
            self.environment.close()
        self.logger.info("Experiment cleanup completed")

def main():
    """主函数"""
    # 设置日志
    setup_logging(log_level="INFO")
    
    # 运行实验
    experiment = Week1Experiment()
    
    try:
        results = experiment.run_experiment()
        print("\n" + "="*50)
        print("WEEK 1 BASELINE EXPERIMENT RESULTS")
        print("="*50)
        print(f"Episodes run: {results['num_episodes']}")
        print(f"Success rate: {results['success_rate']:.2%}")
        print(f"Average steps per episode: {results['average_steps']:.1f}")
        print(f"Average reward per episode: {results['average_reward']:.2f}")
        print("="*50)
        
    except KeyboardInterrupt:
        print("\nExperiment interrupted by user")
    except Exception as e:
        print(f"Experiment failed: {e}")
    finally:
        experiment.cleanup()

if __name__ == "__main__":
    main()
