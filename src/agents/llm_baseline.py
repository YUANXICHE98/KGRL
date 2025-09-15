"""
LLM Baseline Agent for KGRL research framework.

Pure LLM agent for task extraction and baseline decision making.
Serves as the foundation for comparison with enhanced agents.
"""

from typing import Dict, Any, List
import logging

from .base_agent import BaseAgent


class LLMBaselineAgent(BaseAgent):
    """
    Pure LLM baseline agent.
    
    This agent uses only language model capabilities without any
    knowledge graph, memory, or reasoning enhancements. It serves
    as the baseline for comparison in ablation studies.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize the LLM baseline agent."""
        super().__init__(name, config)
        
        # LLM configuration
        self.llm_config = config.get("llm", {})
        self.model_name = self.llm_config.get("model_name", "gpt-4o")
        self.temperature = self.llm_config.get("temperature", 0.7)
        self.max_tokens = self.llm_config.get("max_tokens", 512)
        
        # Task extraction configuration
        self.task_extraction = config.get("task_extraction", {})
        self.use_task_extraction = self.task_extraction.get("enabled", True)
        
        # Decision making configuration
        self.decision_config = config.get("decision_making", {})
        self.strategy = self.decision_config.get("strategy", "direct")
        
        self.logger.info(f"LLM baseline agent '{name}' initialized")
    
    def _initialize_components(self):
        """Initialize LLM baseline components."""
        # No additional components needed for baseline
        pass
    
    def act(self, observation: str, available_actions: List[str]) -> str:
        """
        Select action using pure LLM reasoning.
        
        Args:
            observation: Current environment observation
            available_actions: List of available actions
            
        Returns:
            Selected action string
        """
        import time
        start_time = time.time()
        
        try:
            # Extract task if enabled
            if self.use_task_extraction:
                task_info = self._extract_task(observation)
            else:
                task_info = {"goal": "complete the task"}
            
            # Select action based on strategy
            if self.strategy == "chain_of_thought":
                action = self._chain_of_thought_action(observation, available_actions, task_info)
            else:
                action = self._direct_action(observation, available_actions, task_info)
            
            # Log the decision
            decision_time = time.time() - start_time
            self.log_action(observation, action, decision_time, True)
            
            # Update step counter
            self.step()
            
            return action
            
        except Exception as e:
            self.logger.error(f"Error in LLM baseline action selection: {e}")
            # Fallback to first available action
            fallback_action = available_actions[0] if available_actions else "wait"
            
            decision_time = time.time() - start_time
            self.log_action(observation, fallback_action, decision_time, False, {"error": str(e)})
            
            return fallback_action
    
    def _extract_task(self, observation: str) -> Dict[str, Any]:
        """Extract task information from observation."""
        # Simple keyword-based task extraction
        # In a real implementation, this would use LLM
        
        task_keywords = {
            "find": "search and locate",
            "take": "pick up item",
            "open": "unlock or open",
            "go": "navigate to location",
            "use": "utilize item",
            "examine": "inspect carefully"
        }
        
        obs_lower = observation.lower()
        detected_tasks = []
        
        for keyword, description in task_keywords.items():
            if keyword in obs_lower:
                detected_tasks.append(description)
        
        return {
            "goal": "complete the task",
            "subtasks": detected_tasks[:3],  # Limit to 3 subtasks
            "confidence": 0.7
        }
    
    def _direct_action(self, observation: str, available_actions: List[str], task_info: Dict[str, Any]) -> str:
        """Select action using direct LLM reasoning."""
        # Build prompt
        prompt = self._build_prompt(observation, available_actions, task_info)
        
        # Query LLM (mock implementation)
        response = self._query_llm(prompt)
        
        # Extract action from response
        action = self._extract_action_from_response(response, available_actions)
        
        return action
    
    def _chain_of_thought_action(self, observation: str, available_actions: List[str], task_info: Dict[str, Any]) -> str:
        """Select action using chain-of-thought reasoning."""
        # Build chain-of-thought prompt
        prompt = self._build_cot_prompt(observation, available_actions, task_info)
        
        # Query LLM with reasoning steps
        response = self._query_llm(prompt)
        
        # Extract action from reasoned response
        action = self._extract_action_from_response(response, available_actions)
        
        return action
    
    def _build_prompt(self, observation: str, available_actions: List[str], task_info: Dict[str, Any]) -> str:
        """Build basic prompt for LLM."""
        actions_text = ", ".join(available_actions)
        goal = task_info.get("goal", "complete the task")
        
        prompt = f"""
Current situation: {observation}

Goal: {goal}

Available actions: {actions_text}

Choose the best action to achieve the goal. Respond with just the action name.
"""
        return prompt.strip()
    
    def _build_cot_prompt(self, observation: str, available_actions: List[str], task_info: Dict[str, Any]) -> str:
        """Build chain-of-thought prompt for LLM."""
        actions_text = ", ".join(available_actions)
        goal = task_info.get("goal", "complete the task")
        subtasks = task_info.get("subtasks", [])
        
        prompt = f"""
Current situation: {observation}

Goal: {goal}
"""
        
        if subtasks:
            subtasks_text = "\n".join([f"- {task}" for task in subtasks])
            prompt += f"\nSubtasks identified:\n{subtasks_text}"
        
        prompt += f"""

Available actions: {actions_text}

Let me think step by step:
1. What is the current situation?
2. What needs to be done to achieve the goal?
3. Which action would be most helpful right now?

Based on this reasoning, the best action is:
"""
        return prompt.strip()
    
    def _query_llm(self, prompt: str) -> str:
        """Query the LLM with the given prompt."""
        # Mock LLM response for now
        # In real implementation, this would call OpenAI API or local model
        
        # Simple heuristic-based response for testing
        prompt_lower = prompt.lower()
        
        if "examine" in prompt_lower or "look" in prompt_lower:
            return "examine room"
        elif "take" in prompt_lower or "pick" in prompt_lower:
            return "take key"
        elif "open" in prompt_lower or "unlock" in prompt_lower:
            return "open door"
        elif "go" in prompt_lower or "move" in prompt_lower:
            return "go north"
        else:
            return "examine room"  # Default action
    
    def _extract_action_from_response(self, response: str, available_actions: List[str]) -> str:
        """Extract valid action from LLM response."""
        response_lower = response.lower().strip()
        
        # Try exact match first
        for action in available_actions:
            if action.lower() == response_lower:
                return action
        
        # Try partial match
        for action in available_actions:
            if action.lower() in response_lower or response_lower in action.lower():
                return action
        
        # Try keyword matching
        action_keywords = {
            "examine": ["examine", "look", "inspect", "check"],
            "take": ["take", "pick", "grab", "get"],
            "open": ["open", "unlock", "use key"],
            "go": ["go", "move", "walk", "travel"],
            "use": ["use", "apply", "employ"]
        }
        
        for action in available_actions:
            action_lower = action.lower()
            for base_action, keywords in action_keywords.items():
                if base_action in action_lower:
                    for keyword in keywords:
                        if keyword in response_lower:
                            return action
        
        # Fallback to first available action
        return available_actions[0] if available_actions else "wait"
    
    def _reset_agent_state(self):
        """Reset LLM baseline agent state."""
        # No additional state to reset for baseline agent
        pass
    
    def _cleanup_components(self):
        """Clean up LLM baseline components."""
        # No components to clean up for baseline agent
        pass
    
    def _get_checkpoint_data(self) -> Dict[str, Any]:
        """Get LLM baseline checkpoint data."""
        return {
            "strategy": self.strategy,
            "use_task_extraction": self.use_task_extraction
        }
    
    def _load_checkpoint_data(self, checkpoint: Dict[str, Any]):
        """Load LLM baseline checkpoint data."""
        self.strategy = checkpoint.get("strategy", "direct")
        self.use_task_extraction = checkpoint.get("use_task_extraction", True)
