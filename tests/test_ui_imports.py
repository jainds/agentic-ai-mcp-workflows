#!/usr/bin/env python3
"""
UI Import Tests - Catch circular imports and missing dependencies
"""

import pytest
import sys
import os
import importlib
import importlib.util
from pathlib import Path
import traceback

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "ui"))

class TestUIImports:
    """Test suite for UI component imports"""
    
    def test_ui_components_individual_imports(self):
        """Test that each UI component can be imported individually"""
        components_dir = project_root / "ui" / "components"
        
        # List of component files to test
        component_files = [
            "config.py",
            "auth.py", 
            "agent_client.py",
            "chat.py",
            "monitoring.py",
            "thinking.py"
        ]
        
        for component_file in component_files:
            component_path = components_dir / component_file
            if not component_path.exists():
                pytest.skip(f"Component file {component_file} not found")
                
            module_name = component_file[:-3]  # Remove .py extension
            
            try:
                # Test individual import
                spec = importlib.util.spec_from_file_location(
                    f"ui.components.{module_name}", 
                    component_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                print(f"✅ Successfully imported {component_file}")
                
            except Exception as e:
                pytest.fail(f"Failed to import {component_file}: {str(e)}\n{traceback.format_exc()}")
    
    def test_ui_components_package_import(self):
        """Test that the UI components package can be imported as a whole"""
        try:
            # Test importing the components package
            from ui import components
            print("✅ Successfully imported ui.components package")
            
            # Test that key classes/functions are accessible
            assert hasattr(components, 'UIConfig'), "UIConfig not accessible from components package"
            assert hasattr(components, 'render_authentication'), "render_authentication not accessible"
            assert hasattr(components, 'render_chat_interface'), "render_chat_interface not accessible"
            
        except ImportError as e:
            pytest.fail(f"Failed to import ui.components package: {str(e)}\n{traceback.format_exc()}")
    
    def test_main_ui_import(self):
        """Test that the main UI can be imported"""
        try:
            # Test importing main_ui
            sys.path.insert(0, str(project_root / "ui"))
            import main_ui
            print("✅ Successfully imported main_ui")
            
        except Exception as e:
            pytest.fail(f"Failed to import main_ui: {str(e)}\n{traceback.format_exc()}")
    
    def test_streamlit_app_import(self):
        """Test that streamlit_app can be imported"""
        try:
            # Test importing streamlit_app
            sys.path.insert(0, str(project_root / "ui"))
            import streamlit_app
            print("✅ Successfully imported streamlit_app")
            
        except Exception as e:
            pytest.fail(f"Failed to import streamlit_app: {str(e)}\n{traceback.format_exc()}")
    
    def test_no_circular_imports(self):
        """Test for circular import issues"""
        components_dir = project_root / "ui" / "components"
        
        # Test each component for circular imports
        component_files = [
            "config.py",
            "auth.py",
            "agent_client.py", 
            "chat.py",
            "monitoring.py",
            "thinking.py"
        ]
        
        for component_file in component_files:
            component_path = components_dir / component_file
            if not component_path.exists():
                continue
                
            # Fresh import attempt
            module_name = f"test_circular_{component_file[:-3]}"
            
            try:
                spec = importlib.util.spec_from_file_location(module_name, component_path)
                module = importlib.util.module_from_spec(spec)
                
                # This should complete without hanging (circular imports cause hangs)
                spec.loader.exec_module(module)
                
                print(f"✅ No circular imports detected in {component_file}")
                
            except Exception as e:
                pytest.fail(f"Circular import or other issue in {component_file}: {str(e)}")
    
    def test_relative_imports_used(self):
        """Test that relative imports are used within components directory"""
        components_dir = project_root / "ui" / "components"
        
        for component_file in components_dir.glob("*.py"):
            if component_file.name == "__init__.py":
                continue
                
            content = component_file.read_text()
            
            # Check for problematic absolute imports
            problematic_patterns = [
                "from ui.components.",
                "import ui.components."
            ]
            
            for pattern in problematic_patterns:
                if pattern in content:
                    pytest.fail(
                        f"Found problematic absolute import in {component_file.name}: "
                        f"'{pattern}' should use relative imports instead"
                    )
        
        print("✅ All component files use proper relative imports")
    
    def test_required_dependencies_available(self):
        """Test that required dependencies are available"""
        required_packages = [
            "streamlit",
            "requests", 
            "typing"
        ]
        
        for package in required_packages:
            try:
                importlib.import_module(package)
                print(f"✅ Required package {package} is available")
            except ImportError:
                pytest.fail(f"Required package {package} is not available")
    
    def test_ui_config_accessibility(self):
        """Test that UIConfig can be imported and used"""
        try:
            from ui.components.config import UIConfig
            
            # Test that UIConfig has required attributes
            required_attrs = [
                'ADK_CUSTOMER_SERVICE_ENDPOINTS',
                'ADK_TECHNICAL_AGENT_ENDPOINTS',
                'ADK_ORCHESTRATOR_ENDPOINTS',
                'DEMO_CUSTOMERS',
                'MONITORED_SERVICES'
            ]
            
            for attr in required_attrs:
                assert hasattr(UIConfig, attr), f"UIConfig missing required attribute: {attr}"
            
            # Test that methods work
            assert callable(UIConfig.is_simple_mode), "UIConfig.is_simple_mode should be callable"
            assert callable(UIConfig.is_advanced_mode), "UIConfig.is_advanced_mode should be callable"
            
            print("✅ UIConfig is properly accessible and functional")
            
        except Exception as e:
            pytest.fail(f"UIConfig accessibility test failed: {str(e)}")

class TestStreamlitSpecific:
    """Streamlit-specific import tests"""
    
    def test_streamlit_imports_work(self):
        """Test that streamlit imports work correctly"""
        try:
            import streamlit as st
            print("✅ Streamlit import successful")
            
            # Test that we can access common streamlit functions
            assert hasattr(st, 'title'), "Streamlit missing title function"
            assert hasattr(st, 'sidebar'), "Streamlit missing sidebar"
            assert hasattr(st, 'session_state'), "Streamlit missing session_state"
            
        except ImportError as e:
            pytest.fail(f"Streamlit import failed: {str(e)}")
    
    def test_streamlit_components_can_be_mocked(self):
        """Test that streamlit components can be mocked for testing"""
        try:
            # Mock streamlit for testing
            import sys
            from unittest.mock import MagicMock
            
            # Create mock streamlit
            mock_st = MagicMock()
            mock_st.session_state = {}
            
            # Temporarily replace streamlit
            sys.modules['streamlit'] = mock_st
            
            # Now try importing UI components
            from ui.components.auth import CustomerValidator
            
            # Test that CustomerValidator works
            result = CustomerValidator.validate_customer("CUST001")
            assert isinstance(result, dict), "CustomerValidator should return dict"
            
            print("✅ Streamlit components can be mocked for testing")
            
        except Exception as e:
            pytest.fail(f"Streamlit mocking test failed: {str(e)}")
        
        finally:
            # Clean up - restore real streamlit if available
            if 'streamlit' in sys.modules:
                del sys.modules['streamlit']

if __name__ == "__main__":
    # Run the tests directly
    pytest.main([__file__, "-v"]) 