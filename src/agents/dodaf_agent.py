"""
DODAF框架智能体
基于DO-DA-F决策框架的结构化推理智能体
"""

import time
from typing import List, Dict, Any, Optional
import openai
import anthropic

from .kg_agent import KGAgent
from ..utils.logger import get_logger


class DODAFAgent(KGAgent):
    """基于DODAF框架的智能体"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        """
        初始化DODAFAgent
        
        Args:
            agent_id: 智能体ID
            config: 配置参数
        """
        super().__init__(agent_id, config)
        self.logger = get_logger(f"DODAFAgent_{agent_id}")
        
        # LLM配置
        self.model_name = config.get('model_name', 'gpt-4o')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 150)
        self.use_local_model = config.get('use_local_model', False)
        
        # DODAF特定配置
        self.enable_dodaf_reasoning = config.get('enable_dodaf_reasoning', True)
        self.dodaf_query_priority = config.get('dodaf_query_priority', ['DO', 'DA', 'F'])
        
        # 初始化LLM客户端
        self._initialize_llm_client()
        
        # 统计信息
        self.api_calls = 0
        self.api_response_times = []
        self.dodaf_queries = {'DO': 0, 'DA': 0, 'F': 0}
        
        self.logger.info(f"Initialized DODAFAgent with model: {self.model_name}")
    
    def _initialize_llm_client(self):
        """初始化LLM客户端"""
        if not self.use_local_model:
            if "gpt" in self.model_name.lower():
                self.client = openai.OpenAI()
            elif "claude" in self.model_name.lower():
                self.client = anthropic.Anthropic()
            else:
                raise ValueError(f"Unsupported model: {self.model_name}")
    
    def act(self, observation: str, available_actions: List[str] = None, **kwargs) -> str:
        """
        使用DODAF框架选择动作
        
        Args:
            observation: 环境观测
            available_actions: 可用动作列表
            **kwargs: 其他参数
            
        Returns:
            选择的动作
        """
        start_time = time.time()
        
        try:
            if self.enable_dodaf_reasoning:
                # 使用DODAF结构化推理
                chosen_action = self._dodaf_decision(observation, available_actions)
            else:
                # 简化决策
                chosen_action = self._simple_decision(observation, available_actions)
            
            # 记录统计
            decision_time = time.time() - start_time
            self.api_response_times.append(decision_time)
            
            self.logger.info(f"DODAF Agent decision: {chosen_action} (time: {decision_time:.2f}s)")
            
            return chosen_action
            
        except Exception as e:
            self.logger.error(f"DODAF Agent decision failed: {e}")
            return available_actions[0] if available_actions else "look"
    
    def _dodaf_decision(self, observation: str, available_actions: List[str]) -> str:
        """
        使用DODAF框架进行结构化决策
        
        Args:
            observation: 环境观测
            available_actions: 可用动作列表
            
        Returns:
            选择的动作
        """
        # 1. 检索DODAF结构化知识
        dodaf_knowledge = self._retrieve_dodaf_knowledge(observation)
        
        # 2. 构建DODAF结构化prompt
        prompt = self._build_dodaf_prompt(observation, available_actions, dodaf_knowledge)
        
        # 3. 调用LLM进行决策
        response = self._generate_api_response(prompt)
        
        # 4. 解析响应
        chosen_action = self._parse_dodaf_response(response, available_actions)
        
        return chosen_action
    
    def _retrieve_dodaf_knowledge(self, observation: str) -> Dict[str, List]:
        """
        检索DODAF结构化知识
        
        Args:
            observation: 环境观测
            
        Returns:
            DODAF结构化知识字典
        """
        dodaf_knowledge = {'DO': [], 'DA': [], 'F': []}
        
        if not self.use_knowledge_graph or not self.kg_retriever:
            return dodaf_knowledge
        
        # 提取关键词
        keywords = self._extract_keywords(observation)
        
        # 按DODAF优先级查询
        for dodaf_type in self.dodaf_query_priority:
            try:
                # 构建DODAF查询
                dodaf_query = f"{dodaf_type}:{keywords.split()[0]}" if keywords else f"{dodaf_type}:action"
                
                # 执行查询
                results = self.query_kg('dodaf', dodaf_query, max_results=2)
                dodaf_knowledge[dodaf_type] = results
                self.dodaf_queries[dodaf_type] += 1
                
                # 如果没有DODAF特定结果，尝试关键词查询
                if not results and keywords:
                    keyword_results = self.query_kg('keywords', keywords, max_results=1)
                    # 过滤出对应DODAF类型的结果
                    filtered_results = [fact for fact in keyword_results 
                                      if hasattr(fact, 'dodaf_type') and fact.dodaf_type == dodaf_type]
                    dodaf_knowledge[dodaf_type] = filtered_results
                
            except Exception as e:
                self.logger.warning(f"DODAF {dodaf_type} query failed: {e}")
        
        return dodaf_knowledge
    
    def _build_dodaf_prompt(self, observation: str, available_actions: List[str], 
                           dodaf_knowledge: Dict[str, List]) -> str:
        """
        构建DODAF结构化prompt
        
        Args:
            observation: 环境观测
            available_actions: 可用动作列表
            dodaf_knowledge: DODAF知识
            
        Returns:
            构建的prompt
        """
        # 格式化DODAF知识
        do_knowledge = self._format_dodaf_facts(dodaf_knowledge.get('DO', []), 'Actions')
        da_knowledge = self._format_dodaf_facts(dodaf_knowledge.get('DA', []), 'Conditions')
        f_knowledge = self._format_dodaf_facts(dodaf_knowledge.get('F', []), 'Outcomes')
        
        prompt = f"""You are an intelligent agent using the DODAF (Department of Defense Architecture Framework) for decision making.

Current Observation: {observation}

DODAF Knowledge Structure:

DO (Actions - What needs to be done):
{do_knowledge}

DA (Conditions - Current state and constraints):
{da_knowledge}

F (Outcomes - Expected results and goals):
{f_knowledge}

Available Actions: {', '.join(available_actions)}

Based on the DODAF framework:
1. Analyze the current conditions (DA)
2. Consider available actions (DO) 
3. Evaluate expected outcomes (F)
4. Choose the best action from the available actions

Respond with only the chosen action name.
"""
        return prompt
    
    def _format_dodaf_facts(self, facts: List, category_name: str) -> str:
        """
        格式化DODAF事实
        
        Args:
            facts: 事实列表
            category_name: 类别名称
            
        Returns:
            格式化的文本
        """
        if not facts:
            return f"No {category_name.lower()} knowledge available."
        
        formatted = []
        for fact in facts:
            formatted.append(f"- {fact.subject} {fact.predicate} {fact.object}")
        
        return "\n".join(formatted)
    
    def _parse_dodaf_response(self, response: str, available_actions: List[str]) -> str:
        """
        解析DODAF响应
        
        Args:
            response: LLM响应
            available_actions: 可用动作列表
            
        Returns:
            解析的动作
        """
        # 清理响应
        action = response.strip()
        
        # 移除可能的前缀
        prefixes = ['Action:', 'Chosen action:', 'Decision:', 'Response:']
        for prefix in prefixes:
            if action.lower().startswith(prefix.lower()):
                action = action[len(prefix):].strip()
        
        # 验证动作
        if action in available_actions:
            return action
        
        # 尝试模糊匹配
        action_lower = action.lower()
        for available_action in available_actions:
            if action_lower == available_action.lower():
                return available_action
            if action_lower in available_action.lower() or available_action.lower() in action_lower:
                return available_action
        
        # 如果没有匹配，返回第一个可用动作
        self.logger.warning(f"DODAF response '{action}' not in available actions, using fallback")
        return available_actions[0] if available_actions else "look"
    
    def _simple_decision(self, observation: str, available_actions: List[str]) -> str:
        """
        简化决策（不使用DODAF结构）
        
        Args:
            observation: 环境观测
            available_actions: 可用动作列表
            
        Returns:
            选择的动作
        """
        # 提取关键词并查询KG
        keywords = self._extract_keywords(observation)
        knowledge_facts = self.query_kg('keywords', keywords)
        
        # 构建简化prompt
        knowledge_text = self._format_kg_facts(knowledge_facts)
        
        prompt = f"""Choose the best action based on the observation and knowledge.

Current Observation: {observation}

Relevant Knowledge:
{knowledge_text}

Available Actions: {', '.join(available_actions)}

Respond with only the action name.
"""
        
        # 生成响应
        response = self._generate_api_response(prompt)
        
        # 解析动作
        return self._parse_dodaf_response(response, available_actions)
    
    def _generate_api_response(self, prompt: str) -> str:
        """
        使用API生成响应
        
        Args:
            prompt: 输入prompt
            
        Returns:
            生成的响应
        """
        self.api_calls += 1
        
        try:
            if "gpt" in self.model_name.lower():
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                return response.choices[0].message.content.strip()
            
            elif "claude" in self.model_name.lower():
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
            
            else:
                raise ValueError(f"Unsupported model: {self.model_name}")
                
        except Exception as e:
            self.logger.error(f"API call failed: {e}")
            raise
    
    def get_dodaf_stats(self) -> Dict[str, Any]:
        """获取DODAF统计信息"""
        stats = self.get_config()
        stats.update({
            "api_calls": self.api_calls,
            "dodaf_queries": self.dodaf_queries,
            "avg_api_response_time": sum(self.api_response_times) / len(self.api_response_times) if self.api_response_times else 0
        })
        return stats
    
    def reset(self):
        """重置智能体状态"""
        super().reset()
        self.api_calls = 0
        self.api_response_times = []
        self.dodaf_queries = {'DO': 0, 'DA': 0, 'F': 0}
