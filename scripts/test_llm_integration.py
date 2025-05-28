#!/usr/bin/env python3
"""
Test runner for LLM integration tests.

This script provides easy commands to test different aspects of LLM integration:
- API key validation
- Basic LLM functionality
- Agent LLM integration
- End-to-end workflows

Usage:
    python scripts/test_llm_integration.py --help
    python scripts/test_llm_integration.py unit
    python scripts/test_llm_integration.py integration
    python scripts/test_llm_integration.py all
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not available, continue without it
    pass


def run_command(cmd: List[str], env: Optional[dict] = None) -> int:
    """Run a command and return the exit code"""
    print(f"Running: {' '.join(cmd)}")
    
    # Merge environment variables
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    result = subprocess.run(cmd, env=full_env)
    return result.returncode


def check_api_key() -> bool:
    """Check if a valid API key is available"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ No OPENROUTER_API_KEY found in environment")
        return False
    
    if api_key.startswith("sk-or-v1-test"):
        print("⚠️  Test API key detected - integration tests will be skipped")
        return False
    
    print("✅ Valid API key found")
    return True


def run_unit_tests() -> int:
    """Run unit tests (mocked, no real API calls)"""
    print("\n🧪 Running unit tests (mocked LLM calls)...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/unit/test_llm_client.py",
        "tests/unit/test_agent_llm_integration.py",
        "-v",
        "-m", "not integration",
        "--tb=short"
    ]
    
    return run_command(cmd)


def run_integration_tests() -> int:
    """Run integration tests (requires real API key)"""
    print("\n🌐 Running integration tests (real API calls)...")
    
    if not check_api_key():
        print("Skipping integration tests - no valid API key")
        return 0
    
    cmd = [
        "python", "-m", "pytest",
        "tests/unit/test_llm_client.py",
        "tests/unit/test_agent_llm_integration.py",
        "tests/integration/test_llm_api_integration.py",
        "-v",
        "-m", "integration",
        "--tb=short"
    ]
    
    return run_command(cmd)


def run_api_key_tests() -> int:
    """Run tests specifically for API key validation"""
    print("\n🔑 Running API key validation tests...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/unit/test_llm_client.py::TestOpenRouterClient::test_client_initialization_with_env_key",
        "tests/unit/test_llm_client.py::TestOpenRouterClient::test_client_initialization_with_explicit_key",
        "tests/unit/test_llm_client.py::TestOpenRouterClient::test_client_initialization_without_key_raises_error",
        "tests/integration/test_llm_api_integration.py::TestLLMAPIKeyValidation",
        "-v",
        "--tb=short"
    ]
    
    return run_command(cmd)


def run_agent_tests() -> int:
    """Run tests specifically for agent LLM integration"""
    print("\n🤖 Running agent LLM integration tests...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/unit/test_agent_llm_integration.py",
        "-v",
        "--tb=short"
    ]
    
    return run_command(cmd)


def run_quick_smoke_test() -> int:
    """Run a quick smoke test to verify basic functionality"""
    print("\n💨 Running quick smoke test...")
    
    if not check_api_key():
        print("Running smoke test with mocked API...")
        cmd = [
            "python", "-m", "pytest",
            "tests/unit/test_llm_client.py::TestOpenRouterClient::test_chat_completion_success",
            "tests/unit/test_agent_llm_integration.py::TestSupportAgentLLMIntegration::test_extract_intent_functionality",
            "-v",
            "--tb=short"
        ]
    else:
        print("Running smoke test with real API...")
        cmd = [
            "python", "-m", "pytest",
            "tests/integration/test_llm_api_integration.py::TestRealLLMAPIIntegration::test_basic_chat_completion",
            "tests/integration/test_llm_api_integration.py::TestAgentLLMWorkflows::test_support_agent_intent_extraction",
            "-v",
            "--tb=short"
        ]
    
    return run_command(cmd)


def run_all_tests() -> int:
    """Run all tests"""
    print("\n🎯 Running all tests...")
    
    # Run unit tests first
    unit_result = run_unit_tests()
    if unit_result != 0:
        print("❌ Unit tests failed")
        return unit_result
    
    # Run integration tests if API key is available
    if check_api_key():
        integration_result = run_integration_tests()
        if integration_result != 0:
            print("❌ Integration tests failed")
            return integration_result
    else:
        print("⚠️  Skipping integration tests - no valid API key")
    
    print("✅ All tests passed!")
    return 0


def create_sample_env_file():
    """Create a sample .env file for testing"""
    env_content = """# LLM API Configuration
OPENROUTER_API_KEY=your-openrouter-api-key-here
# Alternative: OPENAI_API_KEY=your-openai-api-key-here
# Alternative: ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Model Configuration
PRIMARY_MODEL=qwen/qwen3-30b-a3b:free
FALLBACK_MODEL=anthropic/claude-3-haiku
EMBEDDING_MODEL=openai/text-embedding-ada-002

# OpenRouter Configuration
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Service URLs (for testing)
CUSTOMER_AGENT_URL=http://localhost:8010
POLICY_AGENT_URL=http://localhost:8011
CLAIMS_DATA_AGENT_URL=http://localhost:8012
"""
    
    env_file = Path(".env.example")
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print(f"✅ Created {env_file}")
    print("📝 Edit this file with your actual API keys and copy to .env")


def main():
    parser = argparse.ArgumentParser(
        description="Test runner for LLM integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_llm_integration.py unit           # Run unit tests only
  python scripts/test_llm_integration.py integration   # Run integration tests
  python scripts/test_llm_integration.py api-key       # Test API key validation
  python scripts/test_llm_integration.py agents        # Test agent integration
  python scripts/test_llm_integration.py smoke         # Quick smoke test
  python scripts/test_llm_integration.py all           # Run all tests
  python scripts/test_llm_integration.py setup         # Create sample .env file

Environment Variables:
  OPENROUTER_API_KEY    Your OpenRouter API key (required for integration tests)
  PRIMARY_MODEL         Primary model to use (default: qwen/qwen3-30b-a3b:free)
  FALLBACK_MODEL        Fallback model (default: anthropic/claude-3-haiku)
        """
    )
    
    parser.add_argument(
        "command",
        choices=["unit", "integration", "api-key", "agents", "smoke", "all", "setup"],
        help="Test command to run"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Change to project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    print(f"🚀 LLM Integration Test Runner")
    print(f"📁 Working directory: {project_root}")
    
    if args.command == "setup":
        create_sample_env_file()
        return 0
    
    # Check if we're in the right directory
    if not Path("agents").exists():
        print("❌ Error: agents directory not found. Make sure you're in the project root.")
        return 1
    
    # Run the appropriate test command
    command_map = {
        "unit": run_unit_tests,
        "integration": run_integration_tests,
        "api-key": run_api_key_tests,
        "agents": run_agent_tests,
        "smoke": run_quick_smoke_test,
        "all": run_all_tests,
    }
    
    try:
        result = command_map[args.command]()
        
        if result == 0:
            print(f"\n✅ {args.command} tests completed successfully!")
        else:
            print(f"\n❌ {args.command} tests failed with exit code {result}")
        
        return result
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 