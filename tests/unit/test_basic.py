"""
Basic unit tests for Insurance AI PoC
"""
import pytest
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_python_version():
    """Test that we're running on a supported Python version"""
    assert sys.version_info >= (3, 11), "Python 3.11+ required"


def test_project_structure():
    """Test that key project directories exist"""
    assert (project_root / "policy_server").exists(), "policy_server directory missing"
    assert (project_root / "insurance-adk").exists(), "insurance-adk directory missing"
    assert (project_root / "requirements.txt").exists(), "requirements.txt missing"


def test_basic_imports():
    """Test that basic Python imports work"""
    import json
    import os
    import sys
    
    # Test that we can import standard library modules
    assert json.loads('{"test": true}')["test"] is True
    assert os.path.exists(str(project_root))


def test_env_file_exists():
    """Test that environment files exist"""
    env_example = project_root / ".env.example"
    assert env_example.exists(), ".env.example file missing"


class TestBasicFunctionality:
    """Test basic functionality"""
    
    def test_can_create_directory(self, tmp_path):
        """Test that we can create directories (filesystem permissions)"""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        assert test_dir.exists()
    
    def test_can_write_file(self, tmp_path):
        """Test that we can write files"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        assert test_file.read_text() == "test content" 