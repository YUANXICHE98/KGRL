"""
Agent基类
定义所有Agent的通用接口和基础功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass

@dataclass
class AgentState:
    """Agent状态类"""
    episode_step: int = 0
    total_reward: float = 0.0
    last_action: Optional[str] = None
    last_observation: Optional[str] = None
    history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.history is None:
            self.history = []
    
    def reset(self):
        """重置状态"""
        self.episode_step = 0
        self.total_reward = 0.0
        self.last_action = None
        self.last_observation = None
        self.history = []
    
    def update(self, action: str, observation: str, reward: float, info: Dict[str, Any] = None):
        """更新状态"""
        self.episode_step += 1
        self.total_reward += reward
        self.last_action = action
        self.last_observation = observation
        
        # 记录历史
        step_info = {
            "step": self.episode_step,
            "action": action,
            "observation": observation,
            "reward": reward,
            "info": info or {}
        }
        self.history.append(step_info)

class BaseAgent(ABC):
    """Agent基类，定义所有Agent的通用接口"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        """
        初始化Agent
        
        Args:
            agent_id: Agent唯一标识符
            config: Agent配置参数
        """
        self.agent_id = agent_id
        self.config = config or {}
        self.state = AgentState()
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{agent_id}")
        
        # 性能统计
        self.stats = {
            "total_episodes": 0,
            "successful_episodes": 0,
            "total_steps": 0,
            "total_reward": 0.0,
            "average_episode_length": 0.0,
            "success_rate": 0.0
        }
    
    @abstractmethod
    def act(self, observation: str, available_actions: List[str] = None, **kwargs) -> str:
        """
        根据观测选择动作
        
        Args:
            observation: 环境观测
            available_actions: 可用动作列表
            **kwargs: 其他参数
            
        Returns:
            选择的动作
        """
        pass
    
    def reset(self):
        """重置Agent状态"""
        self.state.reset()
        self.logger.info(f"Agent {self.agent_id} reset")
    
    def update(self, action: str, observation: str, reward: float, done: bool, info: Dict[str, Any] = None):
        """
        更新Agent状态
        
        Args:
            action: 执行的动作
            observation: 新的观测
            reward: 获得的奖励
            done: 是否结束
            info: 额外信息
        """
        self.state.update(action, observation, reward, info)
        
        if done:
            self._update_episode_stats(reward > 0)  # 简单的成功判断
    
    def _update_episode_stats(self, success: bool):
        """更新episode统计信息"""
        self.stats["total_episodes"] += 1
        self.stats["total_steps"] += self.state.episode_step
        self.stats["total_reward"] += self.state.total_reward
        
        if success:
            self.stats["successful_episodes"] += 1
        
        # 更新平均值
        self.stats["average_episode_length"] = self.stats["total_steps"] / self.stats["total_episodes"]
        self.stats["success_rate"] = self.stats["successful_episodes"] / self.stats["total_episodes"]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取Agent统计信息"""
        return self.stats.copy()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取当前episode的历史记录"""
        return self.state.history.copy()
    
    def save_model(self, path: str):
        """保存模型（子类可重写）"""
        self.logger.info(f"Base agent {self.agent_id} save_model called, but not implemented")
    
    def load_model(self, path: str):
        """加载模型（子类可重写）"""
        self.logger.info(f"Base agent {self.agent_id} load_model called, but not implemented")
    
    def get_config(self) -> Dict[str, Any]:
        """获取Agent配置"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "config": self.config
        }
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.agent_id})"
    
    def __repr__(self) -> str:
        return self.__str__()
