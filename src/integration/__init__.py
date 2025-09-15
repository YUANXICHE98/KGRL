"""
Integration module for KGRL research framework.

This module provides system integration capabilities:
- ExperimentRunner: Unified experiment execution and management
"""

try:
    from .orchestrator import SystemOrchestrator
    from .mode_controller import ModeController
    from .pipeline_manager import PipelineManager
    LEGACY_AVAILABLE = True
except ImportError:
    LEGACY_AVAILABLE = False

from .experiment_runner import ExperimentRunner

__all__ = [
    "ExperimentRunner"
]

if LEGACY_AVAILABLE:
    __all__.extend([
        "SystemOrchestrator",
        "ModeController",
        "PipelineManager"
    ])
