"""
KG检索专门智能体
专门负责知识图谱的查询、检索和知识管理
"""

from typing import List, Dict, Any, Optional, Tuple
import time
import re

from .kg_agent import KGAgent
from ..knowledge.kg_builder import KGFact
from ..utils.logger import get_logger


class QueryAgent(KGAgent):
    """知识图谱检索专门智能体"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        """
        初始化QueryAgent
        
        Args:
            agent_id: 智能体ID
            config: 配置参数
        """
        super().__init__(agent_id, config)
        self.logger = get_logger(f"QueryAgent_{agent_id}")
        
        # 查询配置
        self.default_query_type = config.get('default_query_type', 'keywords')
        self.enable_query_expansion = config.get('enable_query_expansion', True)
        self.enable_result_ranking = config.get('enable_result_ranking', True)
        
        # 查询历史和缓存
        self.query_history = []
        self.query_cache = {}
        self.cache_enabled = config.get('enable_cache', True)
        self.cache_ttl = config.get('cache_ttl', 300)  # 5分钟缓存
        
        self.logger.info(f"Initialized QueryAgent with default_query_type: {self.default_query_type}")
    
    def act(self, observation: str, available_actions: List[str] = None, **kwargs) -> str:
        """
        QueryAgent的act方法主要用于演示，实际使用中主要调用query方法
        
        Args:
            observation: 环境观测
            available_actions: 可用动作列表
            
        Returns:
            查询结果的字符串表示
        """
        # 从观测中提取查询
        query_info = self.extract_query_from_observation(observation)
        
        # 执行查询
        results = self.query(query_info['query'], query_info['query_type'])
        
        # 返回格式化结果
        return self._format_query_results(results)
    
    def query(self, query: str, query_type: str = None, max_results: int = None, **kwargs) -> List[KGFact]:
        """
        执行知识图谱查询
        
        Args:
            query: 查询内容
            query_type: 查询类型
            max_results: 最大结果数
            **kwargs: 其他参数
            
        Returns:
            查询结果列表
        """
        if query_type is None:
            query_type = self.default_query_type
        
        # 检查缓存
        cache_key = f"{query_type}:{query}:{max_results}"
        if self.cache_enabled and cache_key in self.query_cache:
            cache_entry = self.query_cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                self.logger.debug(f"Cache hit for query: {cache_key}")
                return cache_entry['results']
        
        # 查询扩展
        if self.enable_query_expansion:
            expanded_queries = self._expand_query(query, query_type)
        else:
            expanded_queries = [query]
        
        # 执行查询
        all_results = []
        for expanded_query in expanded_queries:
            results = self.query_kg(query_type, expanded_query, max_results, **kwargs)
            all_results.extend(results)
        
        # 去重和排序
        unique_results = self._deduplicate_results(all_results)
        if self.enable_result_ranking:
            ranked_results = self._rank_results(unique_results, query)
        else:
            ranked_results = unique_results
        
        # 限制结果数量
        if max_results:
            ranked_results = ranked_results[:max_results]
        
        # 缓存结果
        if self.cache_enabled:
            self.query_cache[cache_key] = {
                'results': ranked_results,
                'timestamp': time.time()
            }
        
        # 记录查询历史
        self.query_history.append({
            'query': query,
            'query_type': query_type,
            'results_count': len(ranked_results),
            'timestamp': time.time()
        })
        
        self.logger.info(f"Query completed: '{query}' ({query_type}) -> {len(ranked_results)} results")
        
        return ranked_results
    
    def multi_query(self, queries: List[Tuple[str, str]], max_results_per_query: int = None) -> Dict[str, List[KGFact]]:
        """
        执行多个查询
        
        Args:
            queries: 查询列表，每个元素为(query, query_type)
            max_results_per_query: 每个查询的最大结果数
            
        Returns:
            查询结果字典，键为查询字符串
        """
        results = {}
        for query, query_type in queries:
            results[query] = self.query(query, query_type, max_results_per_query)
        return results
    
    def extract_query_from_observation(self, observation: str) -> Dict[str, str]:
        """
        从观测中提取查询信息
        
        Args:
            observation: 环境观测
            
        Returns:
            包含query和query_type的字典
        """
        # 检查是否包含DODAF查询模式
        dodaf_pattern = r'(DO|DA|F):(\w+)'
        dodaf_match = re.search(dodaf_pattern, observation)
        
        if dodaf_match:
            return {
                'query': f"{dodaf_match.group(1)}:{dodaf_match.group(2)}",
                'query_type': 'dodaf'
            }
        
        # 检查是否包含实体查询模式
        entity_pattern = r'entity:(\w+)'
        entity_match = re.search(entity_pattern, observation)
        
        if entity_match:
            return {
                'query': entity_match.group(1),
                'query_type': 'entity'
            }
        
        # 默认使用关键词查询
        keywords = self._extract_keywords(observation)
        return {
            'query': keywords,
            'query_type': 'keywords'
        }
    
    def _expand_query(self, query: str, query_type: str) -> List[str]:
        """
        扩展查询以提高召回率
        
        Args:
            query: 原始查询
            query_type: 查询类型
            
        Returns:
            扩展后的查询列表
        """
        expanded = [query]
        
        if query_type == 'keywords':
            # 对关键词查询进行同义词扩展
            words = query.split()
            if len(words) > 1:
                # 添加单个关键词查询
                expanded.extend(words)
        
        elif query_type == 'dodaf':
            # 对DODAF查询进行相关类型扩展
            if query.startswith('DO:'):
                # 动作查询可能需要条件信息
                entity = query.split(':', 1)[1]
                expanded.append(f"DA:{entity}")
            elif query.startswith('DA:'):
                # 条件查询可能需要动作信息
                entity = query.split(':', 1)[1]
                expanded.append(f"DO:{entity}")
        
        return expanded
    
    def _deduplicate_results(self, results: List[KGFact]) -> List[KGFact]:
        """
        去除重复的查询结果
        
        Args:
            results: 原始结果列表
            
        Returns:
            去重后的结果列表
        """
        seen = set()
        unique_results = []
        
        for fact in results:
            fact_key = (fact.subject, fact.predicate, fact.object)
            if fact_key not in seen:
                seen.add(fact_key)
                unique_results.append(fact)
        
        return unique_results
    
    def _rank_results(self, results: List[KGFact], query: str) -> List[KGFact]:
        """
        对查询结果进行排序
        
        Args:
            results: 查询结果列表
            query: 原始查询
            
        Returns:
            排序后的结果列表
        """
        # 简单的相关性评分
        def relevance_score(fact: KGFact) -> float:
            score = 0.0
            query_lower = query.lower()
            
            # 检查查询词在事实中的出现
            fact_text = f"{fact.subject} {fact.predicate} {fact.object}".lower()
            for word in query_lower.split():
                if word in fact_text:
                    score += 1.0
            
            # DODAF类型加权
            if hasattr(fact, 'dodaf_type') and fact.dodaf_type:
                if fact.dodaf_type in query:
                    score += 2.0
            
            # 置信度加权
            if hasattr(fact, 'confidence'):
                score *= fact.confidence
            
            return score
        
        # 按相关性评分排序
        return sorted(results, key=relevance_score, reverse=True)
    
    def _format_query_results(self, results: List[KGFact]) -> str:
        """
        格式化查询结果为字符串
        
        Args:
            results: 查询结果列表
            
        Returns:
            格式化的结果字符串
        """
        if not results:
            return "No knowledge found for the query."
        
        formatted_results = []
        for i, fact in enumerate(results, 1):
            if hasattr(fact, 'dodaf_type') and fact.dodaf_type:
                formatted_results.append(f"{i}. [{fact.dodaf_type}] {fact.subject} {fact.predicate} {fact.object}")
            else:
                formatted_results.append(f"{i}. {fact.subject} {fact.predicate} {fact.object}")
        
        return "\n".join(formatted_results)
    
    def get_query_history(self) -> List[Dict[str, Any]]:
        """获取查询历史"""
        return self.query_history.copy()
    
    def clear_cache(self):
        """清空查询缓存"""
        self.query_cache.clear()
        self.logger.info("Query cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "cache_size": len(self.query_cache),
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl
        }
