"""
Baseline Agent (Agent 1)
基础LLM Agent，不使用RAG，直接基于观测生成动作
"""

import re
import time
from typing import Dict, Any, List, Optional
import openai
import anthropic
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from .base_agent import BaseAgent
from ..utils.logger import get_logger

class BaselineAgent(BaseAgent):
    """基础LLM Agent，不使用知识图谱检索"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        self.logger = get_logger(f"BaselineAgent_{agent_id}")
        
        # 模型配置
        self.model_name = self.config.get("model_name", "gpt-4o-mini")
        self.use_local_model = self.config.get("use_local_model", False)
        self.max_tokens = self.config.get("max_tokens", 512)
        self.temperature = self.config.get("temperature", 0.7)
        self.max_retries = self.config.get("max_retries", 3)
        
        # 提示词配置
        self.system_prompt = self.config.get("system_prompt", self._get_default_system_prompt())
        self.action_prefix = self.config.get("action_prefix", "Action:")
        
        # 初始化模型
        self._initialize_model()
        
        self.logger.info(f"Initialized BaselineAgent with model: {self.model_name}")
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        return """You are an intelligent agent playing a text-based game. 
Your goal is to complete the given task by choosing appropriate actions.

Instructions:
1. Read the current observation carefully
2. Think about what action would help you progress toward the goal
3. Choose ONE specific action command
4. Respond with only the action, prefixed with "Action:"

Example:
Action: go north

Remember: Only output the action command, nothing else."""
    
    def _initialize_model(self):
        """初始化语言模型"""
        if self.use_local_model:
            self._initialize_local_model()
        else:
            self._initialize_api_model()
    
    def _initialize_local_model(self):
        """初始化本地模型"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            self.logger.info(f"Loaded local model: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to load local model: {e}")
            raise
    
    def _initialize_api_model(self):
        """初始化API模型"""
        if "gpt" in self.model_name.lower():
            from config.base_config import config
            self.client = openai.OpenAI(
                api_key=config.OPENAI_API_KEY,
                base_url=config.OPENAI_BASE_URL
            )
        elif "claude" in self.model_name.lower():
            self.client = anthropic.Anthropic()
        else:
            self.logger.warning(f"Unknown API model: {self.model_name}")
    
    def act(self, observation: str, available_actions: List[str] = None, **kwargs) -> str:
        """
        根据观测生成动作
        
        Args:
            observation: 当前环境观测
            available_actions: 可用动作列表（可选）
            **kwargs: 其他参数
            
        Returns:
            选择的动作
        """
        # 构建提示词
        prompt = self._build_prompt(observation, available_actions)
        
        # 生成响应
        for attempt in range(self.max_retries):
            try:
                response = self._generate_response(prompt)
                action = self._parse_action(response)
                
                if action:
                    self.logger.debug(f"Generated action: {action}")
                    return action
                else:
                    self.logger.warning(f"Failed to parse action from response: {response}")
                    
            except Exception as e:
                self.logger.error(f"Error generating action (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    # 最后一次尝试失败，返回默认动作
                    return self._get_fallback_action(available_actions)
                time.sleep(1)  # 等待后重试
        
        return self._get_fallback_action(available_actions)
    
    def _build_prompt(self, observation: str, available_actions: List[str] = None) -> str:
        """构建输入提示词"""
        prompt_parts = [
            self.system_prompt,
            "",
            f"Current Observation: {observation}",
        ]
        
        if available_actions:
            prompt_parts.extend([
                "",
                "Available Actions:",
                "\n".join(f"- {action}" for action in available_actions)
            ])
        
        # 添加历史上下文（最近几步）
        if self.state.history:
            recent_history = self.state.history[-3:]  # 最近3步
            prompt_parts.extend([
                "",
                "Recent History:",
            ])
            for step in recent_history:
                prompt_parts.append(f"Action: {step['action']}")
                prompt_parts.append(f"Result: {step['observation']}")
        
        prompt_parts.extend([
            "",
            "What action should you take next?",
            f"{self.action_prefix}"
        ])
        
        return "\n".join(prompt_parts)
    
    def _generate_response(self, prompt: str) -> str:
        """生成模型响应"""
        if self.use_local_model:
            return self._generate_local_response(prompt)
        else:
            return self._generate_api_response(prompt)
    
    def _generate_local_response(self, prompt: str) -> str:
        """使用本地模型生成响应"""
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs.input_ids,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        return response.strip()
    
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
    
    def _parse_action(self, response: str) -> Optional[str]:
        """从响应中解析动作"""
        # 移除action前缀
        if self.action_prefix.lower() in response.lower():
            action_part = response.split(self.action_prefix, 1)[-1].strip()
        else:
            action_part = response.strip()
        
        # 清理动作文本
        action = re.sub(r'^[:\s]+', '', action_part)  # 移除开头的冒号和空格
        action = action.split('\n')[0].strip()  # 只取第一行
        action = re.sub(r'["\']', '', action)  # 移除引号
        
        return action if action else None
    
    def _get_fallback_action(self, available_actions: List[str] = None) -> str:
        """获取备用动作"""
        if available_actions:
            return available_actions[0]  # 返回第一个可用动作
        else:
            return "look"  # 默认动作
    
    def save_model(self, path: str):
        """保存模型配置"""
        import json
        config_to_save = {
            "agent_type": "BaselineAgent",
            "model_name": self.model_name,
            "config": self.config,
            "stats": self.stats
        }
        
        with open(path, 'w') as f:
            json.dump(config_to_save, f, indent=2)
        
        self.logger.info(f"Saved BaselineAgent config to {path}")
    
    def load_model(self, path: str):
        """加载模型配置"""
        import json
        
        with open(path, 'r') as f:
            saved_config = json.load(f)
        
        self.config.update(saved_config.get("config", {}))
        self.stats.update(saved_config.get("stats", {}))
        
        self.logger.info(f"Loaded BaselineAgent config from {path}")
