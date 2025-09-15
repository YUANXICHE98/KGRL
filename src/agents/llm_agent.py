"""
LLM智能体封装
将大语言模型封装为智能体，提供统一的LLM调用接口
"""

import time
from typing import List, Dict, Any, Optional, Union
import openai
import anthropic

from .base_agent import BaseAgent
from ..utils.logger import get_logger


class LLMAgent(BaseAgent):
    """LLM智能体封装"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        """
        初始化LLMAgent
        
        Args:
            agent_id: 智能体ID
            config: 配置参数
        """
        super().__init__(agent_id, config)
        self.logger = get_logger(f"LLMAgent_{agent_id}")
        
        # LLM配置
        self.model_name = config.get('model_name', 'gpt-4o')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 512)
        self.use_local_model = config.get('use_local_model', False)
        
        # 提示词配置
        self.system_prompt = config.get('system_prompt', self._get_default_system_prompt())
        self.response_format = config.get('response_format', 'text')  # 'text' or 'json'
        
        # 初始化LLM客户端
        self._initialize_llm_client()
        
        # 统计信息
        self.api_calls = 0
        self.api_response_times = []
        self.total_tokens_used = 0
        self.successful_calls = 0
        self.failed_calls = 0
        
        self.logger.info(f"Initialized LLMAgent with model: {self.model_name}")
    
    def _initialize_llm_client(self):
        """初始化LLM客户端"""
        if not self.use_local_model:
            if "gpt" in self.model_name.lower():
                self.client = openai.OpenAI()
                self.provider = "openai"
            elif "claude" in self.model_name.lower():
                self.client = anthropic.Anthropic()
                self.provider = "anthropic"
            else:
                raise ValueError(f"Unsupported model: {self.model_name}")
        else:
            # 本地模型支持可以在这里添加
            self.provider = "local"
            self.logger.info("Local model support not implemented yet")
    
    def act(self, observation: str, available_actions: List[str] = None, **kwargs) -> str:
        """
        LLMAgent的act方法，主要用于演示
        
        Args:
            observation: 环境观测
            available_actions: 可用动作列表
            **kwargs: 其他参数
            
        Returns:
            LLM生成的响应
        """
        # 构建简单的决策prompt
        if available_actions:
            prompt = f"""Based on the observation, choose the best action.

Observation: {observation}

Available Actions: {', '.join(available_actions)}

Choose one action and respond with only the action name."""
        else:
            prompt = f"""Respond to the following observation:

Observation: {observation}

Provide a helpful response."""
        
        return self.generate(prompt)
    
    def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            **kwargs: 其他生成参数
            
        Returns:
            生成的文本
        """
        start_time = time.time()
        self.api_calls += 1
        
        try:
            # 使用提供的系统提示词或默认的
            sys_prompt = system_prompt or self.system_prompt
            
            # 合并生成参数
            generation_params = {
                'temperature': kwargs.get('temperature', self.temperature),
                'max_tokens': kwargs.get('max_tokens', self.max_tokens)
            }
            
            # 调用相应的LLM
            if self.provider == "openai":
                response = self._generate_openai(prompt, sys_prompt, generation_params)
            elif self.provider == "anthropic":
                response = self._generate_anthropic(prompt, sys_prompt, generation_params)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # 记录成功调用
            self.successful_calls += 1
            response_time = time.time() - start_time
            self.api_response_times.append(response_time)
            
            self.logger.debug(f"LLM generation successful (time: {response_time:.2f}s)")
            
            return response
            
        except Exception as e:
            self.failed_calls += 1
            self.logger.error(f"LLM generation failed: {e}")
            raise
    
    def _generate_openai(self, prompt: str, system_prompt: str, params: Dict[str, Any]) -> str:
        """
        使用OpenAI API生成响应
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            params: 生成参数
            
        Returns:
            生成的文本
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=params['temperature'],
            max_tokens=params['max_tokens']
        )
        
        # 记录token使用量
        if hasattr(response, 'usage') and response.usage:
            self.total_tokens_used += response.usage.total_tokens
        
        return response.choices[0].message.content.strip()
    
    def _generate_anthropic(self, prompt: str, system_prompt: str, params: Dict[str, Any]) -> str:
        """
        使用Anthropic API生成响应
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            params: 生成参数
            
        Returns:
            生成的文本
        """
        # Anthropic的系统提示词处理方式不同
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nHuman: {prompt}\n\nAssistant:"
        else:
            full_prompt = f"Human: {prompt}\n\nAssistant:"
        
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=params['max_tokens'],
            temperature=params['temperature'],
            messages=[{"role": "user", "content": full_prompt}]
        )
        
        # 记录token使用量
        if hasattr(response, 'usage') and response.usage:
            self.total_tokens_used += response.usage.input_tokens + response.usage.output_tokens
        
        return response.content[0].text.strip()
    
    def generate_batch(self, prompts: List[str], system_prompt: str = None, **kwargs) -> List[str]:
        """
        批量生成响应
        
        Args:
            prompts: 提示词列表
            system_prompt: 系统提示词
            **kwargs: 生成参数
            
        Returns:
            生成的响应列表
        """
        responses = []
        for prompt in prompts:
            try:
                response = self.generate(prompt, system_prompt, **kwargs)
                responses.append(response)
            except Exception as e:
                self.logger.error(f"Batch generation failed for prompt: {prompt[:50]}... Error: {e}")
                responses.append("")  # 添加空响应以保持列表长度一致
        
        return responses
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        多轮对话生成
        
        Args:
            messages: 对话消息列表，格式为[{"role": "user/assistant", "content": "..."}]
            **kwargs: 生成参数
            
        Returns:
            生成的响应
        """
        start_time = time.time()
        self.api_calls += 1
        
        try:
            generation_params = {
                'temperature': kwargs.get('temperature', self.temperature),
                'max_tokens': kwargs.get('max_tokens', self.max_tokens)
            }
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=generation_params['temperature'],
                    max_tokens=generation_params['max_tokens']
                )
                result = response.choices[0].message.content.strip()
                
                if hasattr(response, 'usage') and response.usage:
                    self.total_tokens_used += response.usage.total_tokens
            
            elif self.provider == "anthropic":
                # Anthropic需要转换消息格式
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=generation_params['max_tokens'],
                    temperature=generation_params['temperature'],
                    messages=messages
                )
                result = response.content[0].text.strip()
                
                if hasattr(response, 'usage') and response.usage:
                    self.total_tokens_used += response.usage.input_tokens + response.usage.output_tokens
            
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            self.successful_calls += 1
            response_time = time.time() - start_time
            self.api_response_times.append(response_time)
            
            return result
            
        except Exception as e:
            self.failed_calls += 1
            self.logger.error(f"Chat generation failed: {e}")
            raise
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        return """You are a helpful AI assistant. Provide clear, accurate, and concise responses."""
    
    def get_llm_stats(self) -> Dict[str, Any]:
        """获取LLM使用统计"""
        avg_response_time = sum(self.api_response_times) / len(self.api_response_times) if self.api_response_times else 0
        success_rate = self.successful_calls / self.api_calls if self.api_calls > 0 else 0
        
        return {
            "model_name": self.model_name,
            "provider": self.provider,
            "api_calls": self.api_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": success_rate,
            "total_tokens_used": self.total_tokens_used,
            "avg_response_time": avg_response_time,
            "total_response_time": sum(self.api_response_times)
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.api_calls = 0
        self.api_response_times = []
        self.total_tokens_used = 0
        self.successful_calls = 0
        self.failed_calls = 0
    
    def reset(self):
        """重置智能体状态"""
        super().reset()
        self.reset_stats()
    
    def get_config(self) -> Dict[str, Any]:
        """获取智能体配置"""
        config = super().get_config()
        config.update({
            "model_name": self.model_name,
            "provider": self.provider,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "llm_stats": self.get_llm_stats()
        })
        return config
