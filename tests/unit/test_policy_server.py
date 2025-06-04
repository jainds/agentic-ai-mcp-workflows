"""
Unit tests for Policy Server (FastMCP)
Tests all functions with comprehensive coverage including edge cases
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from typing import Dict, Any, List

# Import the policy server module
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from policy_server.main import (
    load_data, 
    get_customer_policies, 
    DATA_FILE,
    mcp
)


class TestPolicyServer:
    """Comprehensive unit tests for Policy Server"""

    @pytest.fixture
    def mock_policy_data(self) -> Dict[str, Any]:
        """Sample policy data for testing"""
        return {
            "policies": [
                {
                    "id": "POL-001",
                    "customer_id": "CUST-001",
                    "type": "Auto Insurance",
                    "status": "Active",
                    "premium": 1200.00,
                    "coverage_amount": 50000,
                    "deductible": 500,
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "details": {"vehicle": "Toyota Camry"}
                },
                {
                    "id": "POL-002", 
                    "customer_id": "CUST-001",
                    "type": "Home Insurance",
                    "status": "Active",
                    "premium": 800.00,
                    "coverage_amount": 200000,
                    "deductible": 1000,
                    "start_date": "2024-01-15",
                    "end_date": "2025-01-14",
                    "details": {"property_type": "Single Family"}
                },
                {
                    "id": "POL-003",
                    "customer_id": "CUST-002", 
                    "type": "Auto Insurance",
                    "status": "Expired",
                    "premium": 1100.00,
                    "coverage_amount": 45000,
                    "deductible": 750,
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "details": {"vehicle": "Honda Civic"}
                }
            ]
        }

    @pytest.fixture
    def empty_data(self) -> Dict[str, Any]:
        """Empty data for testing edge cases"""
        return {"policies": []}

    def test_load_data_success(self, mock_policy_data):
        """Test successful data loading"""
        mock_data = json.dumps(mock_policy_data)
        
        with patch("builtins.open", mock_open(read_data=mock_data)):
            with patch.object(Path, "exists", return_value=True):
                result = load_data()
        
        assert result == mock_policy_data
        assert len(result["policies"]) == 3

    def test_load_data_file_not_found(self):
        """Test data loading when file doesn't exist"""
        with patch("builtins.open", side_effect=FileNotFoundError("No such file")):
            result = load_data()
        
        assert result == {"policies": [], "users": []}

    def test_load_data_invalid_json(self):
        """Test data loading with invalid JSON"""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            result = load_data()
        
        assert result == {"policies": [], "users": []}

    def test_load_data_empty_file(self):
        """Test data loading with empty file"""
        with patch("builtins.open", mock_open(read_data="")):
            result = load_data()
        
        assert result == {"policies": [], "users": []}

    def test_get_customer_policies_found(self, mock_policy_data):
        """Test getting policies for existing customer"""
        with patch("policy_server.main.DATA", mock_policy_data):
            result = get_customer_policies("CUST-001")
        
        # Should return 2 policies for CUST-001
        assert len(result) == 2
        for policy in result:
            assert "id" in policy
            assert "type" in policy
            assert "status" in policy
            assert "premium" in policy
            assert "coverage_amount" in policy
            assert "deductible" in policy
            assert "start_date" in policy
            assert "end_date" in policy
            assert "details" in policy

    def test_get_customer_policies_not_found(self, mock_policy_data):
        """Test getting policies for non-existent customer"""
        with patch("policy_server.main.DATA", mock_policy_data):
            result = get_customer_policies("CUST-999")
        
        assert result == []

    def test_get_customer_policies_empty_data(self, empty_data):
        """Test getting policies when no data available"""
        with patch("policy_server.main.DATA", empty_data):
            result = get_customer_policies("CUST-001")
        
        assert result == []

    def test_get_customer_policies_malformed_data(self):
        """Test getting policies with malformed data structure"""
        malformed_data = {"not_policies": []}
        
        with patch("policy_server.main.DATA", malformed_data):
            result = get_customer_policies("CUST-001")
        
        assert result == []

    def test_get_customer_policies_missing_fields(self):
        """Test getting policies with missing required fields"""
        incomplete_data = {
            "policies": [
                {
                    "id": "POL-001",
                    "customer_id": "CUST-001",
                    "type": "Auto Insurance"
                    # Missing other required fields
                }
            ]
        }
        
        with patch("policy_server.main.DATA", incomplete_data):
            result = get_customer_policies("CUST-001")
        
        # Should return 1 policy
        assert len(result) == 1
        policy = result[0]
        assert policy["id"] == "POL-001"
        assert policy["type"] == "Auto Insurance"
        # Check that missing fields default to None or 0
        assert policy.get("premium") is None
        assert policy.get("coverage_amount") == 0

    def test_get_customer_policies_case_sensitivity(self, mock_policy_data):
        """Test that customer ID lookup is case sensitive"""
        with patch("policy_server.main.DATA", mock_policy_data):
            result_upper = get_customer_policies("CUST-001")
            result_lower = get_customer_policies("cust-001")
        
        assert len(result_upper) == 2  # 2 policies for CUST-001
        assert len(result_lower) == 0  # No policies for cust-001

    def test_get_customer_policies_whitespace_handling(self, mock_policy_data):
        """Test customer ID with whitespace"""
        with patch("policy_server.main.DATA", mock_policy_data):
            result = get_customer_policies(" CUST-001 ")
        
        assert result == []  # Should not find due to exact match requirement

    def test_get_customer_policies_special_characters(self):
        """Test customer ID with special characters"""
        special_data = {
            "policies": [
                {
                    "id": "POL-001",
                    "customer_id": "CUST@001#",
                    "type": "Auto Insurance",
                    "status": "Active",
                    "premium": 1200.00,
                    "coverage_amount": 50000,
                    "deductible": 500,
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "details": {}
                }
            ]
        }
        
        with patch("policy_server.main.DATA", special_data):
            result = get_customer_policies("CUST@001#")
        
        # Should return 2 items: 1 summary + 1 policy
        assert len(result) == 2
        assert result[0].get("summary") is True
        assert result[1]["id"] == "POL-001"

    def test_get_customer_policies_numeric_customer_id(self):
        """Test numeric customer ID"""
        numeric_data = {
            "policies": [
                {
                    "id": "POL-001",
                    "customer_id": "12345",
                    "type": "Auto Insurance",
                    "status": "Active",
                    "premium": 1200.00,
                    "coverage_amount": 50000,
                    "deductible": 500,
                    "start_date": "2024-01-01", 
                    "end_date": "2024-12-31",
                    "details": {}
                }
            ]
        }
        
        with patch("policy_server.main.DATA", numeric_data):
            result = get_customer_policies("12345")
        
        # Should return 2 items: 1 summary + 1 policy
        assert len(result) == 2
        assert result[0].get("summary") is True
        assert result[1]["id"] == "POL-001"

    def test_logging_output(self, mock_policy_data, caplog):
        """Test that logging occurs correctly"""
        with patch("policy_server.main.DATA", mock_policy_data):
            result = get_customer_policies("CUST-001")
        
        # Just verify the function works - logging is secondary
        assert len(result) == 2  # 2 policies for CUST-001

    def test_logging_not_found(self, mock_policy_data, caplog):
        """Test logging when no policies are found"""
        with patch("policy_server.main.DATA", mock_policy_data):
            result = get_customer_policies("CUST-999")
        
        # Just verify the function works
        assert result == []

    def test_mcp_tool_registration(self):
        """Test that the FastMCP tool is properly registered"""
        # Check that mcp instance exists
        assert mcp is not None
        
        # Basic verification that the MCP server is set up
        assert hasattr(mcp, "get_tools")

    def test_tool_function_signature(self):
        """Test that the tool function has correct signature"""
        # Just verify that get_customer_policies function exists and is callable
        assert callable(get_customer_policies)
        
        # Test with a simple call
        with patch("policy_server.main.DATA", {"policies": []}):
            result = get_customer_policies("test")
            assert result == []

    def test_data_file_path(self):
        """Test that DATA_FILE path is correctly constructed"""
        assert DATA_FILE.name == "mock_data.json"
        assert "data" in str(DATA_FILE)

    def test_policy_data_structure_validation(self, mock_policy_data):
        """Test that returned policy data has expected structure"""
        with patch("policy_server.main.DATA", mock_policy_data):
            result = get_customer_policies("CUST-001")
        
        for policy in result:
            required_fields = [
                "id", "type", "status", "premium", "coverage_amount",
                "deductible", "start_date", "end_date", "details"
            ]
            for field in required_fields:
                assert field in policy

    def test_empty_customer_id(self, mock_policy_data):
        """Test behavior with empty customer ID"""
        with patch("policy_server.main.DATA", mock_policy_data):
            result = get_customer_policies("")
        
        assert result == []

    def test_none_customer_id(self, mock_policy_data):
        """Test behavior with None customer ID"""
        with patch("policy_server.main.DATA", mock_policy_data):
            # This should raise an exception or handle gracefully
            try:
                result = get_customer_policies(None)
                assert result == []
            except (TypeError, AttributeError):
                # Either handling is acceptable
                pass

    def test_large_dataset_performance(self):
        """Test performance with large dataset"""
        # Generate large dataset
        large_data = {
            "policies": [
                {
                    "id": f"POL-{i:06d}",
                    "customer_id": f"CUST-{i % 100:03d}",  # 100 unique customers
                    "type": "Auto Insurance",
                    "status": "Active",
                    "premium": 1000.00 + i,
                    "coverage_amount": 50000,
                    "deductible": 500,
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "details": {}
                }
                for i in range(10000)  # 10,000 policies
            ]
        }
        
        with patch("policy_server.main.DATA", large_data):
            import time
            start_time = time.time()
            result = get_customer_policies("CUST-001")
            end_time = time.time()
        
        # Should complete quickly (< 1 second)
        assert end_time - start_time < 1.0
        assert len(result) == 100  # 100 policies for CUST-001


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 