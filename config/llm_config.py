"""
LLM配置文件
支持多种语言模型的配置和比较
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import os

@dataclass
class LLMConfig:
    """单个LLM的配置"""
    name: str
    provider: str  # openai, anthropic, huggingface, local
    model_id: str
    api_key_env: str
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    cost_per_1k_tokens: float = 0.0  # 用于成本估算
    context_length: int = 4096
    supports_function_calling: bool = False
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        if self.provider in ["openai", "anthropic"]:
            return os.getenv(self.api_key_env) is not None
        return True  # 本地模型假设总是可用

# 预定义的LLM配置
AVAILABLE_LLMS = {
    # OpenAI模型
    "gpt-4o": LLMConfig(
        name="GPT-4o",
        provider="openai",
        model_id="gpt-4o",
        api_key_env="OPENAI_API_KEY",
        max_tokens=4096,
        temperature=0.7,
        cost_per_1k_tokens=0.03,
        context_length=128000,
        supports_function_calling=True
    ),
    
    "gpt-4o-mini": LLMConfig(
        name="GPT-4o Mini",
        provider="openai", 
        model_id="gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
        max_tokens=4096,
        temperature=0.7,
        cost_per_1k_tokens=0.0015,
        context_length=128000,
        supports_function_calling=True
    ),
    
    "gpt-3.5-turbo": LLMConfig(
        name="GPT-3.5 Turbo",
        provider="openai",
        model_id="gpt-3.5-turbo",
        api_key_env="OPENAI_API_KEY",
        max_tokens=4096,
        temperature=0.7,
        cost_per_1k_tokens=0.002,
        context_length=16385,
        supports_function_calling=True
    ),
    
    # Anthropic模型
    "claude-3-5-sonnet": LLMConfig(
        name="Claude 3.5 Sonnet",
        provider="anthropic",
        model_id="claude-3-5-sonnet-20241022",
        api_key_env="ANTHROPIC_API_KEY",
        max_tokens=4096,
        temperature=0.7,
        cost_per_1k_tokens=0.015,
        context_length=200000,
        supports_function_calling=False
    ),
    
    "claude-3-haiku": LLMConfig(
        name="Claude 3 Haiku",
        provider="anthropic",
        model_id="claude-3-haiku-20240307",
        api_key_env="ANTHROPIC_API_KEY",
        max_tokens=4096,
        temperature=0.7,
        cost_per_1k_tokens=0.0025,
        context_length=200000,
        supports_function_calling=False
    ),
    
    # 本地/开源模型
    "llama-3.1-8b": LLMConfig(
        name="Llama 3.1 8B",
        provider="huggingface",
        model_id="meta-llama/Llama-3.1-8B-Instruct",
        api_key_env="HF_TOKEN",
        max_tokens=2048,
        temperature=0.7,
        cost_per_1k_tokens=0.0,  # 本地运行无成本
        context_length=8192,
        supports_function_calling=False
    ),
    
    "gemma-2-9b": LLMConfig(
        name="Gemma 2 9B",
        provider="huggingface",
        model_id="google/gemma-2-9b-it",
        api_key_env="HF_TOKEN",
        max_tokens=2048,
        temperature=0.7,
        cost_per_1k_tokens=0.0,
        context_length=8192,
        supports_function_calling=False
    ),
    
    # 模拟模型（用于测试）
    "mock-llm": LLMConfig(
        name="Mock LLM",
        provider="mock",
        model_id="mock-model",
        api_key_env="",
        max_tokens=512,
        temperature=0.7,
        cost_per_1k_tokens=0.0,
        context_length=2048,
        supports_function_calling=False
    )
}

def get_available_llms() -> Dict[str, LLMConfig]:
    """获取当前可用的LLM列表"""
    available = {}
    for key, config in AVAILABLE_LLMS.items():
        if config.is_available():
            available[key] = config
    return available

def get_recommended_llms_for_comparison() -> List[str]:
    """获取推荐用于比较的LLM组合"""
    available = get_available_llms()
    
    # 推荐组合：性能好 + 成本低 + 本地模型
    recommendations = []
    
    # 高性能模型
    if "gpt-4o-mini" in available:
        recommendations.append("gpt-4o-mini")
    elif "gpt-3.5-turbo" in available:
        recommendations.append("gpt-3.5-turbo")
    
    # Anthropic模型
    if "claude-3-haiku" in available:
        recommendations.append("claude-3-haiku")
    
    # 本地模型
    if "llama-3.1-8b" in available:
        recommendations.append("llama-3.1-8b")
    
    # 如果没有API密钥，使用模拟模型
    if not recommendations:
        recommendations.append("mock-llm")
    
    return recommendations

def estimate_cost(llm_key: str, num_tokens: int) -> float:
    """估算使用成本"""
    if llm_key not in AVAILABLE_LLMS:
        return 0.0
    
    config = AVAILABLE_LLMS[llm_key]
    return (num_tokens / 1000) * config.cost_per_1k_tokens

def get_llm_comparison_matrix() -> Dict[str, Any]:
    """获取LLM对比矩阵"""
    available = get_available_llms()
    
    comparison = {
        "models": {},
        "summary": {
            "total_available": len(available),
            "providers": list(set(config.provider for config in available.values())),
            "cost_range": {
                "min": min((config.cost_per_1k_tokens for config in available.values() if config.cost_per_1k_tokens > 0), default=0),
                "max": max((config.cost_per_1k_tokens for config in available.values()), default=0)
            }
        }
    }
    
    for key, config in available.items():
        comparison["models"][key] = {
            "name": config.name,
            "provider": config.provider,
            "cost_per_1k": config.cost_per_1k_tokens,
            "context_length": config.context_length,
            "max_tokens": config.max_tokens,
            "supports_functions": config.supports_function_calling,
            "available": config.is_available()
        }
    
    return comparison

# 全局LLM管理器
class LLMManager:
    """LLM管理器"""
    
    def __init__(self):
        self.configs = AVAILABLE_LLMS
        self.current_llm = None
    
    def set_default_llm(self, llm_key: str):
        """设置默认LLM"""
        if llm_key in self.configs and self.configs[llm_key].is_available():
            self.current_llm = llm_key
            return True
        return False
    
    def get_config(self, llm_key: str = None) -> Optional[LLMConfig]:
        """获取LLM配置"""
        key = llm_key or self.current_llm
        return self.configs.get(key)
    
    def list_available(self) -> List[str]:
        """列出可用的LLM"""
        return list(get_available_llms().keys())
    
    def get_best_available(self) -> str:
        """获取最佳可用LLM"""
        available = get_available_llms()
        
        # 优先级：gpt-4o-mini > claude-3-haiku > gpt-3.5-turbo > 本地模型 > mock
        priority = ["gpt-4o-mini", "claude-3-haiku", "gpt-3.5-turbo", "llama-3.1-8b", "mock-llm"]
        
        for model in priority:
            if model in available:
                return model
        
        # 如果都没有，返回第一个可用的
        return list(available.keys())[0] if available else "mock-llm"

# 全局实例
llm_manager = LLMManager()
