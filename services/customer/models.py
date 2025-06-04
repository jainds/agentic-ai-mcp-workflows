from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CustomerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"


class ContactInfo(BaseModel):
    email: str
    phone: str
    mobile: Optional[str] = None


class Customer(BaseModel):
    customer_id: int
    first_name: str
    last_name: str
    date_of_birth: datetime
    address: Address
    contact: ContactInfo
    status: CustomerStatus = CustomerStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    policy_ids: List[int] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CustomerCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: datetime
    address: Address
    contact: ContactInfo


class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[Address] = None
    contact: Optional[ContactInfo] = None
    status: Optional[CustomerStatus] = None


class CustomerResponse(BaseModel):
    customer_id: int
    first_name: str
    last_name: str
    full_name: str
    email: str
    phone: str
    status: CustomerStatus
    policy_count: int
    
    @classmethod
    def from_customer(cls, customer: Customer):
        # Handle contact as either ContactInfo object or dict
        if hasattr(customer.contact, 'email'):
            email = customer.contact.email
            phone = customer.contact.phone
        elif isinstance(customer.contact, dict):
            email = customer.contact.get('email', '')
            phone = customer.contact.get('phone', '')
        else:
            email = ''
            phone = ''
            
        return cls(
            customer_id=customer.customer_id,
            first_name=customer.first_name,
            last_name=customer.last_name,
            full_name=f"{customer.first_name} {customer.last_name}",
            email=email,
            phone=phone,
            status=customer.status,
            policy_count=len(customer.policy_ids)
        )