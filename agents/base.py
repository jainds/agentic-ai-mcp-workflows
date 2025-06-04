import asyncio
import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import httpx
from pydantic import BaseModel


class AgentType(str, Enum):
    DOMAIN = "domain"
    TECHNICAL = "technical"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentMessage:
    """Standard message format for agent communication"""
    id: str
    sender: str
    recipient: str
    content: Dict[str, Any]
    timestamp: datetime
    message_type: str = "task"
    correlation_id: Optional[str] = None


@dataclass
class AgentTask:
    """Represents a task that can be executed by an agent"""
    task_id: str
    skill_name: str
    parameters: Dict[str, Any]
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class AgentSkill:
    """Decorator for marking agent skills"""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    def __call__(self, func: Callable):
        func._skill_name = self.name
        func._skill_description = self.description
        return func


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, name: str, agent_type: AgentType, port: int = 8000):
        self.name = name
        self.agent_type = agent_type
        self.port = port
        self.skills: Dict[str, Callable] = {}
        self.logger = self._setup_logging()
        self._register_skills()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the agent"""
        logger = logging.getLogger(f"agent.{self.name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def _register_skills(self):
        """Register all skills defined in the agent"""
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, '_skill_name'):
                self.skills[attr._skill_name] = attr
                self.logger.info(f"Registered skill: {attr._skill_name}")

    @abstractmethod
    async def execute_skill(self, skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific skill"""
        pass

    async def process_task(self, task: AgentTask) -> AgentTask:
        """Process a task by executing the appropriate skill"""
        try:
            task.status = TaskStatus.IN_PROGRESS
            self.logger.info(f"Processing task {task.task_id}: {task.skill_name}")
            
            result = await self.execute_skill(task.skill_name, task.parameters)
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            self.logger.info(f"Task {task.task_id} completed successfully")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            
            self.logger.error(f"Task {task.task_id} failed: {str(e)}")
        
        return task

    def get_skill_info(self) -> Dict[str, Dict[str, str]]:
        """Get information about available skills"""
        skill_info = {}
        for skill_name, skill_func in self.skills.items():
            skill_info[skill_name] = {
                "name": skill_name,
                "description": getattr(skill_func, '_skill_description', ''),
                "agent": self.name
            }
        return skill_info


class TechnicalAgent(BaseAgent):
    """Base class for technical agents that interact with backend services"""
    
    def __init__(self, name: str, service_url: str, port: int = 8000):
        self.service_url = service_url
        self.http_client = None
        super().__init__(name, AgentType.TECHNICAL, port)

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        return self.http_client

    async def execute_skill(self, skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a technical skill by calling backend service"""
        if skill_name not in self.skills:
            raise ValueError(f"Skill '{skill_name}' not found")
        
        skill_func = self.skills[skill_name]
        return await skill_func(**parameters)

    async def make_service_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to the backend service"""
        client = await self._get_http_client()
        url = f"{self.service_url}{endpoint}"
        
        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error calling {url}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error calling {url}: {str(e)}")
            raise

    async def close(self):
        """Close HTTP client"""
        if self.http_client:
            await self.http_client.aclose()


class DomainAgent(BaseAgent):
    """Base class for domain agents that orchestrate workflows"""
    
    def __init__(self, name: str, port: int = 8000):
        self.technical_agents: Dict[str, str] = {}  # agent_name -> service_url
        super().__init__(name, AgentType.DOMAIN, port)

    def register_technical_agent(self, agent_name: str, service_url: str):
        """Register a technical agent that this domain agent can call"""
        self.technical_agents[agent_name] = service_url
        self.logger.info(f"Registered technical agent: {agent_name} at {service_url}")

    async def call_technical_agent(self, agent_name: str, skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a skill on a technical agent via A2A protocol"""
        if agent_name not in self.technical_agents:
            raise ValueError(f"Technical agent '{agent_name}' not registered")
        
        agent_url = self.technical_agents[agent_name]
        
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "skill_name": skill_name,
                    "parameters": parameters,
                    "sender": self.name
                }
                
                response = await client.post(f"{agent_url}/execute", json=payload)
                response.raise_for_status()
                
                result = response.json()
                self.logger.info(f"Successfully called {agent_name}.{skill_name}")
                return result
                
            except httpx.HTTPError as e:
                self.logger.error(f"Error calling {agent_name}.{skill_name}: {str(e)}")
                raise

    async def execute_skill(self, skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a domain skill"""
        if skill_name not in self.skills:
            raise ValueError(f"Skill '{skill_name}' not found")
        
        skill_func = self.skills[skill_name]
        return await skill_func(**parameters)


class AgentServer:
    """HTTP server for agents to receive and process requests"""
    
    def __init__(self, agent: BaseAgent):
        self.agent = agent
        
    async def handle_execute_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle skill execution request"""
        skill_name = request_data.get("skill_name")
        parameters = request_data.get("parameters", {})
        sender = request_data.get("sender", "unknown")
        
        task = AgentTask(
            task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            skill_name=skill_name,
            parameters=parameters,
            status=TaskStatus.PENDING
        )
        
        processed_task = await self.agent.process_task(task)
        
        if processed_task.status == TaskStatus.COMPLETED:
            return {
                "success": True,
                "result": processed_task.result,
                "task_id": processed_task.task_id
            }
        else:
            return {
                "success": False,
                "error": processed_task.error,
                "task_id": processed_task.task_id
            }

    async def handle_health_check(self) -> Dict[str, Any]:
        """Handle health check request"""
        return {
            "status": "healthy",
            "agent": self.agent.name,
            "agent_type": self.agent.agent_type,
            "skills": list(self.agent.skills.keys()),
            "timestamp": datetime.now().isoformat()
        }

    async def handle_skills_request(self) -> Dict[str, Any]:
        """Handle request for available skills"""
        return {
            "agent": self.agent.name,
            "skills": self.agent.get_skill_info()
        }


# Utility functions
def skill(name: str, description: str = ""):
    """Decorator for marking methods as agent skills"""
    return AgentSkill(name, description)


def create_task_id() -> str:
    """Create a unique task ID"""
    return f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"


def format_error_response(error: Exception) -> Dict[str, Any]:
    """Format an error response"""
    return {
        "success": False,
        "error": str(error),
        "error_type": type(error).__name__,
        "timestamp": datetime.now().isoformat()
    }


def format_success_response(data: Any) -> Dict[str, Any]:
    """Format a success response"""
    return {
        "success": True,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }