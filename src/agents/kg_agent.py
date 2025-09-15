"""
知识图谱增强智能体基类
为所有使用知识图谱的智能体提供统一的基础功能
"""

from abc import abstractmethod
from typing import List, Dict, Any, Optional
import time

from .base_agent import BaseAgent
from ..knowledge.kg_retriever import KnowledgeGraphRetriever
from ..knowledge.kg_builder import KGFact
from ..utils.logger import get_logger


class KGAgent(BaseAgent):
    """知识图谱增强智能体基类"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        """
        初始化KG智能体
        
        Args:
            agent_id: 智能体ID
            config: 配置参数
        """
        super().__init__(agent_id, config)
        self.logger = get_logger(f"KGAgent_{agent_id}")
        
        # KG相关配置
        self.use_knowledge_graph = config.get('use_knowledge_graph', True)
        self.max_kg_facts = config.get('max_kg_facts', 5)
        self.kg_retriever: Optional[KnowledgeGraphRetriever] = None
        
        # KG统计信息
        self.kg_queries = 0
        self.kg_hits = 0
        self.kg_response_times = []
        
        self.logger.info(f"Initialized KGAgent: use_kg={self.use_knowledge_graph}")
    
    def set_knowledge_retriever(self, retriever: KnowledgeGraphRetriever):
        """
        设置知识检索器
        
        Args:
            retriever: 知识图谱检索器
        """
        self.kg_retriever = retriever
        self.logger.info(f"Knowledge retriever set: {retriever.retriever_id}")
    
    def query_kg(self, query_type: str, query: str, max_results: int = None, **kwargs) -> List[KGFact]:
        """
        统一的知识图谱查询接口
        
        Args:
            query_type: 查询类型 ('keywords', 'dodaf', 'entity')
            query: 查询内容
            max_results: 最大结果数
            **kwargs: 其他参数
            
        Returns:
            查询到的知识事实列表
        """
        if not self.use_knowledge_graph or not self.kg_retriever:
            return []
        
        start_time = time.time()
        self.kg_queries += 1
        
        try:
            # 使用默认max_results如果未指定
            if max_results is None:
                max_results = self.max_kg_facts
            
            # 执行查询
            results = self.kg_retriever.query_kg(query_type, query, max_results=max_results, **kwargs)
            
            # 记录统计
            if results:
                self.kg_hits += 1
            
            query_time = time.time() - start_time
            self.kg_response_times.append(query_time)
            
            self.logger.debug(f"KG query: {query_type}='{query}' -> {len(results)} results ({query_time:.3f}s)")
            
            return results
            
        except Exception as e:
            self.logger.error(f"KG query failed: {e}")
            return []
    
    def get_kg_stats(self) -> Dict[str, Any]:
        """
        获取KG使用统计信息
        
        Returns:
            统计信息字典
        """
        avg_response_time = sum(self.kg_response_times) / len(self.kg_response_times) if self.kg_response_times else 0
        hit_rate = self.kg_hits / self.kg_queries if self.kg_queries > 0 else 0
        
        return {
            "kg_queries": self.kg_queries,
            "kg_hits": self.kg_hits,
            "kg_hit_rate": hit_rate,
            "avg_kg_response_time": avg_response_time,
            "total_kg_response_time": sum(self.kg_response_times)
        }
    
    def reset_kg_stats(self):
        """重置KG统计信息"""
        self.kg_queries = 0
        self.kg_hits = 0
        self.kg_response_times = []
    
    def reset(self):
        """重置智能体状态"""
        super().reset()
        self.reset_kg_stats()
    
    @abstractmethod
    def act(self, observation: str, available_actions: List[str] = None, **kwargs) -> str:
        """
        根据观测选择动作（子类必须实现）
        
        Args:
            observation: 环境观测
            available_actions: 可用动作列表
            **kwargs: 其他参数
            
        Returns:
            选择的动作
        """
        pass
    
    def _extract_keywords(self, text: str) -> str:
        """
        从文本中提取关键词用于KG查询
        
        Args:
            text: 输入文本
            
        Returns:
            关键词字符串
        """
        # 简单的关键词提取逻辑
        import re
        
        # 移除常见停用词
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'you', 'i', 'we', 'they', 'he', 'she', 'it'}
        
        # 提取单词
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 过滤停用词和短词
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # 返回前5个关键词
        return ' '.join(keywords[:5])
    
    def _format_kg_facts(self, facts: List[KGFact]) -> str:
        """
        格式化KG事实为可读文本
        
        Args:
            facts: KG事实列表
            
        Returns:
            格式化的文本
        """
        if not facts:
            return "No relevant knowledge found."
        
        formatted = []
        for fact in facts:
            if hasattr(fact, 'dodaf_type') and fact.dodaf_type:
                formatted.append(f"[{fact.dodaf_type}] {fact.subject} {fact.predicate} {fact.object}")
            else:
                formatted.append(f"{fact.subject} {fact.predicate} {fact.object}")
        
        return "\n".join(formatted)
    
    def get_config(self) -> Dict[str, Any]:
        """获取智能体配置"""
        config = super().get_config()
        config.update({
            "use_knowledge_graph": self.use_knowledge_graph,
            "max_kg_facts": self.max_kg_facts,
            "kg_stats": self.get_kg_stats()
        })
        return config
