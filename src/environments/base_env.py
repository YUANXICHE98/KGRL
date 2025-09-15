"""
Base Environment class for KGRL research framework.

Defines the common interface and basic functionality for all environments.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass


@dataclass
class EnvironmentState:
    """Environment state data class."""
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
        """Reset environment state."""
        self.current_observation = ""
        self.available_actions = []
        self.episode_step = 0
        self.is_done = False
        self.episode_reward = 0.0
        self.info = {}


class BaseEnvironment(ABC):
    """Base environment class defining common interface for all environments."""
    
    def __init__(self, env_id: str, config: Dict[str, Any] = None):
        """
        Initialize environment.
        
        Args:
            env_id: Unique environment identifier
            config: Environment configuration parameters
        """
        self.env_id = env_id
        self.config = config or {}
        self.state = EnvironmentState()
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{env_id}")
        
        # Environment statistics
        self.stats = {
            "total_episodes": 0,
            "total_steps": 0,
            "successful_episodes": 0,
            "average_episode_length": 0.0,
            "success_rate": 0.0
        }
        
        # Environment parameters
        self.max_episode_steps = self.config.get("max_episode_steps", 100)
        self.random_seed = self.config.get("random_seed", 42)
    
    @abstractmethod
    def reset(self) -> str:
        """
        Reset environment to initial state.
        
        Returns:
            Initial observation
        """
        pass
    
    @abstractmethod
    def step(self, action: str) -> Tuple[str, float, bool, Dict[str, Any]]:
        """
        Execute action and return results.
        
        Args:
            action: Action to execute
            
        Returns:
            observation: New observation
            reward: Reward received
            done: Whether episode is finished
            info: Additional information
        """
        pass
    
    @abstractmethod
    def get_available_actions(self) -> List[str]:
        """
        Get list of currently available actions.
        
        Returns:
            List of available actions
        """
        pass
    
    def get_observation(self) -> str:
        """Get current observation."""
        return self.state.current_observation
    
    def is_done(self) -> bool:
        """Check if episode is finished."""
        return self.state.is_done
    
    def get_episode_step(self) -> int:
        """Get current episode step count."""
        return self.state.episode_step
    
    def get_episode_reward(self) -> float:
        """Get current episode total reward."""
        return self.state.episode_reward
    
    def get_info(self) -> Dict[str, Any]:
        """Get additional information."""
        return self.state.info.copy()
    
    def seed(self, seed: int):
        """Set random seed."""
        self.random_seed = seed
        self.logger.info(f"Set random seed to {seed}")
    
    def close(self):
        """Close environment."""
        self.logger.info(f"Environment {self.env_id} closed")
    
    def render(self, mode: str = "human"):
        """Render environment (optional implementation)."""
        if mode == "human":
            print(f"Current observation: {self.state.current_observation}")
            print(f"Available actions: {self.state.available_actions}")
            print(f"Episode step: {self.state.episode_step}")
            print(f"Episode reward: {self.state.episode_reward}")
    
    def _update_episode_stats(self, success: bool):
        """Update episode statistics."""
        self.stats["total_episodes"] += 1
        self.stats["total_steps"] += self.state.episode_step
        
        if success:
            self.stats["successful_episodes"] += 1
        
        # Update averages
        if self.stats["total_episodes"] > 0:
            self.stats["average_episode_length"] = self.stats["total_steps"] / self.stats["total_episodes"]
            self.stats["success_rate"] = self.stats["successful_episodes"] / self.stats["total_episodes"]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get environment statistics."""
        return self.stats.copy()
    
    def get_config(self) -> Dict[str, Any]:
        """Get environment configuration."""
        return {
            "env_id": self.env_id,
            "env_type": self.__class__.__name__,
            "config": self.config
        }
    
    def validate_action(self, action: str) -> bool:
        """
        Validate if action is valid.
        
        Args:
            action: Action to validate
            
        Returns:
            Whether action is valid
        """
        available_actions = self.get_available_actions()
        if not available_actions:
            return True  # If no restrictions, consider valid
        
        # Simple string matching
        return action.lower().strip() in [a.lower().strip() for a in available_actions]
    
    def get_action_space_info(self) -> Dict[str, Any]:
        """Get action space information."""
        return {
            "type": "discrete_text",
            "available_actions": self.get_available_actions(),
            "action_count": len(self.get_available_actions())
        }
    
    def get_observation_space_info(self) -> Dict[str, Any]:
        """Get observation space information."""
        return {
            "type": "text",
            "current_observation": self.get_observation(),
            "observation_length": len(self.get_observation())
        }
    
    def cleanup(self):
        """Clean up environment resources."""
        self.close()
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.env_id})"
    
    def __repr__(self) -> str:
        return self.__str__()
