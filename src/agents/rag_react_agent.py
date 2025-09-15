"""
RAG/ReAct Agent for KGRL research framework.

Enhanced agent with retrieval-augmented generation and ReAct reasoning capabilities.
"""

from typing import Dict, Any, List
import logging

from .base_agent import BaseAgent


class RAGReActAgent(BaseAgent):
    """
    RAG enhanced agent with ReAct reasoning.
    
    This agent combines retrieval-augmented generation with ReAct
    (Reasoning and Acting) capabilities for enhanced decision making.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize the RAG/ReAct agent."""
        super().__init__(name, config)
        
        # RAG configuration
        self.rag_config = config.get("rag", {})
        self.use_rag = self.rag_config.get("enabled", True)
        
        # ReAct configuration
        self.react_config = config.get("react", {})
        self.use_react = self.react_config.get("enabled", True)
        self.max_iterations = self.react_config.get("max_iterations", 5)
        
        self.logger.info(f"RAG/ReAct agent '{name}' initialized")
    
    def _initialize_components(self):
        """Initialize RAG/ReAct components."""
        # Mock initialization for now
        if self.use_rag:
            self.retriever = MockRetriever()
        
        if self.use_react:
            self.reasoner = MockReActReasoner()
    
    def act(self, observation: str, available_actions: List[str]) -> str:
        """
        Select action using RAG and ReAct reasoning.
        
        Args:
            observation: Current environment observation
            available_actions: List of available actions
            
        Returns:
            Selected action string
        """
        import time
        start_time = time.time()
        
        try:
            # Retrieve relevant information if RAG is enabled
            context = {"observation": observation}
            
            if self.use_rag and hasattr(self, 'retriever'):
                retrieved_info = self.retriever.retrieve(observation)
                context["retrieved_info"] = retrieved_info
            
            # Use ReAct reasoning if enabled
            if self.use_react and hasattr(self, 'reasoner'):
                action = self.reasoner.reason_and_act(context, available_actions)
            else:
                action = self._direct_action(context, available_actions)
            
            # Log the decision
            decision_time = time.time() - start_time
            self.log_action(observation, action, decision_time, True)
            
            # Update step counter
            self.step()
            
            return action
            
        except Exception as e:
            self.logger.error(f"Error in RAG/ReAct action selection: {e}")
            # Fallback to first available action
            fallback_action = available_actions[0] if available_actions else "wait"
            
            decision_time = time.time() - start_time
            self.log_action(observation, fallback_action, decision_time, False, {"error": str(e)})
            
            return fallback_action
    
    def _direct_action(self, context: Dict[str, Any], available_actions: List[str]) -> str:
        """Select action directly without ReAct reasoning."""
        observation = context["observation"]
        
        # Simple action selection based on keywords
        obs_lower = observation.lower()
        
        for action in available_actions:
            action_lower = action.lower()
            
            if "examine" in action_lower and ("room" in obs_lower or "look" in obs_lower):
                return action
            elif "take" in action_lower and ("key" in obs_lower or "item" in obs_lower):
                return action
            elif "open" in action_lower and ("door" in obs_lower or "chest" in obs_lower):
                return action
            elif "go" in action_lower and ("exit" in obs_lower or "door" in obs_lower):
                return action
        
        # Fallback to first action
        return available_actions[0] if available_actions else "wait"
    
    def _reset_agent_state(self):
        """Reset RAG/ReAct agent state."""
        if hasattr(self, 'reasoner'):
            self.reasoner.reset()
    
    def _cleanup_components(self):
        """Clean up RAG/ReAct components."""
        if hasattr(self, 'retriever'):
            self.retriever.cleanup()
        if hasattr(self, 'reasoner'):
            self.reasoner.cleanup()
    
    def _get_checkpoint_data(self) -> Dict[str, Any]:
        """Get RAG/ReAct checkpoint data."""
        return {
            "use_rag": self.use_rag,
            "use_react": self.use_react,
            "max_iterations": self.max_iterations
        }
    
    def _load_checkpoint_data(self, checkpoint: Dict[str, Any]):
        """Load RAG/ReAct checkpoint data."""
        self.use_rag = checkpoint.get("use_rag", True)
        self.use_react = checkpoint.get("use_react", True)
        self.max_iterations = checkpoint.get("max_iterations", 5)


class MockRetriever:
    """Mock retriever for testing."""
    
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """Mock retrieval."""
        return [
            {"content": "Keys are used to open doors", "relevance": 0.8},
            {"content": "Examine rooms to find items", "relevance": 0.7}
        ]
    
    def cleanup(self):
        """Mock cleanup."""
        pass


class MockReActReasoner:
    """Mock ReAct reasoner for testing."""
    
    def reason_and_act(self, context: Dict[str, Any], available_actions: List[str]) -> str:
        """Mock ReAct reasoning."""
        observation = context["observation"]
        
        # Simple reasoning based on observation
        if "key" in observation.lower():
            for action in available_actions:
                if "take" in action.lower():
                    return action
        
        if "door" in observation.lower():
            for action in available_actions:
                if "open" in action.lower() or "use" in action.lower():
                    return action
        
        # Default to examine
        for action in available_actions:
            if "examine" in action.lower():
                return action
        
        return available_actions[0] if available_actions else "wait"
    
    def reset(self):
        """Mock reset."""
        pass
    
    def cleanup(self):
        """Mock cleanup."""
        pass
