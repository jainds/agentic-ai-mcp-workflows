from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class ClaimType(str, Enum):
    AUTO_ACCIDENT = "auto_accident"
    AUTO_THEFT = "auto_theft"
    AUTO_VANDALISM = "auto_vandalism"
    HOME_FIRE = "home_fire"
    HOME_THEFT = "home_theft"
    HOME_WATER_DAMAGE = "home_water_damage"
    HOME_STORM = "home_storm"
    HEALTH_MEDICAL = "health_medical"
    HEALTH_EMERGENCY = "health_emergency"
    LIFE_DEATH = "life_death"
    DISABILITY = "disability"
    OTHER = "other"


class ClaimStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    INVESTIGATING = "investigating"
    PENDING_DOCUMENTATION = "pending_documentation"
    APPROVED = "approved"
    DENIED = "denied"
    PAID = "paid"
    CLOSED = "closed"
    REOPENED = "reopened"


class ClaimPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DocumentType(str, Enum):
    POLICE_REPORT = "police_report"
    MEDICAL_REPORT = "medical_report"
    PHOTOS = "photos"
    RECEIPTS = "receipts"
    REPAIR_ESTIMATE = "repair_estimate"
    WITNESS_STATEMENT = "witness_statement"
    DEATH_CERTIFICATE = "death_certificate"
    OTHER = "other"


class ClaimDocument(BaseModel):
    document_id: str
    document_type: DocumentType
    filename: str
    file_url: str
    uploaded_at: datetime = Field(default_factory=datetime.now)
    description: Optional[str] = None


class ClaimNote(BaseModel):
    note_id: str
    author: str
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    is_internal: bool = False


class IncidentDetails(BaseModel):
    incident_date: date
    incident_time: Optional[str] = None
    location: str
    description: str
    police_report_number: Optional[str] = None
    weather_conditions: Optional[str] = None
    witnesses: List[str] = Field(default_factory=list)


class ClaimAmount(BaseModel):
    claimed_amount: Decimal
    assessed_amount: Optional[Decimal] = None
    approved_amount: Optional[Decimal] = None
    paid_amount: Optional[Decimal] = None
    deductible: Optional[Decimal] = None


class Claim(BaseModel):
    claim_id: int
    claim_number: str
    customer_id: int
    policy_id: int
    claim_type: ClaimType
    status: ClaimStatus
    priority: ClaimPriority = ClaimPriority.MEDIUM
    incident_details: IncidentDetails
    claim_amount: ClaimAmount
    adjuster_id: Optional[int] = None
    documents: List[ClaimDocument] = Field(default_factory=list)
    notes: List[ClaimNote] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None
    payment_date: Optional[date] = None
    next_action_date: Optional[date] = None
    estimated_settlement_date: Optional[date] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class ClaimCreate(BaseModel):
    customer_id: int
    policy_id: int
    claim_type: ClaimType
    incident_details: IncidentDetails
    claimed_amount: Decimal
    deductible: Optional[Decimal] = None
    priority: ClaimPriority = ClaimPriority.MEDIUM


class ClaimUpdate(BaseModel):
    status: Optional[ClaimStatus] = None
    priority: Optional[ClaimPriority] = None
    adjuster_id: Optional[int] = None
    assessed_amount: Optional[Decimal] = None
    approved_amount: Optional[Decimal] = None
    next_action_date: Optional[date] = None
    estimated_settlement_date: Optional[date] = None


class ClaimSummary(BaseModel):
    claim_id: int
    claim_number: str
    customer_id: int
    policy_id: int
    claim_type: ClaimType
    status: ClaimStatus
    priority: ClaimPriority
    incident_date: date
    claimed_amount: Decimal
    approved_amount: Optional[Decimal] = None
    created_at: datetime
    days_since_created: int
    
    @classmethod
    def from_claim(cls, claim: Claim):
        today = datetime.now().date()
        created_date = claim.created_at.date()
        days_since = (today - created_date).days
        
        return cls(
            claim_id=claim.claim_id,
            claim_number=claim.claim_number,
            customer_id=claim.customer_id,
            policy_id=claim.policy_id,
            claim_type=claim.claim_type,
            status=claim.status,
            priority=claim.priority,
            incident_date=claim.incident_details.incident_date,
            claimed_amount=claim.claim_amount.claimed_amount,
            approved_amount=claim.claim_amount.approved_amount,
            created_at=claim.created_at,
            days_since_created=days_since
        )


class ClaimStatusUpdate(BaseModel):
    claim_id: int
    previous_status: ClaimStatus
    new_status: ClaimStatus
    reason: str
    updated_by: str
    updated_at: datetime = Field(default_factory=datetime.now)


class ClaimPayment(BaseModel):
    payment_id: str
    claim_id: int
    payment_amount: Decimal
    payment_date: date
    payment_method: str
    check_number: Optional[str] = None
    transaction_reference: Optional[str] = None


class ClaimSearchCriteria(BaseModel):
    customer_id: Optional[int] = None
    policy_id: Optional[int] = None
    claim_type: Optional[ClaimType] = None
    status: Optional[ClaimStatus] = None
    priority: Optional[ClaimPriority] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    adjuster_id: Optional[int] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None