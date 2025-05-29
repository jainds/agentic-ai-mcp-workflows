"""
Base A2A Agent implementation following Google's Agent-to-Agent Protocol.
Provides common functionality for all agents including agent card serving,
task handling, and authentication.
"""

import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import logging
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import httpx
import structlog

logger = structlog.get_logger(__name__)
security = HTTPBearer()


@dataclass
class AgentCard:
    """Agent Card as per A2A specification"""
    name: str
    description: str
    url: str
    version: str
    capabilities: Dict[str, bool]
    endpoints: Dict[str, str]
    schemas: Dict[str, Any]


class TaskRequest(BaseModel):
    """A2A Task Request format"""
    taskId: str
    user: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    

class TaskResponse(BaseModel):
    """A2A Task Response format"""
    taskId: str
    parts: List[Dict[str, Any]]
    status: str = "completed"
    metadata: Optional[Dict[str, Any]] = None


class A2AAgent(ABC):
    """Base class for all A2A agents"""
    
    def __init__(
        self,
        name: str,
        description: str,
        port: int = 8000,
        host: str = "0.0.0.0",
        capabilities: Optional[Dict[str, bool]] = None
    ):
        self.name = name
        self.description = description
        self.port = port
        self.host = host
        self.app = FastAPI(title=f"{name} A2A Agent", version="1.0.0")
        
        # Default capabilities
        self.capabilities = capabilities or {
            "streaming": False,
            "pushNotifications": False,
            "fileUpload": False,
            "messageHistory": True
        }
        
        # Task tracking
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_history: List[Dict[str, Any]] = []
        
        # Agent registry (discovered agents)
        self.agent_registry: Dict[str, AgentCard] = {}
        
        self._setup_routes()
        self._setup_middleware()
    
    def _setup_routes(self):
        """Setup standard A2A endpoints"""
        
        @self.app.get("/.well-known/agent.json")
        async def get_agent_card():
            """Serve agent card as per A2A spec"""
            card = AgentCard(
                name=self.name,
                description=self.description,
                url=f"http://localhost:{self.port}",  # In K8s this would be service URL
                version="1.0.0",
                capabilities=self.capabilities,
                endpoints={
                    "tasks": "/tasks/send",
                    "status": "/tasks/status",
                    "discovery": "/agents/discover"
                },
                schemas={
                    "task_request": TaskRequest.model_json_schema(),
                    "task_response": TaskResponse.model_json_schema()
                }
            )
            return asdict(card)
        
        @self.app.post("/tasks/send", response_model=TaskResponse)
        async def handle_task(
            task: TaskRequest,
            background_tasks: BackgroundTasks,
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            """Handle incoming A2A task"""
            # Validate token (simplified - in production use OAuth2)
            if not self._validate_token(credentials.credentials):
                raise HTTPException(status_code=401, detail="Invalid token")
            
            logger.info("Received A2A task", task_id=task.taskId, agent=self.name)
            
            # Track task
            self.active_tasks[task.taskId] = {
                "task": task.dict(),
                "status": "processing",
                "started_at": datetime.utcnow().isoformat(),
                "agent": self.name
            }
            
            try:
                # Process task (abstract method)
                response = await self.process_task(task)
                
                # Update task status
                self.active_tasks[task.taskId]["status"] = "completed"
                self.active_tasks[task.taskId]["completed_at"] = datetime.utcnow().isoformat()
                self.active_tasks[task.taskId]["response"] = response.dict()
                
                # Move to history
                self.task_history.append(self.active_tasks[task.taskId])
                del self.active_tasks[task.taskId]
                
                logger.info("Task completed", task_id=task.taskId, agent=self.name)
                return response
                
            except Exception as e:
                logger.error("Task failed", task_id=task.taskId, error=str(e), agent=self.name)
                self.active_tasks[task.taskId]["status"] = "failed"
                self.active_tasks[task.taskId]["error"] = str(e)
                raise HTTPException(status_code=500, detail=f"Task processing failed: {str(e)}")
        
        @self.app.get("/tasks/status/{task_id}")
        async def get_task_status(task_id: str):
            """Get status of a specific task"""
            if task_id in self.active_tasks:
                return self.active_tasks[task_id]
            
            # Check history
            for task in self.task_history:
                if task["task"]["taskId"] == task_id:
                    return task
            
            raise HTTPException(status_code=404, detail="Task not found")
        
        @self.app.get("/tasks/active")
        async def get_active_tasks():
            """Get all active tasks"""
            return list(self.active_tasks.values())
        
        @self.app.get("/tasks/history")
        async def get_task_history():
            """Get task history"""
            return self.task_history[-50:]  # Last 50 tasks
        
        @self.app.post("/agents/discover")
        async def discover_agents(agent_urls: List[str]):
            """Discover other agents and cache their cards"""
            discovered = []
            
            async with httpx.AsyncClient() as client:
                for url in agent_urls:
                    try:
                        response = await client.get(f"{url}/.well-known/agent.json")
                        if response.status_code == 200:
                            agent_data = response.json()
                            self.agent_registry[agent_data["name"]] = AgentCard(**agent_data)
                            discovered.append(agent_data)
                    except Exception as e:
                        logger.warning("Failed to discover agent", url=url, error=str(e))
            
            return {"discovered": discovered}
        
        @self.app.get("/agents/registry")
        async def get_agent_registry():
            """Get discovered agents registry"""
            return {name: asdict(card) for name, card in self.agent_registry.items()}
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for Kubernetes"""
            return {
                "status": "healthy",
                "agent": self.name,
                "active_tasks": len(self.active_tasks),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _setup_middleware(self):
        """Setup logging and monitoring middleware"""
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.requests import Request
        import time
        
        class LoggingMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                start_time = time.time()
                response = await call_next(request)
                process_time = time.time() - start_time
                
                logger.info(
                    "Request processed",
                    method=request.method,
                    url=str(request.url),
                    status_code=response.status_code,
                    process_time=process_time
                )
                return response
        
        self.app.add_middleware(LoggingMiddleware)
    
    def _validate_token(self, token: str) -> bool:
        """Validate JWT token (simplified implementation)"""
        # In production, validate JWT with proper verification
        return token and len(token) > 10
    
    async def send_task_to_agent(
        self,
        agent_name: str,
        task_data: Dict[str, Any],
        token: str
    ) -> TaskResponse:
        """Send task to another agent via A2A"""
        if agent_name not in self.agent_registry:
            raise ValueError(f"Agent {agent_name} not found in registry")
        
        agent_card = self.agent_registry[agent_name]
        task_request = TaskRequest(
            taskId=str(uuid.uuid4()),
            user=task_data
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{agent_card.url}/tasks/send",
                json=task_request.dict(),
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                return TaskResponse(**response.json())
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Agent {agent_name} returned error: {response.text}"
                )
    
    @abstractmethod
    async def process_task(self, task: TaskRequest) -> TaskResponse:
        """Process an A2A task - must be implemented by subclasses"""
        pass
    
    def run(self):
        """Run the agent server"""
        import uvicorn
        logger.info(f"Starting {self.name} agent on {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port)


# Utility functions for A2A communication
class A2AClient:
    """Client for sending requests to A2A agents"""
    
    def __init__(self, token: str):
        self.token = token
        self.client = httpx.AsyncClient()
    
    async def discover_agent(self, agent_url: str) -> Optional[AgentCard]:
        """Discover an agent and return its card"""
        try:
            response = await self.client.get(f"{agent_url}/.well-known/agent.json")
            if response.status_code == 200:
                return AgentCard(**response.json())
        except Exception as e:
            logger.error("Failed to discover agent", url=agent_url, error=str(e))
        return None
    
    async def send_task(
        self,
        agent_url: str,
        task_data: Dict[str, Any]
    ) -> TaskResponse:
        """Send a task to an agent"""
        task_request = TaskRequest(
            taskId=str(uuid.uuid4()),
            user=task_data
        )
        
        response = await self.client.post(
            f"{agent_url}/tasks/send",
            json=task_request.dict(),
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        if response.status_code == 200:
            return TaskResponse(**response.json())
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Task failed: {response.text}"
            )
    
    async def get_task_status(self, agent_url: str, task_id: str):
        """Get status of a task"""
        response = await self.client.get(f"{agent_url}/tasks/status/{task_id}")
        if response.status_code == 200:
            return response.json()
        return None
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose() 