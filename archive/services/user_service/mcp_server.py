"""
FastMCP Server for User Service
Integrates with the existing FastAPI user service to provide MCP tools
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastmcp import FastMCP
import structlog

logger = structlog.get_logger(__name__)

class UserMCPServer:
    """FastMCP server for user operations"""
    
    def __init__(self, fastapi_app: FastAPI, users_db: Dict[str, Any]):
        self.app = fastapi_app
        self.users_db = users_db
        
        # Initialize FastMCP server
        self.mcp = FastMCP(
            name="user-service",
            dependencies=["fastapi", "structlog", "pydantic"]
        )
        
        self._setup_tools()
        self._setup_resources()
        self._integrate_with_fastapi()
    
    def _setup_tools(self):
        """Setup MCP tools for user operations"""
        
        # Tool: Get user details
        @self.mcp.tool()
        def get_user(user_id: str) -> Dict[str, Any]:
            """Get detailed information about a specific user"""
            try:
                if user_id not in self.users_db:
                    return {
                        "success": False,
                        "error": f"User {user_id} not found",
                        "user_id": user_id
                    }
                
                user = self.users_db[user_id]
                
                # Remove sensitive information
                safe_user = {k: v for k, v in user.items() if k != 'password_hash'}
                
                return {
                    "success": True,
                    "user": safe_user
                }
            except Exception as e:
                logger.error("Error getting user details", user_id=user_id, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "user_id": user_id
                }
        
        # Tool: Authenticate user
        @self.mcp.tool()
        def authenticate_user(email: str, password: str) -> Dict[str, Any]:
            """Authenticate a user with email and password"""
            try:
                import bcrypt
                import jwt
                from datetime import datetime, timedelta
                import os
                
                # Find user by email
                user = None
                for u in self.users_db.values():
                    if u.get('email', '').lower() == email.lower():
                        user = u
                        break
                
                if not user:
                    return {
                        "success": False,
                        "error": "User not found",
                        "email": email
                    }
                
                # Verify password
                if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    return {
                        "success": False,
                        "error": "Invalid password",
                        "email": email
                    }
                
                # Generate JWT token
                SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
                payload = {
                    "user_id": user['id'],
                    "role": user['role'],
                    "exp": datetime.utcnow() + timedelta(hours=24)
                }
                access_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
                
                # Update last login
                user['last_login'] = datetime.utcnow()
                
                # Remove sensitive information
                safe_user = {k: v for k, v in user.items() if k != 'password_hash'}
                
                return {
                    "success": True,
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": safe_user
                }
                
            except Exception as e:
                logger.error("Error authenticating user", email=email, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "email": email
                }
        
        # Tool: List users
        @self.mcp.tool()
        def list_users(role: Optional[str] = None, status: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
            """List users with optional filtering"""
            try:
                users = list(self.users_db.values())
                
                # Apply filters
                if role:
                    users = [u for u in users if u.get('role') == role]
                
                if status:
                    users = [u for u in users if u.get('status') == status]
                
                # Apply limit
                users = users[:limit]
                
                # Remove sensitive information
                safe_users = []
                for user in users:
                    safe_user = {k: v for k, v in user.items() if k != 'password_hash'}
                    safe_users.append(safe_user)
                
                return {
                    "success": True,
                    "users": safe_users,
                    "total_users": len(safe_users),
                    "filters": {"role": role, "status": status, "limit": limit}
                }
            except Exception as e:
                logger.error("Error listing users", role=role, status=status, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "filters": {"role": role, "status": status, "limit": limit}
                }
        
        # Tool: Create user
        @self.mcp.tool()
        def create_user(email: str, password: str, first_name: str, last_name: str, 
                       role: str, phone: Optional[str] = None) -> Dict[str, Any]:
            """Create a new user"""
            try:
                import bcrypt
                import uuid
                from datetime import datetime
                
                # Check if user already exists
                for user in self.users_db.values():
                    if user.get('email', '').lower() == email.lower():
                        return {
                            "success": False,
                            "error": "User with this email already exists",
                            "email": email
                        }
                
                # Generate new user ID
                user_id = f"user_{str(uuid.uuid4())[:8]}"
                
                # Hash password
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                # Create user object
                new_user = {
                    "id": user_id,
                    "email": email.lower(),
                    "password_hash": password_hash,
                    "first_name": first_name,
                    "last_name": last_name,
                    "role": role,
                    "status": "active",
                    "phone": phone,
                    "created_at": datetime.utcnow(),
                    "last_login": None
                }
                
                # Store in database
                self.users_db[user_id] = new_user
                
                logger.info("New user created", user_id=user_id, email=email)
                
                # Remove sensitive information for response
                safe_user = {k: v for k, v in new_user.items() if k != 'password_hash'}
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "user": safe_user,
                    "message": "User successfully created"
                }
                
            except Exception as e:
                logger.error("Error creating user", email=email, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "email": email
                }
        
        # Tool: Update user
        @self.mcp.tool()
        def update_user(user_id: str, first_name: Optional[str] = None, last_name: Optional[str] = None,
                       phone: Optional[str] = None, role: Optional[str] = None, 
                       status: Optional[str] = None) -> Dict[str, Any]:
            """Update an existing user"""
            try:
                if user_id not in self.users_db:
                    return {
                        "success": False,
                        "error": f"User {user_id} not found",
                        "user_id": user_id
                    }
                
                user = self.users_db[user_id]
                
                # Update fields
                updates = {}
                if first_name is not None:
                    user['first_name'] = first_name
                    updates['first_name'] = first_name
                if last_name is not None:
                    user['last_name'] = last_name
                    updates['last_name'] = last_name
                if phone is not None:
                    user['phone'] = phone
                    updates['phone'] = phone
                if role is not None:
                    user['role'] = role
                    updates['role'] = role
                if status is not None:
                    user['status'] = status
                    updates['status'] = status
                
                logger.info("User updated", user_id=user_id, updates=list(updates.keys()))
                
                # Remove sensitive information for response
                safe_user = {k: v for k, v in user.items() if k != 'password_hash'}
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "user": safe_user,
                    "updates": updates
                }
                
            except Exception as e:
                logger.error("Error updating user", user_id=user_id, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "user_id": user_id
                }
    
    def _setup_resources(self):
        """Setup MCP resources for user data"""
        
        # Resource: Get user profile
        @self.mcp.resource("users://user/{user_id}")
        def get_user_resource(user_id: str) -> Dict[str, Any]:
            """Provides user information as a resource"""
            try:
                if user_id not in self.users_db:
                    return {"error": f"User {user_id} not found", "user_id": user_id}
                
                user = self.users_db[user_id]
                # Remove sensitive information
                safe_user = {k: v for k, v in user.items() if k != 'password_hash'}
                return safe_user
            except Exception as e:
                logger.error("Error getting user resource", user_id=user_id, error=str(e))
                return {"error": str(e), "user_id": user_id}
        
        # Resource: Get users by role
        @self.mcp.resource("users://role/{role}")
        def get_users_by_role_resource(role: str) -> Dict[str, Any]:
            """Provides users by role as a resource"""
            try:
                users = [
                    {k: v for k, v in user.items() if k != 'password_hash'}
                    for user in self.users_db.values()
                    if user.get('role') == role
                ]
                return {
                    "role": role,
                    "users": users,
                    "total_users": len(users)
                }
            except Exception as e:
                logger.error("Error getting users by role resource", role=role, error=str(e))
                return {"error": str(e), "role": role}
    
    def _integrate_with_fastapi(self):
        """Integrate FastMCP with FastAPI by adding endpoints"""
        
        # Add FastMCP endpoints to the existing FastAPI app
        @self.app.get("/mcp/tools")
        async def mcp_list_tools():
            """List available MCP tools"""
            try:
                tools = []
                for tool_name in ['get_user', 'authenticate_user', 'list_users', 'create_user', 'update_user']:
                    tools.append({
                        "name": tool_name,
                        "description": f"MCP tool: {tool_name}",
                        "inputSchema": {"type": "object", "properties": {}}
                    })
                
                return {"tools": tools}
            except Exception as e:
                logger.error("Error listing MCP tools", error=str(e))
                return {"error": str(e), "tools": []}
        
        @self.app.post("/mcp/call")
        async def mcp_call_tool(request: Dict[str, Any]):
            """Call an MCP tool"""
            try:
                method = request.get("method", "")
                params = request.get("params", {})
                
                if method != "tools/call":
                    return {"error": f"Unsupported method: {method}"}
                
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                # Route to the appropriate tool function
                if tool_name == "get_user":
                    result = self._tool_get_user(**arguments)
                elif tool_name == "authenticate_user":
                    result = self._tool_authenticate_user(**arguments)
                elif tool_name == "list_users":
                    result = self._tool_list_users(**arguments)
                elif tool_name == "create_user":
                    result = self._tool_create_user(**arguments)
                elif tool_name == "update_user":
                    result = self._tool_update_user(**arguments)
                else:
                    return {"error": f"Tool '{tool_name}' not found"}
                
                return {
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result)
                            }
                        ]
                    }
                }
            except Exception as e:
                logger.error("Error calling MCP tool", error=str(e))
                return {"error": str(e)}
        
        @self.app.get("/mcp/resources")
        async def mcp_list_resources():
            """List available MCP resources"""
            try:
                resources = [
                    {
                        "uri": "users://user/{user_id}",
                        "name": "user_profile",
                        "description": "Get user profile information"
                    },
                    {
                        "uri": "users://role/{role}",
                        "name": "users_by_role", 
                        "description": "Get all users by role"
                    }
                ]
                
                return {"resources": resources}
            except Exception as e:
                logger.error("Error listing MCP resources", error=str(e))
                return {"error": str(e), "resources": []}
    
    # Helper methods for tool calls (to avoid relying on FastMCP internals)
    def _tool_get_user(self, user_id: str) -> Dict[str, Any]:
        """Internal method for get_user tool"""
        try:
            if user_id not in self.users_db:
                return {
                    "success": False,
                    "error": f"User {user_id} not found",
                    "user_id": user_id
                }
            
            user = self.users_db[user_id]
            
            # Remove sensitive information
            safe_user = {k: v for k, v in user.items() if k != 'password_hash'}
            
            return {
                "success": True,
                "user": safe_user
            }
        except Exception as e:
            logger.error("Error getting user details", user_id=user_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    def _tool_authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Internal method for authenticate_user tool"""
        try:
            import bcrypt
            import jwt
            from datetime import datetime, timedelta
            import os
            
            # Find user by email
            user = None
            for u in self.users_db.values():
                if u.get('email', '').lower() == email.lower():
                    user = u
                    break
            
            if not user:
                return {
                    "success": False,
                    "error": "User not found",
                    "email": email
                }
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                return {
                    "success": False,
                    "error": "Invalid password",
                    "email": email
                }
            
            # Generate JWT token
            SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
            payload = {
                "user_id": user['id'],
                "role": user['role'],
                "exp": datetime.utcnow() + timedelta(hours=24)
            }
            access_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            
            # Update last login
            user['last_login'] = datetime.utcnow()
            
            # Remove sensitive information
            safe_user = {k: v for k, v in user.items() if k != 'password_hash'}
            
            return {
                "success": True,
                "access_token": access_token,
                "token_type": "bearer",
                "user": safe_user
            }
            
        except Exception as e:
            logger.error("Error authenticating user", email=email, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "email": email
            }
    
    def _tool_list_users(self, role: Optional[str] = None, status: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Internal method for list_users tool"""
        try:
            users = list(self.users_db.values())
            
            # Apply filters
            if role:
                users = [u for u in users if u.get('role') == role]
            
            if status:
                users = [u for u in users if u.get('status') == status]
            
            # Apply limit
            users = users[:limit]
            
            # Remove sensitive information
            safe_users = []
            for user in users:
                safe_user = {k: v for k, v in user.items() if k != 'password_hash'}
                safe_users.append(safe_user)
            
            return {
                "success": True,
                "users": safe_users,
                "total_users": len(safe_users),
                "filters": {"role": role, "status": status, "limit": limit}
            }
        except Exception as e:
            logger.error("Error listing users", role=role, status=status, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "filters": {"role": role, "status": status, "limit": limit}
            }
    
    def _tool_create_user(self, email: str, password: str, first_name: str, last_name: str, 
                         role: str, phone: Optional[str] = None) -> Dict[str, Any]:
        """Internal method for create_user tool"""
        try:
            import bcrypt
            import uuid
            from datetime import datetime
            
            # Check if user already exists
            for user in self.users_db.values():
                if user.get('email', '').lower() == email.lower():
                    return {
                        "success": False,
                        "error": "User with this email already exists",
                        "email": email
                    }
            
            # Generate new user ID
            user_id = f"user_{str(uuid.uuid4())[:8]}"
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create user object
            new_user = {
                "id": user_id,
                "email": email.lower(),
                "password_hash": password_hash,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "status": "active",
                "phone": phone,
                "created_at": datetime.utcnow(),
                "last_login": None
            }
            
            # Store in database
            self.users_db[user_id] = new_user
            
            logger.info("New user created", user_id=user_id, email=email)
            
            # Remove sensitive information for response
            safe_user = {k: v for k, v in new_user.items() if k != 'password_hash'}
            
            return {
                "success": True,
                "user_id": user_id,
                "user": safe_user,
                "message": "User successfully created"
            }
            
        except Exception as e:
            logger.error("Error creating user", email=email, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "email": email
            }
    
    def _tool_update_user(self, user_id: str, first_name: Optional[str] = None, last_name: Optional[str] = None,
                         phone: Optional[str] = None, role: Optional[str] = None, 
                         status: Optional[str] = None) -> Dict[str, Any]:
        """Internal method for update_user tool"""
        try:
            if user_id not in self.users_db:
                return {
                    "success": False,
                    "error": f"User {user_id} not found",
                    "user_id": user_id
                }
            
            user = self.users_db[user_id]
            
            # Update fields
            updates = {}
            if first_name is not None:
                user['first_name'] = first_name
                updates['first_name'] = first_name
            if last_name is not None:
                user['last_name'] = last_name
                updates['last_name'] = last_name
            if phone is not None:
                user['phone'] = phone
                updates['phone'] = phone
            if role is not None:
                user['role'] = role
                updates['role'] = role
            if status is not None:
                user['status'] = status
                updates['status'] = status
            
            logger.info("User updated", user_id=user_id, updates=list(updates.keys()))
            
            # Remove sensitive information for response
            safe_user = {k: v for k, v in user.items() if k != 'password_hash'}
            
            return {
                "success": True,
                "user_id": user_id,
                "user": safe_user,
                "updates": updates
            }
            
        except Exception as e:
            logger.error("Error updating user", user_id=user_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            } 