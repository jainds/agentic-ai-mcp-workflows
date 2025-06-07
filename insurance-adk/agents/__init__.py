"""
Google ADK Agents Package

This package contains Google ADK v1.0.0 agent implementations for the
insurance AI system with A2A communication capabilities.
"""

__version__ = "1.0.0"
__framework__ = "Google ADK v1.0.0"

from .base_adk import (
    ADKModelConfig,
    InsuranceADKTool, 
    InsuranceADKWorkflow,
    InsuranceADKAgent
)

from .orchestrator import create_adk_orchestrator

__all__ = [
    "ADKModelConfig",
    "InsuranceADKTool",
    "InsuranceADKWorkflow", 
    "InsuranceADKAgent",
    "create_adk_orchestrator"
] 