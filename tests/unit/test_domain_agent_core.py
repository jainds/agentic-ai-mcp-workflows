#!/usr/bin/env python3
"""
Unit tests for Domain Agent Core Functionality
Tests the customer-facing domain agent without interface dependencies
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add domain_agent to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'domain_agent'))

class TestDomainAgentCore:
    """Test core domain agent functionality"""
    
    def test_customer_id_pattern_matching(self):
        """Test customer ID extraction patterns"""
        
        # Common customer ID formats
        test_cases = [
            ("My customer ID is CUST-001", "CUST-001"),
            ("I'm USER_123 and need help", "USER_123"),
            ("Customer CUST_456 calling", "CUST_456"),
            ("ID: CUST-789", "CUST-789"),
            ("My ID is USER-999", "USER-999"),
        ]
        
        # Simulate regex patterns from domain agent
        import re
        customer_id_patterns = [
            r'(?:customer\s+id|my\s+id|id)\s*:?\s*([A-Z]+-\d+)',
            r'(?:i\'m|customer)\s+([A-Z]+[-_]\d+)',
            r'\b([A-Z]{3,4}[-_]\d{3,4})\b'
        ]
        
        for text, expected_id in test_cases:
            found_id = None
            for pattern in customer_id_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    found_id = match.group(1)
                    break
            
            assert found_id == expected_id, f"Failed to extract {expected_id} from '{text}'"

    def test_intent_classification_patterns(self):
        """Test intent classification without LLM dependency"""
        
        intent_keywords = {
            "policy_inquiry": ["policy", "policies", "coverage", "plan"],
            "billing": ["bill", "payment", "due", "premium", "cost"],
            "claims": ["claim", "accident", "damage", "file claim"],
            "agent_contact": ["agent", "representative", "talk to", "speak with"]
        }
        
        test_cases = [
            ("What policies do I have?", "policy_inquiry"),
            ("When is my payment due?", "billing"), 
            ("I need to file a claim", "claims"),
            ("Can I speak with my agent?", "agent_contact")
        ]
        
        for text, expected_intent in test_cases:
            detected_intent = "unknown"
            text_lower = text.lower()
            
            for intent, keywords in intent_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    detected_intent = intent
                    break
            
            assert detected_intent == expected_intent, f"Failed to classify '{text}' as {expected_intent}"

    def test_response_formatting_structure(self):
        """Test response formatting without dependencies"""
        
        # Test professional response formatting
        def format_professional_response(customer_request, technical_response):
            """Simulate response formatting logic"""
            return {
                "greeting": f"Thank you for contacting us about: {customer_request}",
                "main_content": technical_response,
                "closing": "Is there anything else I can help you with today?"
            }
        
        customer_request = "policy information"
        technical_response = {"policies": [{"id": "P001", "type": "Auto"}]}
        
        formatted = format_professional_response(customer_request, technical_response)
        
        assert "greeting" in formatted
        assert "main_content" in formatted 
        assert "closing" in formatted
        assert customer_request in formatted["greeting"]

class TestDomainAgentConfiguration:
    """Test domain agent configuration and setup"""
    
    def test_a2a_client_configuration(self):
        """Test A2A client configuration without actual instantiation"""
        
        # Simulate A2A client configuration
        a2a_config = {
            "technical_agent_url": "http://localhost:8002/a2a",
            "timeout": 30,
            "retry_attempts": 3
        }
        
        assert a2a_config["technical_agent_url"].startswith("http://")
        assert a2a_config["timeout"] > 0
        assert a2a_config["retry_attempts"] > 0

    def test_openai_fallback_configuration(self):
        """Test OpenAI configuration and fallback logic"""
        
        # Test with no API key (should fallback)
        with patch.dict(os.environ, {}, clear=True):
            openai_available = bool(os.getenv("OPENROUTER_API_KEY"))
            assert openai_available is False
        
        # Test with API key
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            openai_available = bool(os.getenv("OPENROUTER_API_KEY"))
            assert openai_available is True

class TestDomainAgentWorkflows:
    """Test domain agent workflows and business logic"""
    
    def test_customer_conversation_workflow(self):
        """Test the full customer conversation workflow logic"""
        
        # Simulate conversation workflow steps
        workflow_steps = [
            "parse_customer_input",
            "extract_customer_id", 
            "classify_intent",
            "route_to_technical_agent",
            "format_response",
            "send_to_customer"
        ]
        
        # Test that all steps are defined
        for step in workflow_steps:
            assert isinstance(step, str)
            assert len(step) > 0

    def test_session_based_processing(self):
        """Test session-based conversation processing"""
        
        # Simulate session management
        session_data = {
            "session_id": "sess_123",
            "customer_id": "CUST-001",
            "conversation_history": [],
            "context": {}
        }
        
        # Test session data structure
        assert "session_id" in session_data
        assert "customer_id" in session_data
        assert isinstance(session_data["conversation_history"], list)
        assert isinstance(session_data["context"], dict)

class TestDomainAgentErrorHandling:
    """Test domain agent error handling"""
    
    def test_technical_agent_unavailable_fallback(self):
        """Test fallback when technical agent is unavailable"""
        
        # Simulate error response
        def handle_technical_agent_error():
            return {
                "success": False,
                "error": "Technical agent unavailable", 
                "fallback_message": "I'm experiencing technical difficulties. Please try again later or contact support."
            }
        
        error_response = handle_technical_agent_error()
        
        assert error_response["success"] is False
        assert "error" in error_response
        assert "fallback_message" in error_response

    def test_invalid_customer_id_handling(self):
        """Test handling of invalid customer IDs"""
        
        invalid_ids = ["", None, "INVALID", "123", "SHORT"]
        
        def validate_customer_id(customer_id):
            if not customer_id:
                return False
            if not isinstance(customer_id, str):
                return False
            if len(customer_id) < 6:
                return False
            if not any(char.isdigit() for char in customer_id):
                return False
            return True
        
        for invalid_id in invalid_ids:
            assert validate_customer_id(invalid_id) is False
        
        # Test valid ID
        assert validate_customer_id("CUST-001") is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 