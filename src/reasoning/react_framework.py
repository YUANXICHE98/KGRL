"""
ReAct推理框架
实现Reasoning and Acting的循环框架
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from ..utils.logger import get_logger

class ActionType(Enum):
    """动作类型枚举"""
    QUERY_KG = "query_kg"
    EXECUTE_ACTION = "execute_action"
    THINK = "think"
    UNKNOWN = "unknown"

@dataclass
class ReActStep:
    """ReAct步骤"""
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

class ReActFramework:
    """ReAct推理框架"""
    
    def __init__(self, framework_id: str = "default"):
        self.framework_id = framework_id
        self.logger = get_logger(f"ReActFramework_{framework_id}")
        
        # 配置参数
        self.max_reasoning_steps = 5
        self.max_retries = 3
        
        # 当前推理状态
        self.current_steps: List[ReActStep] = []
        self.step_counter = 0
        
        # 解析模式
        self.thought_pattern = r"Thought:\s*(.*?)(?=\n(?:Action:|$))"
        self.action_pattern = r"Action:\s*(.*?)(?=\n(?:Observation:|Thought:|$))"
        self.observation_pattern = r"Observation:\s*(.*?)(?=\n(?:Thought:|Action:|$))"
        
        self.logger.info(f"Initialized ReActFramework: {framework_id}")
    
    def parse_response(self, response: str) -> List[ReActStep]:
        """
        解析LLM响应为ReAct步骤
        
        Args:
            response: LLM的响应文本
            
        Returns:
            解析出的ReAct步骤列表
        """
        steps = []
        
        # 按行分割响应
        lines = response.strip().split('\n')
        current_step = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测思考
            if line.lower().startswith('thought:'):
                if current_step is not None:
                    steps.append(current_step)
                
                self.step_counter += 1
                current_step = ReActStep(step_id=self.step_counter)
                current_step.thought = line[8:].strip()  # 移除"Thought:"
            
            # 检测动作
            elif line.lower().startswith('action:'):
                if current_step is None:
                    self.step_counter += 1
                    current_step = ReActStep(step_id=self.step_counter)
                
                action_content = line[7:].strip()  # 移除"Action:"
                current_step.action_content = action_content
                current_step.action_type = self._classify_action(action_content)
            
            # 检测观测
            elif line.lower().startswith('observation:'):
                if current_step is None:
                    self.step_counter += 1
                    current_step = ReActStep(step_id=self.step_counter)
                
                current_step.observation = line[12:].strip()  # 移除"Observation:"
        
        # 添加最后一个步骤
        if current_step is not None:
            steps.append(current_step)
        
        return steps
    
    def _classify_action(self, action_content: str) -> ActionType:
        """
        分类动作类型
        
        Args:
            action_content: 动作内容
            
        Returns:
            动作类型
        """
        action_lower = action_content.lower().strip()
        
        # 检测知识图谱查询
        if (action_lower.startswith('query_kg(') or 
            'query_kg' in action_lower or
            action_lower.startswith('search_kg(') or
            'search knowledge' in action_lower):
            return ActionType.QUERY_KG
        
        # 检测环境动作执行
        elif (action_lower.startswith('execute_action(') or 
              'execute_action' in action_lower or
              any(cmd in action_lower for cmd in ['go', 'take', 'open', 'close', 'look', 'use', 'put'])):
            return ActionType.EXECUTE_ACTION
        
        # 检测纯思考
        elif action_lower.startswith('think') or 'reasoning' in action_lower:
            return ActionType.THINK
        
        else:
            return ActionType.UNKNOWN
    
    def extract_query_from_action(self, action_content: str) -> Optional[str]:
        """
        从动作中提取查询内容
        
        Args:
            action_content: 动作内容
            
        Returns:
            提取的查询字符串
        """
        # 尝试提取括号内的内容
        match = re.search(r'query_kg\s*\(\s*["\']?(.*?)["\']?\s*\)', action_content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # 尝试提取search_kg的内容
        match = re.search(r'search_kg\s*\(\s*["\']?(.*?)["\']?\s*\)', action_content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # 如果没有找到括号，返回整个动作内容（去除前缀）
        for prefix in ['query_kg', 'search_kg', 'search knowledge about']:
            if action_content.lower().startswith(prefix):
                return action_content[len(prefix):].strip(' ():"\'\'')  
        
        return action_content.strip()
    
    def extract_action_from_action(self, action_content: str) -> Optional[str]:
        """
        从动作中提取环境动作
        
        Args:
            action_content: 动作内容
            
        Returns:
            提取的环境动作
        """
        # 尝试提取括号内的内容
        match = re.search(r'execute_action\s*\(\s*["\']?(.*?)["\']?\s*\)', action_content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # 如果没有找到括号，返回整个动作内容（去除前缀）
        prefix = 'execute_action'
        if action_content.lower().startswith('execute_action'):
            return action_content[len(prefix):].strip(' ():"\'\'')    
        
        return action_content.strip()
    
    def build_react_prompt(self, 
                          observation: str, 
                          goal: str = None,
                          available_actions: List[str] = None,
                          history: List[ReActStep] = None) -> str:
        """
        构建ReAct提示词
        
        Args:
            observation: 当前观测
            goal: 目标描述
            available_actions: 可用动作列表
            history: 历史步骤
            
        Returns:
            构建的提示词
        """
        prompt_parts = [
            "You are an intelligent agent that can reason and act. Use the following format:",
            "",
            "Thought: [your reasoning about the current situation]",
            "Action: query_kg(\"your question about the environment\")",
            "Observation: [knowledge retrieved from knowledge graph]",
            "Thought: [your reasoning based on the knowledge]", 
            "Action: execute_action(\"your chosen action\")",
            "Observation: [environment response]",
            "",
            "Continue this process until you complete the task.",
            ""
        ]
        
        if goal:
            prompt_parts.extend([
                f"Goal: {goal}",
                ""
            ])
        
        prompt_parts.extend([
            f"Current Observation: {observation}",
            ""
        ])
        
        if available_actions:
            prompt_parts.extend([
                "Available Actions:",
                "\n".join(f"- {action}" for action in available_actions),
                ""
            ])
        
        if history:
            prompt_parts.extend([
                "Previous Steps:",
            ])
            for step in history[-3:]:  # 只显示最近3步
                if step.thought:
                    prompt_parts.append(f"Thought: {step.thought}")
                if step.action_content:
                    prompt_parts.append(f"Action: {step.action_content}")
                if step.observation:
                    prompt_parts.append(f"Observation: {step.observation}")
            prompt_parts.append("")
        
        prompt_parts.extend([
            "What should you do next?",
            "Thought:"
        ])
        
        return "\n".join(prompt_parts)
    
    def validate_step(self, step: ReActStep) -> Tuple[bool, str]:
        """
        验证ReAct步骤的有效性
        
        Args:
            step: 要验证的步骤
            
        Returns:
            (是否有效, 错误信息)
        """
        if not step.thought and not step.action_content:
            return False, "Step must contain either thought or action"
        
        if step.action_type == ActionType.QUERY_KG:
            query = self.extract_query_from_action(step.action_content)
            if not query:
                return False, "Query action must contain a valid query"
        
        elif step.action_type == ActionType.EXECUTE_ACTION:
            action = self.extract_action_from_action(step.action_content)
            if not action:
                return False, "Execute action must contain a valid action"
        
        return True, ""
    
    def reset(self):
        """重置推理状态"""
        self.current_steps.clear()
        self.step_counter = 0
        self.logger.debug("Reset ReAct framework state")
    
    def get_reasoning_history(self) -> List[Dict[str, Any]]:
        """获取推理历史"""
        return [step.to_dict() for step in self.current_steps]
    
    def add_step(self, step: ReActStep):
        """添加推理步骤"""
        self.current_steps.append(step)
        self.logger.debug(f"Added ReAct step {step.step_id}: {step.action_type.value}")
    
    def get_last_step(self) -> Optional[ReActStep]:
        """获取最后一个步骤"""
        return self.current_steps[-1] if self.current_steps else None
    
    def should_continue_reasoning(self) -> bool:
        """判断是否应该继续推理"""
        if len(self.current_steps) >= self.max_reasoning_steps:
            return False
        
        last_step = self.get_last_step()
        if last_step and last_step.action_type == ActionType.EXECUTE_ACTION:
            return False  # 执行了环境动作，应该等待环境响应
        
        return True
    
    def format_reasoning_trace(self, include_observations: bool = True) -> str:
        """
        格式化推理轨迹为文本
        
        Args:
            include_observations: 是否包含观测
            
        Returns:
            格式化的推理轨迹
        """
        if not self.current_steps:
            return "No reasoning steps recorded."
        
        lines = []
        for step in self.current_steps:
            if step.thought:
                lines.append(f"Thought: {step.thought}")
            if step.action_content:
                lines.append(f"Action: {step.action_content}")
            if include_observations and step.observation:
                lines.append(f"Observation: {step.observation}")
            lines.append("")  # 空行分隔
            return "\n".join(lines)
