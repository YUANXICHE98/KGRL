"""
Agent配置文件
包含三个核心Agent的配置参数
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from .base_config import BaseConfig

@dataclass
class BaselineAgentConfig:
    """Baseline Agent (Agent 1) 配置"""
    
    # 模型配置
    model_name: str = "gpt-4o-mini"  # 可选: gpt-4o, claude-3-sonnet, llama-3.1-8b
    use_local_model: bool = False
    max_tokens: int = 512
    temperature: float = 0.7
    
    # 提示词配置
    system_prompt: str = """You are an intelligent agent playing a text-based game. 
Your goal is to complete the given task by choosing appropriate actions.
Always respond with a single action command."""
    
    # 动作解析配置
    action_prefix: str = "Action:"
    max_retries: int = 3

@dataclass
class RAGAgentConfig:
    """RAG Agent (Agent 2) 配置"""
    
    # 继承基线配置
    baseline_config: BaselineAgentConfig = BaselineAgentConfig()
    
    # ReAct框架配置
    use_react: bool = True
    max_reasoning_steps: int = 5
    
    # 知识图谱检索配置
    kg_retrieval_method: str = "keyword"  # keyword, embedding, hybrid
    max_retrieved_facts: int = 10
    retrieval_threshold: float = 0.5
    
    # ReAct提示词模板
    react_system_prompt: str = """You are an intelligent agent with access to a knowledge graph.
Use the following format for reasoning:

Thought: [your reasoning about the current situation]
Action: query_kg("your question about the environment")
Observation: [knowledge retrieved from KG]
Thought: [your reasoning based on the knowledge]
Action: execute_action("your chosen action")
Observation: [environment response]

Continue this process until you complete the task."""
    
    # 检索触发条件
    auto_retrieve: bool = True
    retrieve_on_new_location: bool = True
    retrieve_on_failure: bool = True

@dataclass
class PPOAgentConfig:
    """PPO Agent (Agent 3) 配置"""
    
    # 继承RAG配置
    rag_config: RAGAgentConfig = RAGAgentConfig()
    
    # PPO训练配置
    ppo_epochs: int = 4
    mini_batch_size: int = 4
    learning_rate: float = 1e-5
    clip_range: float = 0.2
    value_loss_coef: float = 0.5
    entropy_coef: float = 0.01
    max_grad_norm: float = 1.0
    
    # 奖励函数配置
    reward_components: Dict[str, float] = None
    
    def __post_init__(self):
        if self.reward_components is None:
            self.reward_components = {
                "task_success": 1.0,      # 任务成功奖励
                "step_penalty": -0.01,    # 每步惩罚
                "invalid_action": -0.1,   # 无效动作惩罚
                "successful_query": 0.05, # 成功查询奖励
                "failed_query": -0.02,    # 失败查询惩罚
            }
    
    # 训练数据配置
    buffer_size: int = 10000
    batch_size: int = 32
    update_frequency: int = 100
    
    # 模型保存配置
    save_frequency: int = 1000
    eval_frequency: int = 500

@dataclass
class AgentConfigs:
    """所有Agent配置的集合"""
    
    baseline: BaselineAgentConfig = BaselineAgentConfig()
    rag: RAGAgentConfig = RAGAgentConfig()
    ppo: PPOAgentConfig = PPOAgentConfig()
    
    # 通用配置
    base_config: BaseConfig = BaseConfig()
    
    def get_agent_config(self, agent_type: str):
        """根据类型获取Agent配置"""
        if agent_type.lower() == "baseline":
            return self.baseline
        elif agent_type.lower() == "rag":
            return self.rag
        elif agent_type.lower() == "ppo":
            return self.ppo
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

# 全局Agent配置实例
agent_configs = AgentConfigs()
