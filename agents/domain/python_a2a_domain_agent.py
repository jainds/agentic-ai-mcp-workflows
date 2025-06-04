#!/usr/bin/env python3
"""
Python A2A Domain Agent - Main Entry Point
Uses the modular domain agent architecture with separated components
"""

from .domain_agent_core import PythonA2ADomainAgent, main

# For backward compatibility, expose the main class directly
__all__ = ['PythonA2ADomainAgent', 'main']

if __name__ == "__main__":
    main() 