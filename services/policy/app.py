from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import os
from .models import (
    Policy, PolicyCreate, PolicyUpdate, PolicySummary, PolicyRenewal, PolicyQuote,
    Coverage, PolicyType, PolicyStatus, CoverageType, PaymentFrequency
)

app = FastAPI(
    title="Policy Service API",
    description="Mock policy data service for insurance PoC",
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
mock_policies = {
    202: Policy(
        policy_id=202,
        customer_id=101,
        policy_number="POL-AUTO-202401-001",
        policy_type=PolicyType.AUTO,
        status=PolicyStatus.ACTIVE,
        effective_date=date(2024, 1, 1),
        expiration_date=date(2024, 12, 31),
        issue_date=date(2023, 12, 15),
        premium_amount=Decimal("1200.00"),
        payment_frequency=PaymentFrequency.MONTHLY,
        coverages=[
            Coverage(
                coverage_type=CoverageType.LIABILITY,
                coverage_limit=Decimal("100000"),
                deductible=Decimal("500"),
                premium=Decimal("600.00"),
                description="Bodily injury and property damage liability"
            ),
            Coverage(
                coverage_type=CoverageType.COMPREHENSIVE,
                coverage_limit=Decimal("50000"),
                deductible=Decimal("250"),
                premium=Decimal("400.00"),
                description="Comprehensive coverage for vehicle damage"
            ),
            Coverage(
                coverage_type=CoverageType.COLLISION,
                coverage_limit=Decimal("50000"),
                deductible=Decimal("250"),
                premium=Decimal("200.00"),
                description="Collision coverage"
            )
        ],
        agent_id=301,
        terms_conditions={"max_drivers": 2, "vehicle_year": 2020}
    ),
    203: Policy(
        policy_id=203,
        customer_id=101,
        policy_number="POL-HOME-202401-002",
        policy_type=PolicyType.HOME,
        status=PolicyStatus.ACTIVE,
        effective_date=date(2024, 1, 1),
        expiration_date=date(2024, 12, 31),
        issue_date=date(2023, 12, 20),
        premium_amount=Decimal("1800.00"),
        payment_frequency=PaymentFrequency.ANNUAL,
        coverages=[
            Coverage(
                coverage_type=CoverageType.PROPERTY_DAMAGE,
                coverage_limit=Decimal("300000"),
                deductible=Decimal("1000"),
                premium=Decimal("1200.00"),
                description="Dwelling coverage"
            ),
            Coverage(
                coverage_type=CoverageType.LIABILITY,
                coverage_limit=Decimal("100000"),
                deductible=None,
                premium=Decimal("600.00"),
                description="Personal liability coverage"
            )
        ],
        agent_id=302,
        terms_conditions={"home_value": 300000, "security_system": True}
    ),
    204: Policy(
        policy_id=204,
        customer_id=102,
        policy_number="POL-AUTO-202402-003",
        policy_type=PolicyType.AUTO,
        status=PolicyStatus.ACTIVE,
        effective_date=date(2024, 2, 1),
        expiration_date=date(2025, 1, 31),
        issue_date=date(2024, 1, 15),
        premium_amount=Decimal("900.00"),
        payment_frequency=PaymentFrequency.QUARTERLY,
        coverages=[
            Coverage(
                coverage_type=CoverageType.LIABILITY,
                coverage_limit=Decimal("75000"),
                deductible=Decimal("750"),
                premium=Decimal("500.00"),
                description="Basic liability coverage"
            ),
            Coverage(
                coverage_type=CoverageType.COMPREHENSIVE,
                coverage_limit=Decimal("30000"),
                deductible=Decimal("500"),
                premium=Decimal("400.00"),
                description="Comprehensive coverage"
            )
        ],
        agent_id=301,
        terms_conditions={"max_drivers": 1, "vehicle_year": 2018}
    ),
    205: Policy(
        policy_id=205,
        customer_id=103,
        policy_number="POL-LIFE-202403-004",
        policy_type=PolicyType.LIFE,
        status=PolicyStatus.EXPIRED,
        effective_date=date(2023, 3, 1),
        expiration_date=date(2024, 2, 29),
        issue_date=date(2023, 2, 15),
        premium_amount=Decimal("500.00"),
        payment_frequency=PaymentFrequency.MONTHLY,
        coverages=[
            Coverage(
                coverage_type=CoverageType.LIFE_TERM,
                coverage_limit=Decimal("100000"),
                deductible=None,
                premium=Decimal("500.00"),
                description="Term life insurance coverage"
            )
        ],
        agent_id=303,
        beneficiaries=["John Davis", "Mary Davis"],
        terms_conditions={"term_years": 10, "renewable": True}
    ),
    206: Policy(
        policy_id=206,
        customer_id=103,
        policy_number="POL-HEALTH-202404-005",
        policy_type=PolicyType.HEALTH,
        status=PolicyStatus.ACTIVE,
        effective_date=date(2024, 4, 1),
        expiration_date=date(2025, 3, 31),
        issue_date=date(2024, 3, 15),
        premium_amount=Decimal("2400.00"),
        payment_frequency=PaymentFrequency.MONTHLY,
        coverages=[
            Coverage(
                coverage_type=CoverageType.MEDICAL,
                coverage_limit=Decimal("500000"),
                deductible=Decimal("2000"),
                premium=Decimal("1800.00"),
                description="Medical coverage"
            ),
            Coverage(
                coverage_type=CoverageType.DISABILITY,
                coverage_limit=Decimal("50000"),
                deductible=None,
                premium=Decimal("600.00"),
                description="Disability insurance"
            )
        ],
        agent_id=304,
        terms_conditions={"network_type": "PPO", "prescription_coverage": True}
    )
}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "policy-service", "timestamp": datetime.now().isoformat()}

@app.get("/policy/{policy_id}", response_model=Policy)
async def get_policy(policy_id: int):
    """Get policy by ID"""
    if policy_id not in mock_policies:
        raise HTTPException(status_code=404, detail="Policy not found")
    return mock_policies[policy_id]

@app.get("/policy/{policy_id}/summary", response_model=PolicySummary)
async def get_policy_summary(policy_id: int):
    """Get policy summary information"""
    if policy_id not in mock_policies:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy = mock_policies[policy_id]
    return PolicySummary.from_policy(policy)

@app.get("/policies", response_model=List[PolicySummary])
async def list_policies(
    customer_id: Optional[int] = None,
    policy_type: Optional[PolicyType] = None,
    status: Optional[PolicyStatus] = None,
    limit: int = 10,
    offset: int = 0
):
    """List policies with optional filtering"""
    policies = list(mock_policies.values())
    
    if customer_id:
        policies = [p for p in policies if p.customer_id == customer_id]
    
    if policy_type:
        policies = [p for p in policies if p.policy_type == policy_type]
    
    if status:
        policies = [p for p in policies if p.status == status]
    
    # Apply pagination
    policies = policies[offset:offset + limit]
    
    return [PolicySummary.from_policy(p) for p in policies]

@app.get("/customer/{customer_id}/policies", response_model=List[PolicySummary])
async def get_customer_policies(customer_id: int):
    """Get all policies for a specific customer"""
    customer_policies = [p for p in mock_policies.values() if p.customer_id == customer_id]
    
    if not customer_policies:
        return []
    
    return [PolicySummary.from_policy(p) for p in customer_policies]

@app.post("/policy", response_model=Policy)
async def create_policy(policy_data: PolicyCreate):
    """Create a new policy"""
    # Generate new policy ID
    new_id = max(mock_policies.keys()) + 1 if mock_policies else 1
    
    # Generate policy number
    policy_number = f"POL-{policy_data.policy_type.upper()}-{datetime.now().strftime('%Y%m')}-{new_id:03d}"
    
    new_policy = Policy(
        policy_id=new_id,
        policy_number=policy_number,
        issue_date=date.today(),
        **policy_data.dict()
    )
    
    mock_policies[new_id] = new_policy
    return new_policy

@app.put("/policy/{policy_id}", response_model=Policy)
async def update_policy(policy_id: int, policy_data: PolicyUpdate):
    """Update existing policy"""
    if policy_id not in mock_policies:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy = mock_policies[policy_id]
    update_data = policy_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(policy, field, value)
    
    policy.updated_at = datetime.now()
    return policy

@app.post("/policy/{policy_id}/renew", response_model=Policy)
async def renew_policy(policy_id: int, renewal_data: PolicyRenewal):
    """Renew an existing policy"""
    if policy_id not in mock_policies:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy = mock_policies[policy_id]
    
    # Update renewal fields
    policy.effective_date = renewal_data.new_effective_date
    policy.expiration_date = renewal_data.new_expiration_date
    policy.status = PolicyStatus.ACTIVE
    
    if renewal_data.new_premium_amount:
        policy.premium_amount = renewal_data.new_premium_amount
    
    if renewal_data.coverage_updates:
        policy.coverages = renewal_data.coverage_updates
    
    policy.updated_at = datetime.now()
    return policy

@app.post("/policy/{policy_id}/cancel")
async def cancel_policy(policy_id: int, cancellation_reason: str = "Customer request"):
    """Cancel a policy"""
    if policy_id not in mock_policies:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy = mock_policies[policy_id]
    policy.status = PolicyStatus.CANCELLED
    policy.updated_at = datetime.now()
    
    return {
        "message": f"Policy {policy_id} has been cancelled",
        "reason": cancellation_reason,
        "cancelled_at": datetime.now().isoformat()
    }

@app.get("/policy/{policy_id}/status")
async def get_policy_status(policy_id: int):
    """Get policy status information"""
    if policy_id not in mock_policies:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy = mock_policies[policy_id]
    today = date.today()
    
    return {
        "policy_id": policy_id,
        "policy_number": policy.policy_number,
        "status": policy.status,
        "effective_date": policy.effective_date.isoformat(),
        "expiration_date": policy.expiration_date.isoformat(),
        "is_active": policy.status == PolicyStatus.ACTIVE and policy.expiration_date > today,
        "days_until_expiry": (policy.expiration_date - today).days if policy.expiration_date > today else 0,
        "premium_amount": float(policy.premium_amount),
        "payment_frequency": policy.payment_frequency
    }

@app.get("/policy/{policy_id}/coverages", response_model=List[Coverage])
async def get_policy_coverages(policy_id: int):
    """Get coverage details for a policy"""
    if policy_id not in mock_policies:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return mock_policies[policy_id].coverages

@app.post("/quote", response_model=PolicyQuote)
async def get_policy_quote(quote_request: PolicyQuote):
    """Get a quote for a new policy"""
    # Simple quote calculation (in reality this would be more complex)
    base_premium = sum(coverage.premium for coverage in quote_request.coverage_requests)
    
    # Apply some basic multipliers based on policy type
    multipliers = {
        PolicyType.AUTO: 1.0,
        PolicyType.HOME: 1.2,
        PolicyType.LIFE: 0.8,
        PolicyType.HEALTH: 1.5,
        PolicyType.BUSINESS: 2.0
    }
    
    estimated_premium = base_premium * multipliers.get(quote_request.policy_type, 1.0)
    
    return PolicyQuote(
        customer_id=quote_request.customer_id,
        policy_type=quote_request.policy_type,
        coverage_requests=quote_request.coverage_requests,
        estimated_premium=estimated_premium,
        quote_valid_until=date.today().replace(day=date.today().day + 30),
        terms_conditions=quote_request.terms_conditions
    )

@app.get("/search/policies")
async def search_policies(
    q: str,
    limit: int = 10
):
    """Search policies by policy number or customer details"""
    q = q.lower()
    results = []
    
    for policy in mock_policies.values():
        if (q in policy.policy_number.lower() or 
            str(policy.customer_id) == q):
            results.append(PolicySummary.from_policy(policy))
            
        if len(results) >= limit:
            break
    
    return results

@app.get("/policies/expiring")
async def get_expiring_policies(days: int = 30):
    """Get policies expiring within specified days"""
    today = date.today()
    expiry_threshold = today.replace(day=today.day + days)
    
    expiring = []
    for policy in mock_policies.values():
        if (policy.status == PolicyStatus.ACTIVE and 
            today < policy.expiration_date <= expiry_threshold):
            expiring.append(PolicySummary.from_policy(policy))
    
    return expiring

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("POLICY_SERVICE_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)