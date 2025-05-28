#!/usr/bin/env python3
"""
Simple Integration Test Runner
Run this to test the multi-agent system without pytest dependency
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from integration.test_agent_communication import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 