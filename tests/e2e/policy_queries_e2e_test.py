#!/usr/bin/env python3
"""
Policy Queries E2E Testing Script
Tests various policy-related queries to ensure responses are based on mock data
"""

import asyncio
import json
import time
import subprocess
import threading
from datetime import datetime
from python_a2a import A2AClient
from typing import Dict, List, Any


class PolicyQueriesE2ETester:
    """E2E testing for policy-related queries"""
    
    def __init__(self):
        self.domain_agent_url = "http://localhost:8003"
        self.port_forwards = []
        self.test_results = []
        
        # Test queries covering all requested scenarios
        self.test_queries = [
            # Core requested queries
            {
                "id": "total_coverage",
                "query": "What's the total coverage amount for customer CUST-001?",
                "expected_keywords": ["coverage", "325,000", "total", "75,000", "250,000"],
                "description": "Test total coverage calculation across all policies"
            },
            {
                "id": "policy_types",
                "query": "What types of policies do I have for customer CUST-001?",
                "expected_keywords": ["auto", "life", "policy", "types"],
                "description": "Test policy types identification"
            },
            {
                "id": "payment_due_date", 
                "query": "When is my next payment due for customer CUST-001?",
                "expected_keywords": ["payment", "due", "september", "june", "2024-09-01", "2024-06-15"],
                "description": "Test payment due date information"
            },
            {
                "id": "payment_due_auto",
                "query": "When is my auto insurance payment due for customer CUST-001?",
                "expected_keywords": ["payment", "due", "september", "2024-09-01", "auto", "quarterly"],
                "description": "Test specific auto policy payment due date"
            },
            {
                "id": "payment_due_life",
                "query": "When is my life insurance payment due for customer CUST-001?",
                "expected_keywords": ["payment", "due", "june", "2024-06-15", "life", "monthly"],
                "description": "Test specific life policy payment due date"
            },
            {
                "id": "payment_method_info",
                "query": "What payment method do I have set up for customer CUST-001?",
                "expected_keywords": ["payment", "method", "auto_pay", "auto", "autopay"],
                "description": "Test payment method information retrieval"
            },
            {
                "id": "billing_cycle_info",
                "query": "What are my billing cycles for customer CUST-001?",
                "expected_keywords": ["billing", "cycle", "quarterly", "monthly", "payment"],
                "description": "Test billing cycle information"
            },
            {
                "id": "next_payment_amount",
                "query": "How much is my next payment for customer CUST-001?",
                "expected_keywords": ["payment", "amount", "$95", "$45", "premium"],
                "description": "Test next payment amount information"
            },
            {
                "id": "contact_person",
                "query": "Who is my contact person for policies for customer CUST-001?",
                "expected_keywords": ["michael", "brown", "agent", "contact"],
                "description": "Test assigned agent contact information"
            },
            
            # Additional relevant policy queries
            {
                "id": "policy_details",
                "query": "Show me details of my auto policy for customer CUST-001",
                "expected_keywords": ["honda", "civic", "auto", "liability", "collision"],
                "description": "Test detailed policy information retrieval"
            },
            {
                "id": "premium_amounts",
                "query": "What are my premium amounts for customer CUST-001?",
                "expected_keywords": ["premium", "$95", "$45", "monthly", "quarterly"],
                "description": "Test premium amount and billing cycle information"
            },
            {
                "id": "policy_status",
                "query": "What's the status of my policies for customer CUST-001?",
                "expected_keywords": ["active", "status", "POL-2024"],
                "description": "Test policy status reporting"
            },
            {
                "id": "coverage_limits",
                "query": "What are my coverage limits for customer CUST-001?",
                "expected_keywords": ["75,000", "250,000", "bodily", "injury", "benefit"],
                "description": "Test detailed coverage limits information"
            },
            {
                "id": "deductibles",
                "query": "What are my deductibles for customer CUST-001?",
                "expected_keywords": ["deductible", "$750", "$0", "auto", "life"],
                "description": "Test deductible information across policies"
            },
            {
                "id": "policy_dates",
                "query": "When do my policies expire for customer CUST-001?",
                "expected_keywords": ["expire", "2025", "2034", "end", "date"],
                "description": "Test policy expiration date information"
            }
        ]
    
    def setup_port_forward(self):
        """Set up port forward for domain agent"""
        try:
            cmd = [
                "kubectl", "port-forward", "-n", "insurance-ai-agentic",
                "service/insurance-ai-poc-domain-agent", "8003:8003"
            ]
            
            print("🔌 Setting up port forward for domain agent...")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.port_forwards.append(process)
            time.sleep(3)  # Wait for port forward to establish
            
        except Exception as e:
            print(f"⚠️ Failed to set up port forward: {e}")
    
    def cleanup(self):
        """Clean up port forwards"""
        print("🧹 Cleaning up port forwards...")
        for process in self.port_forwards:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
    
    async def run_query_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single query test"""
        print(f"\n🔍 Testing: {test_case['description']}")
        print(f"Query: {test_case['query']}")
        
        result = {
            "test_id": test_case["id"],
            "description": test_case["description"],
            "query": test_case["query"],
            "success": False,
            "response": "",
            "keywords_found": [],
            "keywords_missing": [],
            "timestamp": datetime.now().isoformat(),
            "response_time": 0
        }
        
        try:
            start_time = time.time()
            
            # Create A2A client and send query
            domain_client = A2AClient(self.domain_agent_url)
            response = domain_client.ask(test_case["query"])
            
            end_time = time.time()
            result["response_time"] = round(end_time - start_time, 2)
            result["response"] = response
            
            # Check for expected keywords
            response_lower = response.lower()
            
            for keyword in test_case["expected_keywords"]:
                if keyword.lower() in response_lower:
                    result["keywords_found"].append(keyword)
                else:
                    result["keywords_missing"].append(keyword)
            
            # Determine success based on keyword matching
            found_percentage = len(result["keywords_found"]) / len(test_case["expected_keywords"])
            result["success"] = found_percentage >= 0.6  # 60% threshold
            
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"Result: {status}")
            print(f"Response time: {result['response_time']}s")
            print(f"Keywords found: {len(result['keywords_found'])}/{len(test_case['expected_keywords'])}")
            
            if result["keywords_missing"]:
                print(f"Missing keywords: {result['keywords_missing']}")
            
            print(f"Response preview: {response[:200]}...")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ Test failed with error: {e}")
        
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all policy query tests"""
        print("🚀 Starting Policy Queries E2E Testing")
        print("=" * 70)
        
        # Set up port forward
        self.setup_port_forward()
        
        # Wait for setup
        print("⏳ Waiting for setup to complete...")
        time.sleep(5)
        
        test_results = []
        
        # Run each test
        for i, test_case in enumerate(self.test_queries, 1):
            print(f"\n📋 Test {i}/{len(self.test_queries)}")
            result = await self.run_query_test(test_case)
            test_results.append(result)
            
            # Brief pause between tests
            time.sleep(1)
        
        # Generate summary
        summary = self.generate_summary(test_results)
        
        return {
            "summary": summary,
            "test_results": test_results,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_summary(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate test summary statistics"""
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results if result.get("success", False))
        failed_tests = total_tests - passed_tests
        
        avg_response_time = sum(result.get("response_time", 0) for result in test_results) / total_tests
        
        # Category analysis
        categories = {
            "Core Requirements": ["total_coverage", "policy_types", "contact_person"],
            "Payment Information": ["payment_due_date", "payment_due_auto", "payment_due_life", "payment_method_info", "billing_cycle_info", "next_payment_amount"],
            "Policy Details": ["policy_details", "premium_amounts", "policy_status"],
            "Coverage Information": ["coverage_limits", "deductibles", "policy_dates"]
        }
        
        category_results = {}
        for category, test_ids in categories.items():
            category_tests = [r for r in test_results if r["test_id"] in test_ids]
            category_passed = sum(1 for r in category_tests if r.get("success", False))
            category_results[category] = {
                "total": len(category_tests),
                "passed": category_passed,
                "success_rate": category_passed / len(category_tests) if category_tests else 0
            }
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": passed_tests / total_tests,
            "avg_response_time": round(avg_response_time, 2),
            "category_breakdown": category_results
        }
    
    def print_detailed_report(self, results: Dict[str, Any]):
        """Print detailed test report"""
        summary = results["summary"]
        
        print("\n" + "=" * 70)
        print("📊 POLICY QUERIES E2E TEST REPORT")
        print("=" * 70)
        
        # Overall results
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed']} ✅")
        print(f"   Failed: {summary['failed']} ❌")
        print(f"   Success Rate: {summary['success_rate']:.1%}")
        print(f"   Average Response Time: {summary['avg_response_time']}s")
        
        # Category breakdown
        print(f"\n📋 CATEGORY BREAKDOWN:")
        for category, stats in summary["category_breakdown"].items():
            rate = stats["success_rate"]
            status = "✅" if rate >= 0.8 else "⚠️" if rate >= 0.6 else "❌"
            print(f"   {category}: {stats['passed']}/{stats['total']} ({rate:.1%}) {status}")
        
        # Individual test results
        print(f"\n🔍 INDIVIDUAL TEST RESULTS:")
        for i, result in enumerate(results["test_results"], 1):
            status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
            print(f"   {i}. {result['description']}: {status}")
            
            if result.get("keywords_missing"):
                print(f"      Missing: {', '.join(result['keywords_missing'])}")
        
        # Mock data validation
        print(f"\n📋 MOCK DATA VALIDATION:")
        
        # Check specific responses for mock data usage
        coverage_test = next((r for r in results["test_results"] if r["test_id"] == "total_coverage"), None)
        if coverage_test:
            if any(amount in coverage_test["response"] for amount in ["75,000", "250,000", "325,000"]):
                print("   ✅ Total Coverage: Using correct mock data amounts")
            else:
                print("   ❌ Total Coverage: Mock data amounts not found in response")
        
        agent_test = next((r for r in results["test_results"] if r["test_id"] == "contact_person"), None)
        if agent_test:
            if any(name in agent_test["response"].lower() for name in ["michael", "brown"]):
                print("   ✅ Contact Person: Using correct agent from mock data")
            else:
                print("   ❌ Contact Person: Agent information not found in response")
        
        payment_test = next((r for r in results["test_results"] if r["test_id"] == "payment_due_date"), None)
        if payment_test:
            if any(date in payment_test["response"].lower() for date in ["june", "september"]):
                print("   ✅ Payment Dates: Using correct dates from mock data")
            else:
                print("   ❌ Payment Dates: Expected dates not found in response")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if summary["success_rate"] >= 0.9:
            print("   🎉 Excellent! All policy query flows working correctly.")
        elif summary["success_rate"] >= 0.7:
            print("   👍 Good performance with minor improvements needed.")
            print("   📝 Review failed tests for missing mock data integration.")
        else:
            print("   ⚠️ Multiple issues detected requiring attention:")
            print("   📝 Check domain agent response formatting")
            print("   📝 Verify mock data integration in policy server")
            print("   📝 Review technical agent data parsing logic")


async def main():
    """Run the policy queries E2E tests"""
    tester = PolicyQueriesE2ETester()
    
    try:
        # Run all tests
        results = await tester.run_all_tests()
        
        # Print detailed report
        tester.print_detailed_report(results)
        
        # Save results to file
        with open("policy_queries_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: policy_queries_test_results.json")
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
    
    finally:
        tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 