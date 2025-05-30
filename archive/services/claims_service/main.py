"""
Claims Service - FastAPI mock enterprise service for claims management.
Provides CRUD operations for insurance claims with authentication.
"""

import os
import uuid
import sys
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator
import structlog

# Try to import shared utilities
try:
    # Add parent directory to path for importing shared utilities
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from shared.port_utils import get_service_port
    PORT_UTILS_AVAILABLE = True
except ImportError:
    PORT_UTILS_AVAILABLE = False
    print("Port utilities not available, using default port handling")

# Try to import FastMCP
try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    print("FastMCP not available, running as standard FastAPI service")

logger = structlog.get_logger(__name__)

# Pydantic models
class Claim(BaseModel):
    claim_id: str = Field(..., description="Unique claim identifier")
    policy_number: str = Field(..., description="Policy number")
    customer_id: str = Field(..., description="Customer identifier")
    incident_date: str = Field(..., description="Date of incident")
    reported_date: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    description: str = Field(..., description="Description of the incident")
    amount: float = Field(..., ge=0, description="Claim amount")
    status: str = Field(default="submitted", description="Claim status")
    claim_type: str = Field(..., description="Type of claim")
    adjuster_id: Optional[str] = Field(None, description="Assigned adjuster")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ClaimCreate(BaseModel):
    policy_number: str
    customer_id: str
    incident_date: str
    description: str
    amount: float = Field(..., ge=0)
    claim_type: str


class ClaimUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = Field(None, ge=0)
    status: Optional[str] = None
    adjuster_id: Optional[str] = None


class Payment(BaseModel):
    payment_id: str = Field(..., description="Unique payment identifier")
    claim_id: str = Field(..., description="Associated claim ID")
    amount: float = Field(..., ge=0, description="Payment amount")
    status: str = Field(default="pending", description="Payment status")
    payment_method: str = Field(default="bank_transfer", description="Payment method")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    processed_at: Optional[str] = Field(None, description="Payment processing timestamp")
    approver: Optional[str] = Field(None, description="Who approved the payment")


class PaymentCreate(BaseModel):
    claim_id: str
    amount: float = Field(..., ge=0)
    payment_method: str = Field(default="bank_transfer")
    approver: Optional[str] = None


# FastAPI app setup
app = FastAPI(
    title="Claims Service",
    description="Mock enterprise service for insurance claims management",
    version="1.0.0",
    openapi_tags=[
        {"name": "claims", "description": "Claims management operations"},
        {"name": "payments", "description": "Payment processing operations"},
        {"name": "health", "description": "Service health endpoints"}
    ]
)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Security
security = HTTPBearer()

# In-memory storage (in production, use a proper database)
claims_db: Dict[str, Claim] = {}
payments_db: Dict[str, Payment] = {}

# Initialize with some mock data
def init_mock_data():
    """Initialize mock claims data"""
    mock_claims = [
        {
            "claim_id": "CLM-001",
            "policy_number": "POL-001",
            "customer_id": "CUST-001",
            "incident_date": "2024-01-10",
            "description": "Minor fender bender in parking lot",
            "amount": 2500.0,
            "status": "approved",
            "claim_type": "auto_collision",
            "adjuster_id": "ADJ-001"
        },
        {
            "claim_id": "CLM-002", 
            "policy_number": "POL-001",
            "customer_id": "CUST-001",
            "incident_date": "2024-03-15",
            "description": "Windshield replacement due to stone chip",
            "amount": 350.0,
            "status": "processing",
            "claim_type": "auto_comprehensive"
        },
        {
            "claim_id": "CLM-003",
            "policy_number": "POL-002",
            "customer_id": "CUST-002", 
            "incident_date": "2024-02-20",
            "description": "Water damage from burst pipe",
            "amount": 8500.0,
            "status": "under_review",
            "claim_type": "home_water_damage",
            "adjuster_id": "ADJ-002"
        }
    ]
    
    for claim_data in mock_claims:
        claim = Claim(**claim_data)
        claims_db[claim.claim_id] = claim
    
    logger.info("Mock claims data initialized", count=len(claims_db))

# Initialize mock data on startup
@app.on_event("startup")
async def startup_event():
    init_mock_data()

# FastMCP Integration
try:
    from mcp_server import ClaimsMCPServer
    claims_mcp = ClaimsMCPServer(app, claims_db)
    logger.info("FastMCP server integrated successfully")
except ImportError as e:
    logger.warning("FastMCP not available, continuing without MCP integration", error=str(e))
except Exception as e:
    logger.error("Failed to initialize FastMCP server", error=str(e))

# Utility functions
def validate_token(token: str) -> bool:
    """Simple token validation (in production, use proper JWT validation)"""
    return token and len(token) > 10

async def get_current_token(credentials = Depends(security)) -> str:
    """Dependency to validate bearer token"""
    if not validate_token(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return credentials.credentials

# Health check endpoints
@app.get("/health", tags=["health"])
async def health_check():
    """Service health check"""
    return {
        "status": "healthy",
        "service": "claims-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "claims_count": len(claims_db),
        "payments_count": len(payments_db)
    }

@app.get("/ready", tags=["health"])
async def readiness_check():
    """Service readiness check"""
    # Check if service is ready to accept requests
    is_ready = len(claims_db) > 0  # Simple check
    
    if not is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )
    
    return {"status": "ready", "service": "claims-service"}

# Claims endpoints
@app.get("/claims", response_model=List[Claim], tags=["claims"])
async def list_claims(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    limit: int = 100,
    token: str = Depends(get_current_token)
):
    """List claims with optional filtering"""
    claims = list(claims_db.values())
    
    # Apply filters
    if status:
        claims = [c for c in claims if c.status == status]
    
    if customer_id:
        claims = [c for c in claims if c.customer_id == customer_id]
    
    # Apply limit
    claims = claims[:limit]
    
    logger.info("Claims listed", count=len(claims), status=status, customer_id=customer_id)
    return claims

@app.get("/claims/{claim_id}", response_model=Claim, tags=["claims"])
async def get_claim(claim_id: str, token: str = Depends(get_current_token)):
    """Get a specific claim by ID"""
    if claim_id not in claims_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )
    
    claim = claims_db[claim_id]
    logger.info("Claim retrieved", claim_id=claim_id)
    return claim

@app.post("/claims", response_model=Claim, status_code=status.HTTP_201_CREATED, tags=["claims"])
async def create_claim(
    claim_data: ClaimCreate,
    token: str = Depends(get_current_token)
):
    """Create a new claim"""
    claim_id = f"CLM-{str(uuid.uuid4())[:8].upper()}"
    
    claim = Claim(
        claim_id=claim_id,
        policy_number=claim_data.policy_number,
        customer_id=claim_data.customer_id,
        incident_date=claim_data.incident_date,
        description=claim_data.description,
        amount=claim_data.amount,
        claim_type=claim_data.claim_type,
        status="submitted"
    )
    
    claims_db[claim_id] = claim
    
    logger.info("Claim created", claim_id=claim_id, amount=claim.amount)
    return claim

@app.put("/claims/{claim_id}", response_model=Claim, tags=["claims"])
async def update_claim(
    claim_id: str,
    claim_update: ClaimUpdate,
    token: str = Depends(get_current_token)
):
    """Update an existing claim"""
    if claim_id not in claims_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )
    
    claim = claims_db[claim_id]
    
    # Update fields
    update_data = claim_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(claim, field, value)
    
    claim.updated_at = datetime.utcnow().isoformat()
    
    logger.info("Claim updated", claim_id=claim_id, updates=list(update_data.keys()))
    return claim

@app.delete("/claims/{claim_id}", tags=["claims"])
async def delete_claim(claim_id: str, token: str = Depends(get_current_token)):
    """Delete a claim"""
    if claim_id not in claims_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )
    
    del claims_db[claim_id]
    
    logger.info("Claim deleted", claim_id=claim_id)
    return {"message": f"Claim {claim_id} deleted successfully"}

# Claims status management
@app.post("/claims/{claim_id}/approve", response_model=Claim, tags=["claims"])
async def approve_claim(
    claim_id: str,
    approver: str = "system",
    token: str = Depends(get_current_token)
):
    """Approve a claim"""
    if claim_id not in claims_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )
    
    claim = claims_db[claim_id]
    claim.status = "approved"
    claim.updated_at = datetime.utcnow().isoformat()
    
    logger.info("Claim approved", claim_id=claim_id, approver=approver)
    return claim

@app.post("/claims/{claim_id}/reject", response_model=Claim, tags=["claims"])
async def reject_claim(
    claim_id: str,
    reason: str = "No reason provided",
    reviewer: str = "system",
    token: str = Depends(get_current_token)
):
    """Reject a claim"""
    if claim_id not in claims_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )
    
    claim = claims_db[claim_id]
    claim.status = "rejected"
    claim.updated_at = datetime.utcnow().isoformat()
    
    logger.info("Claim rejected", claim_id=claim_id, reason=reason, reviewer=reviewer)
    return claim

# Payment endpoints
@app.get("/payments", response_model=List[Payment], tags=["payments"])
async def list_payments(
    claim_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    token: str = Depends(get_current_token)
):
    """List payments with optional filtering"""
    payments = list(payments_db.values())
    
    # Apply filters
    if claim_id:
        payments = [p for p in payments if p.claim_id == claim_id]
    
    if status:
        payments = [p for p in payments if p.status == status]
    
    # Apply limit
    payments = payments[:limit]
    
    logger.info("Payments listed", count=len(payments), claim_id=claim_id, status=status)
    return payments

@app.get("/payments/{payment_id}", response_model=Payment, tags=["payments"])
async def get_payment(payment_id: str, token: str = Depends(get_current_token)):
    """Get a specific payment by ID"""
    if payment_id not in payments_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found"
        )
    
    payment = payments_db[payment_id]
    logger.info("Payment retrieved", payment_id=payment_id)
    return payment

@app.post("/payments", response_model=Payment, status_code=status.HTTP_201_CREATED, tags=["payments"])
async def create_payment(
    payment_data: PaymentCreate,
    token: str = Depends(get_current_token)
):
    """Create a new payment for a claim"""
    # Verify claim exists
    if payment_data.claim_id not in claims_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {payment_data.claim_id} not found"
        )
    
    payment_id = f"PAY-{str(uuid.uuid4())[:8].upper()}"
    
    payment = Payment(
        payment_id=payment_id,
        claim_id=payment_data.claim_id,
        amount=payment_data.amount,
        payment_method=payment_data.payment_method,
        approver=payment_data.approver,
        status="pending"
    )
    
    payments_db[payment_id] = payment
    
    logger.info("Payment created", payment_id=payment_id, claim_id=payment_data.claim_id, amount=payment.amount)
    return payment

@app.post("/payments/{payment_id}/process", response_model=Payment, tags=["payments"])
async def process_payment(
    payment_id: str,
    token: str = Depends(get_current_token)
):
    """Process a pending payment"""
    if payment_id not in payments_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found"
        )
    
    payment = payments_db[payment_id]
    
    if payment.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment {payment_id} is not in pending status"
        )
    
    payment.status = "processed"
    payment.processed_at = datetime.utcnow().isoformat()
    
    logger.info("Payment processed", payment_id=payment_id, amount=payment.amount)
    return payment

# Analytics endpoints
@app.get("/analytics/claims-summary", tags=["analytics"])
async def get_claims_summary(token: str = Depends(get_current_token)):
    """Get claims analytics summary"""
    claims = list(claims_db.values())
    
    total_claims = len(claims)
    total_amount = sum(claim.amount for claim in claims)
    avg_amount = total_amount / total_claims if total_claims > 0 else 0
    
    status_breakdown = {}
    type_breakdown = {}
    
    for claim in claims:
        # Status breakdown
        status_breakdown[claim.status] = status_breakdown.get(claim.status, 0) + 1
        
        # Type breakdown
        type_breakdown[claim.claim_type] = type_breakdown.get(claim.claim_type, 0) + 1
    
    return {
        "total_claims": total_claims,
        "total_amount": total_amount,
        "average_amount": avg_amount,
        "status_breakdown": status_breakdown,
        "type_breakdown": type_breakdown,
        "generated_at": datetime.utcnow().isoformat()
    }

@app.get("/analytics/payments-summary", tags=["analytics"])
async def get_payments_summary(token: str = Depends(get_current_token)):
    """Get payments analytics summary"""
    payments = list(payments_db.values())
    
    total_payments = len(payments)
    total_amount = sum(payment.amount for payment in payments)
    
    status_breakdown = {}
    for payment in payments:
        status_breakdown[payment.status] = status_breakdown.get(payment.status, 0) + 1
    
    return {
        "total_payments": total_payments,
        "total_amount": total_amount,
        "status_breakdown": status_breakdown,
        "generated_at": datetime.utcnow().isoformat()
    }

# Search endpoints
@app.get("/search/claims", response_model=List[Claim], tags=["claims"])
async def search_claims(
    q: str,
    limit: int = 20,
    token: str = Depends(get_current_token)
):
    """Search claims by description or claim ID"""
    query = q.lower()
    matching_claims = []
    
    for claim in claims_db.values():
        if (query in claim.description.lower() or 
            query in claim.claim_id.lower() or
            query in claim.policy_number.lower()):
            matching_claims.append(claim)
    
    # Limit results
    matching_claims = matching_claims[:limit]
    
    logger.info("Claims search performed", query=q, results=len(matching_claims))
    return matching_claims

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("CLAIMS_SERVICE_HOST", "0.0.0.0")
    
    # Use the port utility to find an available port
    if PORT_UTILS_AVAILABLE:
        try:
            port = get_service_port("claims", 8001, host=host)
        except Exception as e:
            print(f"Error finding available port: {e}")
            port = int(os.getenv("CLAIMS_SERVICE_PORT", 8001))
    else:
        port = int(os.getenv("CLAIMS_SERVICE_PORT", 8001))
    
    # Check if we should run as FastMCP or regular FastAPI
    use_fastmcp = os.getenv("USE_FASTMCP", "true").lower() == "true"
    
    if FASTMCP_AVAILABLE and use_fastmcp:
        # Use the properly configured ClaimsMCPServer with real MCP tools
        try:
            from mcp_server import ClaimsMCPServer
            claims_mcp_server = ClaimsMCPServer(app, claims_db)
            
            # Use the MCP server directly
            mcp = claims_mcp_server.mcp
            
            logger.info(f"Starting Claims Service with FastMCP and proper MCP tools on {host}:{port}")
            print(f"  FastMCP endpoints: http://{host}:{port}/mcp/")
            print(f"  MCP tools available: list_claims, get_claim_details, create_claim, update_claim_status")
            mcp.run(transport="streamable-http", host=host, port=port)
        except Exception as e:
            logger.error(f"Failed to start with MCP tools, falling back to regular FastAPI: {e}")
            logger.info(f"Starting Claims Service as FastAPI on {host}:{port}")
            print(f"  Health check: http://{host}:{port}/health")
            print(f"  API docs: http://{host}:{port}/docs")
            uvicorn.run(app, host=host, port=port)
    else:
        logger.info(f"Starting Claims Service as FastAPI on {host}:{port}")
        print(f"  Health check: http://{host}:{port}/health")
        print(f"  API docs: http://{host}:{port}/docs")
        uvicorn.run(app, host=host, port=port) 