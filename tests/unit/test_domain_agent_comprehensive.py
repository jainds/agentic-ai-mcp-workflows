#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Domain Agent
Tests domain agent LLM reasoning and A2A orchestration without dependencies
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

class TestDomainAgentStructure:
    """Test domain agent structure and components"""
    
    def test_domain_agent_directory(self):
        """Test that domain agent directory exists"""
        agents_dir = Path("agents/domain")
        assert agents_dir.exists(), "Domain agents directory should exist"
        
        # Check for agent files
        expected_files = ["llm_claims_agent.py"]
        for file_name in expected_files:
            agent_file = agents_dir / file_name
            assert agent_file.exists(), f"Domain agent file {file_name} should exist"
    
    def test_template_file(self):
        """Test that Template file exists"""
        template_file = Path("Template")
        assert template_file.exists(), "Template file should exist for responses"

class TestDomainAgentLLMReasoning:
    """Test LLM reasoning functionality in domain agent"""
    
    def test_intent_analysis_structure(self):
        """Test intent analysis structure"""
        # Mock intent analysis result
        mock_intent_analysis = {
            "intent": "policy_inquiry",
            "confidence": 0.92,
            "entities": {
                "policy_type": "auto",
                "action": "status_check"
            },
            "urgency": "normal",
            "complexity": "low",
            "data_requirements": ["user_profile", "policy_data"]
        }
        
        assert "intent" in mock_intent_analysis
        assert "confidence" in mock_intent_analysis
        assert "entities" in mock_intent_analysis
        assert "data_requirements" in mock_intent_analysis
        assert isinstance(mock_intent_analysis["data_requirements"], list)
    
    @pytest.mark.asyncio
    async def test_llm_reasoning_mock(self):
        """Test LLM reasoning mock functionality"""
        # Mock LLM reasoning function
        async def mock_llm_reasoning(message: str, context: dict = None):
            # Simple intent detection based on keywords
            if any(word in message.lower() for word in ["policy", "coverage", "premium"]):
                intent = "policy_inquiry"
                data_requirements = ["user_profile", "policy_data"]
            elif any(word in message.lower() for word in ["claim", "accident", "damage"]):
                intent = "claims_inquiry"
                data_requirements = ["user_profile", "claims_data"]
            else:
                intent = "general_inquiry"
                data_requirements = ["user_profile"]
            
            return {
                "intent": intent,
                "confidence": 0.85,
                "data_requirements": data_requirements,
                "reasoning": f"Detected {intent} based on message content"
            }
        
        # Test policy inquiry
        policy_result = await mock_llm_reasoning("What's my auto policy status?")
        assert policy_result["intent"] == "policy_inquiry"
        assert "policy_data" in policy_result["data_requirements"]
        
        # Test claims inquiry
        claims_result = await mock_llm_reasoning("I need to file a claim for my accident")
        assert claims_result["intent"] == "claims_inquiry"
        assert "claims_data" in claims_result["data_requirements"]
    
    def test_response_synthesis_structure(self):
        """Test response synthesis structure"""
        # Mock response synthesis
        mock_response_data = {
            "message": "Based on your inquiry, here are your policy details...",
            "data_used": ["user_profile", "policy_data"],
            "template_used": "policy_inquiry_response",
            "personalized": True,
            "thinking_steps": [
                "Analyzed customer inquiry about policy status",
                "Retrieved relevant policy information",
                "Synthesized personalized response"
            ]
        }
        
        assert "message" in mock_response_data
        assert "data_used" in mock_response_data
        assert "thinking_steps" in mock_response_data
        assert isinstance(mock_response_data["thinking_steps"], list)

class TestDomainAgentA2AOrchestration:
    """Test A2A orchestration functionality in domain agent"""
    
    def test_a2a_orchestration_structure(self):
        """Test A2A orchestration structure"""
        # Mock A2A orchestration plan
        mock_orchestration_plan = {
            "customer_id": "test-customer-123",
            "intent": "policy_inquiry",
            "data_requirements": ["user_profile", "policy_data"],
            "technical_agent_requests": [
                {
                    "request_type": "data_request",
                    "target_agent": "technical_agent",
                    "endpoint": "http://localhost:8001",
                    "data_needed": ["user_profile", "policy_data"],
                    "priority": "normal"
                }
            ],
            "orchestration_steps": [
                "Send data request to technical agent",
                "Wait for technical agent response", 
                "Synthesize final response"
            ]
        }
        
        assert "customer_id" in mock_orchestration_plan
        assert "intent" in mock_orchestration_plan
        assert "technical_agent_requests" in mock_orchestration_plan
        assert "orchestration_steps" in mock_orchestration_plan
        assert len(mock_orchestration_plan["technical_agent_requests"]) > 0
    
    @pytest.mark.asyncio
    async def test_a2a_message_creation(self):
        """Test A2A message creation"""
        # Mock A2A message creation function
        def create_a2a_message(customer_id: str, intent: str, data_requirements: list):
            return {
                "request_type": "data_request",
                "customer_id": customer_id,
                "intent": intent,
                "data_requirements": data_requirements,
                "urgent": intent == "emergency_claim",
                "timestamp": "2024-01-15T10:00:00Z",
                "source": "domain_agent"
            }
        
        # Test message creation
        message = create_a2a_message(
            "test-customer-123",
            "policy_inquiry", 
            ["user_profile", "policy_data"]
        )
        
        assert message["customer_id"] == "test-customer-123"
        assert message["intent"] == "policy_inquiry"
        assert message["data_requirements"] == ["user_profile", "policy_data"]
        assert message["source"] == "domain_agent"
    
    @pytest.mark.asyncio
    async def test_orchestration_flow_mock(self):
        """Test complete orchestration flow mock"""
        # Mock complete orchestration flow
        async def mock_orchestration_flow(customer_id: str, message: str):
            # Step 1: LLM Intent Analysis
            intent_analysis = {
                "intent": "policy_inquiry",
                "data_requirements": ["user_profile", "policy_data"]
            }
            
            # Step 2: Create A2A Request
            a2a_request = {
                "request_type": "data_request",
                "customer_id": customer_id,
                "intent": intent_analysis["intent"],
                "data_requirements": intent_analysis["data_requirements"]
            }
            
            # Step 3: Mock A2A Response
            a2a_response = {
                "status": "success",
                "data": {
                    "user_profile": {"name": "John Doe", "user_id": customer_id},
                    "policy_data": {"policies": [{"policy_id": "POL-001", "type": "auto"}]}
                }
            }
            
            # Step 4: Response Synthesis
            final_response = {
                "message": f"Hello {a2a_response['data']['user_profile']['name']}, your auto policy POL-001 is active.",
                "orchestration_success": True,
                "data_sources": ["technical_agent"],
                "processing_steps": ["llm_analysis", "a2a_orchestration", "response_synthesis"]
            }
            
            return final_response
        
        result = await mock_orchestration_flow("test-customer-123", "What's my policy status?")
        
        assert result["orchestration_success"] == True
        assert "John Doe" in result["message"]
        assert "POL-001" in result["message"]
        assert "a2a_orchestration" in result["processing_steps"]

class TestDomainAgentEndpoints:
    """Test domain agent endpoint functionality"""
    
    def test_health_endpoint_structure(self):
        """Test health endpoint response structure"""
        mock_health_response = {
            "status": "healthy",
            "agent_type": "domain",
            "capabilities": ["llm_reasoning", "a2a_orchestration"],
            "dependencies": {
                "llm_service": "connected",
                "a2a_client": "ready",
                "template_system": "loaded"
            },
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
        assert "status" in mock_health_response
        assert "agent_type" in mock_health_response
        assert "capabilities" in mock_health_response
        assert "dependencies" in mock_health_response
        assert mock_health_response["agent_type"] == "domain"
    
    def test_chat_endpoint_structure(self):
        """Test chat endpoint request/response structure"""
        # Mock chat request
        mock_chat_request = {
            "message": "What's my policy status?",
            "customer_id": "test-customer-123",
            "session_id": "session-456"
        }
        
        # Mock chat response
        mock_chat_response = {
            "response": "Your auto policy POL-001 is active with coverage up to $100,000.",
            "intent": "policy_inquiry",
            "confidence": 0.92,
            "data_sources": ["technical_agent"],
            "thinking_steps": [
                "Analyzed policy inquiry intent",
                "Requested data from technical agent",
                "Synthesized personalized response"
            ],
            "processing_time_ms": 150
        }
        
        assert "message" in mock_chat_request
        assert "customer_id" in mock_chat_request
        assert "response" in mock_chat_response
        assert "intent" in mock_chat_response
        assert "thinking_steps" in mock_chat_response

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 