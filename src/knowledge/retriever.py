"""
Knowledge Retriever for KGRL research framework.

Handles intelligent retrieval of knowledge from various sources including
knowledge graphs, vector databases, and text corpora.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from abc import ABC, abstractmethod


class KnowledgeRetriever:
    """
    Main knowledge retriever that coordinates different retrieval strategies.
    
    Supports multiple retrieval methods:
    - Semantic similarity search
    - Keyword-based retrieval  
    - Graph traversal queries
    - Hybrid retrieval strategies
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the knowledge retriever."""
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Retrieval configuration
        self.max_retrieved_docs = config.get("max_retrieved_docs", 5)
        self.similarity_threshold = config.get("similarity_threshold", 0.7)
        self.use_hybrid_retrieval = config.get("use_hybrid_retrieval", True)
        
        # Initialize retrieval strategies
        self.strategies = {}
        self._initialize_strategies()
        
        self.logger.info("Knowledge retriever initialized")
    
    def _initialize_strategies(self):
        """Initialize different retrieval strategies."""
        strategy_configs = self.config.get("strategies", {})
        
        # Semantic retrieval
        if strategy_configs.get("semantic", {}).get("enabled", True):
            self.strategies["semantic"] = SemanticRetriever(
                strategy_configs.get("semantic", {})
            )
        
        # Keyword retrieval
        if strategy_configs.get("keyword", {}).get("enabled", True):
            self.strategies["keyword"] = KeywordRetriever(
                strategy_configs.get("keyword", {})
            )
        
        # Graph retrieval
        if strategy_configs.get("graph", {}).get("enabled", True):
            self.strategies["graph"] = GraphRetriever(
                strategy_configs.get("graph", {})
            )
    
    def retrieve(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant knowledge for the given query.
        
        Args:
            query: Search query string
            context: Optional context information
            
        Returns:
            List of retrieved knowledge items with relevance scores
        """
        try:
            if self.use_hybrid_retrieval:
                return self._hybrid_retrieve(query, context)
            else:
                return self._single_strategy_retrieve(query, context)
                
        except Exception as e:
            self.logger.error(f"Error in knowledge retrieval: {e}")
            return []
    
    def _hybrid_retrieve(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Perform hybrid retrieval using multiple strategies."""
        all_results = []
        
        # Collect results from all strategies
        for strategy_name, strategy in self.strategies.items():
            try:
                results = strategy.retrieve(query, context)
                # Add strategy information to results
                for result in results:
                    result["retrieval_strategy"] = strategy_name
                all_results.extend(results)
            except Exception as e:
                self.logger.warning(f"Strategy {strategy_name} failed: {e}")
        
        # Merge and rank results
        merged_results = self._merge_and_rank_results(all_results)
        
        # Apply threshold and limit
        filtered_results = [
            result for result in merged_results 
            if result.get("relevance", 0) >= self.similarity_threshold
        ]
        
        return filtered_results[:self.max_retrieved_docs]
    
    def _single_strategy_retrieve(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve using a single strategy (semantic by default)."""
        if "semantic" in self.strategies:
            return self.strategies["semantic"].retrieve(query, context)
        elif self.strategies:
            # Use first available strategy
            strategy_name = list(self.strategies.keys())[0]
            return self.strategies[strategy_name].retrieve(query, context)
        else:
            return []
    
    def _merge_and_rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge results from different strategies and rank by relevance."""
        # Group by content/id to avoid duplicates
        content_groups = {}
        
        for result in results:
            content_key = result.get("id", result.get("content", ""))
            if content_key not in content_groups:
                content_groups[content_key] = []
            content_groups[content_key].append(result)
        
        # Merge duplicate results
        merged_results = []
        for content_key, group in content_groups.items():
            if len(group) == 1:
                merged_results.append(group[0])
            else:
                # Merge multiple results for same content
                merged_result = self._merge_duplicate_results(group)
                merged_results.append(merged_result)
        
        # Sort by relevance score
        merged_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        return merged_results
    
    def _merge_duplicate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple results for the same content."""
        # Take the result with highest relevance as base
        base_result = max(results, key=lambda x: x.get("relevance", 0))
        
        # Combine strategies
        strategies = [r.get("retrieval_strategy", "unknown") for r in results]
        base_result["retrieval_strategy"] = strategies
        
        # Average relevance scores
        relevances = [r.get("relevance", 0) for r in results]
        base_result["relevance"] = sum(relevances) / len(relevances)
        
        return base_result
    
    def cleanup(self):
        """Clean up retriever resources."""
        for strategy in self.strategies.values():
            if hasattr(strategy, 'cleanup'):
                strategy.cleanup()


class RetrievalStrategy(ABC):
    """Abstract base class for retrieval strategies."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def retrieve(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve knowledge using this strategy."""
        pass


class SemanticRetriever(RetrievalStrategy):
    """Semantic similarity-based retrieval."""
    
    def retrieve(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve using semantic similarity."""
        # Mock implementation for now
        mock_results = [
            {
                "id": "semantic_1",
                "content": f"Semantic knowledge related to: {query}",
                "relevance": 0.9,
                "source": "semantic_db"
            },
            {
                "id": "semantic_2", 
                "content": f"Additional semantic context for: {query}",
                "relevance": 0.8,
                "source": "semantic_db"
            }
        ]
        
        return mock_results


class KeywordRetriever(RetrievalStrategy):
    """Keyword-based retrieval."""
    
    def retrieve(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve using keyword matching."""
        # Mock implementation for now
        keywords = query.lower().split()
        
        mock_results = []
        for i, keyword in enumerate(keywords[:2]):  # Limit to 2 keywords
            mock_results.append({
                "id": f"keyword_{i}",
                "content": f"Keyword match for '{keyword}': relevant information",
                "relevance": 0.7 - i * 0.1,
                "source": "keyword_index",
                "matched_keyword": keyword
            })
        
        return mock_results


class GraphRetriever(RetrievalStrategy):
    """Knowledge graph traversal-based retrieval."""
    
    def retrieve(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve using graph traversal."""
        # Mock implementation for now
        mock_results = [
            {
                "id": "graph_1",
                "content": f"Graph knowledge about: {query}",
                "relevance": 0.85,
                "source": "knowledge_graph",
                "graph_path": ["entity1", "relation", "entity2"]
            }
        ]
        
        return mock_results
