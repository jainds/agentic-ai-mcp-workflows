from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uvicorn
import os
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import logging
from enum import Enum
import time
import uuid
import random
import sys
from collections import defaultdict

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('analytics_service_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('analytics_service_request_duration_seconds', 'Request duration')

app = FastAPI(
    title="Analytics Service",
    description="Enterprise Analytics Service for Insurance AI PoC",
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
class DashboardMetrics(BaseModel):
    total_claims: int
    total_policies: int
    total_users: int
    revenue: float
    fraud_rate: float
    customer_satisfaction: float
    processing_time_avg: float
    timestamp: datetime

# Mock data storage
processed_metrics = {
    "total_claims_ytd": 2847,
    "total_policies_active": 15234,
    "total_users": 8765,
    "fraud_cases_detected": 142,
    "average_processing_time": 4.2,
    "customer_satisfaction": 4.3,
    "revenue_ytd": 12450000.50
}

# Helper functions
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

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
    return {"status": "healthy", "service": "analytics-service", "timestamp": datetime.utcnow()}

@app.get("/metrics")
async def metrics():
    return generate_latest()

@app.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(current_user: dict = Depends(verify_token)):
    """Get high-level dashboard metrics"""
    
    # Calculate fraud rate
    total_claims = processed_metrics.get("total_claims_ytd", 0)
    fraud_cases = processed_metrics.get("fraud_cases_detected", 0)
    fraud_rate = (fraud_cases / total_claims * 100) if total_claims > 0 else 0
    
    return DashboardMetrics(
        total_claims=total_claims,
        total_policies=processed_metrics.get("total_policies_active", 0),
        total_users=processed_metrics.get("total_users", 0),
        revenue=processed_metrics.get("revenue_ytd", 0.0),
        fraud_rate=fraud_rate,
        customer_satisfaction=processed_metrics.get("customer_satisfaction", 0.0),
        processing_time_avg=processed_metrics.get("average_processing_time", 0.0),
        timestamp=datetime.utcnow()
    )

@app.get("/analytics/reports")
async def generate_report(report_type: str = "monthly", current_user: dict = Depends(verify_token)):
    """Generate analytics reports"""
    
    if report_type == "monthly":
        return {
            "report_type": "Monthly Analytics Report",
            "period": datetime.utcnow().strftime("%B %Y"),
            "metrics": {
                "claims_processed": random.randint(800, 1200),
                "policies_sold": random.randint(300, 500),
                "revenue": random.uniform(800000, 1200000),
                "customer_satisfaction": random.uniform(4.0, 4.8),
                "fraud_detected": random.randint(10, 25)
            },
            "highlights": [
                "Claims processing time improved by 12%",
                "Customer satisfaction increased to 4.4/5",
                "Fraud detection accuracy improved by 8%"
            ],
            "generated_at": datetime.utcnow()
        }
    
    elif report_type == "fraud":
        return {
            "report_type": "Fraud Analysis Report",
            "period": "Last 90 days",
            "fraud_stats": {
                "total_cases": processed_metrics.get("fraud_cases_detected", 142),
                "amount_saved": random.uniform(500000, 800000),
                "detection_rate": random.uniform(0.85, 0.95),
                "false_positive_rate": random.uniform(0.02, 0.05)
            },
            "top_indicators": [
                "Multiple claims in 30 days",
                "Claims within 48h of policy activation",
                "Inconsistent damage descriptions"
            ],
            "generated_at": datetime.utcnow()
        }
    
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")

# FastMCP Integration
try:
    from mcp_server import AnalyticsMCPServer
    analytics_mcp = AnalyticsMCPServer(app)
    logger.info("FastMCP server integrated successfully")
except ImportError as e:
    logger.warning(f"FastMCP not available, continuing without MCP integration: {e}")
except Exception as e:
    logger.error(f"Failed to initialize FastMCP server: {e}")

if __name__ == "__main__":
    host = os.getenv("ANALYTICS_SERVICE_HOST", "0.0.0.0")
    
    # Use the port utility to find an available port
    if PORT_UTILS_AVAILABLE:
        try:
            port = get_service_port("analytics", 8003, host=host)
        except Exception as e:
            print(f"Error finding available port: {e}")
            port = int(os.getenv("ANALYTICS_SERVICE_PORT", 8003))
    else:
        port = int(os.getenv("ANALYTICS_SERVICE_PORT", 8003))
    
    # Check if we should run as FastMCP or regular FastAPI
    use_fastmcp = os.getenv("USE_FASTMCP", "true").lower() == "true"
    
    if FASTMCP_AVAILABLE and use_fastmcp:
        # Use the properly configured AnalyticsMCPServer with real MCP tools
        try:
            from mcp_server import AnalyticsMCPServer
            analytics_mcp_server = AnalyticsMCPServer(app)
            
            # Use the MCP server directly
            mcp = analytics_mcp_server.mcp
            
            logger.info(f"Starting Analytics Service with FastMCP and proper MCP tools on {host}:{port}")
            print(f"  FastMCP endpoints: http://{host}:{port}/mcp/")
            print(f"  MCP tools available: generate_report, get_customer_metrics, calculate_risk_score")
            mcp.run(transport="streamable-http", host=host, port=port)
        except Exception as e:
            logger.error(f"Failed to start with MCP tools, falling back to regular FastAPI: {e}")
            logger.info(f"Starting Analytics Service as FastAPI on {host}:{port}")
            print(f"  Health check: http://{host}:{port}/health")
            print(f"  API docs: http://{host}:{port}/docs")
            uvicorn.run(app, host=host, port=port)
    else:
        logger.info(f"Starting Analytics Service as FastAPI on {host}:{port}")
        print(f"  Health check: http://{host}:{port}/health")
        print(f"  API docs: http://{host}:{port}/docs")
        uvicorn.run(app, host=host, port=port) 