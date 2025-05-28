from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import os
import uuid
from .models import (
    Claim, ClaimCreate, ClaimUpdate, ClaimSummary, ClaimStatusUpdate, ClaimPayment,
    ClaimDocument, ClaimNote, IncidentDetails, ClaimAmount, DocumentType,
    ClaimType, ClaimStatus, ClaimPriority
)

app = FastAPI(
    title="Claims Service API",
    description="Mock claims data service for insurance PoC",
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
mock_claims = {
    1001: Claim(
        claim_id=1001,
        claim_number="CLM-AUTO-20240115-001",
        customer_id=101,
        policy_id=202,
        claim_type=ClaimType.AUTO_ACCIDENT,
        status=ClaimStatus.UNDER_REVIEW,
        priority=ClaimPriority.HIGH,
        incident_details=IncidentDetails(
            incident_date=date(2024, 1, 15),
            incident_time="14:30",
            location="Main St & Oak Ave, Springfield, IL",
            description="Rear-end collision at traffic light. Other driver ran red light.",
            police_report_number="SPD-2024-0115-789",
            weather_conditions="Clear, dry roads",
            witnesses=["Jane Smith (555-0199)", "Store clerk at corner shop"]
        ),
        claim_amount=ClaimAmount(
            claimed_amount=Decimal("8500.00"),
            assessed_amount=Decimal("7200.00"),
            deductible=Decimal("500.00")
        ),
        adjuster_id=401,
        documents=[
            ClaimDocument(
                document_id="doc-001",
                document_type=DocumentType.POLICE_REPORT,
                filename="police_report_SPD-2024-0115-789.pdf",
                file_url="/documents/police_report_SPD-2024-0115-789.pdf",
                description="Official police report from incident"
            ),
            ClaimDocument(
                document_id="doc-002",
                document_type=DocumentType.PHOTOS,
                filename="accident_photos.zip",
                file_url="/documents/accident_photos.zip",
                description="Photos of vehicle damage and accident scene"
            )
        ],
        notes=[
            ClaimNote(
                note_id="note-001",
                author="Adjuster John Doe",
                content="Initial assessment completed. Vehicle damage consistent with reported incident.",
                is_internal=True
            )
        ],
        next_action_date=date(2024, 1, 25),
        estimated_settlement_date=date(2024, 2, 1)
    ),
    1002: Claim(
        claim_id=1002,
        claim_number="CLM-HOME-20240110-002",
        customer_id=101,
        policy_id=203,
        claim_type=ClaimType.HOME_WATER_DAMAGE,
        status=ClaimStatus.APPROVED,
        priority=ClaimPriority.MEDIUM,
        incident_details=IncidentDetails(
            incident_date=date(2024, 1, 10),
            incident_time="08:00",
            location="123 Main St, Springfield, IL",
            description="Burst water pipe in basement caused flooding",
            weather_conditions="Freezing temperatures overnight"
        ),
        claim_amount=ClaimAmount(
            claimed_amount=Decimal("12000.00"),
            assessed_amount=Decimal("10500.00"),
            approved_amount=Decimal("9500.00"),
            deductible=Decimal("1000.00")
        ),
        adjuster_id=402,
        documents=[
            ClaimDocument(
                document_id="doc-003",
                document_type=DocumentType.PHOTOS,
                filename="water_damage_photos.zip",
                file_url="/documents/water_damage_photos.zip",
                description="Photos of basement flooding and damage"
            ),
            ClaimDocument(
                document_id="doc-004",
                document_type=DocumentType.REPAIR_ESTIMATE,
                filename="plumber_estimate.pdf",
                file_url="/documents/plumber_estimate.pdf",
                description="Professional repair estimate from certified plumber"
            )
        ],
        notes=[
            ClaimNote(
                note_id="note-002",
                author="Adjuster Sarah Wilson",
                content="Damage assessment complete. Approved for $9,500 after deductible.",
                is_internal=False
            )
        ],
        payment_date=date(2024, 1, 20)
    ),
    1003: Claim(
        claim_id=1003,
        claim_number="CLM-AUTO-20240120-003",
        customer_id=102,
        policy_id=204,
        claim_type=ClaimType.AUTO_THEFT,
        status=ClaimStatus.INVESTIGATING,
        priority=ClaimPriority.HIGH,
        incident_details=IncidentDetails(
            incident_date=date(2024, 1, 20),
            incident_time="02:00",
            location="456 Oak Ave, Chicago, IL",
            description="Vehicle stolen from driveway overnight",
            police_report_number="CPD-2024-0120-456"
        ),
        claim_amount=ClaimAmount(
            claimed_amount=Decimal("25000.00"),
            deductible=Decimal("750.00")
        ),
        adjuster_id=403,
        documents=[
            ClaimDocument(
                document_id="doc-005",
                document_type=DocumentType.POLICE_REPORT,
                filename="theft_report_CPD-2024-0120-456.pdf",
                file_url="/documents/theft_report_CPD-2024-0120-456.pdf",
                description="Police report for vehicle theft"
            )
        ],
        notes=[
            ClaimNote(
                note_id="note-003",
                author="Adjuster Mike Johnson",
                content="Investigation ongoing. Waiting for police investigation results.",
                is_internal=True
            )
        ],
        next_action_date=date(2024, 1, 30)
    )
}

# Add some test data for UI testing (customer 12345)
mock_claims.update({
    2001: Claim(
        claim_id=2001,
        claim_number="CLM-AUTO-20240201-001",
        customer_id=12345,
        policy_id=301,
        claim_type=ClaimType.AUTO_ACCIDENT,
        status=ClaimStatus.APPROVED,
        priority=ClaimPriority.MEDIUM,
        incident_details=IncidentDetails(
            incident_date=date(2024, 2, 1),
            incident_time="16:45",
            location="Highway 101, San Francisco, CA",
            description="Minor fender-bender in traffic. No injuries reported.",
            police_report_number="SFPD-2024-0201-345",
            weather_conditions="Light rain",
            witnesses=["Other driver", "Traffic camera footage available"]
        ),
        claim_amount=ClaimAmount(
            claimed_amount=Decimal("3200.00"),
            assessed_amount=Decimal("2800.00"),
            approved_amount=Decimal("2300.00"),
            deductible=Decimal("500.00")
        ),
        adjuster_id=404,
        documents=[
            ClaimDocument(
                document_id="doc-006",
                document_type=DocumentType.PHOTOS,
                filename="accident_scene_photos.zip",
                file_url="/documents/accident_scene_photos.zip",
                description="Photos of minor vehicle damage"
            )
        ],
        notes=[
            ClaimNote(
                note_id="note-004",
                author="Adjuster Lisa Chen",
                content="Minor damage claim approved. Payment of $2,300 processed.",
                is_internal=False
            )
        ],
        payment_date=date(2024, 2, 10)
    ),
    2002: Claim(
        claim_id=2002,
        claim_number="CLM-HOME-20240205-002",
        customer_id=12345,
        policy_id=302,
        claim_type=ClaimType.HOME_BURGLARY,
        status=ClaimStatus.INVESTIGATING,
        priority=ClaimPriority.HIGH,
        incident_details=IncidentDetails(
            incident_date=date(2024, 2, 5),
            incident_time="Unknown",
            location="789 Pine St, San Francisco, CA",
            description="Home burglary discovered upon return from vacation. Electronics and jewelry stolen.",
            police_report_number="SFPD-2024-0205-678"
        ),
        claim_amount=ClaimAmount(
            claimed_amount=Decimal("8500.00"),
            deductible=Decimal("1000.00")
        ),
        adjuster_id=405,
        documents=[
            ClaimDocument(
                document_id="doc-007",
                document_type=DocumentType.POLICE_REPORT,
                filename="burglary_report_SFPD-2024-0205-678.pdf",
                file_url="/documents/burglary_report_SFPD-2024-0205-678.pdf",
                description="Police report for home burglary"
            )
        ],
        notes=[
            ClaimNote(
                note_id="note-005",
                author="Adjuster Mark Rodriguez",
                content="Investigation in progress. Awaiting police investigation results and inventory verification.",
                is_internal=True
            )
        ],
        next_action_date=date(2024, 2, 20)
    )
})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "claims-service", "timestamp": datetime.now().isoformat()}

@app.get("/claim/{claim_id}", response_model=Claim)
async def get_claim(claim_id: int):
    """Get claim by ID"""
    if claim_id not in mock_claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    return mock_claims[claim_id]

@app.get("/claim/{claim_id}/summary", response_model=ClaimSummary)
async def get_claim_summary(claim_id: int):
    """Get claim summary information"""
    if claim_id not in mock_claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim = mock_claims[claim_id]
    return ClaimSummary.from_claim(claim)

@app.get("/claims", response_model=List[ClaimSummary])
async def list_claims(
    customer_id: Optional[int] = None,
    policy_id: Optional[int] = None,
    status: Optional[ClaimStatus] = None,
    claim_type: Optional[ClaimType] = None,
    priority: Optional[ClaimPriority] = None,
    limit: int = 10,
    offset: int = 0
):
    """List claims with optional filtering"""
    claims = list(mock_claims.values())
    
    if customer_id:
        claims = [c for c in claims if c.customer_id == customer_id]
    
    if policy_id:
        claims = [c for c in claims if c.policy_id == policy_id]
    
    if status:
        claims = [c for c in claims if c.status == status]
    
    if claim_type:
        claims = [c for c in claims if c.claim_type == claim_type]
    
    if priority:
        claims = [c for c in claims if c.priority == priority]
    
    # Apply pagination
    claims = claims[offset:offset + limit]
    
    return [ClaimSummary.from_claim(c) for c in claims]

@app.get("/customer/{customer_id}/claims", response_model=List[ClaimSummary])
async def get_customer_claims(customer_id: int):
    """Get all claims for a specific customer"""
    customer_claims = [c for c in mock_claims.values() if c.customer_id == customer_id]
    
    if not customer_claims:
        return []
    
    return [ClaimSummary.from_claim(c) for c in customer_claims]

@app.get("/policy/{policy_id}/claims", response_model=List[ClaimSummary])
async def get_policy_claims(policy_id: int):
    """Get all claims for a specific policy"""
    policy_claims = [c for c in mock_claims.values() if c.policy_id == policy_id]
    
    if not policy_claims:
        return []
    
    return [ClaimSummary.from_claim(c) for c in policy_claims]

@app.post("/claim", response_model=Claim)
async def create_claim(claim_data: ClaimCreate):
    """Create a new claim"""
    # Generate new claim ID
    new_id = max(mock_claims.keys()) + 1 if mock_claims else 1001
    
    # Generate claim number
    claim_number = f"CLM-{claim_data.claim_type.upper().replace('_', '-')}-{datetime.now().strftime('%Y%m%d')}-{new_id:03d}"
    
    new_claim = Claim(
        claim_id=new_id,
        claim_number=claim_number,
        customer_id=claim_data.customer_id,
        policy_id=claim_data.policy_id,
        claim_type=claim_data.claim_type,
        status=ClaimStatus.SUBMITTED,
        priority=claim_data.priority,
        incident_details=claim_data.incident_details,
        claim_amount=ClaimAmount(
            claimed_amount=claim_data.claimed_amount,
            deductible=claim_data.deductible
        )
    )
    
    mock_claims[new_id] = new_claim
    return new_claim

@app.put("/claim/{claim_id}", response_model=Claim)
async def update_claim(claim_id: int, claim_data: ClaimUpdate):
    """Update existing claim"""
    if claim_id not in mock_claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim = mock_claims[claim_id]
    update_data = claim_data.dict(exclude_unset=True)
    
    # Handle special updates to claim_amount
    if "assessed_amount" in update_data:
        claim.claim_amount.assessed_amount = update_data.pop("assessed_amount")
    if "approved_amount" in update_data:
        claim.claim_amount.approved_amount = update_data.pop("approved_amount")
    
    for field, value in update_data.items():
        setattr(claim, field, value)
    
    claim.updated_at = datetime.now()
    return claim

@app.get("/claim/{claim_id}/status")
async def get_claim_status(claim_id: int):
    """Get claim status information"""
    if claim_id not in mock_claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim = mock_claims[claim_id]
    
    return {
        "claim_id": claim_id,
        "claim_number": claim.claim_number,
        "status": claim.status,
        "priority": claim.priority,
        "created_at": claim.created_at.isoformat(),
        "updated_at": claim.updated_at.isoformat(),
        "claimed_amount": float(claim.claim_amount.claimed_amount),
        "assessed_amount": float(claim.claim_amount.assessed_amount) if claim.claim_amount.assessed_amount else None,
        "approved_amount": float(claim.claim_amount.approved_amount) if claim.claim_amount.approved_amount else None,
        "next_action_date": claim.next_action_date.isoformat() if claim.next_action_date else None,
        "estimated_settlement_date": claim.estimated_settlement_date.isoformat() if claim.estimated_settlement_date else None
    }

@app.post("/claim/{claim_id}/status")
async def update_claim_status(claim_id: int, new_status: ClaimStatus, reason: str, updated_by: str = "System"):
    """Update claim status with tracking"""
    if claim_id not in mock_claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim = mock_claims[claim_id]
    previous_status = claim.status
    
    claim.status = new_status
    claim.updated_at = datetime.now()
    
    # Add note for status change
    status_note = ClaimNote(
        note_id=f"note-{uuid.uuid4().hex[:8]}",
        author=updated_by,
        content=f"Status changed from {previous_status} to {new_status}. Reason: {reason}",
        is_internal=True
    )
    claim.notes.append(status_note)
    
    # If approved or paid, set dates
    if new_status == ClaimStatus.PAID:
        claim.payment_date = date.today()
        claim.closed_at = datetime.now()
    elif new_status == ClaimStatus.CLOSED:
        claim.closed_at = datetime.now()
    
    return {
        "message": f"Claim {claim_id} status updated to {new_status}",
        "previous_status": previous_status,
        "new_status": new_status,
        "updated_at": claim.updated_at.isoformat()
    }

@app.get("/claim/{claim_id}/documents", response_model=List[ClaimDocument])
async def get_claim_documents(claim_id: int):
    """Get documents for a claim"""
    if claim_id not in mock_claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return mock_claims[claim_id].documents

@app.post("/claim/{claim_id}/documents", response_model=ClaimDocument)
async def add_claim_document(claim_id: int, document_type: DocumentType, filename: str, description: str = ""):
    """Add a document to a claim"""
    if claim_id not in mock_claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim = mock_claims[claim_id]
    
    new_document = ClaimDocument(
        document_id=f"doc-{uuid.uuid4().hex[:8]}",
        document_type=document_type,
        filename=filename,
        file_url=f"/documents/{filename}",
        description=description
    )
    
    claim.documents.append(new_document)
    claim.updated_at = datetime.now()
    
    return new_document

@app.get("/claim/{claim_id}/notes", response_model=List[ClaimNote])
async def get_claim_notes(claim_id: int, include_internal: bool = False):
    """Get notes for a claim"""
    if claim_id not in mock_claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    notes = mock_claims[claim_id].notes
    
    if not include_internal:
        notes = [note for note in notes if not note.is_internal]
    
    return notes

@app.post("/claim/{claim_id}/notes", response_model=ClaimNote)
async def add_claim_note(claim_id: int, content: str, author: str, is_internal: bool = False):
    """Add a note to a claim"""
    if claim_id not in mock_claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim = mock_claims[claim_id]
    
    new_note = ClaimNote(
        note_id=f"note-{uuid.uuid4().hex[:8]}",
        author=author,
        content=content,
        is_internal=is_internal
    )
    
    claim.notes.append(new_note)
    claim.updated_at = datetime.now()
    
    return new_note

@app.post("/claim/{claim_id}/approve")
async def approve_claim(claim_id: int, approved_amount: Decimal, approver: str):
    """Approve a claim for payment"""
    if claim_id not in mock_claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim = mock_claims[claim_id]
    
    claim.status = ClaimStatus.APPROVED
    claim.claim_amount.approved_amount = approved_amount
    claim.updated_at = datetime.now()
    
    # Add approval note
    approval_note = ClaimNote(
        note_id=f"note-{uuid.uuid4().hex[:8]}",
        author=approver,
        content=f"Claim approved for ${float(approved_amount)}",
        is_internal=False
    )
    claim.notes.append(approval_note)
    
    return {
        "message": f"Claim {claim_id} approved for ${float(approved_amount)}",
        "approved_amount": float(approved_amount),
        "approved_by": approver,
        "approved_at": claim.updated_at.isoformat()
    }

@app.post("/claim/{claim_id}/deny")
async def deny_claim(claim_id: int, reason: str, reviewer: str):
    """Deny a claim"""
    if claim_id not in mock_claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim = mock_claims[claim_id]
    
    claim.status = ClaimStatus.DENIED
    claim.updated_at = datetime.now()
    claim.closed_at = datetime.now()
    
    # Add denial note
    denial_note = ClaimNote(
        note_id=f"note-{uuid.uuid4().hex[:8]}",
        author=reviewer,
        content=f"Claim denied. Reason: {reason}",
        is_internal=False
    )
    claim.notes.append(denial_note)
    
    return {
        "message": f"Claim {claim_id} has been denied",
        "reason": reason,
        "denied_by": reviewer,
        "denied_at": claim.updated_at.isoformat()
    }

@app.post("/claim/{claim_id}/payment", response_model=ClaimPayment)
async def process_claim_payment(claim_id: int, payment_amount: Decimal, payment_method: str = "check"):
    """Process payment for an approved claim"""
    if claim_id not in mock_claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim = mock_claims[claim_id]
    
    if claim.status != ClaimStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Claim must be approved before payment")
    
    # Create payment record
    payment = ClaimPayment(
        payment_id=f"pay-{uuid.uuid4().hex[:8]}",
        claim_id=claim_id,
        payment_amount=payment_amount,
        payment_date=date.today(),
        payment_method=payment_method,
        check_number=f"CHK-{datetime.now().strftime('%Y%m%d')}-{claim_id}" if payment_method == "check" else None
    )
    
    # Update claim
    claim.status = ClaimStatus.PAID
    claim.claim_amount.paid_amount = payment_amount
    claim.payment_date = date.today()
    claim.updated_at = datetime.now()
    
    # Add payment note
    payment_note = ClaimNote(
        note_id=f"note-{uuid.uuid4().hex[:8]}",
        author="Payment System",
        content=f"Payment of ${float(payment_amount)} processed via {payment_method}",
        is_internal=False
    )
    claim.notes.append(payment_note)
    
    return payment

@app.get("/search/claims")
async def search_claims(
    q: str,
    limit: int = 10
):
    """Search claims by claim number, customer ID, or policy ID"""
    q = q.lower()
    results = []
    
    for claim in mock_claims.values():
        if (q in claim.claim_number.lower() or 
            str(claim.customer_id) == q or 
            str(claim.policy_id) == q):
            results.append(ClaimSummary.from_claim(claim))
            
        if len(results) >= limit:
            break
    
    return results

@app.get("/claims/statistics")
async def get_claims_statistics():
    """Get claims statistics"""
    total_claims = len(mock_claims)
    status_counts = {}
    priority_counts = {}
    type_counts = {}
    total_claimed = Decimal("0.00")
    total_paid = Decimal("0.00")
    
    for claim in mock_claims.values():
        # Status counts
        status_counts[claim.status] = status_counts.get(claim.status, 0) + 1
        
        # Priority counts
        priority_counts[claim.priority] = priority_counts.get(claim.priority, 0) + 1
        
        # Type counts
        type_counts[claim.claim_type] = type_counts.get(claim.claim_type, 0) + 1
        
        # Amount totals
        total_claimed += claim.claim_amount.claimed_amount
        if claim.claim_amount.paid_amount:
            total_paid += claim.claim_amount.paid_amount
    
    return {
        "total_claims": total_claims,
        "status_distribution": status_counts,
        "priority_distribution": priority_counts,
        "type_distribution": type_counts,
        "total_claimed_amount": float(total_claimed),
        "total_paid_amount": float(total_paid),
        "average_claim_amount": float(total_claimed / total_claims) if total_claims > 0 else 0
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("CLAIMS_SERVICE_PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)