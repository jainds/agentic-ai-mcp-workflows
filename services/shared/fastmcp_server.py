#!/usr/bin/env python3

"""
Modular FastMCP Server

A properly implemented FastMCP server with modular tool organization,
comprehensive logging, and MCP protocol compliance.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional
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
    sys.exit(1)

from services.shared.fastmcp_data_service import FastMCPDataService
from services.shared.fastmcp_tools import (
    UserTools, PolicyTools, ClaimsTools, AnalyticsTools, QuoteTools
)

# Setup logging
logger = structlog.get_logger(__name__)


class ModularFastMCPServer:
    """Modular FastMCP server with comprehensive logging and tool management"""
    
    def __init__(self, server_name: str = "Insurance Data Service"):
        self.server_name = server_name
        self.mcp_server = None
        self.data_service = None
        self.tool_modules = {}
        self.logger = logger.bind(component="FastMCPServer")
        
        self.logger.info("Initializing modular FastMCP server", server_name=server_name)
    
    def initialize_data_service(self, data_file_path: Optional[str] = None) -> bool:
        """Initialize the data service with proper error handling"""
        try:
            self.logger.info("Initializing data service", data_file=data_file_path)
            self.data_service = FastMCPDataService(data_file_path)
            
            # Log data statistics
            data_stats = {
                "users": len(self.data_service.data.get('users', [])),
                "policies": len(self.data_service.data.get('policies', [])),
                "claims": len(self.data_service.data.get('claims', [])),
                "quotes": len(self.data_service.data.get('quotes', []))
            }
            self.logger.info("Data service initialized successfully", **data_stats)
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize data service", error=str(e), exc_info=True)
            return False
    
    def create_mcp_server(self) -> bool:
        """Create the FastMCP server instance"""
        try:
            if not FASTMCP_AVAILABLE:
                self.logger.error("FastMCP library not available")
                return False
            
            self.logger.info("Creating FastMCP server instance")
            self.mcp_server = FastMCP(self.server_name)
            self.logger.info("FastMCP server instance created successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to create FastMCP server", error=str(e), exc_info=True)
            return False
    
    def initialize_tool_modules(self) -> bool:
        """Initialize all tool modules"""
        try:
            if not self.data_service:
                self.logger.error("Data service not initialized")
                return False
            
            self.logger.info("Initializing tool modules")
            
            # Initialize each tool module
            tool_classes = [
                ("user", UserTools),
                ("policy", PolicyTools),
                ("claims", ClaimsTools),
                ("analytics", AnalyticsTools),
                ("quote", QuoteTools)
            ]
            
            for tool_name, tool_class in tool_classes:
                try:
                    self.logger.info("Initializing tool module", module=tool_name)
                    self.tool_modules[tool_name] = tool_class(self.data_service)
                    self.logger.info("Tool module initialized", module=tool_name)
                except Exception as e:
                    self.logger.error("Failed to initialize tool module", 
                                    module=tool_name, error=str(e))
                    return False
            
            total_modules = len(self.tool_modules)
            self.logger.info("All tool modules initialized successfully", total_modules=total_modules)
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize tool modules", error=str(e), exc_info=True)
            return False
    
    def register_all_tools(self) -> bool:
        """Register all tools with the FastMCP server"""
        try:
            if not self.mcp_server:
                self.logger.error("FastMCP server not created")
                return False
            
            if not self.tool_modules:
                self.logger.error("Tool modules not initialized")
                return False
            
            self.logger.info("Registering all tools with FastMCP server")
            total_tools = 0
            
            for module_name, tool_module in self.tool_modules.items():
                try:
                    self.logger.info("Registering tools from module", module=module_name)
                    tool_module.register_tools(self.mcp_server)
                    # Count tools (estimate based on module)
                    module_tools = {
                        "user": 3, "policy": 3, "claims": 4, 
                        "analytics": 3, "quote": 2
                    }.get(module_name, 0)
                    total_tools += module_tools
                    
                except Exception as e:
                    self.logger.error("Failed to register tools from module", 
                                    module=module_name, error=str(e))
                    return False
            
            self.logger.info("All tools registered successfully", total_tools=total_tools)
            return True
            
        except Exception as e:
            self.logger.error("Failed to register tools", error=str(e), exc_info=True)
            return False
    
    def validate_server_setup(self) -> bool:
        """Validate that the server is properly set up"""
        try:
            self.logger.info("Validating server setup")
            
            # Check server instance
            if not self.mcp_server:
                self.logger.error("FastMCP server not created")
                return False
            
            # Check data service
            if not self.data_service:
                self.logger.error("Data service not initialized")
                return False
            
            # Check tool modules
            if not self.tool_modules:
                self.logger.error("No tool modules initialized")
                return False
            
            expected_modules = {"user", "policy", "claims", "analytics", "quote"}
            actual_modules = set(self.tool_modules.keys())
            
            if not expected_modules.issubset(actual_modules):
                missing = expected_modules - actual_modules
                self.logger.error("Missing tool modules", missing=list(missing))
                return False
            
            self.logger.info("Server setup validation passed")
            return True
            
        except Exception as e:
            self.logger.error("Server setup validation failed", error=str(e), exc_info=True)
            return False
    
    def setup(self, data_file_path: Optional[str] = None) -> bool:
        """Complete server setup process"""
        self.logger.info("Starting FastMCP server setup")
        
        # Step 1: Initialize data service
        if not self.initialize_data_service(data_file_path):
            self.logger.error("Setup failed: data service initialization")
            return False
        
        # Step 2: Create MCP server
        if not self.create_mcp_server():
            self.logger.error("Setup failed: MCP server creation")
            return False
        
        # Step 3: Initialize tool modules
        if not self.initialize_tool_modules():
            self.logger.error("Setup failed: tool modules initialization")
            return False
        
        # Step 4: Register tools
        if not self.register_all_tools():
            self.logger.error("Setup failed: tool registration")
            return False
        
        # Step 5: Validate setup
        if not self.validate_server_setup():
            self.logger.error("Setup failed: validation")
            return False
        
        self.logger.info("FastMCP server setup completed successfully")
        return True
    
    def get_server_info(self) -> dict:
        """Get comprehensive server information"""
        try:
            info = {
                "server_name": self.server_name,
                "fastmcp_available": FASTMCP_AVAILABLE,
                "server_created": self.mcp_server is not None,
                "data_service_ready": self.data_service is not None,
                "tool_modules": list(self.tool_modules.keys()) if self.tool_modules else [],
                "total_tool_modules": len(self.tool_modules) if self.tool_modules else 0
            }
            
            if self.data_service:
                info["data_stats"] = {
                    "users": len(self.data_service.data.get('users', [])),
                    "policies": len(self.data_service.data.get('policies', [])),
                    "claims": len(self.data_service.data.get('claims', [])),
                    "quotes": len(self.data_service.data.get('quotes', []))
                }
            
            return info
            
        except Exception as e:
            self.logger.error("Failed to get server info", error=str(e))
            return {"error": str(e)}
    
    def run(self, transport: str = "sse") -> None:
        """Run the FastMCP server"""
        try:
            if not self.mcp_server:
                self.logger.error("Cannot run: server not set up")
                return
            
            self.logger.info("Starting FastMCP server", transport=transport)
            
            # Log server info before starting
            info = self.get_server_info()
            self.logger.info("Server ready", **info)
            
            # Run the server
            self.mcp_server.run(transport=transport)
            
        except KeyboardInterrupt:
            self.logger.info("Server stopped by user")
        except Exception as e:
            self.logger.error("Server failed to start", error=str(e), exc_info=True)
            raise


def create_fastmcp_server(data_file_path: Optional[str] = None) -> Optional[FastMCP]:
    """Factory function to create and setup a FastMCP server"""
    server = ModularFastMCPServer()
    
    if server.setup(data_file_path):
        logger.info("FastMCP server created successfully")
        return server.mcp_server
    else:
        logger.error("Failed to create FastMCP server")
        return None


def main():
    """Main entry point - runs FastMCP server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Modular FastMCP Insurance Server")
    parser.add_argument("--data-file", help="Path to JSON data file")
    parser.add_argument("--transport", default="sse", choices=["sse", "stdio"], 
                       help="Transport type")
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Log level")
    
    args = parser.parse_args()
    
    # Configure logging level
    import logging
    logging.basicConfig(level=getattr(logging, args.log_level))
    
    if not FASTMCP_AVAILABLE:
        print("❌ FastMCP not available. Please install: pip install fastmcp")
        sys.exit(1)
    
    try:
        # Create and setup server
        server = ModularFastMCPServer()
        
        if not server.setup(args.data_file):
            logger.error("Failed to setup FastMCP server")
            sys.exit(1)
        
        # Run server
        server.run(transport=args.transport)
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error("Server failed", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 