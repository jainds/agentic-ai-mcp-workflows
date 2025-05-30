"""
User Tools Module

FastMCP tools for user management operations.
"""

from typing import Optional
from .base_tools import BaseTools
import structlog

logger = structlog.get_logger(__name__)


class UserTools(BaseTools):
    """User management tools for FastMCP"""
    
    def __init__(self, data_service):
        super().__init__(data_service)
        self.logger.info("User tools initialized")
    
    def get_user(self, user_id: Optional[str] = None, email: Optional[str] = None) -> str:
        """Get user information by ID or email"""
        return self.handle_tool_execution(
            "get_user",
            self.data_service.get_user,
            user_id=user_id,
            email=email
        )
    
    def list_users(self, role: Optional[str] = None, status: Optional[str] = None) -> str:
        """List all users with optional filtering"""
        return self.handle_tool_execution(
            "list_users",
            self.data_service.list_users,
            role=role,
            status=status
        )
    
    def create_user(self, name: str, email: str, role: str = "customer") -> str:
        """Create a new user (mock write operation)"""
        user_data = {"name": name, "email": email, "role": role}
        return self.handle_tool_execution(
            "create_user",
            self.data_service.create_user,
            user_data=user_data
        )
    
    def register_tools(self, mcp_server):
        """Register all user tools with the FastMCP server"""
        self.logger.info("Registering user tools with FastMCP server")
        
        @mcp_server.tool()
        def get_user(user_id: Optional[str] = None, email: Optional[str] = None) -> str:
            """Get user information by ID or email"""
            return self.get_user(user_id=user_id, email=email)
        
        @mcp_server.tool()
        def list_users(role: Optional[str] = None, status: Optional[str] = None) -> str:
            """List all users with optional filtering"""
            return self.list_users(role=role, status=status)
        
        @mcp_server.tool()
        def create_user(name: str, email: str, role: str = "customer") -> str:
            """Create a new user (mock write operation)"""
            return self.create_user(name=name, email=email, role=role)
        
        self.logger.info("User tools registered successfully", tools_count=3) 