"""
Base A2A Agent implementation using Official Google A2A Library.
Provides common functionality for all agents including agent card serving,
task handling, and authentication using the official python-a2a library.
"""

import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import logging
import asyncio

# Official Google A2A Library imports
from python_a2a import (
    A2AServer, A2AClient, AgentCard, Message, TextContent, 
    MessageRole, TaskRequest, TaskResponse, run_server
)
from python_a2a.models import TaskStatus, TaskState

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import httpx
import structlog

logger = structlog.get_logger(__name__)
security = HTTPBearer()


class A2AAgent(A2AServer):
    """Base class for all A2A agents using official Google A2A library"""
    
    def __init__(
        self,
        name: str,
        description: str,
        port: int = 8000,
        host: str = "0.0.0.0",
        capabilities: Optional[Dict[str, bool]] = None,
        version: str = "1.0.0"
    ):
        # Create agent card using official A2A library
        agent_card = AgentCard(
            name=name,
            description=description,
            url=f"http://{host}:{port}",
            version=version,
            capabilities=capabilities or {
                "streaming": False,
                "pushNotifications": False,
                "fileUpload": False,
                "messageHistory": True,
                "google_a2a_compatible": True
            }
        )
        
        # Initialize official A2A server
        super().__init__(agent_card=agent_card)
        
        self.name = name
        self.description = description
        self.port = port
        self.host = host
        
        # Task tracking
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_history: List[Dict[str, Any]] = []
        
        # Agent registry (discovered agents)
        self.agent_registry: Dict[str, AgentCard] = {}
        
        # Setup FastAPI app for additional endpoints
        self.app = FastAPI(title=f"{name} A2A Agent", version=version)
        self._setup_additional_routes()
        
        logger.info("A2A Agent initialized with official Google library", 
                   name=name, port=port)
    
    def _setup_additional_routes(self):
        """Setup additional HTTP endpoints beyond standard A2A"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "agent": self.name,
                "version": self.agent_card.version,
                "capabilities": self.agent_card.capabilities
            }
    
    def handle_task(self, task: TaskRequest) -> TaskResponse:
        """Handle incoming A2A tasks - to be implemented by subclasses"""
        # Default implementation - subclasses should override
        task.status = TaskStatus(
            state=TaskState.COMPLETED,
            message={
                "role": "agent",
                "content": {
                    "type": "text",
                    "text": f"Hello from {self.name}! I received your task."
                }
            }
        )
        
        task.artifacts = [{
            "parts": [{
                "type": "text", 
                "text": f"Task {task.taskId} processed by {self.name}"
            }]
        }]
        
        return task
    
    async def call_agent(self, agent_url: str, task_data: Dict[str, Any]) -> Any:
        """Call another A2A agent using official client"""
        try:
            client = A2AClient(agent_url)
            
            # Create task request
            task_request = TaskRequest(
                taskId=str(uuid.uuid4()),
                user=task_data
            )
            
            # Send task using official A2A client
            response = await client.send_task(task_request)
            
            logger.info("Successfully called A2A agent", 
                       agent_url=agent_url, task_id=task_request.taskId)
            
            return response
            
        except Exception as e:
            logger.error("Failed to call A2A agent", 
                        agent_url=agent_url, error=str(e))
            raise
    
    def run(self):
        """Run the A2A agent server"""
        run_server(self, host=self.host, port=self.port)


# Utility functions for A2A communication using official library
class A2AClientWrapper:
    """Wrapper for A2A client with additional functionality"""
    
    def __init__(self, agent_url: str):
        self.agent_url = agent_url
        self.client = A2AClient(agent_url)
    
    async def discover_agent(self) -> Optional[AgentCard]:
        """Discover an agent and return its card"""
        try:
            # Use official A2A discovery
            agent_card = await self.client.discover()
            return agent_card
        except Exception as e:
            logger.error("Failed to discover agent", url=self.agent_url, error=str(e))
        return None
    
    async def send_message(self, message_text: str) -> str:
        """Send a simple text message to an agent"""
        try:
            message = Message(
                content=TextContent(text=message_text),
                role=MessageRole.USER
            )
            
            response = await self.client.send_message(message)
            
            if response and response.content:
                return response.content.text
            
            return "No response received"
            
        except Exception as e:
            logger.error("Failed to send message", error=str(e))
            raise
    
    async def send_task(self, task_data: Dict[str, Any]) -> TaskResponse:
        """Send a task to an agent"""
        task_request = TaskRequest(
            taskId=str(uuid.uuid4()),
            user=task_data
        )
        
        response = await self.client.send_task(task_request)
        return response
    
    async def close(self):
        """Close the client connection"""
        if hasattr(self.client, 'close'):
            await self.client.close()


# Legacy compatibility - maintain existing interface
class TaskRequest(BaseModel):
    """A2A Task Request format - legacy compatibility"""
    taskId: str
    user: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    """A2A Task Response format - legacy compatibility"""
    taskId: str
    parts: List[Dict[str, Any]]
    status: str = "completed"
    metadata: Optional[Dict[str, Any]] = None


# Export the main classes for backward compatibility
__all__ = [
    'A2AAgent', 
    'A2AClientWrapper', 
    'TaskRequest', 
    'TaskResponse',
    'AgentCard',
    'Message',
    'TextContent',
    'MessageRole',
    'run_server'
] 