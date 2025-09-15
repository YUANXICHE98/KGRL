"""
KGRL: Knowledge Graph Enhanced Reinforcement Learning

A research framework for combining knowledge graphs with reinforcement learning
for complex decision making tasks.
"""

__version__ = "1.0.0"
__author__ = "KGRL Research Team"
__email__ = "research@example.com"

# Core imports
from .agents import *
from .environments import *
from .knowledge import *
from .reasoning import *
from .rl import *
from .integration import *
from .evaluation import *
from .utils import *

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    
    # Core modules
    "agents",
    "environments", 
    "knowledge",
    "reasoning",
    "rl",
    "integration",
    "evaluation",
    "utils",
]
