#!/usr/bin/env python3

"""
Legacy FastMCP Standalone Server

This file is deprecated in favor of the modular FastMCP implementation.
Use services/shared/fastmcp_server.py instead.
"""

import sys
from pathlib import Path
import structlog

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    print("❌ FastMCP not available. Please install: pip install fastmcp")
    FASTMCP_AVAILABLE = False

from services.shared.fastmcp_server import ModularFastMCPServer, create_fastmcp_server

logger = structlog.get_logger(__name__)


def create_fastmcp_server_legacy(data_file_path: str = None) -> FastMCP:
    """
    Legacy function for backward compatibility.
    
    This function is deprecated. Use the modular FastMCP server instead:
    from services.shared.fastmcp_server import create_fastmcp_server
    """
    logger.warning("Using deprecated legacy FastMCP server function. "
                  "Please migrate to services.shared.fastmcp_server.create_fastmcp_server")
    
    return create_fastmcp_server(data_file_path)


def main():
    """
    Main entry point for legacy server.
    
    This is deprecated. Use the modular server instead:
    python services/shared/fastmcp_server.py
    """
    logger.warning("Running deprecated legacy FastMCP server. "
                  "Please use the modular server: python services/shared/fastmcp_server.py")
    
    if not FASTMCP_AVAILABLE:
        print("❌ FastMCP not available. Please install: pip install fastmcp")
        sys.exit(1)
    
    try:
        # Create and run modular server
        server = ModularFastMCPServer("Legacy Insurance Server")
        
        if not server.setup():
            logger.error("Failed to setup FastMCP server")
            sys.exit(1)
        
        logger.info("🚀 Starting Legacy FastMCP Insurance Server...")
        logger.info("📝 Total tool modules: 5")
        logger.info("📝 Total tools: 15")
        
        # Run server
        server.run(transport="sse")
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error("Server failed", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 