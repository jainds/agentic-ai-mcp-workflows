"""
Authentication utilities for A2A agents and MCP servers.
Provides OAuth2, JWT token validation, and security middleware.
"""

import os
import jwt
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import structlog

logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()


@dataclass
class User:
    """User model for authentication"""
    username: str
    email: str
    roles: list[str]
    is_active: bool = True


@dataclass
class TokenData:
    """Token payload data"""
    username: Optional[str] = None
    roles: Optional[list[str]] = None
    exp: Optional[int] = None


class AuthManager:
    """Handles authentication and authorization for agents and services"""
    
    def __init__(self):
        self.users_db: Dict[str, Dict[str, Any]] = {
            # Demo users - in production, use proper user management
            "admin": {
                "username": "admin",
                "email": "admin@insurance.com",
                "hashed_password": self.get_password_hash("admin123"),
                "roles": ["admin", "agent_manager"],
                "is_active": True
            },
            "agent_user": {
                "username": "agent_user",
                "email": "agent@insurance.com", 
                "hashed_password": self.get_password_hash("agent123"),
                "roles": ["agent_user"],
                "is_active": True
            },
            "service_account": {
                "username": "service_account",
                "email": "service@insurance.com",
                "hashed_password": self.get_password_hash("service123"),
                "roles": ["service"],
                "is_active": True
            }
        }
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username"""
        user_dict = self.users_db.get(username)
        if user_dict:
            return User(
                username=user_dict["username"],
                email=user_dict["email"],
                roles=user_dict["roles"],
                is_active=user_dict["is_active"]
            )
        return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user_dict = self.users_db.get(username)
        if not user_dict:
            return None
        if not self.verify_password(password, user_dict["hashed_password"]):
            return None
        return self.get_user(username)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            roles: list = payload.get("roles", [])
            exp: int = payload.get("exp")
            
            if username is None:
                return None
            
            # Check if token is expired
            if exp and exp < time.time():
                return None
                
            return TokenData(username=username, roles=roles, exp=exp)
        except jwt.PyJWTError:
            return None
    
    def has_role(self, user: User, required_role: str) -> bool:
        """Check if user has required role"""
        return required_role in user.roles
    
    def has_any_role(self, user: User, required_roles: list[str]) -> bool:
        """Check if user has any of the required roles"""
        return any(role in user.roles for role in required_roles)


# Global auth manager instance
auth_manager = AuthManager()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = auth_manager.verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    user = auth_manager.get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_roles(required_roles: list[str]):
    """Decorator to require specific roles for endpoint access"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not auth_manager.has_any_role(current_user, required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of these roles: {required_roles}"
            )
        return current_user
    return role_checker


def require_role(required_role: str):
    """Decorator to require specific role for endpoint access"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not auth_manager.has_role(current_user, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires role: {required_role}"
            )
        return current_user
    return role_checker


# Service-to-service authentication
class ServiceAuth:
    """Service-to-service authentication for agent communication"""
    
    def __init__(self):
        self.service_tokens: Dict[str, str] = {
            # Pre-shared service tokens - in production use proper key management
            "claims-agent": self._generate_service_token("claims-agent"),
            "support-agent": self._generate_service_token("support-agent"),
            "policy-agent": self._generate_service_token("policy-agent"),
            "data-agent": self._generate_service_token("data-agent"),
            "notification-agent": self._generate_service_token("notification-agent"),
            "integration-agent": self._generate_service_token("integration-agent")
        }
    
    def _generate_service_token(self, service_name: str) -> str:
        """Generate a service token for inter-service communication"""
        token_data = {
            "sub": service_name,
            "type": "service",
            "roles": ["service"],
            "iat": time.time()
        }
        return auth_manager.create_access_token(token_data, expires_delta=timedelta(days=365))
    
    def get_service_token(self, service_name: str) -> Optional[str]:
        """Get service token for a specific service"""
        return self.service_tokens.get(service_name)
    
    def verify_service_token(self, token: str) -> bool:
        """Verify service token"""
        token_data = auth_manager.verify_token(token)
        if token_data is None:
            return False
        
        # Check if it's a service token
        return "service" in (token_data.roles or [])


# Global service auth instance
service_auth = ServiceAuth()


# Utility functions for token generation and validation
def generate_user_token(username: str, password: str) -> Optional[str]:
    """Generate user token for authentication"""
    user = auth_manager.authenticate_user(username, password)
    if not user:
        return None
    
    token_data = {
        "sub": user.username,
        "roles": user.roles,
        "email": user.email
    }
    return auth_manager.create_access_token(token_data)


def validate_token(token: str) -> bool:
    """Simple token validation for basic checks"""
    if not token or len(token) < 10:
        return False
    
    # Try to verify as JWT token
    token_data = auth_manager.verify_token(token)
    if token_data:
        return True
    
    # Try to verify as service token
    return service_auth.verify_service_token(token)


# Middleware for automatic authentication
class AuthMiddleware:
    """Authentication middleware for FastAPI applications"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # Add authentication logic here if needed
        # For now, pass through to the app
        await self.app(scope, receive, send) 