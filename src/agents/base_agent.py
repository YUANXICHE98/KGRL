"""
Base Agent class for KGRL research framework.

Defines the common interface and functionality for all agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import time
import logging
from dataclasses import dataclass, field

@dataclass
class AgentStatistics:
    """Agent performance statistics."""
    total_actions: int = 0
    successful_actions: int = 0
    total_episodes: int = 0
    successful_episodes: int = 0
    total_decision_time: float = 0.0
    total_reward: float = 0.0
    
    # Component-specific stats
    kg_queries: int = 0
    memory_retrievals: int = 0
    reasoning_iterations: int = 0
    
    # Additional metrics
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate action success rate."""
        if self.total_actions == 0:
            return 0.0
        return self.successful_actions / self.total_actions
    
    @property
    def episode_success_rate(self) -> float:
        """Calculate episode success rate."""
        if self.total_episodes == 0:
            return 0.0
        return self.successful_episodes / self.total_episodes
    
    @property
    def avg_decision_time(self) -> float:
        """Calculate average decision time."""
        if self.total_actions == 0:
            return 0.0
        return self.total_decision_time / self.total_actions
    
    @property
    def avg_reward_per_episode(self) -> float:
        """Calculate average reward per episode."""
        if self.total_episodes == 0:
            return 0.0
        return self.total_reward / self.total_episodes


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the KGRL framework.
    
    Defines the common interface and provides basic functionality
    for statistics tracking, logging, and configuration management.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize the base agent.
        
        Args:
            name: Agent name/identifier
            config: Agent configuration dictionary
        """
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"agent.{name}")
        
        # Statistics tracking
        self.stats = AgentStatistics()
        
        # State tracking
        self.current_episode = 0
        self.current_step = 0
        self.episode_reward = 0.0
        self.episode_start_time = None
        
        # Configuration
        self.enabled_capabilities = self._parse_capabilities(config)
        
        # Initialize components
        self._initialize_components()
    
    def _parse_capabilities(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """Parse capability configuration."""
        capabilities = config.get("capabilities", {})
        return {
            "use_knowledge_graph": capabilities.get("use_knowledge_graph", False),
            "use_memory": capabilities.get("use_memory", False),
            "use_enhanced_reasoning": capabilities.get("use_enhanced_reasoning", False),
            "use_rl": capabilities.get("use_rl", False),
        }
    
    @abstractmethod
    def _initialize_components(self):
        """Initialize agent-specific components."""
        pass
    
    @abstractmethod
    def act(self, observation: str, available_actions: List[str]) -> str:
        """
        Select an action based on the current observation.
        
        Args:
            observation: Current environment observation
            available_actions: List of available actions
            
        Returns:
            Selected action string
        """
        pass
    
    def reset(self):
        """Reset agent state for a new episode."""
        if self.episode_start_time is not None:
            # Update episode statistics for completed episode
            episode_time = time.time() - self.episode_start_time

            # Log episode completion
            self.logger.info(
                f"Episode {self.current_episode} completed: "
                f"reward={self.episode_reward:.2f}, "
                f"steps={self.current_step}, "
                f"time={episode_time:.2f}s"
            )

        # Always increment episode count when reset is called
        self.stats.total_episodes += 1

        # Reset episode state
        self.current_episode += 1
        self.current_step = 0
        self.episode_reward = 0.0
        self.episode_start_time = time.time()

        # Reset agent-specific state
        self._reset_agent_state()
    
    @abstractmethod
    def _reset_agent_state(self):
        """Reset agent-specific state."""
        pass
    
    def update_reward(self, reward: float):
        """Update reward tracking."""
        self.episode_reward += reward
        self.stats.total_reward += reward
    
    def step(self):
        """Increment step counter."""
        self.current_step += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent performance statistics."""
        stats_dict = {
            "total_actions": self.stats.total_actions,
            "successful_actions": self.stats.successful_actions,
            "success_rate": self.stats.success_rate,
            "total_episodes": self.stats.total_episodes,
            "successful_episodes": self.stats.successful_episodes,
            "episode_success_rate": self.stats.episode_success_rate,
            "avg_decision_time": self.stats.avg_decision_time,
            "total_reward": self.stats.total_reward,
            "avg_reward_per_episode": self.stats.avg_reward_per_episode,
            "kg_queries": self.stats.kg_queries,
            "memory_retrievals": self.stats.memory_retrievals,
            "reasoning_iterations": self.stats.reasoning_iterations,
        }
        
        # Add custom metrics
        stats_dict.update(self.stats.custom_metrics)
        
        return stats_dict
    
    def log_action(self, observation: str, action: str, decision_time: float, 
                   success: bool = True, additional_info: Optional[Dict] = None):
        """Log an action for statistics and debugging."""
        # Update statistics
        self.stats.total_actions += 1
        self.stats.total_decision_time += decision_time
        
        if success:
            self.stats.successful_actions += 1
        
        # Log the action
        log_msg = (
            f"Action taken: '{action}' "
            f"(time: {decision_time:.3f}s, success: {success})"
        )
        
        if additional_info:
            log_msg += f" - {additional_info}"
        
        self.logger.debug(log_msg)
    
    def cleanup(self):
        """Clean up agent resources."""
        self.logger.info(f"Agent {self.name} cleanup completed")
        self._cleanup_components()
    
    @abstractmethod
    def _cleanup_components(self):
        """Clean up agent-specific components."""
        pass
    
    def save_checkpoint(self, path: str):
        """Save agent checkpoint."""
        checkpoint = {
            "name": self.name,
            "config": self.config,
            "statistics": self.get_statistics(),
            "current_episode": self.current_episode,
            "enabled_capabilities": self.enabled_capabilities,
        }
        
        # Add agent-specific checkpoint data
        checkpoint.update(self._get_checkpoint_data())
        
        import pickle
        with open(path, 'wb') as f:
            pickle.dump(checkpoint, f)
        
        self.logger.info(f"Checkpoint saved to {path}")
    
    @abstractmethod
    def _get_checkpoint_data(self) -> Dict[str, Any]:
        """Get agent-specific checkpoint data."""
        return {}
    
    def load_checkpoint(self, path: str):
        """Load agent checkpoint."""
        import pickle
        with open(path, 'rb') as f:
            checkpoint = pickle.load(f)
        
        # Restore basic state
        self.current_episode = checkpoint.get("current_episode", 0)
        self.enabled_capabilities = checkpoint.get("enabled_capabilities", {})
        
        # Restore agent-specific state
        self._load_checkpoint_data(checkpoint)
        
        self.logger.info(f"Checkpoint loaded from {path}")
    
    @abstractmethod
    def _load_checkpoint_data(self, checkpoint: Dict[str, Any]):
        """Load agent-specific checkpoint data."""
        pass
    
    def __str__(self) -> str:
        """String representation of the agent."""
        capabilities = [k for k, v in self.enabled_capabilities.items() if v]
        return f"{self.__class__.__name__}(name={self.name}, capabilities={capabilities})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"episode={self.current_episode}, "
            f"step={self.current_step}, "
            f"capabilities={self.enabled_capabilities}"
            f")"
        )
