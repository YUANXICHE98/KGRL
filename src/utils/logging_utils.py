"""
Logging utilities for KGRL research framework.

Provides unified logging configuration and management.
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
    Setup global logging configuration.
    
    Args:
        log_level: Logging level
        log_file: Log file path
        log_format: Log format string
        
    Returns:
        Configured logger
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if file path specified)
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Get logger with specified name.
    
    Args:
        name: Logger name
        log_level: Optional log level override
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    if log_level:
        logger.setLevel(getattr(logging, log_level.upper()))
    
    return logger


def create_experiment_logger(
    experiment_name: str,
    log_dir: str = "experiments/logs",
    log_level: str = "INFO"
) -> logging.Logger:
    """
    Create logger for experiment tracking.
    
    Args:
        experiment_name: Name of the experiment
        log_dir: Directory for log files
        log_level: Logging level
        
    Returns:
        Experiment logger
    """
    # Create timestamp for unique log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{experiment_name}_{timestamp}.log"
    log_filepath = Path(log_dir) / log_filename
    
    # Ensure log directory exists
    log_filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(f"experiment_{experiment_name}")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # File handler
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler for important messages
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"Started experiment logging: {experiment_name}")
    logger.info(f"Log file: {log_filepath}")
    
    return logger


def log_experiment_config(logger: logging.Logger, config: dict):
    """
    Log experiment configuration.
    
    Args:
        logger: Logger instance
        config: Configuration dictionary
    """
    logger.info("=== Experiment Configuration ===")
    for key, value in config.items():
        logger.info(f"{key}: {value}")
    logger.info("=== End Configuration ===")


def log_experiment_results(logger: logging.Logger, results: dict):
    """
    Log experiment results.
    
    Args:
        logger: Logger instance
        results: Results dictionary
    """
    logger.info("=== Experiment Results ===")
    for key, value in results.items():
        logger.info(f"{key}: {value}")
    logger.info("=== End Results ===")


class ExperimentLogger:
    """Experiment logger with structured logging capabilities."""
    
    def __init__(self, experiment_name: str, log_dir: str = "experiments/logs"):
        self.experiment_name = experiment_name
        self.log_dir = Path(log_dir)
        self.logger = create_experiment_logger(experiment_name, str(log_dir))
        
        # Metrics tracking
        self.metrics = {}
        self.step_count = 0
    
    def log_config(self, config: dict):
        """Log experiment configuration."""
        log_experiment_config(self.logger, config)
    
    def log_step(self, step: int, metrics: dict):
        """Log step metrics."""
        self.step_count = step
        
        # Update running metrics
        for key, value in metrics.items():
            if key not in self.metrics:
                self.metrics[key] = []
            self.metrics[key].append(value)
        
        # Log to file
        metric_str = ", ".join([f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" 
                               for k, v in metrics.items()])
        self.logger.info(f"Step {step}: {metric_str}")
    
    def log_episode(self, episode: int, episode_metrics: dict):
        """Log episode metrics."""
        metric_str = ", ".join([f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" 
                               for k, v in episode_metrics.items()])
        self.logger.info(f"Episode {episode}: {metric_str}")
    
    def log_results(self, results: dict):
        """Log final results."""
        log_experiment_results(self.logger, results)
    
    def get_metrics(self) -> dict:
        """Get collected metrics."""
        return self.metrics.copy()
    
    def save_metrics(self, filepath: Optional[str] = None):
        """Save metrics to file."""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.log_dir / f"{self.experiment_name}_metrics_{timestamp}.json"
        
        try:
            import json
            
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            
            self.logger.info(f"Saved metrics to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")
    
    def cleanup(self):
        """Clean up logger resources."""
        # Close all handlers
        for handler in self.logger.handlers:
            handler.close()
        
        self.logger.handlers.clear()
