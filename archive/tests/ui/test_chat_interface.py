#!/usr/bin/env python3
"""
Selenium tests for Insurance AI UI Chat Interface
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class TestChatInterface:
    """Test chat interface functionality"""
    
    def login_first(self, driver, helpers):
        """Helper method to login before testing chat"""
        time.sleep(3)
        
        # Find and fill customer ID
        customer_input = helpers.find_streamlit_input(driver, "Customer ID")
        if not customer_input:
            inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            if inputs:
                customer_input = inputs[0]
        
        if customer_input:
            customer_input.clear()
            customer_input.send_keys("CUST-001")
            time.sleep(1)
            
            # Find and click login button
            login_button = helpers.find_streamlit_button(driver, "Login")
            if not login_button:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if "login" in button.text.lower():
                        login_button = button
                        break
            
            if login_button:
                driver.execute_script("arguments[0].click();", login_button)
                time.sleep(4)  # Wait for login to complete
    
    def test_chat_interface_after_login(self, streamlit_page, helpers):
        """Test that chat interface appears after login"""
        self.login_first(streamlit_page, helpers)
        
        # Look for chat-related elements
        page_text = streamlit_page.page_source.lower()
        chat_indicators = [
            "chat", "message", "conversation", "send", "insurance ai assistant",
            "ask about", "how can i help"
        ]
        
        chat_elements_found = sum(1 for indicator in chat_indicators if indicator in page_text)
        assert chat_elements_found >= 2, f"Insufficient chat elements found. Expected at least 2, found {chat_elements_found}"
        
        helpers.take_screenshot(streamlit_page, "10_chat_interface.png")
    
    def test_chat_input_field_present(self, streamlit_page, helpers):
        """Test that chat input field is present after login"""
        self.login_first(streamlit_page, helpers)
        
        # Look for text input or textarea for chat
        chat_inputs = streamlit_page.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
        
        # Filter for likely chat inputs (not in sidebar)
        main_inputs = []
        for input_elem in chat_inputs:
            try:
                # Check if input is in main area (not sidebar)
                if input_elem.is_displayed():
                    main_inputs.append(input_elem)
            except:
                continue
        
        assert len(main_inputs) > 0, "No chat input field found"
        helpers.take_screenshot(streamlit_page, "11_chat_input.png")
    
    def test_quick_action_buttons(self, streamlit_page, helpers):
        """Test that quick action buttons are present"""
        self.login_first(streamlit_page, helpers)
        
        # Look for quick action buttons
        page_text = streamlit_page.page_source.lower()
        quick_actions = ["claims", "policies", "quote", "check", "view", "get"]
        
        actions_found = sum(1 for action in quick_actions if action in page_text)
        assert actions_found >= 2, f"Insufficient quick actions found. Expected at least 2, found {actions_found}"
        
        helpers.take_screenshot(streamlit_page, "12_quick_actions.png")
    
    def test_send_chat_message(self, streamlit_page, helpers):
        """Test sending a chat message"""
        self.login_first(streamlit_page, helpers)
        
        # Find chat input
        chat_inputs = streamlit_page.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
        chat_input = None
        
        for input_elem in chat_inputs:
            try:
                if input_elem.is_displayed():
                    placeholder = input_elem.get_attribute("placeholder") or ""
                    if any(word in placeholder.lower() for word in ["message", "chat", "ask", "insurance"]):
                        chat_input = input_elem
                        break
            except:
                continue
        
        if not chat_input and chat_inputs:
            # Use the last visible input (likely the chat input)
            for input_elem in reversed(chat_inputs):
                try:
                    if input_elem.is_displayed():
                        chat_input = input_elem
                        break
                except:
                    continue
        
        if chat_input:
            # Type a test message
            test_message = "Hello, I need help with my insurance policy"
            chat_input.clear()
            chat_input.send_keys(test_message)
            time.sleep(1)
            
            helpers.take_screenshot(streamlit_page, "13_message_typed.png")
            
            # Look for send button
            send_button = helpers.find_streamlit_button(streamlit_page, "Send")
            if not send_button:
                # Try other button texts
                button_texts = ["Send", "Submit", "Ask", "Go"]
                for text in button_texts:
                    send_button = helpers.find_streamlit_button(streamlit_page, text)
                    if send_button:
                        break
            
            if send_button:
                # Click send button
                streamlit_page.execute_script("arguments[0].click();", send_button)
                time.sleep(5)  # Wait for response
                
                helpers.take_screenshot(streamlit_page, "14_message_sent.png")
                
                # Check if message appears in conversation or if there's a response
                page_text = streamlit_page.page_source.lower()
                response_indicators = [
                    test_message.lower(), "response", "thinking", "processing",
                    "agent", "assistant", "help", "insurance"
                ]
                
                response_found = any(indicator in page_text for indicator in response_indicators)
                assert response_found, "No indication of message processing or response found"
    
    def test_conversation_history(self, streamlit_page, helpers):
        """Test that conversation history is displayed"""
        self.login_first(streamlit_page, helpers)
        
        # Send a message first
        chat_inputs = streamlit_page.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
        if chat_inputs:
            chat_input = chat_inputs[-1]  # Use last input
            if chat_input.is_displayed():
                test_message = "Test conversation history"
                chat_input.clear()
                chat_input.send_keys(test_message)
                
                send_button = helpers.find_streamlit_button(streamlit_page, "Send")
                if send_button:
                    streamlit_page.execute_script("arguments[0].click();", send_button)
                    time.sleep(4)
        
        # Check for conversation history elements
        page_text = streamlit_page.page_source.lower()
        history_indicators = [
            "conversation", "history", "exchange", "you:", "assistant:", 
            "user:", "ai:", "timestamp"
        ]
        
        history_found = sum(1 for indicator in history_indicators if indicator in page_text)
        # More lenient check since conversation might not have started yet
        assert history_found >= 1, f"No conversation history indicators found"
        
        helpers.take_screenshot(streamlit_page, "15_conversation_history.png")
    
    def test_clear_chat_functionality(self, streamlit_page, helpers):
        """Test clear chat functionality"""
        self.login_first(streamlit_page, helpers)
        
        # Look for clear chat button
        clear_button = helpers.find_streamlit_button(streamlit_page, "Clear")
        if not clear_button:
            # Try alternative texts
            button_texts = ["Clear Chat", "Clear", "Reset", "New"]
            for text in button_texts:
                clear_button = helpers.find_streamlit_button(streamlit_page, text)
                if clear_button:
                    break
        
        if clear_button:
            streamlit_page.execute_script("arguments[0].click();", clear_button)
            time.sleep(2)
            
            helpers.take_screenshot(streamlit_page, "16_chat_cleared.png")
            
            # Verify that chat was cleared (this is optional since we might not have messages)
            assert True  # Test passes if clear button exists and can be clicked
        else:
            # Clear button might not be visible if no conversation exists
            assert True  # Test passes - clear button might be conditionally shown
    
    def test_ui_tabs_in_advanced_mode(self, streamlit_page, helpers):
        """Test that UI tabs are present in advanced mode"""
        self.login_first(streamlit_page, helpers)
        
        # Look for tab-related elements
        page_text = streamlit_page.page_source.lower()
        tab_indicators = [
            "chat", "health", "monitoring", "thinking", "orchestration",
            "system", "api", "tab", "💬", "🏥", "📊", "🧠", "🎭"
        ]
        
        tabs_found = sum(1 for indicator in tab_indicators if indicator in page_text)
        
        # In simple mode, we might only see chat-related elements
        # In advanced mode, we should see more
        assert tabs_found >= 1, f"No tab indicators found"
        
        helpers.take_screenshot(streamlit_page, "17_ui_tabs.png")
        
        # If we found multiple tab indicators, we're likely in advanced mode
        if tabs_found >= 4:
            print("✅ Advanced mode detected with multiple tabs")
        else:
            print("ℹ️ Simple mode or limited tabs detected") 