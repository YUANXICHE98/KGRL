"""
Base Policy classes for KGRL research framework.

Defines abstract interfaces for RL policies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
import logging


class BasePolicy(ABC):
    """Abstract base class for RL policies."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Policy state
        self.is_training = True
        self.step_count = 0
        
    @abstractmethod
    def select_action(self, state: Any, available_actions: List[str]) -> Tuple[str, Dict[str, Any]]:
        """
        Select action given current state.
        
        Args:
            state: Current state observation
            available_actions: List of available actions
            
        Returns:
            Tuple of (selected_action, action_info)
        """
        pass
    
    @abstractmethod
    def update(self, experiences: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Update policy with experiences.
        
        Args:
            experiences: List of experience dictionaries
            
        Returns:
            Training metrics
        """
        pass
    
    def set_training_mode(self, training: bool):
        """Set training mode."""
        self.is_training = training
        self.logger.debug(f"Set training mode to {training}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get policy statistics."""
        return {
            "step_count": self.step_count,
            "is_training": self.is_training,
            "policy_type": self.__class__.__name__
        }
    
    def save_checkpoint(self, filepath: str) -> bool:
        """Save policy checkpoint."""
        try:
            import json
            
            checkpoint = {
                "config": self.config,
                "step_count": self.step_count,
                "is_training": self.is_training,
                "policy_type": self.__class__.__name__
            }
            
            with open(filepath, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            
            self.logger.info(f"Saved policy checkpoint to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            return False
    
    def load_checkpoint(self, filepath: str) -> bool:
        """Load policy checkpoint."""
        try:
            import json
            
            with open(filepath, 'r') as f:
                checkpoint = json.load(f)
            
            self.step_count = checkpoint.get("step_count", 0)
            self.is_training = checkpoint.get("is_training", True)
            
            self.logger.info(f"Loaded policy checkpoint from {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            return False
    
    def cleanup(self):
        """Clean up policy resources."""
        self.step_count = 0


class RandomPolicy(BasePolicy):
    """Random action selection policy for baseline comparison."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.logger.info("Initialized random policy")
    
    def select_action(self, state: Any, available_actions: List[str]) -> Tuple[str, Dict[str, Any]]:
        """Select random action."""
        import random
        
        if not available_actions:
            return "wait", {"confidence": 0.0, "random": True}
        
        action = random.choice(available_actions)
        action_info = {
            "confidence": 1.0 / len(available_actions),
            "random": True,
            "num_actions": len(available_actions)
        }
        
        self.step_count += 1
        
        return action, action_info
    
    def update(self, experiences: List[Dict[str, Any]]) -> Dict[str, float]:
        """Random policy doesn't learn."""
        return {
            "policy_loss": 0.0,
            "experiences_processed": len(experiences)
        }


class GreedyPolicy(BasePolicy):
    """Greedy policy that prefers actions based on simple heuristics."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # Action preferences (higher is better)
        self.action_preferences = {
            "take": 0.8,
            "use": 0.7,
            "open": 0.6,
            "go": 0.5,
            "examine": 0.4,
            "look": 0.3,
            "inventory": 0.2
        }
        
        self.logger.info("Initialized greedy policy")
    
    def select_action(self, state: Any, available_actions: List[str]) -> Tuple[str, Dict[str, Any]]:
        """Select action greedily based on preferences."""
        if not available_actions:
            return "wait", {"confidence": 0.0, "greedy": True}
        
        # Score actions based on preferences
        action_scores = {}
        
        for action in available_actions:
            score = 0.1  # Base score
            
            # Check for preferred action types
            for keyword, preference in self.action_preferences.items():
                if keyword in action.lower():
                    score += preference
                    break
            
            # Bonus for actions that match state context
            state_str = str(state).lower()
            action_words = action.lower().split()
            for word in action_words:
                if word in state_str:
                    score += 0.2
            
            action_scores[action] = score
        
        # Select highest scoring action
        best_action = max(action_scores, key=action_scores.get)
        confidence = action_scores[best_action] / max(action_scores.values())
        
        action_info = {
            "confidence": confidence,
            "greedy": True,
            "action_scores": action_scores
        }
        
        self.step_count += 1
        
        return best_action, action_info
    
    def update(self, experiences: List[Dict[str, Any]]) -> Dict[str, float]:
        """Update action preferences based on rewards."""
        if not experiences:
            return {"policy_loss": 0.0}
        
        # Simple preference update based on rewards
        for exp in experiences:
            action = exp.get("action", "")
            reward = exp.get("reward", 0.0)
            
            # Update preferences for action keywords
            for keyword in self.action_preferences:
                if keyword in action.lower():
                    # Small learning rate
                    self.action_preferences[keyword] += reward * 0.01
                    # Keep preferences in reasonable range
                    self.action_preferences[keyword] = max(0.0, min(1.0, self.action_preferences[keyword]))
                    break
        
        avg_reward = sum(exp.get("reward", 0.0) for exp in experiences) / len(experiences)
        
        return {
            "policy_loss": -avg_reward,  # Negative reward as loss
            "avg_reward": avg_reward,
            "experiences_processed": len(experiences)
        }
