"""
Comprehensive Test Suite for Google ADK Migration
Tests all components of the migrated insurance AI system
"""
import asyncio
import json
import logging
import os
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

# Set environment variables for testing
os.environ["OPENROUTER_API_KEY"] = "test_key"
os.environ["MCP_SERVER_URL"] = "http://localhost:8001/mcp"

# Test the basic ADK integration
class TestADKIntegration:
    """Test Google ADK integration components"""
    
    def test_requirements_includes_google_adk(self):
        """Test that requirements.txt includes Google ADK"""
        with open("requirements.txt", "r") as f:
            content = f.read()
        
        assert "google-adk>=1.0.0" in content
        assert "litellm>=1.55.0" in content
        assert "fastapi>=0.115.0" in content
    
    def test_configuration_files_exist(self):
        """Test that all configuration files exist"""
        config_files = [
            "config/models.yaml",
            "config/openrouter.yaml", 
            "config/prompts/domain_agent.yaml",
            "config/prompts/technical_agent.yaml",
            "config/workflows/customer_workflow.yaml",
            "config/workflows/technical_workflow.yaml"
        ]
        
        for file_path in config_files:
            assert os.path.exists(file_path), f"Configuration file {file_path} missing"
    
    def test_agent_files_exist(self):
        """Test that all agent implementation files exist"""
        agent_files = [
            "agents/base_adk.py",
            "agents/domain_agent.py", 
            "agents/technical_agent.py",
            "agents/orchestrator.py"
        ]
        
        for file_path in agent_files:
            assert os.path.exists(file_path), f"Agent file {file_path} missing"
    
    def test_server_files_exist(self):
        """Test that server implementation files exist"""
        server_files = [
            "server/main.py"
        ]
        
        for file_path in server_files:
            assert os.path.exists(file_path), f"Server file {file_path} missing"


class TestConfigurationLoading:
    """Test configuration loading and parsing"""
    
    def test_model_configuration_valid(self):
        """Test model configuration is valid YAML"""
        with open("config/models.yaml", "r") as f:
            import yaml
            config = yaml.safe_load(f)
        
        assert "models" in config
        assert "domain_agent" in config["models"]
        assert "technical_agent" in config["models"]
        assert "primary" in config["models"]["domain_agent"]
        assert "openrouter/" in config["models"]["domain_agent"]["primary"]
    
    def test_prompt_configuration_valid(self):
        """Test prompt configurations are valid"""
        with open("config/prompts/domain_agent.yaml", "r") as f:
            import yaml
            domain_prompts = yaml.safe_load(f)
        
        required_prompts = [
            "system_prompt",
            "intent_analysis_prompt", 
            "response_formatting_prompt",
            "conversation_planning_prompt"
        ]
        
        for prompt in required_prompts:
            assert prompt in domain_prompts, f"Required prompt {prompt} missing"
            assert isinstance(domain_prompts[prompt], str)
            assert len(domain_prompts[prompt]) > 10  # Basic content check
    
    def test_workflow_configuration_valid(self):
        """Test workflow configurations are valid"""
        with open("config/workflows/customer_workflow.yaml", "r") as f:
            import yaml
            workflow_config = yaml.safe_load(f)
        
        # Note: The workflow structure was simplified for ADK
        assert isinstance(workflow_config, dict)
        assert len(workflow_config) > 0


@pytest.mark.asyncio
class TestMockADKComponents:
    """Test components with mocked ADK dependencies"""
    
    @patch('agents.base_adk.LiteLLMModel')
    @patch('agents.base_adk.Agent')
    def test_adk_model_config_creation(self, mock_agent, mock_litellm):
        """Test ADK model configuration creation"""
        from agents.base_adk import ADKModelConfig
        
        config = ADKModelConfig(
            primary_model="openrouter/anthropic/claude-3.5-sonnet",
            api_key="test_key",
            base_url="https://openrouter.ai/api/v1"
        )
        
        assert config.primary_model == "openrouter/anthropic/claude-3.5-sonnet"
        assert config.api_key == "test_key"
        
        # Test model creation
        model = config.create_model()
        mock_litellm.assert_called_once()
    
    def test_agent_definitions_loading(self):
        """Test agent definition loading"""
        from tools.agent_definitions import PureDomainAgentDefinition, PureTechnicalAgentDefinition
        
        # Test domain agent definition
        domain_def = PureDomainAgentDefinition()
        domain_config = domain_def.get_agent_config()
        
        assert "name" in domain_config
        assert "description" in domain_config
        assert "model_config" in domain_config
        
        # Test technical agent definition
        tech_def = PureTechnicalAgentDefinition()
        tech_config = tech_def.get_agent_config()
        
        assert "name" in tech_config
        assert "description" in tech_config
        assert "model_config" in tech_config
    
    @patch('tools.policy_tools.httpx.AsyncClient')
    async def test_mcp_tool_manager(self, mock_client):
        """Test MCP tool manager functionality"""
        from tools.policy_tools import MCPToolManager
        
        # Mock successful MCP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"policies": ["test_policy"]}
        mock_client.return_value.post = AsyncMock(return_value=mock_response)
        
        manager = MCPToolManager()
        result = await manager.execute_tool_call(
            tool_name="get_customer_policies",
            customer_id="CUST123"
        )
        
        assert result["success"] is True
        assert "data" in result
    
    def test_session_manager_functionality(self):
        """Test session manager functionality"""
        from tools.session_tools import SessionManager
        
        manager = SessionManager()
        
        # Test session creation
        session_id = manager.create_session("CUST123")
        assert isinstance(session_id, str)
        assert len(session_id) > 10  # UUID length check
        
        # Test session retrieval
        session_data = manager.get_session_data(session_id)
        assert session_data["session_id"] == session_id
        assert session_data["customer_id"] == "CUST123"
        assert session_data["authenticated"] is True
        
        # Test session update
        success = manager.update_session(session_id, {"test_field": "test_value"})
        assert success is True
        
        updated_data = manager.get_session_data(session_id)
        assert updated_data["test_field"] == "test_value"


class TestMigrationCompleteness:
    """Test that migration preserves all existing functionality"""
    
    def test_all_current_endpoints_mapped(self):
        """Test that all current API endpoints are mapped in new system"""
        # Based on current system endpoints
        expected_endpoints = [
            "/health",
            "/sessions",
            "/customer/inquiry", 
            "/technical/data",
            "/a2a/handle_task"  # Legacy compatibility
        ]
        
        # Read server file to check endpoints are defined
        with open("server/main.py", "r") as f:
            server_content = f.read()
        
        for endpoint in expected_endpoints:
            assert endpoint in server_content, f"Endpoint {endpoint} not found in server"
    
    def test_mcp_integration_preserved(self):
        """Test that MCP integration is preserved"""
        with open("tools/policy_tools.py", "r") as f:
            content = f.read()
        
        # Check MCP functionality is preserved
        assert "MCPPolicyTool" in content
        assert "get_customer_policies" in content
        assert "get_policy_details" in content
        assert "get_coverage_information" in content
        assert "get_payment_information" in content
    
    def test_monitoring_integration_preserved(self):
        """Test that monitoring integrations are preserved"""
        with open("requirements.txt", "r") as f:
            content = f.read()
        
        # Check monitoring dependencies
        assert "langfuse>=2.60.0" in content
        assert "prometheus-client>=0.22.0" in content
        assert "structlog>=25.3.0" in content
    
    def test_authentication_flow_preserved(self):
        """Test that authentication flow is preserved"""
        with open("tools/session_tools.py", "r") as f:
            content = f.read()
        
        assert "AuthenticationManager" in content
        assert "verify_customer" in content
        assert "check_authorization" in content


class TestADKMigrationValidation:
    """Validate the ADK migration implementation"""
    
    def test_adk_imports_structure(self):
        """Test that ADK imports are properly structured"""
        with open("agents/base_adk.py", "r") as f:
            content = f.read()
        
        # Check official ADK imports
        assert "from adk import Agent, Tool, Model, Workflow, WorkflowStep" in content
        assert "from adk.models import LiteLLMModel" in content
        assert "from adk.tools import FunctionTool" in content
        assert "from adk.workflows import SequentialWorkflow, ParallelWorkflow" in content
    
    def test_litellm_integration(self):
        """Test LiteLLM integration for OpenRouter"""
        with open("agents/base_adk.py", "r") as f:
            content = f.read()
        
        assert "import litellm" in content
        assert "LiteLLMModel" in content
        assert "openrouter.ai/api/v1" in content or "base_url" in content
    
    def test_workflow_definitions(self):
        """Test that workflows are properly defined"""
        with open("agents/orchestrator.py", "r") as f:
            content = f.read()
        
        assert "SequentialWorkflow" in content
        assert "WorkflowStep" in content
        assert "customer_inquiry" in content
        assert "technical_data" in content
    
    def test_fastapi_adk_integration(self):
        """Test FastAPI server integrates with ADK"""
        with open("server/main.py", "r") as f:
            content = f.read()
        
        assert "create_adk_orchestrator" in content
        assert "Google ADK" in content
        assert "orchestrator.route_request" in content


def run_migration_validation():
    """Run comprehensive migration validation"""
    print("🧪 Running Google ADK Migration Validation...")
    
    # Run all test classes
    test_classes = [
        TestADKIntegration,
        TestConfigurationLoading, 
        TestMigrationCompleteness,
        TestADKMigrationValidation
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n📋 Testing {test_class.__name__}...")
        
        instance = test_class()
        methods = [method for method in dir(instance) if method.startswith('test_')]
        
        for method_name in methods:
            total_tests += 1
            try:
                method = getattr(instance, method_name)
                method()
                passed_tests += 1
                print(f"  ✅ {method_name}")
            except Exception as e:
                print(f"  ❌ {method_name}: {str(e)}")
    
    print(f"\n📊 Migration Validation Results:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {total_tests - passed_tests}")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! ADK migration is ready.")
    else:
        print("⚠️  Some tests failed. Review implementation before deployment.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    # Run validation when executed directly
    success = run_migration_validation()
    exit(0 if success else 1) 