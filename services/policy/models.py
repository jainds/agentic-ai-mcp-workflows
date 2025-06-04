from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class PolicyType(str, Enum):
    AUTO = "auto"
    HOME = "home"
    LIFE = "life"
    HEALTH = "health"
    BUSINESS = "business"


class PolicyStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    PENDING = "pending"


class CoverageType(str, Enum):
    LIABILITY = "liability"
    COMPREHENSIVE = "comprehensive"
    COLLISION = "collision"
    PERSONAL_INJURY = "personal_injury"
    PROPERTY_DAMAGE = "property_damage"
    MEDICAL = "medical"
    DISABILITY = "disability"
    LIFE_TERM = "life_term"
    LIFE_WHOLE = "life_whole"


class PaymentFrequency(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"


class Coverage(BaseModel):
    coverage_type: CoverageType
    coverage_limit: Decimal
    deductible: Optional[Decimal] = None
    premium: Decimal
    description: str


class PolicyDetails(BaseModel):
    policy_number: str
    policy_type: PolicyType
    status: PolicyStatus
    effective_date: date
    expiration_date: date
    premium_amount: Decimal
    payment_frequency: PaymentFrequency
    coverages: List[Coverage]
    terms_conditions: Dict[str, Any] = Field(default_factory=dict)


class Policy(BaseModel):
    policy_id: int
    customer_id: int
    policy_number: str
    policy_type: PolicyType
    status: PolicyStatus
    effective_date: date
    expiration_date: date
    issue_date: date
    premium_amount: Decimal
    payment_frequency: PaymentFrequency
    coverages: List[Coverage]
    agent_id: Optional[int] = None
    beneficiaries: List[str] = Field(default_factory=list)
    terms_conditions: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class PolicyCreate(BaseModel):
    customer_id: int
    policy_type: PolicyType
    effective_date: date
    expiration_date: date
    premium_amount: Decimal
    payment_frequency: PaymentFrequency
    coverages: List[Coverage]
    agent_id: Optional[int] = None
    beneficiaries: List[str] = Field(default_factory=list)
    terms_conditions: Dict[str, Any] = Field(default_factory=dict)


class PolicyUpdate(BaseModel):
    status: Optional[PolicyStatus] = None
    premium_amount: Optional[Decimal] = None
    payment_frequency: Optional[PaymentFrequency] = None
    coverages: Optional[List[Coverage]] = None
    beneficiaries: Optional[List[str]] = None
    terms_conditions: Optional[Dict[str, Any]] = None


class PolicySummary(BaseModel):
    policy_id: int
    policy_number: str
    policy_type: PolicyType
    status: PolicyStatus
    customer_id: int
    effective_date: date
    expiration_date: date
    premium_amount: Decimal
    coverage_count: int
    days_until_expiry: Optional[int] = None
    
    @classmethod
    def from_policy(cls, policy: Policy):
        today = date.today()
        days_until_expiry = None
        if policy.expiration_date > today:
            days_until_expiry = (policy.expiration_date - today).days
        
        return cls(
            policy_id=policy.policy_id,
            policy_number=policy.policy_number,
            policy_type=policy.policy_type,
            status=policy.status,
            customer_id=policy.customer_id,
            effective_date=policy.effective_date,
            expiration_date=policy.expiration_date,
            premium_amount=policy.premium_amount,
            coverage_count=len(policy.coverages),
            days_until_expiry=days_until_expiry
        )


class PolicyRenewal(BaseModel):
    policy_id: int
    new_effective_date: date
    new_expiration_date: date
    new_premium_amount: Optional[Decimal] = None
    coverage_updates: Optional[List[Coverage]] = None


class PolicyQuote(BaseModel):
    customer_id: int
    policy_type: PolicyType
    coverage_requests: List[Coverage]
    estimated_premium: Decimal
    quote_valid_until: date
    terms_conditions: Dict[str, Any] = Field(default_factory=dict)