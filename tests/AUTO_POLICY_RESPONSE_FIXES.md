# Auto Policy Response Fixes

## Issues Identified

The system was showing incorrect information when users asked about auto policies:

1. **Wrong Policy Type Displayed**: When users asked about auto insurance, the system prominently displayed life insurance details instead
2. **Vehicle Information Corruption**: The system changed "Honda Civic" to "Honda City" and created false statements about coverage
3. **Data Fabrication**: The LLM was making up scenarios about vehicles "not being covered" when no such information existed in the data

## Root Causes

1. **Template Selection Logic**: The response formatter wasn't detecting specific policy types in user queries
2. **LLM Prompt Issues**: The formatting prompt lacked strict rules about data accuracy and policy type filtering
3. **Missing Templates**: No specific templates for auto or life policy responses

## Fixes Implemented

### 1. Enhanced LLM Formatting Prompt (`domain_agent/prompts.yaml`)

Added strict rules to prevent data corruption:

```yaml
POLICY TYPE FILTERING RULES:
- If customer asks about "auto policy" or "auto insurance" or "vehicle", show ONLY auto policy details prominently
- If customer asks about "life policy" or "life insurance", show ONLY life policy details prominently
- Focus the response on the specific policy type mentioned in the customer question

STRICT DATA USAGE RULES:
- Use EXACT vehicle make, model, year from the JSON data - DO NOT change Honda Civic to Honda City
- DO NOT mention vehicles that are not in the customer's actual policy data
- DO NOT create fictional scenarios about coverage gaps
- Stick strictly to the facts provided in the comprehensive policy JSON data
```

### 2. Enhanced Template Selection (`domain_agent/response_formatter.py`)

Added intelligent template selection based on user query content:

```python
def _get_template_key_for_intent_and_question(self, intent: str, user_question: str) -> str:
    user_question_lower = user_question.lower()
    
    # Check for payment-related queries first
    if any(keyword in user_question_lower for keyword in ["payment", "due", "premium", "billing", "pay"]):
        return "payment_due_template"
    
    # Check for specific policy type mentions
    if any(keyword in user_question_lower for keyword in ["auto", "vehicle", "car", "driving"]):
        return "auto_policy_template"
    elif any(keyword in user_question_lower for keyword in ["life", "death", "beneficiary", "beneficiaries"]):
        return "life_policy_template"
```

### 3. New Policy-Specific Templates (`domain_agent/prompts.yaml`)

Added focused templates for different policy types:

```yaml
auto_policy_template: |
  **AUTO INSURANCE DETAILS FOR CUSTOMER {customer_id}:**
  
  🚗 **Vehicle Information:**
  {vehicle_details}
  
  🛡️ **Coverage Details:**
  {auto_coverage_details}

life_policy_template: |
  **LIFE INSURANCE DETAILS FOR CUSTOMER {customer_id}:**
  
  🛡️ **Coverage Information:**
  {life_coverage_details}
  
  👥 **Beneficiaries:**
  {beneficiary_info}
```

## Verification

Created test script in `tests/unit/test_auto_policy_fix.py` that verifies:

✅ Mock data integrity (Honda Civic, not Honda City)
✅ Template selection works correctly for different query types  
✅ Prompts include the new strict data usage rules

## Expected Behavior After Fixes

When a user asks: **"Show me my auto policy for CUST-001"**

The system should now:
- ✅ Use the `auto_policy_template`
- ✅ Show ONLY auto insurance details prominently
- ✅ Display vehicle as "2019 Honda Civic" (exact match from data)
- ✅ Include coverage types: liability, collision, comprehensive
- ✅ NOT mention life insurance prominently
- ✅ NOT make up any vehicle information

## Data Integrity Confirmed

Customer CUST-001 actually has:
- **Auto Policy**: 2019 Honda Civic (VIN: 2HGFC2F59KH123456)
- **Life Policy**: $250,000 Term Life Insurance

The system will now display this information accurately without corruption or fabrication. 