from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
import os
from .models import Customer, CustomerCreate, CustomerUpdate, CustomerResponse, Address, ContactInfo, CustomerStatus

app = FastAPI(
    title="Customer Service API",
    description="Mock customer data service for insurance PoC",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data store
mock_customers = {
    101: Customer(
        customer_id=101,
        first_name="Alice",
        last_name="Johnson",
        date_of_birth=datetime(1985, 3, 15),
        address=Address(
            street="123 Main St",
            city="Springfield",
            state="IL",
            zip_code="62701"
        ),
        contact=ContactInfo(
            email="alice.johnson@email.com",
            phone="555-0101",
            mobile="555-0102"
        ),
        status=CustomerStatus.ACTIVE,
        policy_ids=[202, 203]
    ),
    102: Customer(
        customer_id=102,
        first_name="Bob",
        last_name="Smith",
        date_of_birth=datetime(1978, 7, 22),
        address=Address(
            street="456 Oak Ave",
            city="Chicago",
            state="IL",
            zip_code="60601"
        ),
        contact=ContactInfo(
            email="bob.smith@email.com",
            phone="555-0201"
        ),
        status=CustomerStatus.ACTIVE,
        policy_ids=[204]
    ),
    103: Customer(
        customer_id=103,
        first_name="Carol",
        last_name="Davis",
        date_of_birth=datetime(1990, 11, 8),
        address=Address(
            street="789 Pine Rd",
            city="Peoria",
            state="IL",
            zip_code="61602"
        ),
        contact=ContactInfo(
            email="carol.davis@email.com",
            phone="555-0301",
            mobile="555-0302"
        ),
        status=CustomerStatus.INACTIVE,
        policy_ids=[205, 206]
    )
}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "customer-service", "timestamp": datetime.now().isoformat()}

@app.get("/customer/{customer_id}", response_model=Customer)
async def get_customer(customer_id: int):
    """Get customer by ID"""
    if customer_id not in mock_customers:
        raise HTTPException(status_code=404, detail="Customer not found")
    return mock_customers[customer_id]

@app.get("/customer/{customer_id}/summary", response_model=CustomerResponse)
async def get_customer_summary(customer_id: int):
    """Get customer summary information"""
    if customer_id not in mock_customers:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer = mock_customers[customer_id]
    return CustomerResponse.from_customer(customer)

@app.get("/customers", response_model=List[CustomerResponse])
async def list_customers(
    status: Optional[CustomerStatus] = None,
    limit: int = 10,
    offset: int = 0
):
    """List customers with optional filtering"""
    customers = list(mock_customers.values())
    
    if status:
        customers = [c for c in customers if c.status == status]
    
    # Apply pagination
    customers = customers[offset:offset + limit]
    
    return [CustomerResponse.from_customer(c) for c in customers]

@app.post("/customer", response_model=Customer)
async def create_customer(customer_data: CustomerCreate):
    """Create a new customer"""
    # Generate new customer ID
    new_id = max(mock_customers.keys()) + 1 if mock_customers else 1
    
    new_customer = Customer(
        customer_id=new_id,
        **customer_data.dict()
    )
    
    mock_customers[new_id] = new_customer
    return new_customer

@app.put("/customer/{customer_id}", response_model=Customer)
async def update_customer(customer_id: int, customer_data: CustomerUpdate):
    """Update existing customer"""
    if customer_id not in mock_customers:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer = mock_customers[customer_id]
    update_data = customer_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "contact" and value is not None:
            # Ensure contact remains a ContactInfo object
            if isinstance(value, dict):
                customer.contact = ContactInfo(**value)
            else:
                customer.contact = value
        elif field == "address" and value is not None:
            # Ensure address remains an Address object
            if isinstance(value, dict):
                customer.address = Address(**value)
            else:
                customer.address = value
        else:
            setattr(customer, field, value)
    
    customer.updated_at = datetime.now()
    return customer

@app.delete("/customer/{customer_id}")
async def delete_customer(customer_id: int):
    """Delete customer (soft delete by setting status to inactive)"""
    if customer_id not in mock_customers:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    mock_customers[customer_id].status = CustomerStatus.INACTIVE
    mock_customers[customer_id].updated_at = datetime.now()
    
    return {"message": f"Customer {customer_id} deactivated"}

@app.get("/customer/{customer_id}/policies")
async def get_customer_policies(customer_id: int):
    """Get list of policy IDs for a customer"""
    if customer_id not in mock_customers:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer = mock_customers[customer_id]
    return {
        "customer_id": customer_id,
        "policy_ids": customer.policy_ids,
        "policy_count": len(customer.policy_ids)
    }

@app.post("/customer/{customer_id}/policies/{policy_id}")
async def add_policy_to_customer(customer_id: int, policy_id: int):
    """Add a policy to a customer"""
    if customer_id not in mock_customers:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer = mock_customers[customer_id]
    if policy_id not in customer.policy_ids:
        customer.policy_ids.append(policy_id)
        customer.updated_at = datetime.now()
    
    return {"message": f"Policy {policy_id} added to customer {customer_id}"}

@app.delete("/customer/{customer_id}/policies/{policy_id}")
async def remove_policy_from_customer(customer_id: int, policy_id: int):
    """Remove a policy from a customer"""
    if customer_id not in mock_customers:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer = mock_customers[customer_id]
    if policy_id in customer.policy_ids:
        customer.policy_ids.remove(policy_id)
        customer.updated_at = datetime.now()
    
    return {"message": f"Policy {policy_id} removed from customer {customer_id}"}

@app.get("/search/customers")
async def search_customers(
    q: str,
    limit: int = 10
):
    """Search customers by name or email"""
    q = q.lower()
    results = []
    
    for customer in mock_customers.values():
        # Handle contact as either ContactInfo object or dict
        contact_email = ""
        if hasattr(customer.contact, 'email'):
            contact_email = customer.contact.email.lower()
        elif isinstance(customer.contact, dict) and 'email' in customer.contact:
            contact_email = customer.contact['email'].lower()
        
        if (q in customer.first_name.lower() or 
            q in customer.last_name.lower() or 
            q in contact_email):
            results.append(CustomerResponse.from_customer(customer))
            
        if len(results) >= limit:
            break
    
    return results

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("CUSTOMER_SERVICE_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)