#!/usr/bin/env python3
"""
Authentication Component for Insurance AI UI
"""

import streamlit as st
from typing import Dict, Any
from .config import UIConfig

class CustomerValidator:
    """Handles customer authentication for demo purposes"""
    
    @classmethod
    def validate_customer(cls, customer_id: str) -> Dict[str, Any]:
        """Validate customer authentication"""
        if customer_id in UIConfig.DEMO_CUSTOMERS:
            return {
                "valid": True,
                "customer_data": {
                    "customer_id": customer_id,
                    **UIConfig.DEMO_CUSTOMERS[customer_id]
                }
            }
        return {"valid": False, "error": "Customer ID not found"}

def render_authentication():
    """Render authentication interface in sidebar"""
    with st.sidebar:
        st.header("🔐 Customer Authentication")
        
        # Mode toggle for advanced features
        if UIConfig.ENABLE_ADVANCED_FEATURES:
            st.markdown("---")
            current_mode = "Advanced" if UIConfig.is_advanced_mode() else "Simple"
            st.info(f"🎛️ UI Mode: {current_mode}")
            
            if st.button("🔄 Toggle UI Mode"):
                # This would require restart in real implementation
                st.info("Restart app with UI_MODE=simple or UI_MODE=advanced")
        
        if not st.session_state.authenticated:
            customer_id = st.text_input("Customer ID", placeholder="CUST-001")
            
            if st.button("Login", type="primary"):
                if customer_id:
                    auth_result = CustomerValidator.validate_customer(customer_id)
                    if auth_result["valid"]:
                        st.session_state.authenticated = True
                        st.session_state.customer_data = auth_result["customer_data"]
                        st.session_state.customer_id = customer_id
                        st.success(f"✅ Welcome, {auth_result['customer_data']['name']}")
                        st.rerun()
                    else:
                        st.error("❌ Authentication failed")
                else:
                    st.error("Please enter a Customer ID")
            
            # Show demo customer IDs
            with st.expander("Demo Customer IDs"):
                for cust_id, data in UIConfig.DEMO_CUSTOMERS.items():
                    st.code(f"{cust_id} - {data['name']}")
                    
        else:
            # Show authenticated user
            customer_data = st.session_state.customer_data
            st.success(f"✅ {customer_data['name']}")
            st.write(f"**Status:** {customer_data['status']}")
            st.write(f"**Type:** {customer_data['type']}")
            
            if st.button("Logout"):
                # Clear all session state
                for key in ['authenticated', 'customer_data', 'customer_id', 
                           'conversation_history', 'api_calls', 'thinking_steps', 
                           'orchestration_data']:
                    if key in st.session_state:
                        if isinstance(st.session_state[key], list):
                            st.session_state[key] = []
                        elif isinstance(st.session_state[key], bool):
                            st.session_state[key] = False
                        else:
                            st.session_state[key] = {}
                st.rerun()

def ensure_authentication() -> bool:
    """Ensure user is authenticated, return authentication status"""
    return st.session_state.get('authenticated', False) 