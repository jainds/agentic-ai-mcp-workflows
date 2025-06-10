"""
Google ADK Agents Package

This package contains official Google ADK v1.2.1 agent implementations for the
insurance AI system with A2A communication capabilities.
"""

__version__ = "1.2.1"
__framework__ = "Google ADK v1.2.1"

from .base_adk import (
    InsuranceADKConfig,
    create_insurance_technical_agent,
    create_insurance_domain_agent,
    create_insurance_coordinator_agent,
    create_a2a_agent_card,
    technical_agent,
    domain_agent,
    coordinator_agent
)

from .orchestrator import create_adk_orchestrator, ADKOrchestrator

__all__ = [
    "InsuranceADKConfig",
    "create_insurance_technical_agent",
    "create_insurance_domain_agent",
    "create_insurance_coordinator_agent",
    "create_a2a_agent_card",
    "technical_agent",
    "domain_agent",
    "coordinator_agent",
    "create_adk_orchestrator",
    "ADKOrchestrator"
] 