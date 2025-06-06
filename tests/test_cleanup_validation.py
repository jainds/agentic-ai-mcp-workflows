"""
Cleanup Validation Test

This test validates that the repository has been properly cleaned up
and only contains the essential components for deployment.
"""

import os
import pytest


class TestRepositoryCleanup:
    """Test that the repository cleanup was successful."""
    
    def test_essential_directories_exist(self):
        """Test that essential directories for the latest implementation exist."""
        essential_dirs = [
            "insurance-adk",
            "policy_server", 
            "monitoring",
            "k8s",
            ".github"
        ]
        
        for directory in essential_dirs:
            assert os.path.exists(directory), f"Essential directory {directory} missing"
    
    def test_old_directories_removed(self):
        """Test that old implementation directories have been removed."""
        old_dirs = [
            "agents",
            "domain_agent", 
            "technical_agent",
            "services",
            "scripts",
            "ui",
            "data",
            ".cleanup_backup",
            "htmlcov"
        ]
        
        for directory in old_dirs:
            assert not os.path.exists(directory), f"Old directory {directory} still exists"
    
    def test_insurance_adk_core_structure(self):
        """Test that the insurance-adk directory has core components."""
        adk_components = [
            "insurance-adk/server",
            "insurance-adk/config",
            "insurance-adk/tools",
            "insurance-adk/workflows",
            "insurance-adk/tests",
            "insurance-adk/README.md",
            "insurance-adk/requirements.txt"
        ]
        
        for component in adk_components:
            assert os.path.exists(component), f"ADK component {component} missing"
    
    def test_deployment_files_preserved(self):
        """Test that essential deployment files are preserved."""
        deployment_files = [
            "deploy.sh",
            "start_port_forwards.sh",
            "Dockerfile",
            "pyproject.toml",
            "requirements.txt",
            "README.md",
            ".env.example"
        ]
        
        for file in deployment_files:
            assert os.path.exists(file), f"Deployment file {file} missing"
    
    def test_requirements_contains_google_adk(self):
        """Test that requirements.txt contains Google ADK dependency."""
        with open("requirements.txt", "r") as f:
            content = f.read()
        
        assert "google-adk" in content, "Google ADK dependency missing from requirements.txt"
        assert "fastapi" in content, "FastAPI dependency missing"
        assert "langfuse" in content, "Langfuse monitoring missing"
    
    def test_readme_updated_for_adk(self):
        """Test that README reflects the ADK implementation."""
        with open("README.md", "r") as f:
            content = f.read()
        
        assert "Google ADK v1.0.0" in content, "README doesn't mention Google ADK"
        assert "insurance-adk" in content, "README doesn't reference ADK directory"
        assert "production-ready" in content.lower(), "README doesn't indicate production readiness"
    
    def test_monitoring_infrastructure_preserved(self):
        """Test that monitoring infrastructure is preserved."""
        monitoring_components = [
            "monitoring/README.md",
            "monitoring/providers",
            "monitoring/interfaces"
        ]
        
        for component in monitoring_components:
            assert os.path.exists(component), f"Monitoring component {component} missing"
    
    def test_deployment_infrastructure_preserved(self):
        """Test that deployment infrastructure is preserved."""
        deployment_components = [
            "k8s",
            ".github/workflows",
            "deploy.sh",
            "start_port_forwards.sh"
        ]
        
        for component in deployment_components:
            assert os.path.exists(component), f"Deployment component {component} missing"
    
    def test_policy_server_preserved(self):
        """Test that policy server (required for MCP) is preserved."""
        policy_components = [
            "policy_server",
            "policy_server/main.py"
        ]
        
        for component in policy_components:
            assert os.path.exists(component), f"Policy server component {component} missing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 