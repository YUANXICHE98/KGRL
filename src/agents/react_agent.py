"""
ReAct推理智能体
实现完整的ReAct推理循环，支持动态知识图谱查询
"""

import time
import re
from typing import List, Dict, Any, Optional, Tuple
import openai
import anthropic

from .kg_agent import KGAgent
from ..reasoning.react_framework import ReActFramework
from ..utils.logger import get_logger


class ReactAgent(KGAgent):
    """ReAct推理智能体"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        """
        初始化ReactAgent
        
        Args:
            agent_id: 智能体ID
            config: 配置参数
        """
        super().__init__(agent_id, config)
        self.logger = get_logger(f"ReactAgent_{agent_id}")
        
        # LLM配置
        self.model_name = config.get('model_name', 'gpt-4o')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 200)
        self.use_local_model = config.get('use_local_model', False)
        
        # ReAct配置
        self.max_react_iterations = config.get('max_react_iterations', 5)
        self.enable_react_reasoning = config.get('enable_react_reasoning', True)
        
        # 初始化LLM客户端
        self._initialize_llm_client()
        
        # ReAct框架
        self.react_framework = ReActFramework() if self.enable_react_reasoning else None
        
        # 统计信息
        self.api_calls = 0
        self.api_response_times = []
        self.reasoning_steps = 0
        self.react_iterations = 0
        
        self.logger.info(f"Initialized ReactAgent with model: {self.model_name}")
    
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
        使用ReAct推理选择动作
        
        Args:
            observation: 环境观测
            available_actions: 可用动作列表
            **kwargs: 其他参数
            
        Returns:
            选择的动作
        """
        start_time = time.time()
        
        try:
            if self.enable_react_reasoning:
                # 使用ReAct推理循环
                chosen_action = self._react_decision_loop(observation, available_actions)
            else:
                # 简化决策（单次KG查询 + LLM决策）
                chosen_action = self._simple_decision(observation, available_actions)
            
            # 记录统计
            decision_time = time.time() - start_time
            self.api_response_times.append(decision_time)
            
            self.logger.info(f"ReactAgent decision: {chosen_action} (time: {decision_time:.2f}s)")
            
            return chosen_action
            
        except Exception as e:
            self.logger.error(f"ReactAgent decision failed: {e}")
            return available_actions[0] if available_actions else "look"
    
    def _react_decision_loop(self, observation: str, available_actions: List[str]) -> str:
        """
        执行ReAct推理循环
        
        Args:
            observation: 环境观测
            available_actions: 可用动作列表
            
        Returns:
            选择的动作
        """
        current_observation = observation
        
        for iteration in range(self.max_react_iterations):
            self.react_iterations += 1
            self.logger.debug(f"ReAct iteration {iteration + 1}")
            
            # 构建ReAct prompt
            prompt = self._build_react_prompt(current_observation, available_actions, iteration)
            
            # 调用LLM
            response = self._generate_api_response(prompt)
            
            # 解析响应
            thought, action, reason = self._parse_react_response(response)
            self.reasoning_steps += 1
            
            self.logger.debug(f"  Thought: {thought[:100]}...")
            self.logger.debug(f"  Action: {action}")
            self.logger.debug(f"  Reason: {reason[:100]}...")
            
            # 检查是否是KG查询动作
            if action and action.startswith('query_kg('):
                # 执行KG查询
                kg_result = self._execute_query_kg_action(action)
                self.logger.debug(f"  KG Result: {kg_result}")
                
                # 将KG结果添加到观察中，继续下一轮思考
                current_observation += f"\nKnowledge: {kg_result}"
                continue
            
            # 检查是否是有效的环境动作
            if action and action in available_actions:
                return action
            
            # 尝试模糊匹配
            matched_action = self._fuzzy_match_action(action, available_actions)
            if matched_action:
                return matched_action
            
            # 如果没有找到有效动作，继续下一轮思考
            current_observation += f"\nPrevious invalid action: {action}"
        
        # 如果ReAct循环结束仍未找到有效动作，返回默认动作
        self.logger.warning("ReAct loop completed without valid action, using fallback")
        return available_actions[0] if available_actions else "look"
    
    def _simple_decision(self, observation: str, available_actions: List[str]) -> str:
        """
        简化决策（不使用ReAct循环）
        
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
        prompt = self._build_simple_prompt(observation, available_actions, knowledge_facts)
        
        # 生成响应
        response = self._generate_api_response(prompt)
        
        # 解析动作
        chosen_action = response.strip()
        
        # 验证动作
        if chosen_action in available_actions:
            return chosen_action
        
        # 尝试模糊匹配
        matched_action = self._fuzzy_match_action(chosen_action, available_actions)
        if matched_action:
            return matched_action
        
        # 返回默认动作
        return available_actions[0] if available_actions else "look"
    
    def _build_react_prompt(self, observation: str, available_actions: List[str], iteration: int) -> str:
        """
        构建ReAct推理prompt
        
        Args:
            observation: 当前观测
            available_actions: 可用动作
            iteration: 当前迭代次数
            
        Returns:
            构建的prompt
        """
        prompt = f"""You are an intelligent agent using ReAct (Reasoning and Acting) framework.

Current Observation: {observation}

Available Actions: {', '.join(available_actions)}

You can also query the knowledge graph using: query_kg('query_type', 'query_content')
- query_kg('keywords', 'key words') - search by keywords
- query_kg('dodaf', 'DO:action') - search DODAF actions
- query_kg('dodaf', 'DA:condition') - search DODAF conditions
- query_kg('entity', 'entity_name') - search by entity

Please think step by step using this format:
Thought: [Your reasoning about what to do next]
Action: [Either an available action or a query_kg() call]
Reason: [Why you chose this action]

Iteration: {iteration + 1}/{self.max_react_iterations}
"""
        return prompt
    
    def _build_simple_prompt(self, observation: str, available_actions: List[str], knowledge_facts) -> str:
        """
        构建简化决策prompt
        
        Args:
            observation: 环境观测
            available_actions: 可用动作
            knowledge_facts: 知识事实
            
        Returns:
            构建的prompt
        """
        knowledge_text = self._format_kg_facts(knowledge_facts)
        
        prompt = f"""You are an intelligent agent. Choose the best action based on the observation and knowledge.

Current Observation: {observation}

Relevant Knowledge:
{knowledge_text}

Available Actions: {', '.join(available_actions)}

Choose one action from the available actions. Respond with only the action name.
"""
        return prompt
    
    def _parse_react_response(self, response: str) -> Tuple[str, str, str]:
        """
        解析ReAct响应
        
        Args:
            response: LLM响应
            
        Returns:
            (thought, action, reason) 元组
        """
        thought = ""
        action = ""
        reason = ""
        
        # 使用正则表达式提取各部分
        thought_match = re.search(r'Thought:\s*(.+?)(?=Action:|Reason:|$)', response, re.DOTALL | re.IGNORECASE)
        if thought_match:
            thought = thought_match.group(1).strip()
        
        action_match = re.search(r'Action:\s*(.+?)(?=Reason:|Thought:|$)', response, re.DOTALL | re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip()
        
        reason_match = re.search(r'Reason:\s*(.+?)(?=Thought:|Action:|$)', response, re.DOTALL | re.IGNORECASE)
        if reason_match:
            reason = reason_match.group(1).strip()
        
        return thought, action, reason
    
    def _execute_query_kg_action(self, action: str) -> str:
        """
        执行query_kg动作
        
        Args:
            action: query_kg动作字符串
            
        Returns:
            查询结果字符串
        """
        try:
            # 解析query_kg调用
            match = re.match(r"query_kg\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", action)
            if not match:
                return "Invalid query_kg format"
            
            query_type, query_content = match.groups()
            
            # 执行查询
            results = self.query_kg(query_type, query_content)
            
            # 格式化结果
            if results:
                return self._format_kg_facts(results)
            else:
                return f"No knowledge found for {query_type}: {query_content}"
                
        except Exception as e:
            self.logger.error(f"Failed to execute query_kg: {e}")
            return f"Query failed: {str(e)}"
    
    def _fuzzy_match_action(self, action: str, available_actions: List[str]) -> Optional[str]:
        """
        模糊匹配动作
        
        Args:
            action: 候选动作
            available_actions: 可用动作列表
            
        Returns:
            匹配的动作或None
        """
        if not action or not available_actions:
            return None
        
        action_lower = action.lower().strip()
        
        # 精确匹配
        for available_action in available_actions:
            if action_lower == available_action.lower():
                return available_action
        
        # 包含匹配
        for available_action in available_actions:
            if action_lower in available_action.lower() or available_action.lower() in action_lower:
                return available_action
        
        return None
    
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
    
    def get_stats(self) -> Dict[str, Any]:
        """获取智能体统计信息"""
        stats = super().get_config()
        stats.update({
            "api_calls": self.api_calls,
            "reasoning_steps": self.reasoning_steps,
            "react_iterations": self.react_iterations,
            "avg_api_response_time": sum(self.api_response_times) / len(self.api_response_times) if self.api_response_times else 0
        })
        return stats
    
    def reset(self):
        """重置智能体状态"""
        super().reset()
        self.api_calls = 0
        self.api_response_times = []
        self.reasoning_steps = 0
        self.react_iterations = 0
