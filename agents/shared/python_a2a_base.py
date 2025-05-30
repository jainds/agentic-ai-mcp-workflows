"""
Base A2A Agent implementation using python-a2a library.
Provides common functionality for all agents including agent card serving,
task handling, and routing capabilities using the python-a2a library.
"""

import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
import logging
import asyncio

# python-a2a library imports
from python_a2a import (
    A2AServer, A2AClient, Message, TextContent, MessageRole, run_server,
    AgentCard, Task, TaskState, AgentSkill
)

from pydantic import BaseModel
import structlog

logger = structlog.get_logger(__name__)


class PythonA2AAgent(A2AServer):
    """Base class for all A2A agents using python-a2a library"""
    
    def __init__(
        self,
        name: str,
        description: str,
        port: int = 8000,
        host: str = "0.0.0.0",
        capabilities: Optional[Dict[str, bool]] = None,
        version: str = "1.0.0",
        skills: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        # Initialize python-a2a server
        super().__init__(**kwargs)
        
        self.name = name
        self.description = description
        self.port = port
        self.host = host
        self.version = version
        
        # Default capabilities
        self.capabilities = capabilities or {
            "streaming": True,
            "pushNotifications": False,
            "fileUpload": False,
            "messageHistory": True,
            "python_a2a_compatible": True
        }
        
        # Default skills if none provided
        self.skills = skills or [{
            "id": f"{name.lower().replace(' ', '-')}-skill",
            "name": f"{name} Core Skill",
            "description": description,
            "tags": ["general", "assistant"],
            "examples": [f"Ask {name} to help you with tasks"],
            "inputModes": ["text"],
            "outputModes": ["text"]
        }]
        
        # Task tracking
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_history: List[Dict[str, Any]] = []
        
        # Agent registry (discovered agents)
        self.agent_registry: Dict[str, str] = {}
        
        logger.info("Python A2A Agent initialized", 
                   name=name, port=port, capabilities=self.capabilities)
    
    def get_agent_card(self) -> Dict[str, Any]:
        """Return the agent card for this agent"""
        return {
            "name": self.name,
            "description": self.description,
            "url": f"http://{self.host}:{self.port}",
            "version": self.version,
            "capabilities": self.capabilities,
            "skills": self.skills,
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"]
        }
    
    def handle_message(self, message: Message) -> Message:
        """
        Handle incoming A2A messages - to be implemented by subclasses
        
        Args:
            message: The incoming A2A message
            
        Returns:
            Message: The response message
        """
        # Default implementation - subclasses should override
        response_text = f"Hello from {self.name}! I received your message: {message.content.text}"
        
        return Message(
            content=TextContent(text=response_text),
            role=MessageRole.AGENT,
            parent_message_id=getattr(message, 'message_id', None),
            conversation_id=getattr(message, 'conversation_id', None)
        )
    
    async def call_agent_async(self, agent_url: str, message_text: str) -> str:
        """Call another A2A agent asynchronously"""
        client = A2AClient(agent_url)
        
        # Create message
        message = Message(
            content=TextContent(text=message_text),
            role=MessageRole.USER
        )
        
        # Send message using python-a2a client
        response = client.send_message(message)
        
        logger.info("Successfully called A2A agent", 
                   agent_url=agent_url, message_id=getattr(message, 'message_id', None))
        
        # Handle different response types
        if hasattr(response, 'content') and hasattr(response.content, 'text'):
            return response.content.text
        elif hasattr(response, 'text'):
            return response.text
        else:
            return str(response)
    
    def call_agent(self, agent_url: str, message_text: str) -> str:
        """Call another A2A agent synchronously"""
        client = A2AClient(agent_url)
        
        # Create message
        message = Message(
            content=TextContent(text=message_text),
            role=MessageRole.USER
        )
        
        # Send message using python-a2a client
        response = client.send_message(message)
        
        logger.info("Successfully called A2A agent", 
                   agent_url=agent_url, message_id=getattr(message, 'message_id', None))
        
        # Handle different response types
        if hasattr(response, 'content') and hasattr(response.content, 'text'):
            return response.content.text
        elif hasattr(response, 'text'):
            return response.text
        else:
            return str(response)
    
    def register_agent(self, agent_name: str, agent_url: str):
        """Register another agent for easy communication"""
        self.agent_registry[agent_name] = agent_url
        logger.info("Registered agent", name=agent_name, url=agent_url)
    
    def call_registered_agent(self, agent_name: str, message_text: str) -> str:
        """Call a registered agent by name"""
        if agent_name not in self.agent_registry:
            raise ValueError(f"Agent '{agent_name}' not registered. Available agents: {list(self.agent_registry.keys())}")
        
        return self.call_agent(self.agent_registry[agent_name], message_text)
    
    def run(self):
        """Run the A2A agent server"""
        run_server(self, host=self.host, port=self.port)


# Utility functions for A2A communication using python-a2a library
class PythonA2AClientWrapper:
    """Wrapper for python-a2a client with additional functionality"""
    
    def __init__(self, agent_url: str):
        self.agent_url = agent_url
        self.client = A2AClient(agent_url)
    
    def discover_agent(self) -> Optional[Dict[str, Any]]:
        """Discover an agent and return its card"""
        try:
            # Use python-a2a discovery (assuming it has a discovery method)
            # This would need to be implemented based on the actual python-a2a API
            agent_card = self.client.get_agent_card() if hasattr(self.client, 'get_agent_card') else None
            return agent_card
        except Exception as e:
            logger.error("Failed to discover agent", url=self.agent_url, error=str(e))
        return None
    
    def send_message(self, message_text: str) -> str:
        """Send a simple text message to an agent"""
        try:
            # Create message
            message = Message(
                content=TextContent(text=message_text),
                role=MessageRole.USER
            )
            
            response = self.client.send_message(message)
            
            if response and response.content:
                return response.content.text
            
            return "No response received"
            
        except Exception as e:
            logger.error("Failed to send message", error=str(e))
            raise
    
    def send_task_request(self, task_data: Dict[str, Any]) -> str:
        """Send a task request to an agent"""
        # Convert task data to message format
        task_text = json.dumps(task_data) if isinstance(task_data, dict) else str(task_data)
        return self.send_message(task_text)


# Export the main classes
__all__ = [
    'PythonA2AAgent', 
    'PythonA2AClientWrapper', 
    'Message', 
    'TextContent',
    'MessageRole',
    'run_server'
] 