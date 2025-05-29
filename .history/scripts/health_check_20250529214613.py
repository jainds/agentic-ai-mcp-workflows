#!/usr/bin/env python3
"""
Health Check Script for Insurance AI PoC
Provides health and readiness endpoints for all services
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Insurance AI Health Check")

@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint - returns 200 if service is alive"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "insurance-ai-component",
            "version": "1.0.0"
        }
    )

@app.get("/ready")
async def readiness_check() -> JSONResponse:
    """Readiness check endpoint - returns 200 if service is ready to accept traffic"""
    # In a real implementation, check dependencies like database connections, etc.
    checks = {
        "database": await _check_database(),
        "external_apis": await _check_external_apis(),
        "memory": await _check_memory(),
        "disk": await _check_disk()
    }
    
    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_ready else "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        }
    )

async def _check_database() -> bool:
    """Check database connectivity"""
    # Mock database check - in real implementation, ping the actual database
    await asyncio.sleep(0.1)  # Simulate database check
    return True

async def _check_external_apis() -> bool:
    """Check external API connectivity"""
    # Mock external API check
    await asyncio.sleep(0.1)
    return True

async def _check_memory() -> bool:
    """Check memory usage"""
    # Mock memory check
    import psutil
    try:
        memory = psutil.virtual_memory()
        return memory.percent < 90  # Return False if memory usage > 90%
    except:
        return True  # If psutil not available, assume OK

async def _check_disk() -> bool:
    """Check disk usage"""
    # Mock disk check
    import psutil
    try:
        disk = psutil.disk_usage('/')
        return (disk.used / disk.total) < 0.9  # Return False if disk usage > 90%
    except:
        return True  # If psutil not available, assume OK

if __name__ == "__main__":
    import uvicorn
    
    # Start health check server on port 9000
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    ) 