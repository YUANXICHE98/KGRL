"""
环境配置文件
包含TextWorld和ALFWorld环境的配置参数
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path

@dataclass
class TextWorldConfig:
    """TextWorld环境配置"""
    
    # 基础配置
    env_name: str = "textworld"
    max_episode_steps: int = 100
    
    # 游戏生成配置
    nb_objects: int = 10
    nb_rooms: int = 5
    quest_length: int = 5
    quest_breadth: int = 2
    
    # 任务类型配置
    task_types: List[str] = None
    
    def __post_init__(self):
        if self.task_types is None:
            self.task_types = [
                "treasure_hunter",  # 寻宝任务
                "cooking",         # 烹饪任务
                "cleaning",        # 清洁任务
            ]
    
    # 难度配置
    difficulty_levels: Dict[str, Dict[str, int]] = None
    
    def __post_init__(self):
        if self.difficulty_levels is None:
            self.difficulty_levels = {
                "easy": {
                    "nb_objects": 5,
                    "nb_rooms": 3,
                    "quest_length": 3
                },
                "medium": {
                    "nb_objects": 10,
                    "nb_rooms": 5,
                    "quest_length": 5
                },
                "hard": {
                    "nb_objects": 15,
                    "nb_rooms": 8,
                    "quest_length": 8
                }
            }
    
    # 观测配置
    include_description: bool = True
    include_inventory: bool = True
    include_objective: bool = True
    include_command_templates: bool = False
    
    # 动作空间配置
    admissible_commands: bool = True
    max_admissible_commands: int = 20

@dataclass
class ALFWorldConfig:
    """ALFWorld环境配置"""
    
    # 基础配置
    env_name: str = "alfworld"
    max_episode_steps: int = 50
    
    # 数据集配置
    split: str = "train"  # train, valid_seen, valid_unseen
    data_path: Optional[Path] = None
    
    # 任务类型
    task_types: List[str] = None
    
    def __post_init__(self):
        if self.task_types is None:
            self.task_types = [
                "pick_and_place_simple",
                "pick_and_place_with_movable_recep",
                "pick_clean_then_place_in_recep",
                "pick_heat_then_place_in_recep",
                "pick_cool_then_place_in_recep",
                "look_at_obj_in_light",
                "pick_two_obj_and_place"
            ]
    
    # 观测配置
    observation_type: str = "text"  # text, image, both
    include_goal: bool = True
    include_admissible_commands: bool = True
    
    # 评估配置
    num_eval_games: int = 134  # ALFWorld验证集大小

@dataclass
class EnvironmentConfig:
    """环境配置集合"""
    
    # 环境选择
    primary_env: str = "textworld"  # textworld, alfworld
    
    # 具体环境配置
    textworld: TextWorldConfig = TextWorldConfig()
    alfworld: ALFWorldConfig = ALFWorldConfig()
    
    # 通用配置
    random_seed: int = 42
    render_mode: Optional[str] = None  # human, rgb_array, None
    
    # 评估配置
    eval_episodes: int = 50
    eval_max_steps: int = 100
    eval_timeout: float = 300.0  # 5分钟超时
    
    # 数据收集配置
    collect_trajectories: bool = True
    save_trajectories: bool = True
    trajectory_format: str = "json"  # json, pickle
    
    def get_env_config(self, env_name: str = None):
        """获取指定环境的配置"""
        env_name = env_name or self.primary_env
        
        if env_name.lower() == "textworld":
            return self.textworld
        elif env_name.lower() == "alfworld":
            return self.alfworld
        else:
            raise ValueError(f"Unknown environment: {env_name}")
    
    def get_task_config(self, task_name: str, env_name: str = None) -> Dict[str, Any]:
        """获取特定任务的配置"""
        env_config = self.get_env_config(env_name)
        
        if hasattr(env_config, 'difficulty_levels') and task_name in env_config.difficulty_levels:
            return env_config.difficulty_levels[task_name]
        
        return {}

# 全局环境配置实例
env_config = EnvironmentConfig()
