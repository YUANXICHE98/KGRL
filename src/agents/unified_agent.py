"""
Unified Agent for KGRL research framework.

Integrates all capabilities (LLM, KG, Memory, Reasoning, RL) into a single
configurable agent that can be used for ablation studies and full system evaluation.
"""

from typing import Dict, Any, List, Optional
import time
import logging

try:
    from .base_agent import BaseAgent
except ImportError:
    from agents.base_agent import BaseAgent

try:
    from ..knowledge import GraphManager, KnowledgeRetriever, KnowledgeUpdater
except ImportError:
    from knowledge.graph_manager import GraphManager
    from knowledge.retriever import KnowledgeRetriever
    from knowledge.updater import KnowledgeUpdater

try:
    from ..reasoning import ReActPlanner, DODAFReasoner, StrategySelector
except ImportError:
    # Mock reasoning components for now
    ReActPlanner = None
    DODAFReasoner = None
    StrategySelector = None

try:
    from ..utils import ConfigLoader
except ImportError:
    # Mock config loader for now
    ConfigLoader = None


class UnifiedAgent(BaseAgent):
    """
    Unified agent integrating all KGRL capabilities.
    
    This agent can be configured to enable/disable different capabilities:
    - LLM baseline (always enabled)
    - Knowledge Graph integration (optional)
    - Memory system (optional) 
    - Enhanced reasoning (optional)
    - Reinforcement Learning (optional)
    
    The configuration determines which components are active, enabling
    comprehensive ablation studies and system evaluation.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize the unified agent.
        
        Args:
            name: Agent identifier
            config: Configuration dictionary with capability settings
        """
        super().__init__(name, config)
        
        # Core LLM configuration
        self.llm_config = config.get("llm", {})
        self.model_name = self.llm_config.get("model_name", "gpt-4o")
        self.temperature = self.llm_config.get("temperature", 0.7)
        self.max_tokens = self.llm_config.get("max_tokens", 512)
        
        # Component instances (initialized in _initialize_components)
        self.graph_manager = None
        self.knowledge_retriever = None
        self.knowledge_updater = None
        self.react_planner = None
        self.dodaf_reasoner = None
        self.strategy_selector = None
        
        # State tracking
        self.conversation_history = []
        self.current_context = {}
        
        self.logger.info(f"Unified agent '{name}' initialized with capabilities: {self.enabled_capabilities}")
    
    def _initialize_components(self):
        """Initialize components based on enabled capabilities."""
        
        # Initialize Knowledge Graph components
        if self.enabled_capabilities["use_knowledge_graph"]:
            kg_config = self.config.get("knowledge_graph", {})

            if GraphManager:
                self.graph_manager = GraphManager(kg_config.get("storage", {}))
            else:
                self.graph_manager = None

            if KnowledgeRetriever:
                self.knowledge_retriever = KnowledgeRetriever(kg_config.get("retrieval", {}))
            else:
                self.knowledge_retriever = None

            if KnowledgeUpdater:
                self.knowledge_updater = KnowledgeUpdater(kg_config.get("update", {}))
            else:
                self.knowledge_updater = None

            self.logger.info("Knowledge Graph components initialized")
        
        # Initialize Memory system
        if self.enabled_capabilities["use_memory"]:
            memory_config = self.config.get("memory", {})
            # Memory system initialization would go here
            # For now, we'll use a simple list-based memory
            self.short_term_memory = []
            self.medium_term_memory = []
            
            self.logger.info("Memory system initialized")
        
        # Initialize Enhanced Reasoning
        if self.enabled_capabilities["use_enhanced_reasoning"]:
            reasoning_config = self.config.get("reasoning", {})

            if reasoning_config.get("use_react", True) and ReActPlanner:
                self.react_planner = ReActPlanner(reasoning_config.get("react", {}))
            else:
                self.react_planner = None

            if reasoning_config.get("use_dodaf", True) and DODAFReasoner:
                self.dodaf_reasoner = DODAFReasoner(reasoning_config.get("dodaf", {}))
            else:
                self.dodaf_reasoner = None

            if StrategySelector:
                self.strategy_selector = StrategySelector(reasoning_config.get("strategy", {}))
            else:
                self.strategy_selector = None
            
            self.logger.info("Enhanced reasoning components initialized")
        
        # Initialize RL components
        if self.enabled_capabilities["use_rl"]:
            rl_config = self.config.get("rl", {})
            # RL initialization would go here
            self.logger.info("RL components initialized")
    
    def act(self, observation: str, available_actions: List[str]) -> str:
        """
        Select an action based on the current observation.
        
        Args:
            observation: Current environment observation
            available_actions: List of available actions
            
        Returns:
            Selected action string
        """
        start_time = time.time()
        
        try:
            # Update context
            self.current_context = {
                "observation": observation,
                "available_actions": available_actions,
                "step": self.current_step,
                "episode": self.current_episode
            }
            
            # Process observation through enabled components
            processed_context = self._process_observation(observation)
            
            # Select action using appropriate strategy
            action = self._select_action(processed_context, available_actions)
            
            # Post-process and update state
            self._post_process_action(action, processed_context)
            
            # Log the decision
            decision_time = time.time() - start_time
            self.log_action(observation, action, decision_time, True)
            
            # Update step counter
            self.step()
            
            return action
            
        except Exception as e:
            self.logger.error(f"Error in action selection: {e}")
            # Fallback to random action
            import random
            fallback_action = random.choice(available_actions) if available_actions else "wait"
            
            decision_time = time.time() - start_time
            self.log_action(observation, fallback_action, decision_time, False, {"error": str(e)})
            
            return fallback_action
    
    def _process_observation(self, observation: str) -> Dict[str, Any]:
        """Process observation through enabled components."""
        context = {"observation": observation}
        
        # Knowledge Graph processing
        if self.enabled_capabilities["use_knowledge_graph"] and self.knowledge_retriever:
            try:
                # Retrieve relevant knowledge
                kg_query = self._create_kg_query(observation)
                retrieved_knowledge = self.knowledge_retriever.retrieve(kg_query)
                context["knowledge"] = retrieved_knowledge
                
                # Update statistics
                self.stats.kg_queries += 1
                
            except Exception as e:
                self.logger.warning(f"KG retrieval failed: {e}")
                context["knowledge"] = []
        
        # Memory processing
        if self.enabled_capabilities["use_memory"]:
            try:
                # Retrieve relevant memories
                relevant_memories = self._retrieve_memories(observation)
                context["memories"] = relevant_memories
                
                # Store current observation in memory
                self._store_memory(observation)
                
                # Update statistics
                self.stats.memory_retrievals += 1
                
            except Exception as e:
                self.logger.warning(f"Memory processing failed: {e}")
                context["memories"] = []
        
        return context
    
    def _select_action(self, context: Dict[str, Any], available_actions: List[str]) -> str:
        """Select action using appropriate strategy."""
        
        # Enhanced reasoning
        if self.enabled_capabilities["use_enhanced_reasoning"]:
            return self._reasoning_based_action(context, available_actions)
        
        # RL-based action selection
        elif self.enabled_capabilities["use_rl"]:
            return self._rl_based_action(context, available_actions)
        
        # Knowledge-enhanced LLM
        elif self.enabled_capabilities["use_knowledge_graph"] or self.enabled_capabilities["use_memory"]:
            return self._knowledge_enhanced_action(context, available_actions)
        
        # Pure LLM baseline
        else:
            return self._llm_baseline_action(context, available_actions)
    
    def _reasoning_based_action(self, context: Dict[str, Any], available_actions: List[str]) -> str:
        """Select action using enhanced reasoning."""
        
        if self.react_planner:
            # Use ReAct planning
            reasoning_result = self.react_planner.plan(
                observation=context["observation"],
                available_actions=available_actions,
                context=context
            )
            
            self.stats.reasoning_iterations += reasoning_result.get("iterations", 1)
            return reasoning_result["action"]
        
        elif self.dodaf_reasoner:
            # Use DODAF reasoning
            reasoning_result = self.dodaf_reasoner.reason(
                observation=context["observation"],
                available_actions=available_actions,
                context=context
            )
            
            return reasoning_result["action"]
        
        else:
            # Fallback to knowledge-enhanced action
            return self._knowledge_enhanced_action(context, available_actions)
    
    def _rl_based_action(self, context: Dict[str, Any], available_actions: List[str]) -> str:
        """Select action using RL policy."""
        # RL implementation would go here
        # For now, fallback to reasoning-based action
        return self._reasoning_based_action(context, available_actions)
    
    def _knowledge_enhanced_action(self, context: Dict[str, Any], available_actions: List[str]) -> str:
        """Select action using knowledge-enhanced LLM."""
        
        # Build enhanced prompt with knowledge and memories
        prompt = self._build_enhanced_prompt(context, available_actions)
        
        # Get LLM response
        response = self._query_llm(prompt)
        
        # Extract action from response
        action = self._extract_action(response, available_actions)
        
        return action
    
    def _llm_baseline_action(self, context: Dict[str, Any], available_actions: List[str]) -> str:
        """Select action using pure LLM baseline."""
        
        # Build basic prompt
        prompt = self._build_basic_prompt(context["observation"], available_actions)
        
        # Get LLM response
        response = self._query_llm(prompt)
        
        # Extract action from response
        action = self._extract_action(response, available_actions)
        
        return action
    
    def _create_kg_query(self, observation: str) -> Dict[str, Any]:
        """Create knowledge graph query from observation."""
        # Simple keyword extraction for now
        keywords = observation.lower().split()
        return {
            "query_type": "keywords",
            "keywords": keywords[:5],  # Limit to top 5 keywords
            "max_results": 10
        }
    
    def _retrieve_memories(self, observation: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories."""
        if not hasattr(self, 'short_term_memory'):
            return []
        
        # Simple similarity-based retrieval
        relevant_memories = []
        obs_words = set(observation.lower().split())
        
        for memory in self.short_term_memory[-10:]:  # Check recent memories
            memory_words = set(memory.get("content", "").lower().split())
            overlap = len(obs_words.intersection(memory_words))
            
            if overlap > 0:
                relevant_memories.append({
                    **memory,
                    "relevance_score": overlap / len(obs_words.union(memory_words))
                })
        
        # Sort by relevance and return top 5
        relevant_memories.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant_memories[:5]
    
    def _store_memory(self, observation: str):
        """Store observation in memory."""
        if not hasattr(self, 'short_term_memory'):
            return
        
        memory_entry = {
            "content": observation,
            "timestamp": time.time(),
            "episode": self.current_episode,
            "step": self.current_step
        }
        
        self.short_term_memory.append(memory_entry)
        
        # Maintain memory size limit
        max_short_term = 50
        if len(self.short_term_memory) > max_short_term:
            # Move oldest to medium-term memory
            if hasattr(self, 'medium_term_memory'):
                self.medium_term_memory.extend(self.short_term_memory[:-max_short_term])
            self.short_term_memory = self.short_term_memory[-max_short_term:]
    
    def _build_enhanced_prompt(self, context: Dict[str, Any], available_actions: List[str]) -> str:
        """Build enhanced prompt with knowledge and memories."""
        prompt_parts = []
        
        # Basic observation
        prompt_parts.append(f"Current situation: {context['observation']}")
        
        # Add knowledge if available
        if context.get("knowledge"):
            knowledge_text = "\n".join([str(k) for k in context["knowledge"][:5]])
            prompt_parts.append(f"Relevant knowledge:\n{knowledge_text}")
        
        # Add memories if available
        if context.get("memories"):
            memory_text = "\n".join([m.get("content", "") for m in context["memories"][:3]])
            prompt_parts.append(f"Relevant past experiences:\n{memory_text}")
        
        # Available actions
        actions_text = ", ".join(available_actions)
        prompt_parts.append(f"Available actions: {actions_text}")
        
        # Instruction
        prompt_parts.append("Choose the best action and respond with just the action name.")
        
        return "\n\n".join(prompt_parts)
    
    def _build_basic_prompt(self, observation: str, available_actions: List[str]) -> str:
        """Build basic prompt for LLM baseline."""
        actions_text = ", ".join(available_actions)
        return (
            f"Current situation: {observation}\n\n"
            f"Available actions: {actions_text}\n\n"
            f"Choose the best action and respond with just the action name."
        )
    
    def _query_llm(self, prompt: str) -> str:
        """Query the LLM with the given prompt."""
        # Mock LLM response for now
        # In real implementation, this would call OpenAI API or local model
        return "examine room"  # Placeholder response
    
    def _extract_action(self, response: str, available_actions: List[str]) -> str:
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
        
        # Fallback to first available action
        return available_actions[0] if available_actions else "wait"
    
    def _post_process_action(self, action: str, context: Dict[str, Any]):
        """Post-process action and update knowledge if needed."""
        
        # Update knowledge graph if enabled
        if (self.enabled_capabilities["use_knowledge_graph"] and 
            self.knowledge_updater and 
            context.get("knowledge")):
            
            try:
                # Create update based on action and context
                update_data = {
                    "action": action,
                    "observation": context["observation"],
                    "timestamp": time.time()
                }
                
                self.knowledge_updater.update(update_data)
                
            except Exception as e:
                self.logger.warning(f"KG update failed: {e}")
    
    def _reset_agent_state(self):
        """Reset agent-specific state."""
        self.conversation_history = []
        self.current_context = {}
        
        # Reset component states
        if hasattr(self, 'short_term_memory'):
            # Move short-term to medium-term memory
            if hasattr(self, 'medium_term_memory'):
                self.medium_term_memory.extend(self.short_term_memory)
            self.short_term_memory = []
    
    def _cleanup_components(self):
        """Clean up agent-specific components."""
        if self.graph_manager:
            self.graph_manager.cleanup()
        
        # Clear memory
        if hasattr(self, 'short_term_memory'):
            self.short_term_memory.clear()
        if hasattr(self, 'medium_term_memory'):
            self.medium_term_memory.clear()
    
    def _get_checkpoint_data(self) -> Dict[str, Any]:
        """Get agent-specific checkpoint data."""
        return {
            "conversation_history": self.conversation_history,
            "short_term_memory": getattr(self, 'short_term_memory', []),
            "medium_term_memory": getattr(self, 'medium_term_memory', []),
        }
    
    def _load_checkpoint_data(self, checkpoint: Dict[str, Any]):
        """Load agent-specific checkpoint data."""
        self.conversation_history = checkpoint.get("conversation_history", [])

        if hasattr(self, 'short_term_memory'):
            self.short_term_memory = checkpoint.get("short_term_memory", [])
        if hasattr(self, 'medium_term_memory'):
            self.medium_term_memory = checkpoint.get("medium_term_memory", [])

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        # Get base stats from parent class
        base_stats = self.get_statistics()

        # Add unified agent specific stats
        unified_stats = {
            "capabilities": self.enabled_capabilities,
            "conversation_turns": len(self.conversation_history),
            "kg_queries": getattr(self, '_kg_query_count', 0),
            "memory_retrievals": getattr(self, '_memory_retrieval_count', 0),
            "reasoning_iterations": getattr(self, '_reasoning_iteration_count', 0)
        }

        # Merge stats
        base_stats.update(unified_stats)
        return base_stats
