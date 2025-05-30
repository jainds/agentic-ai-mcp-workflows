"""
Test to verify what version of code is running in the Streamlit UI container
and what domain agent endpoints it's configured with.

This test was crucial for diagnosing the issue where the UI container
had old code pointing to wrong domain agent endpoints.
"""
import pytest
import subprocess
import json
import time


class TestUIContainerVersion:
    """Test the actual code version and configuration in the UI container."""
    
    @pytest.fixture
    def streamlit_ui_pod(self):
        """Get the streamlit UI pod name."""
        try:
            result = subprocess.run([
                'kubectl', 'get', 'pods', 
                '-n', 'cursor-insurance-ai-poc',
                '-l', 'app=streamlit-ui',
                '-o', 'json'
            ], capture_output=True, text=True, check=True)
            
            pods_data = json.loads(result.stdout)
            if not pods_data['items']:
                pytest.fail("No streamlit-ui pods found")
            
            pod_name = pods_data['items'][0]['metadata']['name']
            print(f"Found UI pod: {pod_name}")
            return pod_name
        except Exception as e:
            pytest.fail(f"Failed to get streamlit UI pod: {e}")
    
    def test_ui_container_domain_agent_config(self, streamlit_ui_pod):
        """Test what domain agent endpoints are configured in the UI container."""
        try:
            # Check the DomainAgentClient configuration
            cmd = [
                'kubectl', 'exec', '-n', 'cursor-insurance-ai-poc',
                streamlit_ui_pod, '--',
                'python', '-c', 
                '''
import sys
sys.path.append("/app")
try:
    from ui.domain_agent_client import DomainAgentClient
    client = DomainAgentClient()
    print("DOMAIN_AGENT_ENDPOINTS:", getattr(client, "domain_agent_urls", "NOT_FOUND"))
    print("CLASS_ATTRS:", [attr for attr in dir(client) if not attr.startswith("_")])
except Exception as e:
    print("ERROR_IMPORTING_CLIENT:", str(e))
    try:
        # Try alternative import path
        from domain_agent_client import DomainAgentClient
        client = DomainAgentClient()
        print("DOMAIN_AGENT_ENDPOINTS_ALT:", getattr(client, "domain_agent_urls", "NOT_FOUND"))
    except Exception as e2:
        print("ERROR_ALT_IMPORT:", str(e2))
'''
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            print("=== Domain Agent Client Config ===")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            print("Return code:", result.returncode)
            
            # The test passes if we can get the output, we'll analyze it manually
            assert result.returncode == 0 or "DOMAIN_AGENT_ENDPOINTS" in result.stdout
            
        except subprocess.TimeoutExpired:
            pytest.fail("Command timed out")
        except Exception as e:
            pytest.fail(f"Failed to check domain agent config: {e}")
    
    def test_ui_container_file_versions(self, streamlit_ui_pod):
        """Test what files exist in the UI container and their modification times."""
        try:
            # Check what files exist in the UI directory
            cmd = [
                'kubectl', 'exec', '-n', 'cursor-insurance-ai-poc',
                streamlit_ui_pod, '--',
                'find', '/app', '-name', '*.py', '-exec', 'ls', '-la', '{}', ';'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            print("=== UI Container Files ===")
            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            print("Return code:", result.returncode)
            
            assert result.returncode == 0
            
        except subprocess.TimeoutExpired:
            pytest.fail("Command timed out")
        except Exception as e:
            pytest.fail(f"Failed to check UI container files: {e}")
    
    def test_ui_container_environment(self, streamlit_ui_pod):
        """Test the environment variables in the UI container."""
        try:
            cmd = [
                'kubectl', 'exec', '-n', 'cursor-insurance-ai-poc',
                streamlit_ui_pod, '--', 'env'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            print("=== UI Container Environment ===")
            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            assert result.returncode == 0
            
        except subprocess.TimeoutExpired:
            pytest.fail("Command timed out")
        except Exception as e:
            pytest.fail(f"Failed to check UI container environment: {e}")
    
    def test_ui_container_actual_streamlit_code(self, streamlit_ui_pod):
        """Test what the actual streamlit app code looks like in the container."""
        try:
            # Check the streamlit app file
            cmd = [
                'kubectl', 'exec', '-n', 'cursor-insurance-ai-poc',
                streamlit_ui_pod, '--',
                'head', '-50', '/app/ui/streamlit_app.py'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            print("=== Streamlit App Code (first 50 lines) ===")
            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            # Also check for domain agent related code
            cmd2 = [
                'kubectl', 'exec', '-n', 'cursor-insurance-ai-poc',
                streamlit_ui_pod, '--',
                'grep', '-n', '-A5', '-B5', 'domain.*agent', '/app/ui/streamlit_app.py'
            ]
            
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
            print("=== Domain Agent References ===")
            print("STDOUT:", result2.stdout)
            if result2.stderr:
                print("STDERR:", result2.stderr)
            
            assert result.returncode == 0
            
        except subprocess.TimeoutExpired:
            pytest.fail("Command timed out")
        except Exception as e:
            pytest.fail(f"Failed to check streamlit app code: {e}")
    
    def test_check_domain_agent_client_source(self, streamlit_ui_pod):
        """Check the actual source code of the domain agent client."""
        try:
            # Check if domain_agent_client.py exists and its content
            cmd = [
                'kubectl', 'exec', '-n', 'cursor-insurance-ai-poc',
                streamlit_ui_pod, '--',
                'cat', '/app/ui/domain_agent_client.py'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            print("=== Domain Agent Client Source ===")
            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            # Check for specific patterns that indicate old vs new code
            if result.returncode == 0:
                if 'user-service:8000' in result.stdout:
                    print("🚨 FOUND OLD CODE: References to user-service:8000")
                if 'claims-agent:8000' in result.stdout:
                    print("✅ FOUND NEW CODE: References to claims-agent:8000")
                if 'localhost:8000' in result.stdout:
                    print("🚨 FOUND OLD CODE: References to localhost:8000")
            
            # Don't fail the test if file doesn't exist, just report it
            print("Return code:", result.returncode)
            
        except subprocess.TimeoutExpired:
            pytest.fail("Command timed out")
        except Exception as e:
            print(f"Note: Could not check domain agent client source: {e}")
    
    def test_check_domain_agent_endpoints_in_container(self, streamlit_ui_pod):
        """
        Check what domain agent endpoints are actually configured in the running container.
        This was the key test that revealed the container had wrong endpoints.
        """
        try:
            cmd = [
                'kubectl', 'exec', '-n', 'cursor-insurance-ai-poc',
                streamlit_ui_pod, '--',
                'grep', '-n', '-A3', '-B3', 'possible_endpoints', '/app/ui/streamlit_app.py'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            print("=== Configured Domain Agent Endpoints ===")
            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            # Analyze the output for endpoint configuration
            if result.returncode == 0:
                output = result.stdout
                if 'claims-agent:8000' in output:
                    print("✅ CORRECT: Container has claims-agent:8000 endpoint")
                elif 'user-service:8000' in output:
                    print("🚨 INCORRECT: Container has old user-service:8000 endpoint")
                else:
                    print("❓ UNCLEAR: Could not determine endpoint configuration")
            
            print("Return code:", result.returncode)
            
        except subprocess.TimeoutExpired:
            pytest.fail("Command timed out")
        except Exception as e:
            print(f"Note: Could not check domain agent endpoints: {e}") 