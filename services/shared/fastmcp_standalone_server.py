#!/usr/bin/env python3
"""
Standalone FastMCP Server
A complete FastMCP server implementation for insurance data operations
Can be run independently for testing and development
"""

import asyncio
import os
import uvicorn
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from mcp.server.sse import SseServerTransport
from .fastmcp_data_service import get_data_service

# Setup logging
logger = structlog.get_logger(__name__)

class StandaloneFastMCPServer:
    """Standalone FastMCP server with proper SSE transport"""
    
    def __init__(self, port: int = 9000, host: str = "0.0.0.0"):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="FastMCP Insurance Server",
            description="Insurance data service using FastMCP with proper MCP protocol",
            version="1.0.0"
        )
        
        # Initialize data service
        self.data_service = get_data_service()
        
        # Setup SSE transport
        self.sse = SseServerTransport("/messages/")
        
        # Setup FastAPI app
        self._setup_app()
    
    def _setup_app(self):
        """Setup FastAPI application with proper MCP integration"""
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                tools_count = len(self.data_service.get_available_tools())
                return JSONResponse({
                    "status": "healthy",
                    "service": "fastmcp-insurance-server",
                    "tools_count": tools_count,
                    "mcp_protocol": "sse"
                })
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return JSONResponse({
                    "status": "unhealthy",
                    "error": str(e)
                }, status_code=503)
        
        # Root endpoint
        @self.app.get("/")
        async def root():
            """Root endpoint with service information"""
            return {
                "service": "FastMCP Insurance Server",
                "version": "1.0.0",
                "mcp_protocol": "sse",
                "endpoints": {
                    "health": "/health",
                    "sse": "/sse",
                    "messages": "/messages/"
                },
                "tools_available": len(self.data_service.get_available_tools())
            }
        
        # SSE endpoint for MCP protocol
        @self.app.get("/sse")
        async def handle_sse(request: Request):
            """
            SSE endpoint that connects to the MCP server
            
            This endpoint establishes a Server-Sent Events connection with the client
            and forwards communication to the Model Context Protocol server.
            """
            logger.info("SSE connection requested")
            
            try:
                # Get the MCP server instance
                mcp_server = self.data_service.get_server()
                if not mcp_server:
                    logger.error("MCP server not available from data service")
                    return JSONResponse({
                        "error": "MCP server not available"
                    }, status_code=503)
                
                # Use SSE transport to establish connection
                async with self.sse.connect_sse(
                    request.scope, 
                    request.receive, 
                    request._send
                ) as (read_stream, write_stream):
                    logger.info("SSE connection established, running MCP server")
                    
                    # Run the MCP server with the established streams
                    await mcp_server._mcp_server.run(
                        read_stream,
                        write_stream,
                        mcp_server._mcp_server.create_initialization_options(),
                    )
                    
            except Exception as e:
                logger.error(f"SSE connection failed: {e}", exc_info=True)
                return JSONResponse({
                    "error": f"SSE connection failed: {str(e)}"
                }, status_code=500)
        
        # Mount the messages endpoint for SSE transport
        self.app.router.routes.append(
            Mount("/messages", app=self.sse.handle_post_message)
        )
        
        logger.info("FastMCP server configured with proper SSE transport")
    
    def run(self):
        """Run the server"""
        logger.info(f"Starting FastMCP Insurance Server on {self.host}:{self.port}")
        logger.info(f"Available Tools: {len(self.data_service.get_available_tools())}")
        logger.info("Using proper MCP protocol with SSE transport")
        
        # List available tools for debugging
        tools = self.data_service.get_available_tools()
        for tool in tools:
            logger.info(f"Tool available: {tool['name']} - {tool['description']}")
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="FastMCP Insurance Server with SSE")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9000, help="Port to bind to")
    parser.add_argument("--data-file", help="Path to JSON data file")
    
    args = parser.parse_args()
    
    # Set data file if provided
    if args.data_file:
        os.environ["FASTMCP_DATA_FILE"] = args.data_file
    
    # Create and run server
    server = StandaloneFastMCPServer(port=args.port, host=args.host)
    server.run()


if __name__ == "__main__":
    main() 