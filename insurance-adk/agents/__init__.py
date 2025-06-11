"""
Google ADK Agents Package

This package contains Google ADK v1.2.1 agent implementations for the
insurance AI system with A2A communication capabilities.
"""

__version__ = "1.2.1"
__framework__ = "Google ADK v1.2.1"

from .orchestrator import create_adk_orchestrator, ADKOrchestrator

__all__ = [
    "create_adk_orchestrator",
    "ADKOrchestrator"
] 