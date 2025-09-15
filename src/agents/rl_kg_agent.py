"""
RL KG Agent for KGRL research framework.

Reinforcement learning agent with knowledge graph integration.
"""

from typing import Dict, Any, List
import logging

from .base_agent import BaseAgent


class RLKGAgent(BaseAgent):
    """
    Reinforcement Learning agent with Knowledge Graph integration.
    
    This agent uses RL algorithms (PPO, DQN, etc.) enhanced with
    knowledge graph features for improved decision making.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize the RL KG agent."""
        super().__init__(name, config)
        
        # RL configuration
        self.rl_config = config.get("rl_algorithm", {})
        self.algorithm_name = self.rl_config.get("name", "PPO")
        
        # KG configuration
        self.kg_config = config.get("knowledge_graph", {})
        self.use_kg_features = self.kg_config.get("enabled", True)
        
        self.logger.info(f"RL KG agent '{name}' initialized with {self.algorithm_name}")
    
    def _initialize_components(self):
        """Initialize RL KG components."""
        # Mock initialization for now
        if self.algorithm_name == "PPO":
            self.policy = MockPPOPolicy()
        elif self.algorithm_name == "DQN":
            self.policy = MockDQNPolicy()
        else:
            self.policy = MockPPOPolicy()  # Default
        
        if self.use_kg_features:
            self.kg_feature_extractor = MockKGFeatureExtractor()
    
    def act(self, observation: str, available_actions: List[str]) -> str:
        """
        Select action using RL policy with KG features.
        
        Args:
            observation: Current environment observation
            available_actions: List of available actions
            
        Returns:
            Selected action string
        """
        import time
        start_time = time.time()
        
        try:
            # Extract features
            features = self._extract_features(observation, available_actions)
            
            # Get action from policy
            action_idx = self.policy.select_action(features)
            
            # Map to actual action
            if 0 <= action_idx < len(available_actions):
                action = available_actions[action_idx]
            else:
                action = available_actions[0] if available_actions else "wait"
            
            # Log the decision
            decision_time = time.time() - start_time
            self.log_action(observation, action, decision_time, True)
            
            # Update step counter
            self.step()
            
            return action
            
        except Exception as e:
            self.logger.error(f"Error in RL KG action selection: {e}")
            # Fallback to first available action
            fallback_action = available_actions[0] if available_actions else "wait"
            
            decision_time = time.time() - start_time
            self.log_action(observation, fallback_action, decision_time, False, {"error": str(e)})
            
            return fallback_action
    
    def _extract_features(self, observation: str, available_actions: List[str]) -> Dict[str, Any]:
        """Extract features for RL policy."""
        features = {
            "observation": observation,
            "num_actions": len(available_actions),
            "step": self.current_step,
            "episode": self.current_episode
        }
        
        # Add KG features if enabled
        if self.use_kg_features and hasattr(self, 'kg_feature_extractor'):
            kg_features = self.kg_feature_extractor.extract(observation)
            features.update(kg_features)
        
        return features
    
    def update_policy(self, reward: float, done: bool):
        """Update RL policy with reward signal."""
        if hasattr(self, 'policy'):
            self.policy.update(reward, done)
    
    def _reset_agent_state(self):
        """Reset RL KG agent state."""
        if hasattr(self, 'policy'):
            self.policy.reset_episode()
    
    def _cleanup_components(self):
        """Clean up RL KG components."""
        if hasattr(self, 'policy'):
            self.policy.cleanup()
        if hasattr(self, 'kg_feature_extractor'):
            self.kg_feature_extractor.cleanup()
    
    def _get_checkpoint_data(self) -> Dict[str, Any]:
        """Get RL KG checkpoint data."""
        checkpoint = {
            "algorithm_name": self.algorithm_name,
            "use_kg_features": self.use_kg_features
        }
        
        if hasattr(self, 'policy'):
            checkpoint["policy_state"] = self.policy.get_state()
        
        return checkpoint
    
    def _load_checkpoint_data(self, checkpoint: Dict[str, Any]):
        """Load RL KG checkpoint data."""
        self.algorithm_name = checkpoint.get("algorithm_name", "PPO")
        self.use_kg_features = checkpoint.get("use_kg_features", True)
        
        if hasattr(self, 'policy') and "policy_state" in checkpoint:
            self.policy.load_state(checkpoint["policy_state"])


class MockPPOPolicy:
    """Mock PPO policy for testing."""
    
    def __init__(self):
        self.step_count = 0
    
    def select_action(self, features: Dict[str, Any]) -> int:
        """Mock action selection."""
        # Simple heuristic based on observation
        observation = features.get("observation", "").lower()
        
        if "key" in observation:
            return 1  # Take action
        elif "door" in observation:
            return 2  # Open/use action
        else:
            return 0  # Examine action
    
    def update(self, reward: float, done: bool):
        """Mock policy update."""
        self.step_count += 1
    
    def reset_episode(self):
        """Mock episode reset."""
        pass
    
    def get_state(self) -> Dict[str, Any]:
        """Mock state getter."""
        return {"step_count": self.step_count}
    
    def load_state(self, state: Dict[str, Any]):
        """Mock state loader."""
        self.step_count = state.get("step_count", 0)
    
    def cleanup(self):
        """Mock cleanup."""
        pass


class MockDQNPolicy:
    """Mock DQN policy for testing."""
    
    def __init__(self):
        self.step_count = 0
    
    def select_action(self, features: Dict[str, Any]) -> int:
        """Mock action selection."""
        # Simple heuristic
        return self.step_count % 3  # Cycle through actions
    
    def update(self, reward: float, done: bool):
        """Mock policy update."""
        self.step_count += 1
    
    def reset_episode(self):
        """Mock episode reset."""
        pass
    
    def get_state(self) -> Dict[str, Any]:
        """Mock state getter."""
        return {"step_count": self.step_count}
    
    def load_state(self, state: Dict[str, Any]):
        """Mock state loader."""
        self.step_count = state.get("step_count", 0)
    
    def cleanup(self):
        """Mock cleanup."""
        pass


class MockKGFeatureExtractor:
    """Mock KG feature extractor for testing."""
    
    def extract(self, observation: str) -> Dict[str, Any]:
        """Mock feature extraction."""
        return {
            "kg_entities": len(observation.split()),  # Simple entity count
            "kg_relations": 1 if "with" in observation or "in" in observation else 0,
            "kg_confidence": 0.8
        }
    
    def cleanup(self):
        """Mock cleanup."""
        pass
