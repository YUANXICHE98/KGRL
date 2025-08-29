"""
基础配置文件
包含项目的全局配置参数
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

@dataclass
class BaseConfig:
    """基础配置类"""
    
    # 项目路径
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    RESULTS_DIR: Path = PROJECT_ROOT / "results"
    LOGS_DIR: Path = RESULTS_DIR / "logs"
    MODELS_DIR: Path = RESULTS_DIR / "models"
    PLOTS_DIR: Path = RESULTS_DIR / "plots"
    
    # 知识图谱路径
    KG_DIR: Path = DATA_DIR / "knowledge_graphs"
    TRAINING_DATA_DIR: Path = DATA_DIR / "training_data"
    EVALUATION_DATA_DIR: Path = DATA_DIR / "evaluation_data"
    
    # 模型配置
    DEFAULT_MODEL_NAME: str = "meta-llama/Llama-3.1-8B-Instruct"
    MAX_LENGTH: int = 2048
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    
    # API配置
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    WANDB_API_KEY: Optional[str] = os.getenv("WANDB_API_KEY")
    
    # 训练配置
    BATCH_SIZE: int = 8
    LEARNING_RATE: float = 1e-5
    NUM_EPOCHS: int = 3
    GRADIENT_ACCUMULATION_STEPS: int = 4
    WARMUP_STEPS: int = 100
    
    # 评估配置
    EVAL_BATCH_SIZE: int = 16
    NUM_EVAL_EPISODES: int = 50
    MAX_EPISODE_LENGTH: int = 100
    
    # 随机种子
    RANDOM_SEED: int = 42
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def __post_init__(self):
        """初始化后创建必要的目录"""
        self.create_directories()
    
    def create_directories(self):
        """创建必要的目录结构"""
        directories = [
            self.DATA_DIR,
            self.RESULTS_DIR,
            self.LOGS_DIR,
            self.MODELS_DIR,
            self.PLOTS_DIR,
            self.KG_DIR,
            self.TRAINING_DATA_DIR,
            self.EVALUATION_DATA_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            key: str(value) if isinstance(value, Path) else value
            for key, value in self.__dict__.items()
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'BaseConfig':
        """从字典创建配置对象"""
        return cls(**config_dict)

# 全局配置实例
config = BaseConfig()
