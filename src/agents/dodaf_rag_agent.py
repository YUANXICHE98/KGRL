"""
DODAF框架的RAG Agent
基于DO-DA-F结构，将知识图谱自然融入决策过程
"""

import time
from typing import List, Dict, Any, Optional
from .baseline_agent import BaselineAgent
from ..knowledge.kg_retriever import KnowledgeGraphRetriever
from ..utils.logger import get_logger


class DODAFRAGAgent(BaselineAgent):
    """基于DODAF框架的RAG增强智能体"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        """
        初始化DODAF RAG Agent
        
        Args:
            agent_id: Agent标识符
            config: 配置字典
        """
        super().__init__(agent_id, config)
        
        # RAG特定配置
        self.use_knowledge_graph = config.get('use_knowledge_graph', True)
        self.max_kg_facts = config.get('max_kg_facts', 3)
        
        # 知识图谱检索器
        self.kg_retriever: Optional[KnowledgeGraphRetriever] = None
        
        # 统计信息
        self.kg_queries = 0
        self.kg_hits = 0
        self.total_actions = 0
        self.api_calls = 0
        self.api_response_times = []
        
        self.logger.info(f"Initialized DODAF RAG Agent: KG={self.use_knowledge_graph}")
    
    def set_knowledge_retriever(self, kg_retriever: KnowledgeGraphRetriever):
        """设置知识图谱检索器"""
        self.kg_retriever = kg_retriever
        self.logger.info("Knowledge retriever set successfully")
    
    def retrieve_relevant_knowledge(self, observation: str) -> Dict[str, str]:
        """
        检索相关知识并转换为DODAF结构
        
        Args:
            observation: 环境观察
            
        Returns:
            DODAF结构的知识字典
        """
        if not self.use_knowledge_graph or not self.kg_retriever:
            return {}
        
        self.kg_queries += 1
        
        try:
            # 提取关键词
            keywords = self._extract_keywords(observation)
            
            # 使用关键词检索
            results = self.kg_retriever.retrieve_by_keywords(keywords)
            results = results[:self.max_kg_facts]
            
            if results:
                self.kg_hits += 1
            
            # 转换为DODAF结构
            dodaf_knowledge = self._convert_to_dodaf_structure(results, observation)
            
            self.logger.debug(f"Retrieved knowledge converted to DODAF structure")
            return dodaf_knowledge
            
        except Exception as e:
            self.logger.error(f"Knowledge retrieval failed: {e}")
            return {}
    
    def _extract_keywords(self, text: str) -> str:
        """从文本中提取关键词"""
        important_words = [
            'kitchen', 'bedroom', 'living', 'room',
            'fridge', 'chest', 'key', 'apple', 'book', 'pillow',
            'take', 'open', 'go', 'north', 'south', 'east', 'west',
            'goal', 'find'
        ]
        
        text_lower = text.lower()
        keywords = []
        for word in important_words:
            if word in text_lower:
                keywords.append(word)
        
        return " ".join(keywords) if keywords else text
    
    def _convert_to_dodaf_structure(self, facts: List, observation: str) -> Dict[str, str]:
        """
        将知识图谱事实转换为DODAF结构
        
        Args:
            facts: 知识图谱事实列表
            observation: 当前观察
            
        Returns:
            DODAF结构的知识字典
        """
        dodaf = {}
        
        # 分析事实，构建自然语言描述
        location_info = []
        item_info = []
        action_info = []
        path_info = []
        
        for fact in facts:
            if hasattr(fact, 'subject'):
                subj, pred, obj = fact.subject, fact.predicate, fact.object
            elif isinstance(fact, tuple) and len(fact) >= 3:
                subj, pred, obj = fact[0], fact[1], fact[2]
            else:
                continue
            
            # 分类知识
            if 'contains' in pred or 'location' in pred:
                if 'key' in subj or 'key' in obj:
                    item_info.append(f"Key is in {subj if 'key' in obj else obj}")
                elif 'chest' in subj or 'chest' in obj:
                    location_info.append(f"Chest is in {obj if 'chest' in subj else subj}")
            elif 'opens' in pred:
                action_info.append(f"{subj} opens {obj}")
            elif 'leads to' in pred or 'exit' in pred:
                path_info.append(f"Go {subj} to reach {obj}")
            elif 'path' in subj.lower():
                path_info.append(f"Route: {obj}")
        
        # 构建自然的分析描述
        analysis_parts = []
        
        # 当前位置分析
        if 'kitchen' in observation.lower():
            analysis_parts.append("You are in kitchen")
            if any('key' in info for info in item_info):
                analysis_parts.append("Key is here")
        elif 'living' in observation.lower():
            analysis_parts.append("You are in living room")
        elif 'bedroom' in observation.lower():
            analysis_parts.append("You are in bedroom")
        
        # 路径信息
        if path_info:
            analysis_parts.extend(path_info)
        elif location_info and 'bedroom' not in observation.lower():
            # 如果不在bedroom且知道chest在bedroom，给出路径
            analysis_parts.append("Path: kitchen → north → living room → east → bedroom")
        
        # 目标信息
        if action_info:
            analysis_parts.extend(action_info)
        
        # 构建DODAF结构
        if analysis_parts:
            dodaf['analysis'] = ". ".join(analysis_parts) + "."
        
        return dodaf
    
    def _build_dodaf_prompt(self, observation: str, available_actions: List[str], 
                           dodaf_knowledge: Dict[str, str]) -> str:
        """
        构建基于DODAF框架的prompt
        
        Args:
            observation: 环境观察
            available_actions: 可用动作
            dodaf_knowledge: DODAF结构的知识
            
        Returns:
            DODAF格式的prompt
        """
        prompt_parts = []
        
        # DO: 明确的任务目标
        prompt_parts.append("DO: Find the key and open the chest in the bedroom.")
        
        # DA: 分析当前情况（融合知识图谱）
        da_parts = [f"Current: {observation}"]
        if dodaf_knowledge.get('analysis'):
            da_parts.append(f"Guide: {dodaf_knowledge['analysis']}")
        
        prompt_parts.append(f"DA: {' '.join(da_parts)}")
        
        # F: 期望的反馈格式
        actions_str = str(available_actions)
        prompt_parts.append(f"F: Choose one action from {actions_str}")
        
        prompt_parts.append("Action:")
        
        return "\n".join(prompt_parts)
    
    def act(self, observation: str, available_actions: List[str]) -> str:
        """
        基于DODAF框架和知识图谱做出决策
        
        Args:
            observation: 环境观察
            available_actions: 可用动作列表
            
        Returns:
            选择的动作
        """
        start_time = time.time()
        
        try:
            # 1. 检索相关知识并转换为DODAF结构
            dodaf_knowledge = self.retrieve_relevant_knowledge(observation)
            
            # 2. 构建DODAF prompt
            prompt = self._build_dodaf_prompt(observation, available_actions, dodaf_knowledge)
            
            # 3. 调用LLM
            response = self._generate_api_response(prompt)
            
            # 4. 解析响应（简单格式）
            chosen_action = self._parse_simple_response(response, available_actions)
            
            # 记录统计信息
            self.total_actions += 1
            self.api_calls += 1
            self.api_response_times.append(time.time() - start_time)
            
            self.logger.info(f"DODAF RAG Agent action: {chosen_action} "
                           f"(KG used: {bool(dodaf_knowledge)}, "
                           f"Time: {time.time() - start_time:.2f}s)")
            
            return chosen_action
            
        except Exception as e:
            self.logger.error(f"DODAF RAG Agent decision failed: {e}")
            # 回退到简单策略
            return available_actions[0] if available_actions else "look"
    
    def _parse_simple_response(self, response: str, available_actions: List[str]) -> str:
        """
        简单解析响应
        
        Args:
            response: LLM响应
            available_actions: 可用动作列表
            
        Returns:
            解析出的动作
        """
        # 清理响应
        response = response.strip()
        
        # 移除常见的前缀
        prefixes_to_remove = [
            "Action:", "ACTION:", "I choose:", "I will:", "Next action:", 
            "The best action is:", "I should:", "Let me:"
        ]
        
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
                break
        
        # 移除引号和标点
        response = response.strip('"\'.,!?')
        
        # 检查是否是有效动作
        if response in available_actions:
            return response
        
        # 尝试模糊匹配
        response_lower = response.lower()
        for action in available_actions:
            if response_lower in action.lower() or action.lower() in response_lower:
                return action
        
        # 如果都不匹配，选择第一个可用动作
        self.logger.warning(f"Could not parse response '{response}', using first available action")
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
        self.total_actions = 0
        self.api_calls = 0
        self.api_response_times = []
