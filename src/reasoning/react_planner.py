"""
ReAct Planner for KGRL research framework.

Implements Reasoning and Acting framework for structured decision making.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import logging


class ActionType(Enum):
    """Action type enumeration."""
    QUERY_KG = "query_kg"
    EXECUTE_ACTION = "execute_action"
    THINK = "think"
    UNKNOWN = "unknown"


@dataclass
class ReActStep:
    """ReAct step data structure."""
    step_id: int
    thought: str = ""
    action_type: ActionType = ActionType.UNKNOWN
    action_content: str = ""
    observation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "thought": self.thought,
            "action_type": self.action_type.value,
            "action_content": self.action_content,
            "observation": self.observation
        }


class ReActPlanner:
    """ReAct reasoning framework for structured planning."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Configuration parameters
        self.max_reasoning_steps = self.config.get("max_reasoning_steps", 5)
        self.max_retries = self.config.get("max_retries", 3)
        
        # Current reasoning state
        self.current_steps: List[ReActStep] = []
        self.step_counter = 0
        
        # Parsing patterns
        self.thought_pattern = r"Thought:\s*(.*?)(?=\n(?:Action:|$))"
        self.action_pattern = r"Action:\s*(.*?)(?=\n(?:Observation:|Thought:|$))"
        self.observation_pattern = r"Observation:\s*(.*?)(?=\n(?:Thought:|Action:|$))"
        
        self.logger.info("Initialized ReAct planner")
    
    def plan_action(self, context: Dict[str, Any], available_actions: List[str]) -> str:
        """
        Plan action using ReAct reasoning.
        
        Args:
            context: Current context including observation and retrieved info
            available_actions: List of available actions
            
        Returns:
            Selected action
        """
        try:
            # Build ReAct prompt
            prompt = self._build_react_prompt(context, available_actions)
            
            # Get LLM response (mock for now)
            response = self._query_llm(prompt)
            
            # Parse response into steps
            steps = self.parse_response(response)
            self.current_steps.extend(steps)
            
            # Extract final action
            action = self._extract_final_action(steps, available_actions)
            
            return action
            
        except Exception as e:
            self.logger.error(f"Error in ReAct planning: {e}")
            # Fallback to first available action
            return available_actions[0] if available_actions else "wait"
    
    def parse_response(self, response: str) -> List[ReActStep]:
        """
        Parse LLM response into ReAct steps.
        
        Args:
            response: LLM response text
            
        Returns:
            List of parsed ReAct steps
        """
        steps = []
        
        # Split response by lines
        lines = response.strip().split('\n')
        current_step = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect thought
            if line.lower().startswith('thought:'):
                if current_step is not None:
                    steps.append(current_step)
                
                self.step_counter += 1
                current_step = ReActStep(step_id=self.step_counter)
                current_step.thought = line[8:].strip()  # Remove "Thought:"
            
            # Detect action
            elif line.lower().startswith('action:'):
                if current_step is None:
                    self.step_counter += 1
                    current_step = ReActStep(step_id=self.step_counter)
                
                action_content = line[7:].strip()  # Remove "Action:"
                current_step.action_content = action_content
                current_step.action_type = self._classify_action(action_content)
            
            # Detect observation
            elif line.lower().startswith('observation:'):
                if current_step is not None:
                    current_step.observation = line[12:].strip()  # Remove "Observation:"
        
        # Add final step if exists
        if current_step is not None:
            steps.append(current_step)
        
        return steps
    
    def _build_react_prompt(self, context: Dict[str, Any], available_actions: List[str]) -> str:
        """Build ReAct reasoning prompt."""
        observation = context.get("observation", "")
        retrieved_info = context.get("retrieved_info", [])
        
        prompt = f"""You are an intelligent agent that uses reasoning to make decisions.
Use the following format:

Thought: [your reasoning about the current situation]
Action: [the action you want to take]
Observation: [what you observe after the action]

Current situation: {observation}

Available actions: {', '.join(available_actions)}
"""
        
        if retrieved_info:
            info_text = "\n".join([item.get("content", "") for item in retrieved_info])
            prompt += f"\nRelevant knowledge:\n{info_text}\n"
        
        prompt += "\nNow, think step by step and choose the best action:\n\nThought:"
        
        return prompt
    
    def _query_llm(self, prompt: str) -> str:
        """Query LLM with prompt (mock implementation)."""
        # Mock ReAct response for testing
        if "key" in prompt.lower():
            return """Thought: I need to find a key to progress. Let me look around.
Action: take key
Observation: I successfully took the key."""
        elif "door" in prompt.lower() or "chest" in prompt.lower():
            return """Thought: I have a key and see something that might need to be opened.
Action: use key on door
Observation: The door opens successfully."""
        else:
            return """Thought: I should examine my surroundings to understand the situation better.
Action: examine room
Observation: I can see the room clearly now."""
    
    def _classify_action(self, action_content: str) -> ActionType:
        """Classify action type based on content."""
        action_lower = action_content.lower()
        
        if any(keyword in action_lower for keyword in ["query", "search", "find", "knowledge"]):
            return ActionType.QUERY_KG
        elif any(keyword in action_lower for keyword in ["take", "go", "use", "open", "examine"]):
            return ActionType.EXECUTE_ACTION
        elif any(keyword in action_lower for keyword in ["think", "consider", "analyze"]):
            return ActionType.THINK
        else:
            return ActionType.EXECUTE_ACTION  # Default to execution
    
    def _extract_final_action(self, steps: List[ReActStep], available_actions: List[str]) -> str:
        """Extract final action from ReAct steps."""
        if not steps:
            return available_actions[0] if available_actions else "wait"
        
        # Get the last action step
        for step in reversed(steps):
            if step.action_type == ActionType.EXECUTE_ACTION and step.action_content:
                # Try to match with available actions
                action_content = step.action_content.lower().strip()
                
                # Exact match
                for action in available_actions:
                    if action.lower().strip() == action_content:
                        return action
                
                # Partial match
                for action in available_actions:
                    if action_content in action.lower() or action.lower() in action_content:
                        return action
                
                # Keyword matching
                for action in available_actions:
                    action_words = action.lower().split()
                    content_words = action_content.split()
                    if any(word in action_words for word in content_words):
                        return action
        
        # Fallback to first available action
        return available_actions[0] if available_actions else "wait"
    
    def get_reasoning_trace(self) -> List[Dict[str, Any]]:
        """Get the current reasoning trace."""
        return [step.to_dict() for step in self.current_steps]
    
    def reset(self):
        """Reset the planner state."""
        self.current_steps.clear()
        self.step_counter = 0
    
    def cleanup(self):
        """Clean up planner resources."""
        self.reset()
