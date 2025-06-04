import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.base import (
    BaseAgent, TechnicalAgent, DomainAgent, AgentType, TaskStatus, 
    AgentTask, AgentServer, skill, create_task_id
)


class TestBaseAgent:
    """Test base agent functionality"""
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        
        class TestAgent(BaseAgent):
            async def execute_skill(self, skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
                return {"result": "test"}
        
        agent = TestAgent("TestAgent", AgentType.TECHNICAL, 8000)
        
        assert agent.name == "TestAgent"
        assert agent.agent_type == AgentType.TECHNICAL
        assert agent.port == 8000
        assert isinstance(agent.skills, dict)
        assert agent.logger is not None

    def test_skill_registration(self):
        """Test skill registration via decorator"""
        
        class TestAgent(BaseAgent):
            @skill("TestSkill", "A test skill")
            def test_skill(self, param1: str) -> str:
                return f"result: {param1}"
            
            async def execute_skill(self, skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
                if skill_name in self.skills:
                    return {"result": self.skills[skill_name](**parameters)}
                return {"error": "Skill not found"}
        
        agent = TestAgent("TestAgent", AgentType.TECHNICAL)
        
        assert "TestSkill" in agent.skills
        assert hasattr(agent.skills["TestSkill"], '_skill_name')
        assert agent.skills["TestSkill"]._skill_name == "TestSkill"
        assert agent.skills["TestSkill"]._skill_description == "A test skill"

    @pytest.mark.asyncio
    async def test_task_processing(self):
        """Test task processing"""
        
        class TestAgent(BaseAgent):
            @skill("EchoSkill", "Echoes input")
            def echo_skill(self, message: str) -> str:
                return f"Echo: {message}"
            
            async def execute_skill(self, skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
                if skill_name == "EchoSkill":
                    result = self.echo_skill(**parameters)
                    return {"success": True, "result": result}
                return {"success": False, "error": "Skill not found"}
        
        agent = TestAgent("TestAgent", AgentType.TECHNICAL)
        
        task = AgentTask(
            task_id="test_task_1",
            skill_name="EchoSkill",
            parameters={"message": "Hello World"},
            status=TaskStatus.PENDING
        )
        
        processed_task = await agent.process_task(task)
        
        assert processed_task.status == TaskStatus.COMPLETED
        assert processed_task.result["success"] is True
        assert processed_task.result["result"] == "Echo: Hello World"
        assert processed_task.completed_at is not None

    @pytest.mark.asyncio
    async def test_task_processing_error(self):
        """Test task processing with error"""
        
        class TestAgent(BaseAgent):
            async def execute_skill(self, skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
                raise Exception("Test error")
        
        agent = TestAgent("TestAgent", AgentType.TECHNICAL)
        
        task = AgentTask(
            task_id="test_task_error",
            skill_name="NonExistentSkill",
            parameters={},
            status=TaskStatus.PENDING
        )
        
        processed_task = await agent.process_task(task)
        
        assert processed_task.status == TaskStatus.FAILED
        assert processed_task.error == "Test error"
        assert processed_task.completed_at is not None

    def test_get_skill_info(self):
        """Test getting skill information"""
        
        class TestAgent(BaseAgent):
            @skill("Skill1", "First skill")
            def skill1(self):
                pass
            
            @skill("Skill2", "Second skill")
            def skill2(self):
                pass
            
            async def execute_skill(self, skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
                return {}
        
        agent = TestAgent("TestAgent", AgentType.TECHNICAL)
        skill_info = agent.get_skill_info()
        
        assert len(skill_info) == 2
        assert "Skill1" in skill_info
        assert "Skill2" in skill_info
        assert skill_info["Skill1"]["description"] == "First skill"
        assert skill_info["Skill2"]["description"] == "Second skill"
        assert skill_info["Skill1"]["agent"] == "TestAgent"


class TestTechnicalAgent:
    """Test technical agent functionality"""
    
    @pytest.mark.asyncio
    async def test_technical_agent_init(self):
        """Test technical agent initialization"""
        agent = TechnicalAgent("TestTechAgent", "http://test-service:8000")
        
        assert agent.name == "TestTechAgent"
        assert agent.agent_type == AgentType.TECHNICAL
        assert agent.service_url == "http://test-service:8000"
        assert agent.http_client is None

    @pytest.mark.asyncio
    async def test_http_client_creation(self):
        """Test HTTP client creation"""
        agent = TechnicalAgent("TestTechAgent", "http://test-service:8000")
        
        client = await agent._get_http_client()
        assert client is not None
        
        # Should return same client on subsequent calls
        client2 = await agent._get_http_client()
        assert client is client2
        
        await agent.close()

    @pytest.mark.asyncio
    async def test_skill_execution(self):
        """Test skill execution in technical agent"""
        
        class TestTechnicalAgent(TechnicalAgent):
            @skill("GetData", "Gets data from service")
            async def get_data(self, id: int) -> Dict[str, Any]:
                return {"id": id, "data": "test_data"}
        
        agent = TestTechnicalAgent("TestAgent", "http://test-service:8000")
        
        result = await agent.execute_skill("GetData", {"id": 123})
        
        assert result["id"] == 123
        assert result["data"] == "test_data"
        
        await agent.close()


class TestDomainAgent:
    """Test domain agent functionality"""
    
    def test_domain_agent_init(self):
        """Test domain agent initialization"""
        agent = DomainAgent("TestDomainAgent")
        
        assert agent.name == "TestDomainAgent"
        assert agent.agent_type == AgentType.DOMAIN
        assert isinstance(agent.technical_agents, dict)

    def test_technical_agent_registration(self):
        """Test registering technical agents"""
        agent = DomainAgent("TestDomainAgent")
        
        agent.register_technical_agent("CustomerAgent", "http://customer-agent:8010")
        agent.register_technical_agent("PolicyAgent", "http://policy-agent:8011")
        
        assert "CustomerAgent" in agent.technical_agents
        assert "PolicyAgent" in agent.technical_agents
        assert agent.technical_agents["CustomerAgent"] == "http://customer-agent:8010"
        assert agent.technical_agents["PolicyAgent"] == "http://policy-agent:8011"

    @pytest.mark.asyncio
    async def test_skill_execution(self):
        """Test skill execution in domain agent"""
        
        class TestDomainAgent(DomainAgent):
            @skill("ProcessRequest", "Processes a request")
            async def process_request(self, request: str) -> Dict[str, Any]:
                return {"processed": True, "request": request}
        
        agent = TestDomainAgent("TestAgent")
        
        result = await agent.execute_skill("ProcessRequest", {"request": "test_request"})
        
        assert result["processed"] is True
        assert result["request"] == "test_request"


class TestAgentServer:
    """Test agent server functionality"""
    
    @pytest.mark.asyncio
    async def test_execute_request_handling(self):
        """Test handling execute requests"""
        
        class TestAgent(BaseAgent):
            @skill("TestSkill", "Test skill")
            def test_skill(self, value: str) -> str:
                return f"processed: {value}"
            
            async def execute_skill(self, skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
                if skill_name == "TestSkill":
                    result = self.test_skill(**parameters)
                    return {"result": result}
                return {"error": "Skill not found"}
        
        agent = TestAgent("TestAgent", AgentType.TECHNICAL)
        server = AgentServer(agent)
        
        request_data = {
            "skill_name": "TestSkill",
            "parameters": {"value": "test_value"},
            "sender": "test_sender"
        }
        
        response = await server.handle_execute_request(request_data)
        
        assert response["success"] is True
        assert response["result"]["result"] == "processed: test_value"
        assert "task_id" in response

    @pytest.mark.asyncio
    async def test_execute_request_error(self):
        """Test handling execute requests with errors"""
        
        class TestAgent(BaseAgent):
            async def execute_skill(self, skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
                raise Exception("Test error")
        
        agent = TestAgent("TestAgent", AgentType.TECHNICAL)
        server = AgentServer(agent)
        
        request_data = {
            "skill_name": "NonExistentSkill",
            "parameters": {},
            "sender": "test_sender"
        }
        
        response = await server.handle_execute_request(request_data)
        
        assert response["success"] is False
        assert "error" in response
        assert "task_id" in response

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check handling"""
        
        class TestAgent(BaseAgent):
            @skill("TestSkill", "Test skill")
            def test_skill(self):
                pass
            
            async def execute_skill(self, skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
                return {}
        
        agent = TestAgent("TestAgent", AgentType.TECHNICAL)
        server = AgentServer(agent)
        
        response = await server.handle_health_check()
        
        assert response["status"] == "healthy"
        assert response["agent"] == "TestAgent"
        assert response["agent_type"] == AgentType.TECHNICAL
        assert "skills" in response
        assert "TestSkill" in response["skills"]
        assert "timestamp" in response

    @pytest.mark.asyncio
    async def test_skills_request(self):
        """Test skills request handling"""
        
        class TestAgent(BaseAgent):
            @skill("Skill1", "First skill")
            def skill1(self):
                pass
            
            @skill("Skill2", "Second skill")  
            def skill2(self):
                pass
            
            async def execute_skill(self, skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
                return {}
        
        agent = TestAgent("TestAgent", AgentType.TECHNICAL)
        server = AgentServer(agent)
        
        response = await server.handle_skills_request()
        
        assert response["agent"] == "TestAgent"
        assert "skills" in response
        assert len(response["skills"]) == 2
        assert "Skill1" in response["skills"]
        assert "Skill2" in response["skills"]


class TestUtilities:
    """Test utility functions"""
    
    def test_create_task_id(self):
        """Test task ID creation"""
        task_id1 = create_task_id()
        task_id2 = create_task_id()
        
        assert task_id1.startswith("task_")
        assert task_id2.startswith("task_")
        assert task_id1 != task_id2
        assert len(task_id1) > 10  # Should have timestamp

    def test_agent_task_creation(self):
        """Test AgentTask creation"""
        task = AgentTask(
            task_id="test_task",
            skill_name="TestSkill",
            parameters={"param1": "value1"},
            status=TaskStatus.PENDING
        )
        
        assert task.task_id == "test_task"
        assert task.skill_name == "TestSkill"
        assert task.parameters == {"param1": "value1"}
        assert task.status == TaskStatus.PENDING
        assert task.result is None
        assert task.error is None
        assert task.created_at is not None
        assert task.completed_at is None

    def test_skill_decorator(self):
        """Test skill decorator functionality"""
        
        @skill("TestDecoratorSkill", "Test decorator")
        def test_function():
            return "test"
        
        assert hasattr(test_function, '_skill_name')
        assert hasattr(test_function, '_skill_description')
        assert test_function._skill_name == "TestDecoratorSkill"
        assert test_function._skill_description == "Test decorator"