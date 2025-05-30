"""
Response Generation Module for Domain Agent
Handles professional response preparation and template generation
"""

from typing import Dict, Any, List
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


class ResponseGenerator:
    """
    Handles response generation and professional template formatting for the domain agent
    """
    
    def __init__(self, template_enhancement_enabled: bool = True):
        """
        Initialize the response generator
        
        Args:
            template_enhancement_enabled: Whether to use professional templates
        """
        self.template_enhancement_enabled = template_enhancement_enabled
        self.response_template = self._load_professional_template()
    
    def _load_professional_template(self) -> str:
        """Load the professional response template from file"""
        try:
            template_path = Path("Template")
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = f.read().strip()
                logger.info("Professional response template loaded successfully")
                return template
        except Exception as e:
            logger.warning(f"Could not load professional template: {e}")
        
        # Fallback professional template
        return """Thank you for your inquiry. I've conducted a comprehensive analysis of your request.

**Current Status:**
Based on my review, here's what I found:
• {primary_status}
• Current state: **{current_state}**
• Estimated timeline: **{estimated_timeline}**

**Detailed Analysis:**
{detailed_analysis}

**Your Account Overview:**
• {account_summary}
• Customer type: **{customer_type}**

**Next Steps:**
{next_steps}

**Contact Information:**
If you need immediate assistance, please don't hesitate to contact our support team.

Is there any specific aspect you'd like me to explain in more detail?"""
    
    def prepare_response(self, intent_analysis: Dict[str, Any], execution_results: Dict[str, Any], user_text: str) -> str:
        """
        Role 3: Prepare professional response using templates
        """
        try:
            # Check if this is an information gathering response
            if execution_results.get("execution_status") == "pending_information":
                return self._prepare_information_gathering_response(execution_results, intent_analysis)
            
            # Check for execution errors
            if execution_results.get("execution_status") == "error":
                return self._generate_error_response(intent_analysis, user_text, execution_results.get("error", "Unknown error"))
            
            # Normal successful execution
            if self.template_enhancement_enabled and self.response_template:
                return self._generate_template_response(intent_analysis, execution_results, user_text)
            else:
                return self._generate_enhanced_fallback_response(
                    intent_analysis.get("primary_intent", "general_inquiry"),
                    execution_results.get("execution_status", "completed"),
                    execution_results.get("aggregated_data", {})
                )
                
        except Exception as e:
            logger.error("Response preparation failed", error=str(e))
            return self._generate_error_response(intent_analysis, user_text, str(e))
    
    def _prepare_information_gathering_response(self, execution_results: Dict[str, Any], intent_analysis: Dict[str, Any]) -> str:
        """Prepare response when we need more information from the user"""
        primary_intent = intent_analysis.get("primary_intent", "your request")
        questions = execution_results.get("questions_to_ask", [])
        
        if not questions:
            questions = ["Could you provide more details about your request?"]
        
        # Format questions nicely
        if len(questions) == 1:
            question_text = questions[0]
        else:
            question_text = "I need a few details to help you better:\n" + "\n".join(f"• {q}" for q in questions)
        
        return f"""Thank you for your inquiry about {primary_intent.replace('_', ' ')}.

To provide you with the most accurate and helpful information, I need to gather some additional details.

{question_text}

Once I have this information, I'll be able to give you a comprehensive response with all the details you need.

Please feel free to provide these details, and I'll take care of the rest!"""
    
    def _generate_template_response(self, intent_analysis: Dict[str, Any], execution_results: Dict[str, Any], user_text: str) -> str:
        """Generate response using professional template"""
        try:
            aggregated_data = execution_results.get("aggregated_data", {})
            primary_intent = intent_analysis.get("primary_intent", "general_inquiry")
            execution_status = execution_results.get("execution_status", "completed")
            
            # Build template variables
            template_vars = {
                "primary_status": self._get_primary_status(intent_analysis, aggregated_data, execution_status),
                "current_state": execution_status.title(),
                "estimated_timeline": "Immediate",
                "detailed_analysis": self._build_detailed_analysis(intent_analysis, aggregated_data, execution_results),
                "account_summary": self._build_account_summary(aggregated_data),
                "customer_type": aggregated_data.get("customer_data", {}).get("customer_type", "Standard"),
                "next_steps": self._build_next_steps(intent_analysis, aggregated_data, execution_status)
            }
            
            # Apply template
            response = self.response_template.format(**template_vars)
            
            logger.info("Template response generated successfully", 
                       intent=primary_intent, template_vars_count=len(template_vars))
            
            return response
            
        except Exception as e:
            logger.error("Template response generation failed", error=str(e))
            # Fallback to enhanced response
            return self._generate_enhanced_fallback_response(
                intent_analysis.get("primary_intent", "general_inquiry"),
                execution_results.get("execution_status", "completed"),
                execution_results.get("aggregated_data", {})
            )
    
    def _get_primary_status(self, intent_analysis: Dict[str, Any], aggregated_data: Dict[str, Any], execution_status: str) -> str:
        """Generate primary status based on intent and results"""
        primary_intent = intent_analysis.get("primary_intent", "general_inquiry")
        
        if primary_intent == "claim_status":
            claims_data = aggregated_data.get("claims_data", {})
            claim_status = claims_data.get("status", "under review")
            return f"Your claim is currently {claim_status}"
        elif primary_intent == "policy_inquiry":
            policy_data = aggregated_data.get("policy_data", {})
            active_policies = policy_data.get("active_policies", 0)
            return f"You have {active_policies} active insurance policies"
        elif primary_intent == "billing_question":
            billing_data = aggregated_data.get("billing_data", {})
            next_due = billing_data.get("next_payment_due", "N/A")
            return f"Your next payment is due {next_due}"
        elif primary_intent == "quote_request":
            quote_data = aggregated_data.get("quote_data", {})
            quote_amount = quote_data.get("monthly_premium", "N/A")
            return f"Your estimated monthly premium is ${quote_amount}"
        else:
            return f"Your {primary_intent.replace('_', ' ')} has been processed successfully"
    
    def _build_detailed_analysis(self, intent_analysis: Dict[str, Any], aggregated_data: Dict[str, Any], execution_results: Dict[str, Any]) -> str:
        """Build detailed analysis section"""
        primary_intent = intent_analysis.get("primary_intent", "general_inquiry")
        
        analysis_parts = []
        
        # Add intent-specific analysis
        if primary_intent == "claim_status":
            claims_data = aggregated_data.get("claims_data", {})
            if claims_data:
                analysis_parts.append(f"I've reviewed your claims history and found {len(claims_data.get('claims', []))} total claims.")
                analysis_parts.append(f"Most recent claim status: {claims_data.get('status', 'under review')}")
        
        elif primary_intent == "policy_inquiry":
            policy_data = aggregated_data.get("policy_data", {})
            if policy_data:
                analysis_parts.append(f"Your current policy portfolio includes {policy_data.get('active_policies', 0)} active policies.")
                analysis_parts.append(f"Total annual premium: ${policy_data.get('annual_premium', 0):,.2f}")
        
        # Add execution metadata
        successful_steps = execution_results.get("successful_steps", 0)
        total_steps = execution_results.get("total_steps", 0)
        analysis_parts.append(f"Successfully completed {successful_steps} of {total_steps} information gathering steps.")
        
        return " ".join(analysis_parts) if analysis_parts else "I've processed your request and gathered the relevant information from our systems."
    
    def _build_account_summary(self, aggregated_data: Dict[str, Any]) -> str:
        """Build account summary section"""
        customer_data = aggregated_data.get("customer_data", {})
        policy_data = aggregated_data.get("policy_data", {})
        
        summary_parts = []
        if customer_data.get("customer_id"):
            summary_parts.append(f"Customer ID: {customer_data['customer_id']}")
        if policy_data.get("active_policies"):
            summary_parts.append(f"Active policies: {policy_data['active_policies']}")
        
        return " | ".join(summary_parts) if summary_parts else "Account information retrieved successfully"
    
    def _build_next_steps(self, intent_analysis: Dict[str, Any], aggregated_data: Dict[str, Any], execution_status: str) -> str:
        """Build next steps section"""
        primary_intent = intent_analysis.get("primary_intent", "general_inquiry")
        
        if primary_intent == "claim_status":
            return """1. Your claim will continue to be processed according to our standard timeline
2. You'll receive updates via email as the status changes
3. Contact our claims department if you have additional documentation"""
        
        elif primary_intent == "policy_inquiry":
            return """1. Review the policy details provided above
2. Contact your agent if you need coverage adjustments
3. Set up automatic payments to ensure continuous coverage"""
        
        elif primary_intent == "quote_request":
            return """1. Review the quote details and coverage options
2. Contact our sales team to finalize your policy
3. Have your documentation ready for policy activation"""
        
        else:
            return """1. The information provided should address your inquiry
2. Contact customer service for additional questions
3. Keep your policy information updated for faster service"""
    
    def _generate_enhanced_fallback_response(self, primary_intent: str, execution_status: str, aggregated_data: Dict[str, Any]) -> str:
        """Generate enhanced fallback response when template is not available"""
        context = aggregated_data.get("customer_data", {})
        policy_data = aggregated_data.get("policy_data", {})
        claims_data = aggregated_data.get("claims_data", {})
        
        return f"""Thank you for your inquiry. I've completed a comprehensive analysis of your request.

**Current Status:**
Based on my review of your {primary_intent.replace('_', ' ')}, here's what I found:
• Processing status: **{execution_status.title()}**
• Account type: **{context.get('customer_type', 'Standard')} Customer**
• Active policies: **{policy_data.get('active_policies', 0)}**

**Summary:**
I've processed your request regarding {primary_intent.replace('_', ' ')} and gathered the relevant information from our systems. {f"Your claim status is currently {claims_data.get('status', 'under review')}." if 'claim' in primary_intent else "Your account information has been retrieved and reviewed."}

**Next Steps:**
1. The information I've provided reflects the current state of your account
2. If you need additional details, please let me know your specific questions
3. For urgent matters, you can contact our support team directly

**Professional Note:**
As a valued {context.get('customer_type', 'Standard')} customer, you have access to our full range of services and support options.

Is there any specific aspect of your {primary_intent.replace('_', ' ')} that you'd like me to explain in more detail?"""
    
    def _generate_error_response(self, intent_analysis: Dict[str, Any], user_text: str, error_msg: str) -> str:
        """Generate professional error response"""
        primary_intent = intent_analysis.get("primary_intent", "your inquiry")
        
        return f"""Thank you for contacting us regarding {primary_intent.replace('_', ' ')}.

**Current Status:**
I've encountered a technical issue while processing your request, but I'm committed to helping you resolve your inquiry.

**What Happened:**
While gathering information from our systems, I experienced a temporary processing delay. This doesn't affect your account or any pending transactions.

**Next Steps:**
1. **Immediate**: You can try rephrasing your question or asking about a specific aspect
2. **Alternative**: Contact our customer service team directly for immediate assistance
3. **Follow-up**: I'll be available to help once the technical issue is resolved

**Professional Assistance:**
Our support team is standing by to provide immediate assistance with any urgent matters.

Please let me know how else I can help you, or feel free to try your request again in a few moments.""" 