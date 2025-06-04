import pytest
import asyncio
from fastapi.testclient import TestClient
from datetime import datetime, date
import sys
import os

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services'))

from customer.app import app
from customer.models import Customer, CustomerStatus, Address, ContactInfo


class TestCustomerService:
    """Unit tests for Customer Service API"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "customer-service"
        assert "timestamp" in data
    
    def test_get_customer_existing(self):
        """Test getting an existing customer"""
        response = self.client.get("/customer/101")
        assert response.status_code == 200
        data = response.json()
        assert data["customer_id"] == 101
        assert data["first_name"] == "Alice"
        assert data["last_name"] == "Johnson"
        assert data["status"] == "active"
        assert len(data["policy_ids"]) == 2
    
    def test_get_customer_not_found(self):
        """Test getting a non-existent customer"""
        response = self.client.get("/customer/999")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Customer not found"
    
    def test_get_customer_summary(self):
        """Test getting customer summary"""
        response = self.client.get("/customer/101/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["customer_id"] == 101
        assert data["full_name"] == "Alice Johnson"
        assert data["email"] == "alice.johnson@email.com"
        assert data["policy_count"] == 2
    
    def test_list_customers(self):
        """Test listing customers"""
        response = self.client.get("/customers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # We have at least 3 mock customers
        
        # Check first customer structure
        customer = data[0]
        assert "customer_id" in customer
        assert "full_name" in customer
        assert "status" in customer
    
    def test_list_customers_with_status_filter(self):
        """Test listing customers with status filter"""
        response = self.client.get("/customers?status=active")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned customers should be active
        for customer in data:
            assert customer["status"] == "active"
    
    def test_list_customers_with_pagination(self):
        """Test listing customers with pagination"""
        response = self.client.get("/customers?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 2
    
    def test_create_customer(self):
        """Test creating a new customer"""
        new_customer_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01T00:00:00",
            "address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "zip_code": "12345",
                "country": "USA"
            },
            "contact": {
                "email": "john.doe@test.com",
                "phone": "555-1234"
            }
        }
        
        response = self.client.post("/customer", json=new_customer_data)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["status"] == "active"
        assert "customer_id" in data
    
    def test_update_customer(self):
        """Test updating an existing customer"""
        update_data = {
            "first_name": "Alice Updated",
            "contact": {
                "email": "alice.updated@email.com",
                "phone": "555-0101",
                "mobile": "555-0102"
            }
        }
        
        response = self.client.put("/customer/101", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Alice Updated"
        assert data["contact"]["email"] == "alice.updated@email.com"
    
    def test_update_customer_not_found(self):
        """Test updating a non-existent customer"""
        update_data = {"first_name": "Test"}
        
        response = self.client.put("/customer/999", json=update_data)
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Customer not found"
    
    def test_delete_customer(self):
        """Test deleting (deactivating) a customer"""
        response = self.client.delete("/customer/103")
        assert response.status_code == 200
        data = response.json()
        assert "deactivated" in data["message"]
    
    def test_delete_customer_not_found(self):
        """Test deleting a non-existent customer"""
        response = self.client.delete("/customer/999")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Customer not found"
    
    def test_get_customer_policies(self):
        """Test getting customer policies"""
        response = self.client.get("/customer/101/policies")
        assert response.status_code == 200
        data = response.json()
        assert data["customer_id"] == 101
        assert "policy_ids" in data
        assert "policy_count" in data
        assert len(data["policy_ids"]) == data["policy_count"]
    
    def test_add_policy_to_customer(self):
        """Test adding a policy to a customer"""
        response = self.client.post("/customer/101/policies/999")
        assert response.status_code == 200
        data = response.json()
        assert "added" in data["message"]
    
    def test_remove_policy_from_customer(self):
        """Test removing a policy from a customer"""
        response = self.client.delete("/customer/101/policies/202")
        assert response.status_code == 200
        data = response.json()
        assert "removed" in data["message"]
    
    def test_search_customers(self):
        """Test searching customers"""
        response = self.client.get("/search/customers?q=alice")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should find Alice Johnson (name may have been updated by previous test)
        found_alice = any("alice" in customer["first_name"].lower() for customer in data)
        assert found_alice
    
    def test_search_customers_by_email(self):
        """Test searching customers by email"""
        # Search for updated email since previous test may have modified it
        response = self.client.get("/search/customers?q=alice.updated@email.com")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # Should find Alice Johnson (with updated email)
        found_customer = data[0]
        assert "alice" in found_customer["email"].lower()
    
    def test_search_customers_no_results(self):
        """Test searching customers with no results"""
        response = self.client.get("/search/customers?q=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestCustomerModels:
    """Unit tests for Customer models"""
    
    def test_customer_response_from_customer(self):
        """Test CustomerResponse.from_customer method"""
        customer = Customer(
            customer_id=123,
            first_name="Test",
            last_name="User",
            date_of_birth=datetime(1990, 1, 1),
            address=Address(
                street="123 Test St",
                city="Test City", 
                state="TS",
                zip_code="12345"
            ),
            contact=ContactInfo(
                email="test@example.com",
                phone="555-1234"
            ),
            policy_ids=[1, 2, 3]
        )
        
        from customer.models import CustomerResponse
        response = CustomerResponse.from_customer(customer)
        
        assert response.customer_id == 123
        assert response.full_name == "Test User"
        assert response.email == "test@example.com"
        assert response.policy_count == 3
    
    def test_customer_status_enum(self):
        """Test CustomerStatus enum values"""
        assert CustomerStatus.ACTIVE == "active"
        assert CustomerStatus.INACTIVE == "inactive"
        assert CustomerStatus.SUSPENDED == "suspended"
    
    def test_address_model(self):
        """Test Address model"""
        address = Address(
            street="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345"
        )
        assert address.country == "USA"  # Default value
    
    def test_contact_info_model(self):
        """Test ContactInfo model"""
        contact = ContactInfo(
            email="test@example.com",
            phone="555-1234"
        )
        assert contact.mobile is None  # Optional field


if __name__ == "__main__":
    pytest.main([__file__])