#!/usr/bin/env python3
"""
Python A2A Technical Agent Implementation
Provides specialized technical capabilities via python-a2a protocol
"""

import json
import uuid
import time
import random
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import logging

# python-a2a library imports
from python_a2a import (
    A2AServer, A2AClient, Message, TextContent, MessageRole, run_server
)

# FastAPI for HTTP endpoints
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our base
import sys
import os
sys.path.append('.')
from agents.shared.python_a2a_base import PythonA2AAgent

import structlog

logger = structlog.get_logger(__name__)

# Pydantic models for HTTP API
class TaskRequest(BaseModel):
    action: str
    data: Dict[str, Any] = {}
    context: Dict[str, Any] = {}

class TaskResponse(BaseModel):
    result: Dict[str, Any]
    status: str
    agent_type: str
    timestamp: str

class PythonA2ATechnicalAgent(PythonA2AAgent):
    """
    Technical agent for executing tasks using python-a2a
    
    Responsibilities:
    - Execute specific technical tasks routed from domain agent
    - Provide data access and analytics capabilities
    - Handle API integrations and external service calls
    - Manage notifications and communications
    - Perform tool-based operations
    """
    
    def __init__(self, port: int = 8002, agent_type: str = "data"):
        self.agent_type = agent_type
        
        # Define capabilities based on agent type
        capabilities = {
            "streaming": True,
            "pushNotifications": False,
            "fileUpload": False,
            "messageHistory": True,
            "taskExecution": True,
            "dataAccess": agent_type in ["data", "analytics"],
            "apiIntegration": True,
            "toolOperations": agent_type in ["fastmcp", "tools"],
            "notifications": agent_type == "notification",
            "python_a2a_compatible": True
        }
        
        # Define skills based on agent type
        skills = self.get_skills_by_type(agent_type)
        
        # Initialize A2A agent with python-a2a library
        super().__init__(
            name=f"{agent_type.title()}TechnicalAgent",
            description=f"Technical agent specialized in {agent_type} operations for insurance domain",
            port=port,
            capabilities=capabilities,
            skills=skills,
            version="2.0.0"
        )
        
        # Initialize agent-specific resources based on type
        self.initialize_agent_resources()
        
        # Setup HTTP endpoints for Kubernetes deployment
        self.setup_http_endpoints()
        
        logger.info("Python A2A Technical Agent initialized",
                   agent_type=agent_type, port=port)
    
    def get_skills_by_type(self, agent_type: str) -> List[Dict[str, Any]]:
        """Get skills based on agent type"""
        if agent_type == "data":
            return [
                {
                    "id": "data-retrieval",
                    "name": "Data Retrieval",
                    "description": "Retrieve data from databases and data sources",
                    "tags": ["database", "query", "retrieval"],
                    "examples": ["Fetch user policy details", "Get claim history"],
                    "inputModes": ["text", "query"],
                    "outputModes": ["json", "text"]
                },
                {
                    "id": "data-analysis",
                    "name": "Data Analysis",
                    "description": "Perform analytics and calculations on data",
                    "tags": ["analytics", "calculation", "insights"],
                    "examples": ["Calculate premium", "Analyze claim patterns"],
                    "inputModes": ["json", "data"],
                    "outputModes": ["json", "analysis"]
                },
                {
                    "id": "data-validation",
                    "name": "Data Validation",
                    "description": "Validate data integrity and business rules",
                    "tags": ["validation", "rules", "integrity"],
                    "examples": ["Validate policy eligibility", "Check claim requirements"],
                    "inputModes": ["json", "data"],
                    "outputModes": ["validation-result"]
                }
            ]
        elif agent_type == "notification":
            return [
                {
                    "id": "send-notification",
                    "name": "Send Notification",
                    "description": "Send notifications via various channels",
                    "tags": ["notification", "email", "sms", "push"],
                    "examples": ["Send claim confirmation", "Policy update alert"],
                    "inputModes": ["text", "notification-request"],
                    "outputModes": ["delivery-status"]
                },
                {
                    "id": "notification-tracking",
                    "name": "Notification Tracking",
                    "description": "Track notification delivery and engagement",
                    "tags": ["tracking", "analytics", "engagement"],
                    "examples": ["Track email opens", "Check SMS delivery"],
                    "inputModes": ["tracking-request"],
                    "outputModes": ["tracking-report"]
                }
            ]
        elif agent_type == "fastmcp":
            return [
                {
                    "id": "tool-execution",
                    "name": "Tool Execution",
                    "description": "Execute various tools and external services",
                    "tags": ["tools", "mcp", "external-apis"],
                    "examples": ["Run fraud detection", "Calculate risk score"],
                    "inputModes": ["tool-request", "parameters"],
                    "outputModes": ["tool-result"]
                },
                {
                    "id": "service-integration",
                    "name": "Service Integration",
                    "description": "Integrate with external services and APIs",
                    "tags": ["integration", "api", "services"],
                    "examples": ["Credit check API", "Weather service"],
                    "inputModes": ["api-request"],
                    "outputModes": ["api-response"]
                }
            ]
        else:
            return [
                {
                    "id": "general-technical",
                    "name": "General Technical Operations",
                    "description": "Handle general technical tasks",
                    "tags": ["general", "technical"],
                    "examples": ["Process technical requests"],
                    "inputModes": ["text"],
                    "outputModes": ["text"]
                }
            ]
    
    def initialize_agent_resources(self):
        """Initialize resources based on agent type"""
        if self.agent_type == "data":
            # Initialize database connections and data caches
            self.initialize_data_resources()
        elif self.agent_type == "notification":
            # Initialize notification services
            self.initialize_notification_resources()
        elif self.agent_type == "fastmcp":
            # Initialize MCP tools and external services
            self.initialize_mcp_resources()
    
    def initialize_data_resources(self):
        """Initialize data-related resources"""
        # Mock database connections (in real implementation, use actual DB connections)
        self.db_connections = {
            "user_db": "postgresql://localhost:5432/users",
            "policy_db": "postgresql://localhost:5432/policies",
            "claims_db": "postgresql://localhost:5432/claims"
        }
        
        # Data caches
        self.customer_cache: Dict[str, Dict[str, Any]] = {}
        self.policy_cache: Dict[str, Dict[str, Any]] = {}
        self.claims_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("Data resources initialized")
    
    def initialize_notification_resources(self):
        """Initialize notification-related resources"""
        self.notification_channels = {
            "email": {"service": "sendgrid", "api_key": os.getenv("SENDGRID_API_KEY")},
            "sms": {"service": "twilio", "api_key": os.getenv("TWILIO_API_KEY")},
            "push": {"service": "firebase", "api_key": os.getenv("FIREBASE_API_KEY")}
        }
        
        self.notification_templates = {
            "claim_confirmation": "Your claim {claim_id} has been received and is being processed.",
            "policy_update": "Your policy {policy_id} has been updated. Please review the changes.",
            "payment_reminder": "Payment for policy {policy_id} is due on {due_date}."
        }
        
        logger.info("Notification resources initialized")
    
    def initialize_mcp_resources(self):
        """Initialize MCP and tool-related resources"""
        self.available_tools = {
            "fraud_detection": {
                "name": "Fraud Detection Tool",
                "description": "Analyze claims for potential fraud",
                "parameters": ["claim_data", "threshold"]
            },
            "risk_assessment": {
                "name": "Risk Assessment Tool",
                "description": "Calculate risk scores for policies",
                "parameters": ["policy_data", "customer_data"]
            },
            "credit_check": {
                "name": "Credit Check Tool",
                "description": "Perform credit checks on customers",
                "parameters": ["customer_id", "ssn"]
            }
        }
        
        logger.info("MCP resources initialized")
    
    def handle_message(self, message: Message) -> Message:
        """
        Handle incoming task messages from domain agent
        """
        try:
            user_text = message.content.text
            conversation_id = getattr(message, 'conversation_id', str(uuid.uuid4()))
            
            logger.info("Processing technical task", 
                       text=user_text[:100], 
                       conversation_id=conversation_id,
                       agent_type=self.agent_type)
            
            # Parse task data
            try:
                task_data = json.loads(user_text)
            except json.JSONDecodeError:
                # If not JSON, treat as plain text task
                task_data = {"action": "general_inquiry", "query": user_text}
            
            # Execute the task based on action
            result = self.execute_task(task_data)
            
            return Message(
                content=TextContent(text=json.dumps(result)),
                role=MessageRole.AGENT,
                parent_message_id=getattr(message, 'message_id', None),
                conversation_id=conversation_id
            )
            
        except Exception as e:
            logger.error("Error processing technical task", error=str(e))
            error_result = {
                "status": "error",
                "error": str(e),
                "agent_type": self.agent_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return Message(
                content=TextContent(text=json.dumps(error_result)),
                role=MessageRole.AGENT,
                parent_message_id=getattr(message, 'message_id', None),
                conversation_id=getattr(message, 'conversation_id', None)
            )
    
    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task based on task data"""
        action = task_data.get("action", "unknown")
        
        logger.info("Executing task", action=action, agent_type=self.agent_type)
        
        # Route to appropriate handler based on agent type and action
        if self.agent_type == "data":
            return self.execute_data_task(action, task_data)
        elif self.agent_type == "notification":
            return self.execute_notification_task(action, task_data)
        elif self.agent_type == "fastmcp":
            return self.execute_mcp_task(action, task_data)
        else:
            return self.execute_general_task(action, task_data)
    
    def execute_data_task(self, action: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data-related tasks"""
        result = {
            "task_id": str(uuid.uuid4()),
            "action": action,
            "agent_type": "data",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            if action == "validate_policy":
                # Mock policy validation
                policy_id = task_data.get("plan_context", {}).get("entities", {}).get("policy_id", "POL123456")
                result["data"] = {
                    "policy_id": policy_id,
                    "valid": True,
                    "status": "active",
                    "coverage_amount": 250000,
                    "premium": 1200.00
                }
                
            elif action == "fetch_policy_details":
                # Mock policy details retrieval
                policy_id = task_data.get("plan_context", {}).get("entities", {}).get("policy_id", "POL123456")
                result["data"] = {
                    "policy_id": policy_id,
                    "holder_name": "John Doe",
                    "policy_type": "Auto Insurance",
                    "coverage_amount": 250000,
                    "premium": 1200.00,
                    "deductible": 500,
                    "effective_date": "2024-01-01",
                    "expiry_date": "2024-12-31"
                }
                
            elif action == "create_claim_record":
                # Mock claim creation
                claim_id = f"CLM{random.randint(100000, 999999)}"
                result["data"] = {
                    "claim_id": claim_id,
                    "status": "submitted",
                    "submission_date": datetime.utcnow().isoformat(),
                    "estimated_processing_time": "5-7 business days"
                }
                
            elif action == "fetch_billing_history":
                # Mock billing history
                result["data"] = {
                    "billing_history": [
                        {"date": "2024-01-01", "amount": 100.00, "status": "paid"},
                        {"date": "2024-02-01", "amount": 100.00, "status": "paid"},
                        {"date": "2024-03-01", "amount": 100.00, "status": "pending"}
                    ],
                    "total_paid": 200.00,
                    "outstanding_balance": 100.00
                }
                
            elif action == "general_information_lookup":
                # Mock general information lookup
                query = task_data.get("plan_context", {}).get("user_request", "")
                result["data"] = {
                    "query": query,
                    "information": "Based on your inquiry, here are the relevant details from our insurance database.",
                    "related_policies": ["POL123456", "POL789012"],
                    "suggested_actions": ["Review policy details", "Contact customer service"]
                }
                
            else:
                result["data"] = {"message": f"Data action '{action}' completed successfully"}
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def execute_notification_task(self, action: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notification-related tasks"""
        result = {
            "task_id": str(uuid.uuid4()),
            "action": action,
            "agent_type": "notification",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            if action == "send_claim_confirmation":
                # Mock sending claim confirmation
                claim_id = task_data.get("previous_results", [{}])[-1].get("result", {}).get("data", {}).get("claim_id", "CLM123456")
                result["data"] = {
                    "notification_id": str(uuid.uuid4()),
                    "claim_id": claim_id,
                    "recipient": "customer@example.com",
                    "channel": "email",
                    "status": "sent",
                    "sent_at": datetime.utcnow().isoformat()
                }
                
            elif action == "send_policy_update":
                # Mock policy update notification
                result["data"] = {
                    "notification_id": str(uuid.uuid4()),
                    "policy_id": "POL123456",
                    "recipient": "customer@example.com",
                    "channel": "email",
                    "status": "sent",
                    "sent_at": datetime.utcnow().isoformat()
                }
                
            else:
                result["data"] = {"message": f"Notification action '{action}' completed successfully"}
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def execute_mcp_task(self, action: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP/tool-related tasks"""
        result = {
            "task_id": str(uuid.uuid4()),
            "action": action,
            "agent_type": "fastmcp",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            if action == "fraud_detection_check":
                # Mock fraud detection
                claim_data = task_data.get("previous_results", [{}])[-1].get("result", {}).get("data", {})
                fraud_score = random.uniform(0.0, 1.0)
                result["data"] = {
                    "fraud_score": fraud_score,
                    "risk_level": "low" if fraud_score < 0.3 else ("medium" if fraud_score < 0.7 else "high"),
                    "confidence": random.uniform(0.8, 0.95),
                    "factors_analyzed": ["claim_amount", "customer_history", "timing_patterns"],
                    "recommendation": "proceed" if fraud_score < 0.7 else "investigate"
                }
                
            elif action == "risk_assessment":
                # Mock risk assessment
                risk_score = random.uniform(0.0, 1.0)
                result["data"] = {
                    "risk_score": risk_score,
                    "risk_category": "low" if risk_score < 0.4 else ("medium" if risk_score < 0.7 else "high"),
                    "factors": ["driving_history", "location", "vehicle_type"],
                    "premium_adjustment": random.uniform(-0.1, 0.2)
                }
                
            else:
                result["data"] = {"message": f"MCP action '{action}' completed successfully"}
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def execute_general_task(self, action: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute general tasks"""
        result = {
            "task_id": str(uuid.uuid4()),
            "action": action,
            "agent_type": self.agent_type,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"message": f"General action '{action}' completed successfully"}
        }
        
        return result

    def setup_http_endpoints(self):
        """Setup HTTP endpoints for Kubernetes health checks and API access"""
        self.app = FastAPI(
            title=f"Python A2A Technical Agent - {self.agent_type}", 
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for Kubernetes"""
            return {
                "status": "healthy",
                "agent_type": self.agent_type,
                "version": "1.0.0",
                "capabilities": self.capabilities,
                "skills": len(self.skills),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.get("/ready")
        async def readiness_check():
            """Readiness check endpoint for Kubernetes"""
            return {
                "status": "ready",
                "agent_type": self.agent_type,
                "resources_initialized": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.post("/task", response_model=TaskResponse)
        async def task_endpoint(request: TaskRequest):
            """Task execution endpoint for direct HTTP communication"""
            try:
                # Execute the task through the technical agent
                result = self.execute_task({
                    "action": request.action,
                    **request.data,
                    **request.context
                })
                
                return TaskResponse(
                    result=result,
                    status="completed",
                    agent_type=self.agent_type,
                    timestamp=datetime.utcnow().isoformat()
                )
                
            except Exception as e:
                logger.error("Task endpoint error", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/agent-card")
        async def get_agent_card_endpoint():
            """Get agent card endpoint"""
            return self.get_agent_card()

    def run_http_server(self, host: str = "0.0.0.0", port: int = None):
        """Run the HTTP server for Kubernetes deployment"""
        if port is None:
            port = self.port
        logger.info("Starting Technical Agent HTTP server", 
                   agent_type=self.agent_type, host=host, port=port)
        uvicorn.run(self.app, host=host, port=port)


def main():
    """Run the Python A2A Technical Agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Python A2A Technical Agent")
    parser.add_argument("--port", type=int, default=8002, help="Port to run the agent on")
    parser.add_argument("--agent-type", default="data", choices=["data", "notification", "fastmcp"],
                       help="Type of technical agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the agent to")
    parser.add_argument("--mode", choices=["http", "a2a"], default="http",
                       help="Server mode: http for Kubernetes, a2a for native A2A protocol")
    
    args = parser.parse_args()
    
    # Create the technical agent
    agent = PythonA2ATechnicalAgent(port=args.port, agent_type=args.agent_type)
    
    logger.info("Starting Python A2A Technical Agent", 
               agent_type=args.agent_type, host=args.host, port=args.port, mode=args.mode)
    
    if args.mode == "http":
        # Run HTTP server for Kubernetes deployment
        agent.run_http_server(host=args.host, port=args.port)
    else:
        # Run native A2A server
        agent.host = args.host
        agent.run()


if __name__ == "__main__":
    main() 