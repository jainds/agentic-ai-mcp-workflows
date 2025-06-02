# Focused Policy Server APIs Guide

## Overview

The policy server has been refactored from a single comprehensive API into multiple focused APIs that allow clients to request only the specific information they need. This improves performance, reduces data transfer, and provides better granular control.

## API Categories

### 📋 Policy Overview APIs

#### `get_policy_summary(customer_id: str)`
**Purpose**: Get a high-level summary of all customer policies
**Returns**: 
- Policy count, types, and total coverage
- Active policy count
- Total premium amount
- Upcoming payment dates

**Example Usage**:
```python
summary = await client.call_tool("get_policy_summary", {"customer_id": "CUST-001"})
# Returns: {"total_policies": 2, "policy_types": ["auto", "life"], "total_coverage": 325000.00, ...}
```

#### `get_policy_list(customer_id: str)`
**Purpose**: Get a simple list of policies with basic information
**Returns**: List of policies with ID, type, status, premium, coverage amount, and dates

**Example Usage**:
```python
policies = await client.call_tool("get_policy_list", {"customer_id": "CUST-001"})
# Returns: [{"id": "POL-2024-AUTO-002", "type": "auto", "premium": 95.00, ...}, ...]
```

### 💰 Payment & Billing APIs

#### `get_payment_information(customer_id: str, policy_type: Optional[str] = None)`
**Purpose**: Get payment and billing details for customer policies
**Parameters**:
- `customer_id`: Required customer ID
- `policy_type`: Optional filter by policy type (auto, home, life, etc.)

**Returns**: Payment schedules, billing cycles, payment methods, due dates

**Example Usage**:
```python
# All payment info
payments = await client.call_tool("get_payment_information", {"customer_id": "CUST-001"})

# Auto policies only
auto_payments = await client.call_tool("get_payment_information", 
                                     {"customer_id": "CUST-001", "policy_type": "auto"})
```

#### `get_upcoming_payments(customer_id: str, days_ahead: int = 30)`
**Purpose**: Get upcoming payment due dates within specified timeframe
**Returns**: Sorted list of upcoming payments with due dates and amounts

### 🛡️ Coverage & Details APIs

#### `get_policy_coverage(customer_id: str, policy_type: Optional[str] = None)`
**Purpose**: Get coverage details and limits for customer policies
**Returns**: Coverage amounts, deductibles, policy limits, and coverage types

**Example Usage**:
```python
coverage = await client.call_tool("get_policy_coverage", {"customer_id": "CUST-001"})
# Returns coverage details, deductibles, policy limits
```

#### `get_policy_details(policy_id: str)`
**Purpose**: Get complete details for a specific policy
**Returns**: Full policy information including coverage, payments, agent details, and policy-specific data

**Example Usage**:
```python
details = await client.call_tool("get_policy_details", {"policy_id": "POL-2024-AUTO-002"})
# Returns complete policy details including vehicle information, agent info, etc.
```

### 👥 Agent & Contact APIs

#### `get_assigned_agents(customer_id: str)`
**Purpose**: Get information about agents assigned to customer policies
**Returns**: Agent contact information and which policy types they handle

**Example Usage**:
```python
agents = await client.call_tool("get_assigned_agents", {"customer_id": "CUST-001"})
# Returns: [{"name": "Michael Brown", "email": "...", "handles_policy_types": ["auto", "life"], ...}]
```

### 🔄 Legacy API (Backward Compatibility)

#### `get_customer_policies(customer_id: str)`
**Purpose**: Legacy comprehensive API that returns all policy information
**Note**: Maintained for backward compatibility, but consider using focused APIs instead

## Performance Benefits

### Data Transfer Optimization
- **Focused APIs**: Transfer only needed data (e.g., 200-500 bytes for payment info)
- **Legacy API**: Transfers all data (e.g., 2000+ bytes comprehensive data)
- **Savings**: Up to 70-80% reduction in data transfer for specific queries

### Response Time Improvements
- **Focused APIs**: Faster processing due to limited data scope
- **Caching**: Better caching opportunities for specific data types
- **Scaling**: Individual endpoints can be optimized separately

### Use Case Examples

#### Scenario 1: Customer wants payment information only
```python
# ✅ Efficient - Focused API
payments = await client.call_tool("get_payment_information", {"customer_id": "CUST-001"})

# ❌ Inefficient - Legacy API (returns all data)
all_data = await client.call_tool("get_customer_policies", {"customer_id": "CUST-001"})
```

#### Scenario 2: Customer wants auto policy coverage details only
```python
# ✅ Efficient - Focused API with filter
auto_coverage = await client.call_tool("get_policy_coverage", 
                                     {"customer_id": "CUST-001", "policy_type": "auto"})

# ❌ Inefficient - Get all and filter client-side
all_data = await client.call_tool("get_customer_policies", {"customer_id": "CUST-001"})
```

#### Scenario 3: Dashboard showing policy summary
```python
# ✅ Efficient - Summary API
summary = await client.call_tool("get_policy_summary", {"customer_id": "CUST-001"})

# ❌ Inefficient - Process comprehensive data
all_data = await client.call_tool("get_customer_policies", {"customer_id": "CUST-001"})
```

## Technical Agent Integration

The technical agent supports all focused APIs through the enhanced skill system:

### Available Skills:
- `get_policy_summary_skill`
- `get_payment_information_skill` 
- `get_policy_coverage_skill`
- `get_assigned_agents_skill`
- Plus the legacy `get_customer_policies_skill`

### Intelligent Request Routing
The technical agent can route requests to the most appropriate API based on customer intent:

```python
# Customer asks "What are my upcoming payments?"
# → Routes to get_payment_information_skill

# Customer asks "What's my auto coverage?"  
# → Routes to get_policy_coverage_skill with policy_type="auto"

# Customer asks "Who is my agent?"
# → Routes to get_assigned_agents_skill
```

## Testing the APIs

Use the provided test script to compare focused vs comprehensive APIs:

```bash
python test_focused_apis.py
```

This will:
- Test all focused APIs individually
- Compare performance with legacy comprehensive API  
- Show data transfer savings
- Demonstrate filtering capabilities

## Migration Strategy

### For New Implementations:
1. Use focused APIs for specific data needs
2. Use legacy API only when you need all policy data
3. Consider combining multiple focused calls for complex scenarios

### For Existing Implementations:
1. Legacy API remains fully functional
2. Gradually migrate to focused APIs for performance gains
3. Test focused APIs in parallel before switching

### Best Practices:
- **Single Data Type**: Use focused APIs (e.g., only payments → `get_payment_information`)
- **Multiple Data Types**: Consider if multiple focused calls vs single comprehensive call is better
- **Dashboard/Summary**: Use `get_policy_summary` for overview displays
- **Specific Policy**: Use `get_policy_details` for drill-down views
- **Filtered Data**: Use focused APIs with type filters (e.g., auto-only payments)

## Error Handling

All APIs return consistent error structures:
```json
{
  "error": "Customer CUST-999 not found",
  "customer_id": "CUST-999"
}
```

Individual API failures don't affect others, allowing for better error isolation and recovery strategies. 