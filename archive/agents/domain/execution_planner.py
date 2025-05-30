"""
Execution Planning Module for Domain Agent
Handles execution planning, task coordination, and agent orchestration
"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class ExecutionPlanner:
    """
    Handles execution planning and task orchestration for the domain agent
    """
    
    def __init__(self, agent_registry: Dict[str, str], call_agent_func):
        """
        Initialize the execution planner
        
        Args:
            agent_registry: Registry of available agents
            call_agent_func: Function to call other agents
        """
        self.agent_registry = agent_registry
        self.call_agent = call_agent_func
    
    def create_execution_plan(self, intent_analysis: Dict[str, Any], user_text: str, customer_id: str = None) -> Dict[str, Any]:
        """
        Create a detailed execution plan based on intent analysis
        Handle missing information by identifying what questions to ask
        """
        primary_intent = intent_analysis.get("primary_intent", "general_inquiry")
        complexity = intent_analysis.get("complexity", "simple")
        entities = intent_analysis.get("entities", {})
        
        # Check for missing critical information (this would use IntentAnalyzer methods)
        missing_info = self._identify_missing_information(primary_intent, entities, customer_id)
        
        if missing_info:
            return {
                "type": "information_gathering",
                "primary_intent": primary_intent,
                "missing_information": missing_info,
                "questions_to_ask": self._generate_clarifying_questions(missing_info, primary_intent),
                "next_steps": "Collect required information before proceeding",
                "status": "pending_information"
            }
        
        # We have enough information to proceed
        return self._create_execution_plan_with_info(intent_analysis, user_text, customer_id)
    
    def _identify_missing_information(self, intent: str, entities: Dict[str, Any], customer_id: str = None) -> List[str]:
        """Identify what information is missing for the given intent"""
        missing = []
        
        # Critical information requirements by intent
        intent_requirements = {
            "claim_filing": ["customer_id", "incident_details"],
            "claim_status": ["customer_id"],
            "policy_inquiry": ["customer_id"],
            "billing_question": ["customer_id"],
            "quote_request": ["coverage_type"],
            "general_inquiry": []
        }
        
        required_info = intent_requirements.get(intent, [])
        
        for requirement in required_info:
            if requirement == "customer_id" and not customer_id:
                missing.append("customer_id")
            elif requirement == "incident_details" and not any(
                key in entities for key in ["incident_date", "incident_type", "damage_description"]
            ):
                missing.append("incident_details")
            elif requirement == "coverage_type" and not any(
                key in entities for key in ["coverage_type", "vehicle_type", "property_type"]
            ):
                missing.append("coverage_type")
        
        return missing
    
    def _generate_clarifying_questions(self, missing_info: List[str], intent: str) -> List[str]:
        """Generate clarifying questions for missing information"""
        questions = []
        
        question_templates = {
            "customer_id": "Could you please provide your customer ID or policy number so I can look up your account?",
            "incident_details": "To help you file your claim, could you provide details about the incident (date, type of damage, and description)?",
            "coverage_type": "What type of insurance coverage are you interested in? (auto, home, life, etc.)",
        }
        
        for info in missing_info:
            if info in question_templates:
                questions.append(question_templates[info])
            else:
                questions.append(f"I need additional information about {info.replace('_', ' ')} to help you better.")
        
        return questions
    
    def _create_execution_plan_with_info(self, intent_analysis: Dict[str, Any], user_text: str, customer_id: str) -> Dict[str, Any]:
        """Create execution plan when we have sufficient information"""
        primary_intent = intent_analysis.get("primary_intent", "general_inquiry")
        complexity = intent_analysis.get("complexity", "simple")
        entities = intent_analysis.get("entities", {})
        
        # Create execution plan based on intent
        if primary_intent == "claim_status":
            return self._create_claim_status_plan(entities, customer_id, complexity)
        elif primary_intent == "policy_inquiry":
            return self._create_policy_inquiry_plan(entities, customer_id, complexity)
        elif primary_intent == "claim_filing":
            return self._create_claim_filing_plan(entities, customer_id, complexity)
        elif primary_intent == "billing_question":
            return self._create_billing_plan(entities, customer_id, complexity)
        elif primary_intent == "quote_request":
            return self._create_quote_plan(entities, complexity)
        else:
            return self._create_general_plan(entities, customer_id, complexity)
    
    def _create_claim_status_plan(self, entities: Dict[str, Any], customer_id: str, complexity: str) -> Dict[str, Any]:
        """Create execution plan for claim status inquiries"""
        return {
            "type": "sequential_execution",
            "primary_intent": "claim_status",
            "complexity": complexity,
            "steps": [
                {
                    "step_id": "fetch_customer_data",
                    "agent": "data_agent",
                    "action": "fetch_customer_data",
                    "parameters": {"customer_id": customer_id},
                    "expected_output": "customer_info",
                    "timeout": 30
                },
                {
                    "step_id": "get_claims_history",
                    "agent": "data_agent", 
                    "action": "get_claims_history",
                    "parameters": {"customer_id": customer_id},
                    "expected_output": "claims_data",
                    "timeout": 30
                }
            ],
            "coordination": "sequential",
            "timeout": 60,
            "status": "ready_to_execute"
        }
    
    def _create_policy_inquiry_plan(self, entities: Dict[str, Any], customer_id: str, complexity: str) -> Dict[str, Any]:
        """Create execution plan for policy inquiries"""
        return {
            "type": "parallel_execution",
            "primary_intent": "policy_inquiry",
            "complexity": complexity,
            "steps": [
                {
                    "step_id": "fetch_policy_details",
                    "agent": "data_agent",
                    "action": "fetch_policy_details",
                    "parameters": {"customer_id": customer_id},
                    "expected_output": "policy_data",
                    "timeout": 30
                },
                {
                    "step_id": "calculate_current_benefits",
                    "agent": "data_agent",
                    "action": "calculate_current_benefits",
                    "parameters": {"customer_id": customer_id},
                    "expected_output": "benefits_data",
                    "timeout": 30
                }
            ],
            "coordination": "parallel",
            "timeout": 45,
            "status": "ready_to_execute"
        }
    
    def _create_claim_filing_plan(self, entities: Dict[str, Any], customer_id: str, complexity: str) -> Dict[str, Any]:
        """Create execution plan for claim filing"""
        return {
            "type": "sequential_execution",
            "primary_intent": "claim_filing",
            "complexity": complexity,
            "steps": [
                {
                    "step_id": "validate_customer",
                    "agent": "data_agent",
                    "action": "fetch_customer_data",
                    "parameters": {"customer_id": customer_id},
                    "expected_output": "customer_info",
                    "timeout": 30
                },
                {
                    "step_id": "create_new_claim",
                    "agent": "data_agent",
                    "action": "create_claim",
                    "parameters": {
                        "customer_id": customer_id,
                        "incident_details": entities.get("incident_details", {}),
                        "incident_date": entities.get("incident_date"),
                        "incident_type": entities.get("incident_type", "auto")
                    },
                    "expected_output": "claim_confirmation",
                    "timeout": 45
                }
            ],
            "coordination": "sequential",
            "timeout": 90,
            "status": "ready_to_execute"
        }
    
    def _create_billing_plan(self, entities: Dict[str, Any], customer_id: str, complexity: str) -> Dict[str, Any]:
        """Create execution plan for billing inquiries"""
        return {
            "type": "sequential_execution",
            "primary_intent": "billing_question",
            "complexity": complexity,
            "steps": [
                {
                    "step_id": "fetch_billing_info",
                    "agent": "data_agent",
                    "action": "fetch_billing_information",
                    "parameters": {"customer_id": customer_id},
                    "expected_output": "billing_data",
                    "timeout": 30
                }
            ],
            "coordination": "sequential",
            "timeout": 45,
            "status": "ready_to_execute"
        }
    
    def _create_quote_plan(self, entities: Dict[str, Any], complexity: str) -> Dict[str, Any]:
        """Create execution plan for quote requests"""
        coverage_type = entities.get("coverage_type", "auto")
        return {
            "type": "sequential_execution",
            "primary_intent": "quote_request",
            "complexity": complexity,
            "steps": [
                {
                    "step_id": "generate_quote",
                    "agent": "data_agent",
                    "action": "generate_quote",
                    "parameters": {
                        "coverage_type": coverage_type,
                        "vehicle_info": entities.get("vehicle_info", {}),
                        "customer_info": entities.get("customer_info", {})
                    },
                    "expected_output": "quote_data",
                    "timeout": 45
                }
            ],
            "coordination": "sequential",
            "timeout": 60,
            "status": "ready_to_execute"
        }
    
    def _create_general_plan(self, entities: Dict[str, Any], customer_id: str, complexity: str) -> Dict[str, Any]:
        """Create execution plan for general inquiries"""
        return {
            "type": "simple_execution",
            "primary_intent": "general_inquiry",
            "complexity": complexity,
            "steps": [
                {
                    "step_id": "general_info",
                    "agent": "data_agent",
                    "action": "general_inquiry",
                    "parameters": {"query": entities.get("query", "General information request")},
                    "expected_output": "general_response",
                    "timeout": 30
                }
            ],
            "coordination": "simple",
            "timeout": 45,
            "status": "ready_to_execute"
        }
    
    def execute_plan(self, execution_plan: Dict[str, Any], conversation_id: str) -> Dict[str, Any]:
        """
        Role 2: Execute the plan by routing tasks to technical agents
        """
        try:
            coordination_type = execution_plan.get("coordination", "sequential")
            steps = execution_plan.get("steps", [])
            
            logger.info("Executing plan", 
                       type=execution_plan.get("type"),
                       coordination=coordination_type,
                       steps_count=len(steps))
            
            if coordination_type == "sequential":
                step_results = self.execute_sequential_steps(steps, execution_plan)
            elif coordination_type == "parallel":
                step_results = self.execute_parallel_steps(steps, execution_plan)
            else:
                # Simple execution - just run the single step
                step_results = self.execute_sequential_steps(steps, execution_plan)
            
            # Aggregate results
            aggregated_data = self._aggregate_step_results(step_results)
            
            return {
                "execution_status": "completed" if step_results else "failed",
                "step_results": step_results,
                "aggregated_data": aggregated_data,
                "coordination_type": coordination_type,
                "total_steps": len(steps),
                "successful_steps": len([r for r in step_results if r.get("success")])
            }
            
        except Exception as e:
            logger.error("Plan execution failed", error=str(e))
            return {
                "execution_status": "error",
                "error": str(e),
                "step_results": [],
                "aggregated_data": {}
            }
    
    def execute_sequential_steps(self, steps: List[Dict[str, Any]], execution_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute steps sequentially, passing results between steps"""
        step_results = []
        context = {"previous_results": []}
        
        for step in steps:
            try:
                logger.info("Executing step", step_id=step.get("step_id"), agent=step.get("agent"))
                
                # Prepare parameters with context
                step_params = step.get("parameters", {}).copy()
                step_params["context"] = context
                step_params["previous_results"] = context["previous_results"]
                
                # Build task data for the agent
                task_data = {
                    "action": step.get("action"),
                    **step_params
                }
                
                # Call the technical agent
                agent_name = step.get("agent")
                if agent_name not in self.agent_registry:
                    raise ValueError(f"Agent {agent_name} not available in registry")
                
                agent_response = self.call_agent(self.agent_registry[agent_name], json.dumps(task_data))
                
                # Parse agent response
                try:
                    if isinstance(agent_response, str):
                        parsed_response = json.loads(agent_response)
                    else:
                        parsed_response = agent_response
                except json.JSONDecodeError:
                    parsed_response = {"raw_response": agent_response}
                
                step_result = {
                    "step_id": step.get("step_id"),
                    "agent": agent_name,
                    "action": step.get("action"),
                    "success": True,
                    "data": parsed_response,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                step_results.append(step_result)
                context["previous_results"].append(step_result)
                
                logger.info("Step completed successfully", step_id=step.get("step_id"))
                
            except Exception as e:
                logger.error("Step execution failed", step_id=step.get("step_id"), error=str(e))
                step_result = {
                    "step_id": step.get("step_id"),
                    "agent": step.get("agent"),
                    "action": step.get("action"),
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                step_results.append(step_result)
                # Continue with next step even if one fails
        
        return step_results
    
    def execute_parallel_steps(self, steps: List[Dict[str, Any]], execution_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute steps in parallel for faster execution"""
        # For now, execute sequentially - can be enhanced with actual parallel execution later
        return self.execute_sequential_steps(steps, execution_plan)
    
    def _aggregate_step_results(self, step_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from multiple steps into a cohesive data structure"""
        aggregated = {
            "customer_data": {},
            "policy_data": {},
            "claims_data": {},
            "billing_data": {},
            "quote_data": {},
            "general_data": {},
            "metadata": {
                "total_steps": len(step_results),
                "successful_steps": len([r for r in step_results if r.get("success")]),
                "failed_steps": len([r for r in step_results if not r.get("success")]),
                "execution_time": datetime.utcnow().isoformat()
            }
        }
        
        # Process each step result
        for result in step_results:
            if not result.get("success"):
                continue
            
            action = result.get("action", "")
            data = result.get("data", {})
            
            # Categorize data based on action type
            if "customer" in action or "fetch_customer_data" in action:
                aggregated["customer_data"].update(data)
            elif "policy" in action or "fetch_policy_details" in action:
                aggregated["policy_data"].update(data)
            elif "claim" in action or "get_claims_history" in action:
                aggregated["claims_data"].update(data)
            elif "billing" in action:
                aggregated["billing_data"].update(data)
            elif "quote" in action:
                aggregated["quote_data"].update(data)
            else:
                aggregated["general_data"].update(data)
        
        return aggregated 