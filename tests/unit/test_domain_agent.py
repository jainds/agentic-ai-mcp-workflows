"""
Domain Agent Tests - SOLID Principles Implementation

Single Responsibility: Each test class focuses on one specific aspect
Open/Closed: Extensible test structure  
Liskov Substitution: Proper mocking contracts
Interface Segregation: Focused test interfaces
Dependency Inversion: Abstract dependencies properly

Focus: Testing the customer ID parsing issue from logs and core Domain Agent functionality
"""

import pytest
import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from domain_agent.main import DomainAgent


class TestDomainAgentCustomerIdParsing:
    """
    SINGLE RESPONSIBILITY: Focus on the critical customer ID parsing issue
    Tests the specific case where 'customer CUST-001' becomes 'user_CUST' in logs
    """
    
    @pytest.fixture
    def agent(self):
        """Create agent without external dependencies"""
        with patch.dict(os.environ, {}, clear=True):
            return DomainAgent()
    
    def test_problematic_parsing_case_from_logs(self, agent):
        """Test the exact case from logs: 'Tell me about my policies please for customer CUST-001'"""
        text = "Tell me about my policies please for customer CUST-001"
        
        result = agent._rule_based_intent_analysis(text)
        
        # This should NOT extract 'user_CUST' - that's the bug we're investigating
        assert result["customer_id"] == "CUST-001", f"Expected CUST-001, got {result['customer_id']}"
        assert result["original_customer_mention"] == "CUST-001"
        assert result["primary_intent"] == "policy_inquiry"
    
    def test_cust_dash_format_variations(self, agent):
        """Test variations of CUST-XXX format"""
        test_cases = [
            "Tell me about my policies please for customer CUST-001",
            "Show policies for customer CUST-123", 
            "Get customer CUST-999 information",
            "Check customer CUST-001 policies",
        ]
        
        for text in test_cases:
            result = agent._rule_based_intent_analysis(text)
            customer_id = result["customer_id"]
            
            # Should extract the full CUST-XXX, not partial matches
            assert customer_id.startswith("CUST-"), f"Failed for '{text}' - got {customer_id}"
            assert len(customer_id) >= 8, f"Customer ID too short: {customer_id}"
            assert result["primary_intent"] == "policy_inquiry"
    
    def test_user_underscore_format(self, agent):
        """Test user_XXX format extraction - updated to match implementation"""
        test_cases = [
            ("Tell me about my policies please for customer user_003", "user_003", "policy_inquiry"),
            ("Show policies for user_123", "user_123", "policy_inquiry"),  # Has "policies" keyword
            ("Check user_001 information", "user_001", "general_inquiry"),  # No policy keywords
        ]
        
        for text, expected_id, expected_intent in test_cases:
            result = agent._rule_based_intent_analysis(text)
            assert result["customer_id"] == expected_id
            assert result["primary_intent"] == expected_intent, f"Failed intent for '{text}' - got {result['primary_intent']}, expected {expected_intent}"
    
    def test_intent_classification_accuracy(self, agent):
        """Test intent classification for different request types"""
        test_cases = [
            # Policy inquiries
            ("Show my policies", "policy_inquiry"),
            ("What coverage do I have?", "policy_inquiry"),
            ("Check my premiums", "policy_inquiry"),
            
            # Claim status
            ("Check my claim status", "claim_status"),
            ("File a claim", "claim_status"),
            ("Claim update please", "claim_status"),
            
            # General inquiries
            ("What is insurance?", "general_inquiry"),
            ("How does this work?", "general_inquiry"),
            ("Hello", "general_inquiry"),
        ]
        
        for text, expected_intent in test_cases:
            result = agent._rule_based_intent_analysis(text)
            assert result["primary_intent"] == expected_intent, f"Failed for '{text}' - got {result['primary_intent']}"
    
    def test_regex_pattern_edge_cases(self, agent):
        """Test edge cases that might cause partial matches"""
        test_cases = [
            # These should NOT cause 'user_CUST' extraction
            ("customer CUST-001 needs help", "CUST-001"),
            ("for customer CUST-001 please", "CUST-001"),
            ("customer CUST-001, show policies", "CUST-001"),
            ("Help customer CUST-001 with policies", "CUST-001"),
        ]
        
        for text, expected_id in test_cases:
            result = agent._rule_based_intent_analysis(text)
            assert result["customer_id"] == expected_id, f"Regex issue for '{text}' - got {result['customer_id']}"
            # Should NOT contain partial matches like 'user_CUST'
            assert "user_CUST" not in str(result["customer_id"]), f"Partial match detected: {result['customer_id']}"


class TestDomainAgentA2ACommunication:
    """
    SINGLE RESPONSIBILITY: Focus on A2A communication with Technical Agent
    DEPENDENCY INVERSION: Abstract A2A client dependencies
    """
    
    @pytest.fixture
    def agent(self):
        with patch.dict(os.environ, {}, clear=True):
            return DomainAgent()
    
    def test_technical_client_creation(self, agent):
        """Test A2A client creation for Technical Agent"""
        with patch('domain_agent.main.A2AClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            client = agent._get_technical_client()
            
            assert client == mock_client
            mock_client_class.assert_called_once_with(agent.technical_agent_url)
    
    def test_technical_client_reuse(self, agent):
        """Test that A2A client is reused after creation"""
        with patch('domain_agent.main.A2AClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            client1 = agent._get_technical_client()
            client2 = agent._get_technical_client()
            
            assert client1 == client2
            assert mock_client_class.call_count == 1
    
    def test_conversation_skill_with_technical_agent(self, agent):
        """Test conversation skill that communicates with Technical Agent"""
        with patch.object(agent, '_analyze_intent') as mock_analyze:
            mock_analyze.return_value = {
                "primary_intent": "policy_inquiry",
                "customer_id": "CUST-001",
                "confidence": 0.9,
                "method": "rules"
            }
            
            with patch.object(agent, '_get_technical_client') as mock_client_getter:
                mock_client = Mock()
                mock_client.ask.return_value = "Found 2 policies for customer CUST-001"
                mock_client_getter.return_value = mock_client
                
                result = agent.handle_customer_conversation("Show policies for customer CUST-001")
                
                # Verify A2A communication
                mock_client.ask.assert_called_once()
                assert "CUST-001" in mock_client.ask.call_args[0][0]
                
                # Verify response formatting
                assert "Thank you for your inquiry" in result
                assert "Found 2 policies" in result


class TestDomainAgentSessionBasedProcessing:
    """
    SINGLE RESPONSIBILITY: Focus on session-based processing
    Tests the priority system: session data > parsing
    """
    
    @pytest.fixture
    def agent(self):
        with patch.dict(os.environ, {}, clear=True):
            return DomainAgent()
    
    def test_session_based_task_handling(self, agent):
        """Test task handling with session data (no parsing needed)"""
        mock_task = Mock()
        mock_task.message = {
            "content": {"text": "Show my policies"}
        }
        mock_task.session = {
            "customer_id": "CUST-001",
            "authenticated": True,
            "customer_data": {"name": "John Smith"}
        }
        mock_task.metadata = {"ui_mode": "simple"}
        
        with patch.object(agent, 'handle_customer_conversation_with_session') as mock_handler:
            mock_handler.return_value = "Policy information retrieved"
            
            result_task = agent.handle_task(mock_task)
            
            # Verify session-based processing was used (no parsing)
            mock_handler.assert_called_once()
            args = mock_handler.call_args[0]
            
            # Check that session customer ID was used
            assert args[1] == "CUST-001"  # customer_id parameter
            assert args[2]["customer_id"] == "CUST-001"  # session_data
            assert args[3]["method"] == "session"  # intent_analysis method
            assert args[3]["confidence"] == 1.0  # 100% confidence for session data
    
    def test_fallback_to_parsing_without_session(self, agent):
        """Test fallback to parsing when no session data available"""
        mock_task = Mock()
        mock_task.message = {
            "content": {"text": "Show policies for customer CUST-001"}
        }
        mock_task.session = {}  # No session data
        mock_task.metadata = {}
        
        with patch.object(agent, '_analyze_intent') as mock_analyze:
            mock_analyze.return_value = {
                "primary_intent": "policy_inquiry",
                "customer_id": "CUST-001",
                "method": "rules"
            }
            
            with patch.object(agent, 'handle_customer_conversation_with_session') as mock_handler:
                mock_handler.return_value = "Policy information retrieved"
                
                result_task = agent.handle_task(mock_task)
                
                # Verify parsing was used as fallback
                mock_analyze.assert_called_once()
                mock_handler.assert_called_once()


class TestDomainAgentResponseFormatting:
    """
    SINGLE RESPONSIBILITY: Focus on professional response formatting
    INTERFACE SEGREGATION: Focused on response generation
    """
    
    @pytest.fixture
    def agent(self):
        with patch.dict(os.environ, {}, clear=True):
            return DomainAgent()
    
    def test_policy_inquiry_response_formatting(self, agent):
        """Test professional formatting for policy inquiries"""
        technical_response = "Found 2 policies for customer CUST-001: Health, Auto"
        
        result = agent._format_professional_response(
            "policy_inquiry", 
            technical_response, 
            "CUST-001"
        )
        
        assert "Thank you for your inquiry" in result
        assert "Account Summary" in result
        assert "Need Additional Help" in result
        assert technical_response in result
    
    def test_claim_status_response_formatting(self, agent):
        """Test professional formatting for claim status"""
        technical_response = "Checking claim for customer CUST-001"
        
        result = agent._format_professional_response(
            "claim_status", 
            technical_response, 
            "CUST-001"
        )
        
        assert "Thank you for checking on your claim" in result
        assert "What This Means" in result
        assert "Next Steps" in result
    
    def test_general_inquiry_response_formatting(self, agent):
        """Test professional formatting for general inquiries"""
        technical_response = "I'm here to help"
        
        result = agent._format_professional_response(
            "general_inquiry", 
            technical_response
        )
        
        assert "Thank you for contacting" in result
        assert "How I Can Help" in result
        assert "Policy information" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 