"""
Environments module for KGRL research framework.

This module provides environment adapters for different text-based environments:
- BaseEnvironment: Abstract base class for all environments
- TextWorldAdapter: TextWorld environment with mock fallback
"""

from .base_env import BaseEnvironment, EnvironmentState
from .textworld_adapter import TextWorldAdapter

__all__ = [
    "BaseEnvironment",
    "EnvironmentState", 
    "TextWorldAdapter"
]
