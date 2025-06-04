#!/usr/bin/env python3
"""
Enhanced Policy FastMCP Server
Simple, business-focused API design for insurance policy management
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

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

def get_customer_policies_internal(customer_id: str) -> List[Dict[str, Any]]:
    """Internal helper to get customer policies"""
    return [
        policy for policy in DATA.get("policies", [])
        if policy.get("customer_id") == customer_id
    ]

# ============================================
# SIMPLE BUSINESS-FOCUSED APIS
# ============================================

@mcp.tool()
def get_policies(customer_id: str) -> List[Dict[str, Any]]:
    """
    Get basic list of customer policies with essential billing information
    
    Args:
        customer_id: The customer's ID
        
    Returns:
        List of policies with premium and billing cycle information
    """
    logger.info(f"Getting policies for customer: {customer_id}")
    
    customer_policies = get_customer_policies_internal(customer_id)
    
    if not customer_policies:
        return []
    
    # Return policy list with billing cycle information always included
    policies = []
    for policy in customer_policies:
        policies.append({
            "id": policy.get("id"),
            "type": policy.get("type"),
            "status": policy.get("status"),
            "premium": policy.get("premium"),
            "billing_cycle": policy.get("billing_cycle"),  # Always include billing cycle
            "coverage_amount": policy.get("coverage_amount")
        })
    
    logger.info(f"Returning {len(policies)} policies with billing cycle information")
    return policies

@mcp.tool()
def get_agent(customer_id: str) -> Dict[str, Any]:
    """
    Get agent information for customer
    
    Args:
        customer_id: The customer's ID
        
    Returns:
        Agent contact information
    """
    logger.info(f"Getting agent for customer: {customer_id}")
    
    customer_policies = get_customer_policies_internal(customer_id)
    
    if not customer_policies:
        return {"error": f"No policies found for customer {customer_id}"}
    
    # Get the first agent (assuming customer has one primary agent)
    first_policy = customer_policies[0]
    agent_info = get_agent_info(first_policy.get("assigned_agent_id", ""))
    
    if not agent_info:
        return {"error": "No agent assigned"}
    
    # Add policy types this agent handles
    handled_policies = list(set(p.get("type") for p in customer_policies if p.get("assigned_agent_id") == agent_info["id"]))
    agent_info["handles_policy_types"] = handled_policies
    
    logger.info(f"Found agent: {agent_info.get('name')}")
    return agent_info

@mcp.tool()
def get_policy_types(customer_id: str) -> List[str]:
    """
    Get policy types for customer
    
    Args:
        customer_id: The customer's ID
        
    Returns:
        List of policy types (auto, life, home, etc.)
    """
    logger.info(f"Getting policy types for customer: {customer_id}")
    
    customer_policies = get_customer_policies_internal(customer_id)
    
    policy_types = list(set(p.get("type") for p in customer_policies if p.get("type")))
    
    logger.info(f"Found policy types: {policy_types}")
    return policy_types

@mcp.tool()
def get_policy_list(customer_id: str) -> List[Dict[str, Any]]:
    """
    Get detailed policy list with more information than get_policies
    
    Args:
        customer_id: The customer's ID
        
    Returns:
        Detailed list of policies with dates and coverage info
    """
    logger.info(f"Getting detailed policy list for customer: {customer_id}")
    
    customer_policies = get_customer_policies_internal(customer_id)
    
    if not customer_policies:
        return []
    
    # Return detailed policy list
    policy_list = []
    for policy in customer_policies:
        policy_list.append({
            "id": policy.get("id"),
            "type": policy.get("type"),
            "status": policy.get("status"),
            "premium": policy.get("premium"),
            "coverage_amount": policy.get("coverage_amount"),
            "deductible": policy.get("deductible"),
            "start_date": policy.get("start_date"),
            "end_date": policy.get("end_date"),
            "billing_cycle": policy.get("billing_cycle")
        })
    
    logger.info(f"Returning detailed list of {len(policy_list)} policies")
    return policy_list

@mcp.tool()
def get_payment_information(customer_id: str) -> List[Dict[str, Any]]:
    """
    Get payment information for customer policies
    
    Args:
        customer_id: The customer's ID
        
    Returns:
        Payment details including due dates and amounts
    """
    logger.info(f"Getting payment information for customer: {customer_id}")
    
    customer_policies = get_customer_policies_internal(customer_id)
    
    payment_info = []
    for policy in customer_policies:
        payment_info.append({
            "policy_id": policy.get("id"),
            "policy_type": policy.get("type"),
            "premium": policy.get("premium"),
            "billing_cycle": policy.get("billing_cycle"),
            "next_payment_due": policy.get("next_payment_due"),
            "payment_method": policy.get("payment_method"),
            "status": policy.get("status")
        })
    
    logger.info(f"Returning payment info for {len(payment_info)} policies")
    return payment_info

@mcp.tool()
def get_coverage_information(customer_id: str) -> List[Dict[str, Any]]:
    """
    Get coverage information for customer policies
    
    Args:
        customer_id: The customer's ID
        
    Returns:
        Coverage details and limits
    """
    logger.info(f"Getting coverage information for customer: {customer_id}")
    
    customer_policies = get_customer_policies_internal(customer_id)
    
    coverage_info = []
    for policy in customer_policies:
        coverage_details = policy.get("details", {})
        coverage_info.append({
            "policy_id": policy.get("id"),
            "policy_type": policy.get("type"),
            "coverage_amount": policy.get("coverage_amount"),
            "deductible": policy.get("deductible"),
            "coverage_types": coverage_details.get("coverage_types", []),
            "policy_limits": coverage_details.get("policy_limits", {}),
            "status": policy.get("status")
        })
    
    logger.info(f"Returning coverage info for {len(coverage_info)} policies")
    return coverage_info

@mcp.tool()
def get_policy_details(policy_id: str) -> Dict[str, Any]:
    """
    Get complete details for a specific policy
    
    Args:
        policy_id: The specific policy ID
        
    Returns:
        Complete policy information
    """
    logger.info(f"Getting policy details for: {policy_id}")
    
    # Find the specific policy
    policy = None
    for p in DATA.get("policies", []):
        if p.get("id") == policy_id:
            policy = p
            break
    
    if not policy:
        logger.warning(f"Policy not found: {policy_id}")
        return {"error": f"Policy {policy_id} not found"}
    
    # Get agent information
    agent_info = get_agent_info(policy.get("assigned_agent_id", ""))
    
    # Build comprehensive policy details
    policy_details = {
        "id": policy.get("id"),
        "customer_id": policy.get("customer_id"),
        "type": policy.get("type"),
        "status": policy.get("status"),
        "premium": policy.get("premium"),
        "coverage_amount": policy.get("coverage_amount"),
        "deductible": policy.get("deductible"),
        "start_date": policy.get("start_date"),
        "end_date": policy.get("end_date"),
        "billing_cycle": policy.get("billing_cycle"),
        "next_payment_due": policy.get("next_payment_due"),
        "payment_method": policy.get("payment_method"),
        "assigned_agent": agent_info,
        "details": policy.get("details", {})
    }
    
    logger.info(f"Returning policy details for {policy_id}")
    return policy_details

@mcp.tool()
def get_deductibles(customer_id: str) -> List[Dict[str, Any]]:
    """
    Get deductible information for customer policies
    
    Args:
        customer_id: The customer's ID
        
    Returns:
        Deductible amounts for each policy
    """
    logger.info(f"Getting deductibles for customer: {customer_id}")
    
    customer_policies = get_customer_policies_internal(customer_id)
    
    deductibles = []
    for policy in customer_policies:
        deductibles.append({
            "policy_id": policy.get("id"),
            "policy_type": policy.get("type"),
            "deductible": policy.get("deductible"),
            "coverage_amount": policy.get("coverage_amount"),
            "status": policy.get("status")
        })
    
    logger.info(f"Returning deductibles for {len(deductibles)} policies")
    return deductibles

@mcp.tool()
def get_recommendations(customer_id: str) -> List[Dict[str, Any]]:
    """
    Get product recommendations for customer
    
    Args:
        customer_id: The customer's ID
        
    Returns:
        Recommended insurance products based on current policies
    """
    logger.info(f"Getting recommendations for customer: {customer_id}")
    
    customer_policies = get_customer_policies_internal(customer_id)
    
    if not customer_policies:
        return []
    
    # Get current policy types
    current_types = set(p.get("type") for p in customer_policies)
    
    # Basic recommendation logic
    recommendations = []
    
    # If customer has auto, recommend home insurance
    if "auto" in current_types and "home" not in current_types:
        recommendations.append({
            "product_type": "home",
            "reason": "Bundle discount available with your auto insurance",
            "potential_savings": "Up to 15% discount on both policies",
            "priority": "high"
        })
    
    # If customer has home, recommend auto insurance
    if "home" in current_types and "auto" not in current_types:
        recommendations.append({
            "product_type": "auto",
            "reason": "Bundle discount available with your home insurance",
            "potential_savings": "Up to 15% discount on both policies",
            "priority": "high"
        })
    
    # If customer is young (assume based on policy details), recommend life insurance
    if "life" not in current_types:
        recommendations.append({
            "product_type": "life",
            "reason": "Protect your family's financial future",
            "potential_savings": "Lower premiums when you're younger",
            "priority": "medium"
        })
    
    # If customer has multiple policies, recommend umbrella coverage
    if len(customer_policies) >= 2 and not any("umbrella" in p.get("type", "") for p in customer_policies):
        recommendations.append({
            "product_type": "umbrella",
            "reason": "Additional liability protection across all your policies",
            "potential_savings": "Comprehensive protection at low cost",
            "priority": "medium"
        })
    
    logger.info(f"Generated {len(recommendations)} recommendations")
    return recommendations

# ============================================
# LEGACY COMPREHENSIVE API (for backward compatibility)
# ============================================

@mcp.tool()
def get_customer_policies(customer_id: str) -> List[Dict[str, Any]]:
    """
    LEGACY: Get all policies for a specific customer with comprehensive details
    (Maintained for backward compatibility - consider using specific APIs instead)
    
    Args:
        customer_id: The customer's ID to look up policies for
        
    Returns:
        List of policy dictionaries containing comprehensive policy details
    """
    logger.info(f"LEGACY API: Looking up comprehensive policies for customer: {customer_id}")
    
    # Find policies for the customer
    customer_policies = get_customer_policies_internal(customer_id)
    
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
    
    logger.info(f"LEGACY API: Returning {len(result)} policy objects for customer: {customer_id}")
    return result

if __name__ == "__main__":
    # Check command line arguments for port
    port = 8001
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    logger.info(f"Starting Enhanced Policy FastMCP Server on port {port}")
    logger.info("Available Simple Business APIs:")
    logger.info("  📋 Basic:")
    logger.info("    - get_policies: Simple policy list")
    logger.info("    - get_agent: Agent contact information")
    logger.info("    - get_policy_types: Policy types for customer")
    logger.info("  📄 Detailed:")
    logger.info("    - get_policy_list: Detailed policy list")
    logger.info("    - get_policy_details: Complete policy information")
    logger.info("  💰 Financial:")
    logger.info("    - get_payment_information: Payment details")
    logger.info("    - get_deductibles: Deductible amounts")
    logger.info("  🛡️  Coverage:")
    logger.info("    - get_coverage_information: Coverage details")
    logger.info("  🎯 Recommendations:")
    logger.info("    - get_recommendations: Product recommendations")
    logger.info("  🔄 Legacy:")
    logger.info("    - get_customer_policies: Comprehensive (backward compatibility)")
    
    # Run the FastMCP server using the correct method
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port) 