from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, UTC
import uvicorn
import os
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import bcrypt
import logging
from enum import Enum
import time
import uuid
import sys
# Add parent directory to path for importing shared utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import shared utilities
try:
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('user_service_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('user_service_request_duration_seconds', 'Request duration')

app = FastAPI(
    title="User Service",
    description="Enterprise User Management Service for Insurance AI PoC",
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
class UserRole(str, Enum):
    ADMIN = "admin"
    AGENT = "agent"
    CUSTOMER = "customer"
    UNDERWRITER = "underwriter"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    role: UserRole
    phone: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def email_must_be_valid(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus
    phone: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Mock database
users_db = {}
sessions_db = {}

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(user_id: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(UTC) + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if user_id not in users_db:
            raise HTTPException(status_code=401, detail="Invalid token")
        return users_db[user_id]
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Initialize sample data
def initialize_sample_data():
    sample_users = [
        {
            "id": "user_001",
            "email": "admin@insurance.com",
            "password": "admin123",
            "first_name": "Admin",
            "last_name": "User",
            "role": UserRole.ADMIN,
            "status": UserStatus.ACTIVE,
            "phone": "+1-555-0100"
        },
        {
            "id": "user_002", 
            "email": "agent@insurance.com",
            "password": "agent123",
            "first_name": "Jane",
            "last_name": "Smith",
            "role": UserRole.AGENT,
            "status": UserStatus.ACTIVE,
            "phone": "+1-555-0101"
        },
        {
            "id": "user_003",
            "email": "customer@insurance.com", 
            "password": "customer123",
            "first_name": "John",
            "last_name": "Doe",
            "role": UserRole.CUSTOMER,
            "status": UserStatus.ACTIVE,
            "phone": "+1-555-0102"
        }
    ]
    
    for user_data in sample_users:
        user_id = user_data["id"]  # Don't pop, just get the ID
        password = user_data.pop("password")  # Only pop the password
        user_data["password_hash"] = hash_password(password)
        user_data["created_at"] = datetime.now(UTC)
        user_data["last_login"] = None
        users_db[user_id] = user_data

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
    return {"status": "healthy", "service": "user-service", "timestamp": datetime.now(UTC)}

@app.get("/metrics")
async def metrics():
    return generate_latest()

@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    # Check if user already exists
    for existing_user in users_db.values():
        if existing_user["email"] == user.email:
            raise HTTPException(status_code=400, detail="User already exists")
    
    user_id = f"user_{str(uuid.uuid4())[:8]}"
    user_data = {
        "id": user_id,
        "email": user.email,
        "password_hash": hash_password(user.password),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "status": UserStatus.ACTIVE,
        "phone": user.phone,
        "created_at": datetime.now(UTC),
        "last_login": None
    }
    
    users_db[user_id] = user_data
    
    return UserResponse(**{k: v for k, v in user_data.items() if k != "password_hash"})

@app.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    user = None
    for user_data in users_db.values():
        if user_data["email"] == login_data.email:
            user = user_data
            break
    
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user["status"] != UserStatus.ACTIVE:
        raise HTTPException(status_code=401, detail="Account is not active")
    
    # Update last login
    user["last_login"] = datetime.now(UTC)
    
    access_token = create_access_token(user["id"], user["role"])
    
    user_response = UserResponse(**{k: v for k, v in user.items() if k != "password_hash"})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@app.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(verify_token)):
    if current_user["role"] not in [UserRole.ADMIN, UserRole.AGENT]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return [UserResponse(**{k: v for k, v in user.items() if k != "password_hash"}) 
            for user in users_db.values()]

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: dict = Depends(verify_token)):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Users can only see their own data unless they're admin/agent
    if (current_user["id"] != user_id and 
        current_user["role"] not in [UserRole.ADMIN, UserRole.AGENT]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    user = users_db[user_id]
    return UserResponse(**{k: v for k, v in user.items() if k != "password_hash"})

@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate, current_user: dict = Depends(verify_token)):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Users can only update their own data unless they're admin
    if (current_user["id"] != user_id and current_user["role"] != UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    user = users_db[user_id]
    
    # Update fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        user[field] = value
    
    return UserResponse(**{k: v for k, v in user.items() if k != "password_hash"})

@app.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(verify_token)):
    if current_user["role"] != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    del users_db[user_id]
    return {"message": "User deleted successfully"}

@app.get("/users/{user_id}/profile", response_model=UserResponse)
async def get_user_profile(user_id: str, current_user: dict = Depends(verify_token)):
    return await get_user(user_id, current_user)

@app.get("/analytics/users")
async def get_user_analytics(current_user: dict = Depends(verify_token)):
    if current_user["role"] not in [UserRole.ADMIN, UserRole.AGENT]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    total_users = len(users_db)
    active_users = sum(1 for user in users_db.values() if user["status"] == UserStatus.ACTIVE)
    
    role_distribution = {}
    for user in users_db.values():
        role = user["role"]
        role_distribution[role] = role_distribution.get(role, 0) + 1
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "role_distribution": role_distribution,
        "timestamp": datetime.now(UTC)
    }

# Initialize sample data on startup
initialize_sample_data()

# FastMCP Integration
try:
    from mcp_server import UserMCPServer
    user_mcp = UserMCPServer(app, users_db)
    logger.info("FastMCP server integrated successfully")
except ImportError as e:
    logger.warning(f"FastMCP not available, continuing without MCP integration: {e}")
except Exception as e:
    logger.error(f"Failed to initialize FastMCP server: {e}")

if __name__ == "__main__":
    host = os.getenv("USER_SERVICE_HOST", "0.0.0.0")
    
    # Use the port utility to find an available port
    if PORT_UTILS_AVAILABLE:
        try:
            port = get_service_port("user", 8000, host=host)
        except Exception as e:
            print(f"Error finding available port: {e}")
            port = int(os.getenv("USER_SERVICE_PORT", 8000))
    else:
        port = int(os.getenv("USER_SERVICE_PORT", 8000))
    
    # Check if we should run as FastMCP or regular FastAPI
    use_fastmcp = os.getenv("USE_FASTMCP", "true").lower() == "true"
    
    if FASTMCP_AVAILABLE and use_fastmcp:
        # Use the properly configured UserMCPServer with real MCP tools
        try:
            from mcp_server import UserMCPServer
            user_mcp_server = UserMCPServer(app, users_db)
            
            # Use the MCP server directly
            mcp = user_mcp_server.mcp
            
            logger.info(f"Starting User Service with FastMCP and proper MCP tools on {host}:{port}")
            print(f"  FastMCP endpoints: http://{host}:{port}/mcp/")
            print(f"  MCP tools available: get_user, authenticate_user, list_users, create_user, update_user")
            mcp.run(transport="streamable-http", host=host, port=port)
        except Exception as e:
            logger.error(f"Failed to start with MCP tools, falling back to regular FastAPI: {str(e)}")
            logger.info(f"Starting User Service as FastAPI on {host}:{port}")
            print(f"  Health check: http://{host}:{port}/health")
            print(f"  API docs: http://{host}:{port}/docs")
            uvicorn.run(app, host=host, port=port)
    else:
        logger.info(f"Starting User Service as FastAPI on {host}:{port}")
        print(f"  Health check: http://{host}:{port}/health")
        print(f"  API docs: http://{host}:{port}/docs")
        uvicorn.run(app, host=host, port=port) 