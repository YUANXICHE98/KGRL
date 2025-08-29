"""
简化的RAG Agent
专注于核心功能，去除复杂的ReAct推理
"""

import time
from typing import List, Dict, Any, Optional
from .baseline_agent import BaselineAgent
from ..knowledge.kg_retriever import KnowledgeGraphRetriever
from ..utils.logger import get_logger


class SimpleRAGAgent(BaselineAgent):
    """简化的RAG增强智能体"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        """
        初始化简化RAG Agent
        
        Args:
            agent_id: Agent标识符
            config: 配置字典
        """
        super().__init__(agent_id, config)
        
        # RAG特定配置
        self.use_knowledge_graph = config.get('use_knowledge_graph', True)
        self.max_kg_facts = config.get('max_kg_facts', 3)  # 减少到3个
        self.kg_retrieval_method = config.get('kg_retrieval_method', 'keywords')  # 使用更简单的关键词检索
        
        # 知识图谱检索器
        self.kg_retriever: Optional[KnowledgeGraphRetriever] = None
        
        # 统计信息
        self.kg_queries = 0
        self.kg_hits = 0
        
        self.logger.info(f"Initialized Simple RAG Agent: KG={self.use_knowledge_graph}")
    
    def set_knowledge_retriever(self, kg_retriever: KnowledgeGraphRetriever):
        """设置知识图谱检索器"""
        self.kg_retriever = kg_retriever
        self.logger.info("Knowledge retriever set successfully")
    
    def retrieve_relevant_knowledge(self, observation: str) -> List[str]:
        """
        检索相关知识并转换为简单字符串列表
        
        Args:
            observation: 环境观察
            
        Returns:
            相关知识的字符串列表
        """
        if not self.use_knowledge_graph or not self.kg_retriever:
            return []
        
        self.kg_queries += 1
        
        try:
            # 提取关键词
            keywords = self._extract_keywords(observation)
            
            # 使用关键词检索（更简单可靠）
            if self.kg_retrieval_method == 'keywords':
                results = self.kg_retriever.retrieve_by_keywords(keywords)
            else:
                results = self.kg_retriever.retrieve_by_similarity(keywords, max_results=self.max_kg_facts)
                results = [fact for fact, score in results if score > 0.1]
            
            # 限制结果数量
            results = results[:self.max_kg_facts]
            
            if results:
                self.kg_hits += 1
            
            # 转换为简单字符串
            knowledge_strings = []
            for fact in results:
                if hasattr(fact, 'subject'):  # KGFact对象
                    knowledge_strings.append(f"{fact.subject} {fact.predicate} {fact.object}")
                elif isinstance(fact, tuple) and len(fact) >= 3:  # 元组格式
                    knowledge_strings.append(f"{fact[0]} {fact[1]} {fact[2]}")
            
            self.logger.debug(f"Retrieved {len(knowledge_strings)} knowledge facts")
            return knowledge_strings
            
        except Exception as e:
            self.logger.error(f"Knowledge retrieval failed: {e}")
            return []
    
    def _extract_keywords(self, text: str) -> str:
        """从文本中提取关键词"""
        # 简化的关键词提取
        important_words = ['kitchen', 'bedroom', 'living', 'fridge', 'chest', 'key', 'apple', 'book', 'take', 'open', 'go']
        
        text_lower = text.lower()
        keywords = []
        for word in important_words:
            if word in text_lower:
                keywords.append(word)
        
        return " ".join(keywords) if keywords else text
    
    def build_simple_prompt(self, observation: str, available_actions: List[str], 
                           knowledge: List[str]) -> str:
        """
        构建简化的知识增强prompt
        
        Args:
            observation: 环境观察
            available_actions: 可用动作
            knowledge: 相关知识列表
            
        Returns:
            简化的prompt
        """
        prompt_parts = []
        
        # 基础任务描述
        prompt_parts.append("You are playing a text adventure game. Your goal is to find the key and open the chest in the bedroom.")
        
        # 当前观察
        prompt_parts.append(f"\nCurrent situation: {observation}")
        
        # 添加相关知识（如果有）
        if knowledge:
            prompt_parts.append(f"\nRelevant facts: {', '.join(knowledge)}")
        
        # 可用动作
        prompt_parts.append(f"\nAvailable actions: {available_actions}")
        
        # 简单的决策指导
        prompt_parts.append("\nChoose the best action to progress towards your goal. Respond with only the action name.")
        
        return "\n".join(prompt_parts)
    
    def act(self, observation: str, available_actions: List[str]) -> str:
        """
        基于观察和知识图谱做出决策（简化版）
        
        Args:
            observation: 环境观察
            available_actions: 可用动作列表
            
        Returns:
            选择的动作
        """
        start_time = time.time()
        
        try:
            # 1. 检索相关知识
            knowledge = self.retrieve_relevant_knowledge(observation)
            
            # 2. 构建简化prompt
            prompt = self.build_simple_prompt(observation, available_actions, knowledge)
            
            # 3. 调用LLM（使用父类的方法）
            response = self._generate_api_response(prompt)
            
            # 4. 简单解析响应
            chosen_action = response.strip()
            
            # 5. 验证动作有效性
            if chosen_action not in available_actions:
                # 尝试模糊匹配
                for action in available_actions:
                    if chosen_action.lower() in action.lower() or action.lower() in chosen_action.lower():
                        chosen_action = action
                        break
                else:
                    # 如果仍然无效，选择第一个可用动作
                    chosen_action = available_actions[0] if available_actions else "look"
                    self.logger.warning(f"Invalid action, fallback to: {chosen_action}")
            
            # 记录统计信息
            self.total_actions += 1
            self.api_calls += 1
            self.api_response_times.append(time.time() - start_time)
            
            self.logger.info(f"Simple RAG Agent action: {chosen_action} "
                           f"(KG facts: {len(knowledge)}, "
                           f"Time: {time.time() - start_time:.2f}s)")
            
            return chosen_action
            
        except Exception as e:
            self.logger.error(f"Simple RAG Agent decision failed: {e}")
            # 回退到简单策略
            return available_actions[0] if available_actions else "look"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取Agent统计信息"""
        base_stats = super().get_stats()
        
        # 添加RAG特定统计
        rag_stats = {
            'kg_queries': self.kg_queries,
            'kg_hits': self.kg_hits,
            'kg_hit_rate': self.kg_hits / self.kg_queries if self.kg_queries > 0 else 0,
            'use_knowledge_graph': self.use_knowledge_graph
        }
        
        base_stats.update(rag_stats)
        return base_stats
    
    def reset(self):
        """重置Agent状态"""
        super().reset()
        self.kg_queries = 0
        self.kg_hits = 0
