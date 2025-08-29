"""
RAG Agent - 知识图谱增强的智能体
集成知识图谱检索和ReAct推理框架
"""

import time
from typing import List, Dict, Any, Optional, Tuple
import openai
import anthropic

from .base_agent import BaseAgent
from ..knowledge.kg_retriever import KnowledgeGraphRetriever
from ..reasoning.react_framework import ReActFramework
from ..utils.logger import get_logger


class RAGAgent(BaseAgent):
    """RAG增强的智能体"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        """
        初始化RAG Agent
        
        Args:
            agent_id: Agent标识符
            config: 配置字典，包含模型、KG等配置
        """
        super().__init__(agent_id, config)

        # 基础配置
        self.model_name = config.get('model_name', 'gpt-4o')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 200)

        # RAG特定配置
        self.use_knowledge_graph = config.get('use_knowledge_graph', True)
        self.use_react_reasoning = config.get('use_react_reasoning', True)
        self.max_kg_facts = config.get('max_kg_facts', 5)
        self.kg_retrieval_method = config.get('kg_retrieval_method', 'semantic')
        
        # 知识图谱检索器
        self.kg_retriever: Optional[KnowledgeGraphRetriever] = None

        # ReAct推理框架
        self.react_framework: Optional[ReActFramework] = None
        if self.use_react_reasoning:
            self.react_framework = ReActFramework()

        # 统计信息
        self.kg_queries = 0
        self.kg_hits = 0
        self.reasoning_steps = 0
        self.total_actions = 0
        self.api_calls = 0
        self.api_response_times = []

        # 初始化API客户端
        self._init_api_client()

        self.logger.info(f"Initialized RAG Agent: KG={self.use_knowledge_graph}, "
                        f"ReAct={self.use_react_reasoning}")
    
    def set_knowledge_retriever(self, kg_retriever: KnowledgeGraphRetriever):
        """设置知识图谱检索器"""
        self.kg_retriever = kg_retriever
        self.logger.info("Knowledge retriever set successfully")
    
    def query_kg(self, query_type: str, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        KG查询接口 - 支持ReAct框架调用

        Args:
            query_type: 查询类型 (keywords/dodaf/entity)
            query: 查询内容
            max_results: 最大结果数

        Returns:
            匹配的事实字典列表
        """
        if not self.use_knowledge_graph or not self.kg_retriever:
            return []
        
        self.kg_queries += 1
        
        try:
            # 使用统一的query_kg接口
            results = self.kg_retriever.query_kg(query_type, query, max_results)

            if results:
                self.kg_hits += 1

            # 转换为字典格式
            knowledge_facts = []
            for fact in results:
                if hasattr(fact, 'subject'):  # KGFact对象
                    knowledge_facts.append({
                        'subject': fact.subject,
                        'predicate': fact.predicate,
                        'object': fact.object,
                        'confidence': getattr(fact, 'confidence', 1.0),
                        'dodaf_type': getattr(fact, 'dodaf_type', 'DA')
                    })
                elif isinstance(fact, tuple) and len(fact) >= 3:  # 元组格式
                    knowledge_facts.append({
                        'subject': fact[0],
                        'predicate': fact[1],
                        'object': fact[2],
                        'confidence': fact[3] if len(fact) > 3 else 1.0,
                        'dodaf_type': 'DA'
                    })

            self.logger.debug(f"Retrieved {len(knowledge_facts)} knowledge facts via {query_type}: {query}")
            return knowledge_facts
            
        except Exception as e:
            self.logger.error(f"Knowledge retrieval failed: {e}")
            return []
    
    def build_enhanced_prompt(self, observation: str, available_actions: List[str], 
                            knowledge_facts: List[Dict[str, Any]]) -> str:
        """
        构建知识增强的prompt
        
        Args:
            observation: 环境观察
            available_actions: 可用动作
            knowledge_facts: 检索到的知识事实
            
        Returns:
            增强后的prompt
        """
        prompt_parts = []
        
        # 基础任务描述
        prompt_parts.append("""You are an intelligent agent playing a text-based adventure game.
Your goal is to complete the given task by taking appropriate actions.

Current situation:""")
        
        prompt_parts.append(f"Observation: {observation}")
        
        # 添加知识图谱信息
        if knowledge_facts:
            prompt_parts.append("\nRelevant knowledge from your knowledge base:")
            for i, fact in enumerate(knowledge_facts, 1):
                confidence_str = f" (confidence: {fact['confidence']:.2f})" if fact['confidence'] < 1.0 else ""
                prompt_parts.append(f"{i}. {fact['subject']} {fact['predicate']} {fact['object']}{confidence_str}")
        
        # 可用动作
        prompt_parts.append(f"\nAvailable actions: {available_actions}")
        
        # 决策指导
        if self.use_react_reasoning:
            prompt_parts.append("""
Please think step by step and choose the best action:

1. THOUGHT: Analyze the current situation and consider the relevant knowledge
2. ACTION: Choose one action from the available actions
3. REASON: Explain why this action is the best choice

Format your response as:
THOUGHT: [your analysis]
ACTION: [chosen action]
REASON: [your reasoning]""")
        else:
            prompt_parts.append("""
Based on the observation and your knowledge, choose the best action from the available actions.
Respond with only the action name.""")
        
        return "\n".join(prompt_parts)
    
    def parse_react_response(self, response: str) -> Tuple[str, str, str]:
        """
        解析ReAct格式的响应
        
        Args:
            response: LLM的响应
            
        Returns:
            (thought, action, reason) 元组
        """
        thought = ""
        action = ""
        reason = ""
        
        lines = response.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('THOUGHT:'):
                current_section = 'thought'
                thought = line[8:].strip()
            elif line.startswith('ACTION:'):
                current_section = 'action'
                action = line[7:].strip()
            elif line.startswith('REASON:'):
                current_section = 'reason'
                reason = line[7:].strip()
            elif current_section and line:
                if current_section == 'thought':
                    thought += " " + line
                elif current_section == 'action':
                    action += " " + line
                elif current_section == 'reason':
                    reason += " " + line
        
        return thought.strip(), action.strip(), reason.strip()
    
    def act(self, observation: str, available_actions: List[str]) -> str:
        """
        基于ReAct框架和动态KG查询做出决策

        Args:
            observation: 环境观察
            available_actions: 可用动作列表

        Returns:
            选择的动作
        """
        start_time = time.time()

        try:
            if self.use_react_reasoning:
                # 使用真正的ReAct循环 - 不预先检索KG
                return self._react_decision_loop(observation, available_actions, start_time)
            else:
                # 简化决策（仍然支持一次KG查询）
                query_keywords = self._extract_keywords(observation)
                knowledge_facts = self.query_kg('keywords', query_keywords, max_results=self.max_kg_facts)

                prompt = self.build_enhanced_prompt(observation, available_actions, knowledge_facts)
                response = self._generate_api_response(prompt)
                chosen_action = response.strip()

                # 验证和记录
                if chosen_action in available_actions:
                    self._record_decision_stats(start_time, True)
                    return chosen_action

                matched_action = self._fuzzy_match_action(chosen_action, available_actions)
                if matched_action:
                    self._record_decision_stats(start_time, True)
                    return matched_action

                self.logger.warning(f"Invalid action '{chosen_action}', using fallback")
                self._record_decision_stats(start_time, False)
                return available_actions[0] if available_actions else "look"

        except Exception as e:
            self.logger.error(f"RAG Agent decision failed: {e}")
            return available_actions[0] if available_actions else "look"

    def _react_decision_loop(self, observation: str, available_actions: List[str], start_time: float) -> str:
        """
        真正的ReAct决策循环：Thought → Action(query_kg) → Observation → 决策
        """
        max_iterations = 3  # 最多3轮思考
        current_observation = observation

        for iteration in range(max_iterations):
            self.logger.debug(f"ReAct iteration {iteration + 1}")

            # 构建ReAct prompt（不包含KG信息）
            prompt = self._build_react_prompt(current_observation, available_actions, iteration)

            # 调用LLM
            response = self._generate_api_response(prompt)

            # 解析响应
            thought, action, reason = self.parse_react_response(response)
            self.reasoning_steps += 1

            self.logger.debug(f"  Thought: {thought[:100]}...")
            self.logger.debug(f"  Action: {action}")
            self.logger.debug(f"  Reason: {reason[:100]}...")

            # 检查是否是KG查询动作
            if action.startswith('query_kg('):
                # 执行KG查询
                kg_result = self._execute_query_kg_action(action)
                self.logger.debug(f"  KG Result: {kg_result}")

                # 将KG结果添加到观察中，继续下一轮思考
                current_observation += f"\nKnowledge: {kg_result}"
                continue

            # 检查是否是有效的游戏动作
            if action in available_actions:
                self._record_decision_stats(start_time, True)
                self.logger.info(f"ReAct chose valid action: {action}")
                return action

            # 尝试模糊匹配
            matched_action = self._fuzzy_match_action(action, available_actions)
            if matched_action:
                self._record_decision_stats(start_time, True)
                self.logger.info(f"ReAct chose matched action: {matched_action} (from {action})")
                return matched_action

            # 如果动作无效，继续下一轮思考
            self.logger.warning(f"Invalid action '{action}', continuing ReAct loop")
            current_observation += f"\nNote: '{action}' is not a valid action. Available: {available_actions}"

        # 如果所有迭代都没有产生有效动作，回退
        self.logger.warning("ReAct loop failed to produce valid action, using fallback")
        self._record_decision_stats(start_time, False)
        return available_actions[0] if available_actions else "look"

    def _build_react_prompt(self, observation: str, available_actions: List[str], iteration: int) -> str:
        """
        构建ReAct prompt（不包含KG信息，支持query_kg调用）
        """
        prompt_parts = []

        prompt_parts.append("You are an intelligent agent playing a text-based adventure game.")
        prompt_parts.append("Your goal is to find the key and open the chest in the bedroom.")
        prompt_parts.append("")
        prompt_parts.append(f"Current situation: {observation}")
        prompt_parts.append(f"Available game actions: {available_actions}")
        prompt_parts.append("")
        prompt_parts.append("You can also query the knowledge graph using:")
        prompt_parts.append("- query_kg('keywords', 'your query') - search by keywords")
        prompt_parts.append("- query_kg('dodaf', 'DO:action') - find actions")
        prompt_parts.append("- query_kg('dodaf', 'DA:condition') - find conditions")
        prompt_parts.append("- query_kg('dodaf', 'F:outcome') - find outcomes")
        prompt_parts.append("")
        prompt_parts.append("Think step by step and choose your next action:")
        prompt_parts.append("")
        prompt_parts.append("THOUGHT: [analyze the situation]")
        prompt_parts.append("ACTION: [choose a game action OR query_kg(...)]")
        prompt_parts.append("REASON: [explain your choice]")

        return "\n".join(prompt_parts)

    def _execute_query_kg_action(self, action: str) -> str:
        """
        执行query_kg动作并返回结果

        Args:
            action: query_kg调用字符串，如 "query_kg('keywords', 'kitchen key')"

        Returns:
            查询结果的字符串表示
        """
        try:
            # 简单解析query_kg调用
            # 格式: query_kg('type', 'query')
            import re
            match = re.search(r"query_kg\s*\(\s*['\"]([^'\"]+)['\"],\s*['\"]([^'\"]*)['\"]", action)

            if match:
                query_type = match.group(1)
                query = match.group(2)

                self.logger.debug(f"Executing KG query: {query_type} - {query}")

                # 执行查询
                results = self.query_kg(query_type, query, max_results=3)

                if results:
                    result_strings = []
                    for fact in results:
                        dodaf_type = fact.get('dodaf_type', 'DA')
                        result_strings.append(f"[{dodaf_type}] {fact['subject']} {fact['predicate']} {fact['object']}")
                    return "; ".join(result_strings)
                else:
                    return "No relevant knowledge found"
            else:
                return "Invalid query_kg format"

        except Exception as e:
            self.logger.error(f"Failed to execute query_kg: {e}")
            return f"Query failed: {str(e)}"

    def _fuzzy_match_action(self, action: str, available_actions: List[str]) -> str:
        """
        模糊匹配动作
        """
        action_lower = action.lower()
        for available_action in available_actions:
            if action_lower in available_action.lower() or available_action.lower() in action_lower:
                return available_action
        return None

    def _record_decision_stats(self, start_time: float, success: bool):
        """
        记录决策统计信息
        """
        self.total_actions += 1
        self.api_calls += 1
        self.api_response_times.append(time.time() - start_time)

        if not success:
            self.logger.warning("Decision process failed, used fallback action")
    
    def _extract_keywords(self, text: str) -> str:
        """从文本中提取关键词用于知识检索"""
        # 简单的关键词提取，可以后续优化
        keywords = []
        important_words = ['kitchen', 'bedroom', 'fridge', 'chest', 'key', 'apple', 'book']
        
        text_lower = text.lower()
        for word in important_words:
            if word in text_lower:
                keywords.append(word)
        
        return " ".join(keywords) if keywords else text
    
    def get_stats(self) -> Dict[str, Any]:
        """获取Agent统计信息"""
        base_stats = super().get_stats()
        
        # 添加RAG特定统计
        rag_stats = {
            'kg_queries': self.kg_queries,
            'kg_hits': self.kg_hits,
            'kg_hit_rate': self.kg_hits / self.kg_queries if self.kg_queries > 0 else 0,
            'reasoning_steps': self.reasoning_steps,
            'use_knowledge_graph': self.use_knowledge_graph,
            'use_react_reasoning': self.use_react_reasoning
        }
        
        base_stats.update(rag_stats)
        return base_stats
    
    def reset(self):
        """重置Agent状态"""
        super().reset()
        self.kg_queries = 0
        self.kg_hits = 0
        self.reasoning_steps = 0
        self.total_actions = 0
        self.api_calls = 0
        self.api_response_times = []

    def _init_api_client(self):
        """初始化API客户端"""
        if "gpt" in self.model_name.lower():
            import openai
            from config.base_config import config
            self.client = openai.OpenAI(
                api_key=config.OPENAI_API_KEY,
                base_url=config.OPENAI_BASE_URL
            )
        elif "claude" in self.model_name.lower():
            import anthropic
            self.client = anthropic.Anthropic()
        else:
            self.logger.warning(f"Unknown API model: {self.model_name}")

    def _generate_api_response(self, prompt: str) -> str:
        """使用API生成响应"""
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
