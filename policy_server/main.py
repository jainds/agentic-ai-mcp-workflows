#!/usr/bin/env python3
"""
Enhanced Policy FastMCP Server
Comprehensive policy information with payment and agent details
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

import structlog
from fastmcp import FastMCP

# Setup logging - simplified configuration
structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Policy Service")

# Load mock data
DATA_FILE = Path(__file__).parent.parent / "data" / "mock_data.json"

def load_data() -> Dict[str, Any]:
    """Load mock data from JSON file"""
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            logger.info(f"Loaded data with {len(data.get('policies', []))} policies")
            return data
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return {"policies": [], "users": []}

# Global data store
DATA = load_data()

def get_agent_info(agent_id: str) -> Dict[str, Any]:
    """Get agent information by ID"""
    for user in DATA.get("users", []):
        if user.get("id") == agent_id:
            return {
                "id": user.get("id"),
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                "email": user.get("email"),
                "phone": user.get("phone"),
                "role": user.get("role")
            }
    return {}

@mcp.tool()
def get_customer_policies(customer_id: str) -> List[Dict[str, Any]]:
    """
    Get all policies for a specific customer with comprehensive details
    
    Args:
        customer_id: The customer's ID to look up policies for
        
    Returns:
        List of policy dictionaries containing comprehensive policy details
    """
    logger.info(f"Looking up comprehensive policies for customer: {customer_id}")
    
    # Find policies for the customer
    customer_policies = [
        policy for policy in DATA.get("policies", [])
        if policy.get("customer_id") == customer_id
    ]
    
    if not customer_policies:
        logger.warning(f"No policies found for customer: {customer_id}")
        return []
    
    logger.info(f"Found {len(customer_policies)} policies for customer: {customer_id}")
    
    # Build comprehensive policy information
    result = []
    total_coverage = 0
    
    for policy in customer_policies:
        # Get agent information
        agent_info = get_agent_info(policy.get("assigned_agent_id", ""))
        
        # Calculate total coverage
        coverage_amount = policy.get("coverage_amount", 0)
        total_coverage += coverage_amount
        
        comprehensive_policy = {
            "id": policy.get("id"),
            "type": policy.get("type"),
            "status": policy.get("status"),
            "premium": policy.get("premium"),
            "coverage_amount": coverage_amount,
            "deductible": policy.get("deductible"),
            "start_date": policy.get("start_date"),
            "end_date": policy.get("end_date"),
            
            # Payment information
            "billing_cycle": policy.get("billing_cycle"),
            "next_payment_due": policy.get("next_payment_due"),
            "payment_method": policy.get("payment_method"),
            
            # Agent information
            "assigned_agent": agent_info,
            
            # Detailed policy information
            "details": policy.get("details", {}),
        }
        
        result.append(comprehensive_policy)
    
    # Add summary information as the first item
    summary = {
        "summary": True,
        "customer_id": customer_id,
        "total_policies": len(result),
        "policy_types": list(set(p.get("type") for p in customer_policies)),
        "next_payment_dates": list(set(p.get("next_payment_due") for p in customer_policies if p.get("next_payment_due"))),
        "assigned_agents": list(set(p.get("assigned_agent", {}).get("name") for p in result if p.get("assigned_agent", {}).get("name")))
    }
    
    # Insert summary at the beginning
    result.insert(0, summary)
    
    logger.info(f"Returning comprehensive data: {len(result)} items (1 summary + {len(result)-1} policies)")
    
    return result

if __name__ == "__main__":
    # Check command line arguments for port
    port = 8001
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    logger.info(f"Starting Enhanced Policy FastMCP Server on port {port}")
    logger.info(f"Available tool: get_customer_policies (with comprehensive details)")
    
    # Run the FastMCP server using the correct method
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port) 