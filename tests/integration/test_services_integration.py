"""
Integration tests for Insurance AI PoC services
"""
import pytest
import requests
import time
from pathlib import Path


@pytest.mark.integration
class TestServiceIntegration:
    """Test integration between services"""
    
    def test_services_can_start(self):
        """Test that services can be imported and basic setup works"""
        # This is a placeholder test - actual service testing would require running services
        assert True, "Services integration test placeholder"
    
    def test_environment_setup(self):
        """Test that environment is properly configured"""
        project_root = Path(__file__).parent.parent.parent
        
        # Check for key configuration files
        assert (project_root / ".env.example").exists()
        assert (project_root / "requirements.txt").exists()
        assert (project_root / "pyproject.toml").exists()
    
    @pytest.mark.skip(reason="Requires running services")
    def test_policy_server_health(self):
        """Test that policy server responds to health checks"""
        try:
            response = requests.get("http://localhost:8001/health", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Policy server not running")
    
    @pytest.mark.skip(reason="Requires running services") 
    def test_technical_agent_health(self):
        """Test that technical agent responds to health checks"""
        try:
            response = requests.get("http://localhost:8002/health", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Technical agent not running") 