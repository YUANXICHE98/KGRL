"""
环境基类
定义所有环境的通用接口和基础功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass

@dataclass
class EnvironmentState:
    """环境状态类"""
    current_observation: str = ""
    available_actions: List[str] = None
    episode_step: int = 0
    is_done: bool = False
    episode_reward: float = 0.0
    info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.available_actions is None:
            self.available_actions = []
        if self.info is None:
            self.info = {}
    
    def reset(self):
        """重置环境状态"""
        self.current_observation = ""
        self.available_actions = []
        self.episode_step = 0
        self.is_done = False
        self.episode_reward = 0.0
        self.info = {}

class BaseEnvironment(ABC):
    """环境基类，定义所有环境的通用接口"""
    
    def __init__(self, env_id: str, config: Dict[str, Any] = None):
        """
        初始化环境
        
        Args:
            env_id: 环境唯一标识符
            config: 环境配置参数
        """
        self.env_id = env_id
        self.config = config or {}
        self.state = EnvironmentState()
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{env_id}")
        
        # 环境统计
        self.stats = {
            "total_episodes": 0,
            "total_steps": 0,
            "successful_episodes": 0,
            "average_episode_length": 0.0,
            "success_rate": 0.0
        }
        
        # 环境参数
        self.max_episode_steps = self.config.get("max_episode_steps", 100)
        self.random_seed = self.config.get("random_seed", 42)
    
    @abstractmethod
    def reset(self) -> str:
        """
        重置环境到初始状态
        
        Returns:
            初始观测
        """
        pass
    
    @abstractmethod
    def step(self, action: str) -> Tuple[str, float, bool, Dict[str, Any]]:
        """
        执行动作并返回结果
        
        Args:
            action: 要执行的动作
            
        Returns:
            observation: 新的观测
            reward: 获得的奖励
            done: 是否结束
            info: 额外信息
        """
        pass
    
    @abstractmethod
    def get_available_actions(self) -> List[str]:
        """
        获取当前可用的动作列表
        
        Returns:
            可用动作列表
        """
        pass
    
    def get_observation(self) -> str:
        """获取当前观测"""
        return self.state.current_observation
    
    def is_done(self) -> bool:
        """检查是否结束"""
        return self.state.is_done
    
    def get_episode_step(self) -> int:
        """获取当前episode步数"""
        return self.state.episode_step
    
    def get_episode_reward(self) -> float:
        """获取当前episode总奖励"""
        return self.state.episode_reward
    
    def get_info(self) -> Dict[str, Any]:
        """获取额外信息"""
        return self.state.info.copy()
    
    def seed(self, seed: int):
        """设置随机种子"""
        self.random_seed = seed
        self.logger.info(f"Set random seed to {seed}")
    
    def close(self):
        """关闭环境"""
        self.logger.info(f"Environment {self.env_id} closed")
    
    def render(self, mode: str = "human"):
        """渲染环境（可选实现）"""
        if mode == "human":
            print(f"Current observation: {self.state.current_observation}")
            print(f"Available actions: {self.state.available_actions}")
            print(f"Episode step: {self.state.episode_step}")
            print(f"Episode reward: {self.state.episode_reward}")
    
    def _update_episode_stats(self, success: bool):
        """更新episode统计信息"""
        self.stats["total_episodes"] += 1
        self.stats["total_steps"] += self.state.episode_step
        
        if success:
            self.stats["successful_episodes"] += 1
        
        # 更新平均值
        self.stats["average_episode_length"] = self.stats["total_steps"] / self.stats["total_episodes"]
        self.stats["success_rate"] = self.stats["successful_episodes"] / self.stats["total_episodes"]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取环境统计信息"""
        return self.stats.copy()
    
    def get_config(self) -> Dict[str, Any]:
        """获取环境配置"""
        return {
            "env_id": self.env_id,
            "env_type": self.__class__.__name__,
            "config": self.config
        }
    
    def validate_action(self, action: str) -> bool:
        """
        验证动作是否有效
        
        Args:
            action: 要验证的动作
            
        Returns:
            动作是否有效
        """
        available_actions = self.get_available_actions()
        if not available_actions:
            return True  # 如果没有限制，则认为有效
        
        # 简单的字符串匹配
        return action.lower().strip() in [a.lower().strip() for a in available_actions]
    
    def get_action_space_info(self) -> Dict[str, Any]:
        """获取动作空间信息"""
        return {
            "type": "discrete_text",
            "available_actions": self.get_available_actions(),
            "action_count": len(self.get_available_actions())
        }
    
    def get_observation_space_info(self) -> Dict[str, Any]:
        """获取观测空间信息"""
        return {
            "type": "text",
            "current_observation": self.get_observation(),
            "observation_length": len(self.get_observation())
        }
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.env_id})"
    
    def __repr__(self) -> str:
        return self.__str__()
