from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uvicorn
import os
import jwt
import logging
from enum import Enum
import time
import uuid
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('policy_service_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('policy_service_request_duration_seconds', 'Request duration')

app = FastAPI(
    title="Policy Service",
    description="Enterprise Policy Management Service for Insurance AI PoC",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")

# Models
class PolicyType(str, Enum):
    AUTO = "auto"
    HOME = "home"
    LIFE = "life"
    HEALTH = "health"
    COMMERCIAL = "commercial"

class PolicyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"

class Coverage(BaseModel):
    type: str
    limit: float
    deductible: float
    premium: float

class PolicyCreate(BaseModel):
    policy_number: Optional[str] = None
    customer_id: str
    policy_type: PolicyType
    coverage_amount: float
    premium_amount: float
    deductible: float
    start_date: datetime
    end_date: datetime
    coverages: List[Coverage] = []
    
    @validator('coverage_amount', 'premium_amount', 'deductible')
    def amounts_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

class PolicyUpdate(BaseModel):
    coverage_amount: Optional[float] = None
    premium_amount: Optional[float] = None
    deductible: Optional[float] = None
    status: Optional[PolicyStatus] = None
    end_date: Optional[datetime] = None
    coverages: Optional[List[Coverage]] = None

class PolicyResponse(BaseModel):
    id: str
    policy_number: str
    customer_id: str
    policy_type: PolicyType
    status: PolicyStatus
    coverage_amount: float
    premium_amount: float
    deductible: float
    start_date: datetime
    end_date: datetime
    coverages: List[Coverage]
    created_at: datetime
    updated_at: datetime

class QuoteRequest(BaseModel):
    customer_id: str
    policy_type: PolicyType
    coverage_amount: float
    customer_age: Optional[int] = None
    customer_location: Optional[str] = None
    risk_factors: Optional[Dict[str, Any]] = {}

class QuoteResponse(BaseModel):
    quote_id: str
    customer_id: str
    policy_type: PolicyType
    coverage_amount: float
    estimated_premium: float
    recommended_deductible: float
    risk_score: float
    valid_until: datetime
    coverages: List[Coverage]

# Mock database
policies_db = {}
quotes_db = {}

# Helper functions
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def generate_policy_number(policy_type: PolicyType) -> str:
    prefix = {
        PolicyType.AUTO: "AUTO",
        PolicyType.HOME: "HOME", 
        PolicyType.LIFE: "LIFE",
        PolicyType.HEALTH: "HLTH",
        PolicyType.COMMERCIAL: "COMM"
    }
    return f"{prefix[policy_type]}-{str(uuid.uuid4())[:8].upper()}"

def calculate_premium(policy_type: PolicyType, coverage_amount: float, risk_factors: Dict) -> float:
    base_rates = {
        PolicyType.AUTO: 0.015,
        PolicyType.HOME: 0.008,
        PolicyType.LIFE: 0.012,
        PolicyType.HEALTH: 0.020,
        PolicyType.COMMERCIAL: 0.025
    }
    
    base_premium = coverage_amount * base_rates.get(policy_type, 0.015)
    
    # Apply risk factor multipliers
    risk_multiplier = 1.0
    if risk_factors.get("age", 0) > 65:
        risk_multiplier *= 1.2
    if risk_factors.get("previous_claims", 0) > 2:
        risk_multiplier *= 1.3
    
    return base_premium * risk_multiplier

def generate_coverages(policy_type: PolicyType, coverage_amount: float) -> List[Coverage]:
    coverage_templates = {
        PolicyType.AUTO: [
            {"type": "Liability", "limit": coverage_amount * 0.5, "deductible": 500, "premium": coverage_amount * 0.008},
            {"type": "Collision", "limit": coverage_amount * 0.3, "deductible": 1000, "premium": coverage_amount * 0.005},
            {"type": "Comprehensive", "limit": coverage_amount * 0.2, "deductible": 500, "premium": coverage_amount * 0.003}
        ],
        PolicyType.HOME: [
            {"type": "Dwelling", "limit": coverage_amount * 0.8, "deductible": 1000, "premium": coverage_amount * 0.006},
            {"type": "Personal Property", "limit": coverage_amount * 0.2, "deductible": 500, "premium": coverage_amount * 0.002}
        ],
        PolicyType.LIFE: [
            {"type": "Death Benefit", "limit": coverage_amount, "deductible": 0, "premium": coverage_amount * 0.012}
        ],
        PolicyType.HEALTH: [
            {"type": "Medical", "limit": coverage_amount * 0.8, "deductible": 2000, "premium": coverage_amount * 0.015},
            {"type": "Prescription", "limit": coverage_amount * 0.2, "deductible": 100, "premium": coverage_amount * 0.005}
        ],
        PolicyType.COMMERCIAL: [
            {"type": "General Liability", "limit": coverage_amount * 0.6, "deductible": 5000, "premium": coverage_amount * 0.015},
            {"type": "Property", "limit": coverage_amount * 0.4, "deductible": 2500, "premium": coverage_amount * 0.010}
        ]
    }
    
    templates = coverage_templates.get(policy_type, [])
    return [Coverage(**template) for template in templates]

# Initialize sample data
def initialize_sample_data():
    sample_policies = [
        {
            "id": "policy_001",
            "policy_number": "AUTO-12345ABC",
            "customer_id": "user_003",
            "policy_type": PolicyType.AUTO,
            "status": PolicyStatus.ACTIVE,
            "coverage_amount": 50000.0,
            "premium_amount": 1200.0,
            "deductible": 500.0,
            "start_date": datetime.utcnow() - timedelta(days=30),
            "end_date": datetime.utcnow() + timedelta(days=335),
            "coverages": [],
            "created_at": datetime.utcnow() - timedelta(days=30),
            "updated_at": datetime.utcnow() - timedelta(days=30)
        },
        {
            "id": "policy_002",
            "policy_number": "HOME-67890DEF",
            "customer_id": "user_003",
            "policy_type": PolicyType.HOME,
            "status": PolicyStatus.ACTIVE,
            "coverage_amount": 250000.0,
            "premium_amount": 2000.0,
            "deductible": 1000.0,
            "start_date": datetime.utcnow() - timedelta(days=60),
            "end_date": datetime.utcnow() + timedelta(days=305),
            "coverages": [],
            "created_at": datetime.utcnow() - timedelta(days=60),
            "updated_at": datetime.utcnow() - timedelta(days=60)
        }
    ]
    
    for policy_data in sample_policies:
        policy_id = policy_data["id"]
        policy_data["coverages"] = generate_coverages(policy_data["policy_type"], policy_data["coverage_amount"])
        policies_db[policy_id] = policy_data

# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    
    response = await call_next(request)
    
    REQUEST_DURATION.observe(time.time() - start_time)
    return response

# Routes
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "policy-service", "timestamp": datetime.utcnow()}

@app.get("/metrics")
async def metrics():
    return generate_latest()

@app.post("/quotes", response_model=QuoteResponse)
async def create_quote(quote_request: QuoteRequest, current_user: dict = Depends(verify_token)):
    quote_id = f"quote_{str(uuid.uuid4())[:8]}"
    
    risk_score = calculate_premium(
        quote_request.policy_type, 
        quote_request.coverage_amount, 
        quote_request.risk_factors
    ) / quote_request.coverage_amount
    
    estimated_premium = calculate_premium(
        quote_request.policy_type,
        quote_request.coverage_amount,
        quote_request.risk_factors
    )
    
    recommended_deductible = min(quote_request.coverage_amount * 0.05, 2500)
    coverages = generate_coverages(quote_request.policy_type, quote_request.coverage_amount)
    
    quote_data = {
        "quote_id": quote_id,
        "customer_id": quote_request.customer_id,
        "policy_type": quote_request.policy_type,
        "coverage_amount": quote_request.coverage_amount,
        "estimated_premium": estimated_premium,
        "recommended_deductible": recommended_deductible,
        "risk_score": risk_score,
        "valid_until": datetime.utcnow() + timedelta(days=30),
        "coverages": coverages,
        "created_at": datetime.utcnow()
    }
    
    quotes_db[quote_id] = quote_data
    
    return QuoteResponse(**quote_data)

@app.post("/policies", response_model=PolicyResponse)
async def create_policy(policy: PolicyCreate, current_user: dict = Depends(verify_token)):
    policy_id = f"policy_{str(uuid.uuid4())[:8]}"
    policy_number = policy.policy_number or generate_policy_number(policy.policy_type)
    
    coverages = policy.coverages or generate_coverages(policy.policy_type, policy.coverage_amount)
    
    policy_data = {
        "id": policy_id,
        "policy_number": policy_number,
        "customer_id": policy.customer_id,
        "policy_type": policy.policy_type,
        "status": PolicyStatus.ACTIVE,
        "coverage_amount": policy.coverage_amount,
        "premium_amount": policy.premium_amount,
        "deductible": policy.deductible,
        "start_date": policy.start_date,
        "end_date": policy.end_date,
        "coverages": coverages,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    policies_db[policy_id] = policy_data
    
    return PolicyResponse(**policy_data)

@app.get("/policies", response_model=List[PolicyResponse])
async def get_policies(customer_id: Optional[str] = None, current_user: dict = Depends(verify_token)):
    policies = list(policies_db.values())
    
    if customer_id:
        policies = [p for p in policies if p["customer_id"] == customer_id]
    
    return [PolicyResponse(**policy) for policy in policies]

@app.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: str, current_user: dict = Depends(verify_token)):
    if policy_id not in policies_db:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy = policies_db[policy_id]
    return PolicyResponse(**policy)

@app.put("/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(policy_id: str, policy_update: PolicyUpdate, current_user: dict = Depends(verify_token)):
    if policy_id not in policies_db:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy = policies_db[policy_id]
    
    # Update fields
    update_data = policy_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        policy[field] = value
    
    policy["updated_at"] = datetime.utcnow()
    
    return PolicyResponse(**policy)

@app.delete("/policies/{policy_id}")
async def cancel_policy(policy_id: str, current_user: dict = Depends(verify_token)):
    if policy_id not in policies_db:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy = policies_db[policy_id]
    policy["status"] = PolicyStatus.CANCELLED
    policy["updated_at"] = datetime.utcnow()
    
    return {"message": "Policy cancelled successfully"}

@app.get("/policies/{policy_id}/coverage")
async def get_policy_coverage(policy_id: str, current_user: dict = Depends(verify_token)):
    if policy_id not in policies_db:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy = policies_db[policy_id]
    return {
        "policy_id": policy_id,
        "coverage_amount": policy["coverage_amount"],
        "coverages": policy["coverages"],
        "deductible": policy["deductible"]
    }

@app.get("/analytics/policies")
async def get_policy_analytics(current_user: dict = Depends(verify_token)):
    total_policies = len(policies_db)
    active_policies = sum(1 for p in policies_db.values() if p["status"] == PolicyStatus.ACTIVE)
    
    type_distribution = {}
    total_coverage = 0
    total_premiums = 0
    
    for policy in policies_db.values():
        policy_type = policy["policy_type"]
        type_distribution[policy_type] = type_distribution.get(policy_type, 0) + 1
        total_coverage += policy["coverage_amount"]
        total_premiums += policy["premium_amount"]
    
    return {
        "total_policies": total_policies,
        "active_policies": active_policies,
        "cancelled_policies": total_policies - active_policies,
        "type_distribution": type_distribution,
        "total_coverage_amount": total_coverage,
        "total_premium_revenue": total_premiums,
        "average_coverage": total_coverage / total_policies if total_policies > 0 else 0,
        "timestamp": datetime.utcnow()
    }

# Initialize sample data on startup
initialize_sample_data()

if __name__ == "__main__":
    port = int(os.getenv("POLICY_SERVICE_PORT", 8000))
    host = os.getenv("POLICY_SERVICE_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port) 