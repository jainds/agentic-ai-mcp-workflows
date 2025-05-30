"""
Base Tools Module

Provides base functionality and logging for all FastMCP tool modules.
"""

import structlog
from typing import Dict, Any, Optional
import json
from pathlib import Path

logger = structlog.get_logger(__name__)


class BaseTools:
    """Base class for all FastMCP tool categories"""
    
    def __init__(self, data_service):
        self.data_service = data_service
        self.logger = logger.bind(tool_category=self.__class__.__name__)
        self.logger.info("Initializing tool category", category=self.__class__.__name__)
    
    def log_tool_call(self, tool_name: str, params: Dict[str, Any]) -> None:
        """Log a tool call with parameters"""
        self.logger.info("Tool called", 
                        tool=tool_name, 
                        params=self._safe_log_params(params))
    
    def log_tool_result(self, tool_name: str, result: Dict[str, Any]) -> None:
        """Log tool result"""
        success = result.get('success', False)
        if success:
            self.logger.info("Tool completed successfully", 
                           tool=tool_name,
                           data_count=len(result.get('data', [])) if isinstance(result.get('data'), list) else 1)
        else:
            self.logger.error("Tool failed", 
                            tool=tool_name,
                            error=result.get('error', 'Unknown error'))
    
    def log_tool_error(self, tool_name: str, error: Exception) -> None:
        """Log tool execution error"""
        self.logger.error("Tool execution failed", 
                         tool=tool_name,
                         error=str(error),
                         exc_info=True)
    
    def _safe_log_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Safely log parameters, removing sensitive data"""
        safe_params = {}
        for key, value in params.items():
            if key.lower() in ['password', 'token', 'secret', 'key']:
                safe_params[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 100:
                safe_params[key] = value[:97] + "..."
            else:
                safe_params[key] = value
        return safe_params
    
    def format_mcp_response(self, result: Dict[str, Any]) -> str:
        """Format result as MCP-compliant string response"""
        try:
            return json.dumps(result, default=str, ensure_ascii=False)
        except Exception as e:
            self.logger.error("Failed to format MCP response", error=str(e))
            return json.dumps({
                "success": False,
                "error": f"Response formatting failed: {str(e)}"
            })
    
    def handle_tool_execution(self, tool_name: str, tool_func, **kwargs) -> str:
        """Standard tool execution handler with logging"""
        try:
            self.log_tool_call(tool_name, kwargs)
            
            # Execute the tool function
            result = tool_func(**kwargs)
            
            self.log_tool_result(tool_name, result)
            return self.format_mcp_response(result)
            
        except Exception as e:
            self.log_tool_error(tool_name, e)
            error_result = {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
                "tool": tool_name
            }
            return self.format_mcp_response(error_result) 