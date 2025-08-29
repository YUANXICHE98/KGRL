"""
日志工具模块
提供统一的日志配置和管理功能
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    设置全局日志配置
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径
        log_format: 日志格式
        
    Returns:
        配置好的logger
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 创建根logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有handlers
    logger.handlers.clear()
    
    # 创建formatter
    formatter = logging.Formatter(log_format)
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件handler（如果指定了文件路径）
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    获取指定名称的logger
    
    Args:
        name: logger名称
        log_level: 日志级别
        
    Returns:
        logger实例
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # 如果logger没有handlers，使用默认配置
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # 创建控制台handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level.upper()))
        
        # 创建formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger

def create_experiment_logger(
    experiment_name: str,
    log_dir: str = "results/logs",
    log_level: str = "INFO"
) -> logging.Logger:
    """
    为实验创建专用logger
    
    Args:
        experiment_name: 实验名称
        log_dir: 日志目录
        log_level: 日志级别
        
    Returns:
        实验logger
    """
    # 创建带时间戳的日志文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{experiment_name}_{timestamp}.log"
    log_path = Path(log_dir) / log_filename
    
    # 确保日志目录存在
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger(f"experiment_{experiment_name}")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有handlers
    logger.handlers.clear()
    
    # 创建formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件handler
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Created experiment logger for: {experiment_name}")
    logger.info(f"Log file: {log_path}")
    
    return logger

class LoggerMixin:
    """Logger混入类，为其他类提供日志功能"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = None
    
    @property
    def logger(self) -> logging.Logger:
        """获取logger实例"""
        if self._logger is None:
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
    
    def log_info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
    
    def log_error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
    
    def log_debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)
