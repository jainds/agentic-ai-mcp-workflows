#!/usr/bin/env python3
"""
Minimal Policy FastMCP Server
Single tool for reading customer policies
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
        return {"policies": []}

# Global data store
DATA = load_data()

@mcp.tool()
def get_customer_policies(customer_id: str) -> List[Dict[str, Any]]:
    """
    Get all policies for a specific customer
    
    Args:
        customer_id: The customer's ID to look up policies for
        
    Returns:
        List of policy dictionaries containing policy details
    """
    logger.info(f"Looking up policies for customer: {customer_id}")
    
    # Find policies for the customer
    customer_policies = [
        policy for policy in DATA.get("policies", [])
        if policy.get("customer_id") == customer_id
    ]
    
    if not customer_policies:
        logger.warning(f"No policies found for customer: {customer_id}")
        return []
    
    logger.info(f"Found {len(customer_policies)} policies for customer: {customer_id}")
    
    # Clean up the policies for return
    result = []
    for policy in customer_policies:
        clean_policy = {
            "id": policy.get("id"),
            "type": policy.get("type"),
            "status": policy.get("status"),
            "premium": policy.get("premium"),
            "coverage_amount": policy.get("coverage_amount"),
            "deductible": policy.get("deductible"),
            "start_date": policy.get("start_date"),
            "end_date": policy.get("end_date"),
            "details": policy.get("details", {})
        }
        result.append(clean_policy)
    
    return result

if __name__ == "__main__":
    # Check command line arguments for port
    port = 8001
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    logger.info(f"Starting Policy FastMCP Server on port {port}")
    logger.info(f"Available tool: get_customer_policies")
    
    # Run the FastMCP server using the correct method
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port) 