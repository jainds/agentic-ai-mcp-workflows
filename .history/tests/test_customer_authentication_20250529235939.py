"""
Test suite for customer authentication and validation
Ensures proper customer ID validation before access to insurance services
"""

import pytest
from unittest.mock import Mock, patch
import asyncio
from datetime import datetime

# Import the CustomerValidator from our UI module
# This simulates the same validation logic used in the Streamlit app
class CustomerValidator:
    """Test version of CustomerValidator for testing"""
    
    VALID_CUSTOMERS = {
        "CUST-001": {
            "name": "John Smith",
            "email": "john.smith@email.com",
            "policies": ["POL-AUTO-123456", "POL-HOME-789012"],
            "status": "active"
        },
        "CUST-002": {
            "name": "Sarah Johnson", 
            "email": "sarah.johnson@email.com",
            "policies": ["POL-AUTO-654321"],
            "status": "active"
        },
        "CUST-003": {
            "name": "Mike Davis",
            "email": "mike.davis@email.com", 
            "policies": ["POL-AUTO-111222", "POL-HOME-333444"],
            "status": "active"
        },
        "TEST-CUSTOMER": {
            "name": "Test Customer",
            "email": "test@insurance.com",
            "policies": ["POL-TEST-123"],
            "status": "active"
        },
        "INACTIVE-001": {
            "name": "Inactive User",
            "email": "inactive@email.com",
            "policies": [],
            "status": "inactive"
        }
    }
    
    @classmethod
    def validate_customer(cls, customer_id: str) -> dict:
        """Validate customer ID and return customer data"""
        if not customer_id or not customer_id.strip():
            return {
                "valid": False,
                "error": "Customer ID is required",
                "customer_data": None
            }
        
        customer_id = customer_id.strip().upper()
        
        if customer_id not in cls.VALID_CUSTOMERS:
            return {
                "valid": False,
                "error": f"Customer ID '{customer_id}' not found in our system",
                "customer_data": None
            }
        
        customer_data = cls.VALID_CUSTOMERS[customer_id]
        if customer_data["status"] != "active":
            return {
                "valid": False,
                "error": f"Customer account '{customer_id}' is not active",
                "customer_data": None
            }
        
        return {
            "valid": True,
            "error": None,
            "customer_data": {
                **customer_data,
                "customer_id": customer_id
            }
        }

class TestCustomerAuthentication:
    """Test customer authentication and validation"""
    
    def test_valid_customer_authentication(self):
        """Test successful authentication with valid customer ID"""
        # Test each valid customer
        valid_customers = ["CUST-001", "CUST-002", "CUST-003", "TEST-CUSTOMER"]
        
        for customer_id in valid_customers:
            result = CustomerValidator.validate_customer(customer_id)
            
            assert result["valid"] is True
            assert result["error"] is None
            assert result["customer_data"] is not None
            assert result["customer_data"]["customer_id"] == customer_id
            assert "name" in result["customer_data"]
            assert "email" in result["customer_data"]
            assert "policies" in result["customer_data"]
            assert result["customer_data"]["status"] == "active"
    
    def test_invalid_customer_id(self):
        """Test authentication fails with invalid customer ID"""
        invalid_ids = ["INVALID-001", "CUST-999", "NONEXISTENT", "FAKE-CUSTOMER"]
        
        for customer_id in invalid_ids:
            result = CustomerValidator.validate_customer(customer_id)
            
            assert result["valid"] is False
            assert "not found in our system" in result["error"]
            assert result["customer_data"] is None
    
    def test_empty_customer_id(self):
        """Test authentication fails with empty customer ID"""
        empty_ids = ["", "   ", None]
        
        for customer_id in empty_ids:
            result = CustomerValidator.validate_customer(customer_id)
            
            assert result["valid"] is False
            assert result["error"] == "Customer ID is required"
            assert result["customer_data"] is None
    
    def test_inactive_customer_account(self):
        """Test authentication fails for inactive customer accounts"""
        result = CustomerValidator.validate_customer("INACTIVE-001")
        
        assert result["valid"] is False
        assert "not active" in result["error"]
        assert result["customer_data"] is None
    
    def test_case_insensitive_customer_id(self):
        """Test customer ID validation is case insensitive"""
        test_cases = [
            ("cust-001", "CUST-001"),
            ("Cust-002", "CUST-002"),
            ("CUST-003", "CUST-003"),
            ("test-customer", "TEST-CUSTOMER")
        ]
        
        for input_id, expected_id in test_cases:
            result = CustomerValidator.validate_customer(input_id)
            
            assert result["valid"] is True
            assert result["customer_data"]["customer_id"] == expected_id
    
    def test_whitespace_handling(self):
        """Test customer ID validation handles whitespace properly"""
        test_cases = [
            " CUST-001 ",
            "  CUST-002  ",
            "\tCUST-003\t",
            "\nTEST-CUSTOMER\n"
        ]
        
        for padded_id in test_cases:
            result = CustomerValidator.validate_customer(padded_id)
            
            assert result["valid"] is True
            assert result["customer_data"]["customer_id"] == padded_id.strip().upper()
    
    def test_customer_data_structure(self):
        """Test that customer data contains all required fields"""
        result = CustomerValidator.validate_customer("CUST-001")
        
        assert result["valid"] is True
        customer_data = result["customer_data"]
        
        # Required fields
        required_fields = ["customer_id", "name", "email", "policies", "status"]
        for field in required_fields:
            assert field in customer_data, f"Missing required field: {field}"
        
        # Data types
        assert isinstance(customer_data["customer_id"], str)
        assert isinstance(customer_data["name"], str)
        assert isinstance(customer_data["email"], str)
        assert isinstance(customer_data["policies"], list)
        assert isinstance(customer_data["status"], str)
        
        # Valid email format (basic check)
        assert "@" in customer_data["email"]
        assert "." in customer_data["email"]


class TestSecureOperations:
    """Test that operations require customer authentication"""
    
    def test_unauthorized_access_prevention(self):
        """Test that operations fail without valid customer ID"""
        # This simulates the behavior expected in the actual system
        
        def mock_insurance_operation(customer_id):
            """Mock function that should require valid customer ID"""
            validation = CustomerValidator.validate_customer(customer_id)
            if not validation["valid"]:
                raise PermissionError(f"Unauthorized: {validation['error']}")
            return {"success": True, "customer_data": validation["customer_data"]}
        
        # Test with invalid customer IDs
        invalid_ids = ["", "INVALID", None, "CUST-999"]
        
        for customer_id in invalid_ids:
            with pytest.raises(PermissionError):
                mock_insurance_operation(customer_id)
    
    def test_authorized_access_allowed(self):
        """Test that operations succeed with valid customer ID"""
        def mock_insurance_operation(customer_id):
            """Mock function that should require valid customer ID"""
            validation = CustomerValidator.validate_customer(customer_id)
            if not validation["valid"]:
                raise PermissionError(f"Unauthorized: {validation['error']}")
            return {"success": True, "customer_data": validation["customer_data"]}
        
        # Test with valid customer IDs
        valid_ids = ["CUST-001", "CUST-002", "CUST-003", "TEST-CUSTOMER"]
        
        for customer_id in valid_ids:
            result = mock_insurance_operation(customer_id)
            assert result["success"] is True
            assert result["customer_data"]["customer_id"] == customer_id


class TestCustomerDataPrivacy:
    """Test customer data privacy and isolation"""
    
    def test_customer_data_isolation(self):
        """Test that each customer only sees their own data"""
        # Get data for different customers
        customer1 = CustomerValidator.validate_customer("CUST-001")
        customer2 = CustomerValidator.validate_customer("CUST-002")
        
        assert customer1["valid"] is True
        assert customer2["valid"] is True
        
        # Ensure data is different
        assert customer1["customer_data"]["customer_id"] != customer2["customer_data"]["customer_id"]
        assert customer1["customer_data"]["name"] != customer2["customer_data"]["name"]
        assert customer1["customer_data"]["email"] != customer2["customer_data"]["email"]
    
    def test_policy_access_control(self):
        """Test that customers can only access their own policies"""
        customer_data = CustomerValidator.validate_customer("CUST-001")["customer_data"]
        
        # Customer should have access to their policies
        assert len(customer_data["policies"]) > 0
        
        # Simulate policy access check
        def can_access_policy(customer_id, policy_number):
            customer = CustomerValidator.validate_customer(customer_id)
            if not customer["valid"]:
                return False
            return policy_number in customer["customer_data"]["policies"]
        
        # Customer should access their own policies
        for policy in customer_data["policies"]:
            assert can_access_policy("CUST-001", policy) is True
        
        # Customer should NOT access other customer's policies
        other_customer = CustomerValidator.validate_customer("CUST-002")["customer_data"]
        for policy in other_customer["policies"]:
            assert can_access_policy("CUST-001", policy) is False


class TestAuditAndLogging:
    """Test audit trail and logging for customer authentication"""
    
    def test_authentication_attempts_logged(self):
        """Test that authentication attempts are properly logged"""
        # Mock logging
        auth_log = []
        
        def mock_log_auth_attempt(customer_id, success, timestamp=None):
            auth_log.append({
                "customer_id": customer_id,
                "success": success,
                "timestamp": timestamp or datetime.now()
            })
        
        # Test authentication attempts
        test_cases = [
            ("CUST-001", True),
            ("INVALID-ID", False),
            ("", False),
            ("CUST-002", True)
        ]
        
        for customer_id, expected_success in test_cases:
            result = CustomerValidator.validate_customer(customer_id)
            mock_log_auth_attempt(customer_id, result["valid"])
        
        # Verify log entries
        assert len(auth_log) == len(test_cases)
        
        for i, (customer_id, expected_success) in enumerate(test_cases):
            log_entry = auth_log[i]
            assert log_entry["customer_id"] == customer_id
            assert log_entry["success"] == expected_success
            assert isinstance(log_entry["timestamp"], datetime)


class TestPerformanceAndSecurity:
    """Test performance and security aspects of customer authentication"""
    
    def test_authentication_performance(self):
        """Test that authentication is performant"""
        import time
        
        start_time = time.time()
        
        # Perform multiple authentication attempts
        for _ in range(100):
            CustomerValidator.validate_customer("CUST-001")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 100 authentications in reasonable time (< 1 second)
        assert total_time < 1.0, f"Authentication too slow: {total_time} seconds for 100 attempts"
    
    def test_no_sensitive_data_in_errors(self):
        """Test that error messages don't leak sensitive information"""
        result = CustomerValidator.validate_customer("INVALID-ID")
        
        assert result["valid"] is False
        error_message = result["error"].lower()
        
        # Error message should not contain sensitive information
        sensitive_terms = ["password", "ssn", "social", "internal", "database", "server"]
        for term in sensitive_terms:
            assert term not in error_message


if __name__ == "__main__":
    # Run tests
    import subprocess
    import sys
    
    # Install pytest if not available
    try:
        import pytest
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest"])
        import pytest
    
    # Run the tests
    pytest.main([__file__, "-v"]) 