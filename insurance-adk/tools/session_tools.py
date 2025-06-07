"""
ADK-Compatible Session Management Tools
Migrated from existing session management system
"""
import uuid
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta


class SessionManager:
    """Session management for ADK system - direct migration from current system"""
    
    def __init__(self):
        self.name = "session_manager"
        self.description = "Manage customer sessions - migrated from current system"
        # Use same session storage as current system
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    def create_session(self, customer_id: Optional[str] = None) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "customer_id": customer_id,
            "authenticated": customer_id is not None,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "conversation_history": [],
            "preferences": {},
            "context": {}
        }
        
        self.sessions[session_id] = session_data
        self.logger.info(f"Created session {session_id} for customer {customer_id}")
        return session_id
    
    def get_session_data(self, session_id: str) -> Dict[str, Any]:
        """Get session data - same as current system"""
        if session_id not in self.sessions:
            # Create default session if not exists
            return {
                "session_id": session_id,
                "authenticated": False,
                "customer_id": None,
                "conversation_history": [],
                "preferences": {},
                "context": {},
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }
        
        # Update last activity
        self.sessions[session_id]["last_activity"] = datetime.now().isoformat()
        return self.sessions[session_id]
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session - same as current system"""
        try:
            if session_id not in self.sessions:
                self.sessions[session_id] = self.get_session_data(session_id)
            
            self.sessions[session_id].update(updates)
            self.sessions[session_id]["last_activity"] = datetime.now().isoformat()
            
            self.logger.debug(f"Updated session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating session {session_id}: {str(e)}")
            return False
    
    def authenticate_customer(self, session_id: str, customer_id: str) -> bool:
        """Authenticate customer - current system logic"""
        try:
            # Same authentication logic as current system
            self.update_session(session_id, {
                "authenticated": True,
                "customer_id": customer_id,
                "authenticated_at": datetime.now().isoformat()
            })
            
            self.logger.info(f"Authenticated customer {customer_id} in session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication error for session {session_id}: {str(e)}")
            return False
    
    def add_conversation_entry(self, session_id: str, message: str, response: str, intent: str = None) -> bool:
        """Add conversation entry to session history"""
        try:
            session_data = self.get_session_data(session_id)
            
            conversation_entry = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "response": response,
                "intent": intent
            }
            
            session_data["conversation_history"].append(conversation_entry)
            self.update_session(session_id, {"conversation_history": session_data["conversation_history"]})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding conversation entry: {str(e)}")
            return False
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for session"""
        session_data = self.get_session_data(session_id)
        history = session_data.get("conversation_history", [])
        
        # Return most recent entries
        return history[-limit:] if len(history) > limit else history
    
    def validate_session(self, session_id: str) -> bool:
        """Validate session data"""
        if not session_id:
            return False
        
        session_data = self.get_session_data(session_id)
        
        # Check if session is expired (24 hours)
        try:
            last_activity = datetime.fromisoformat(session_data.get("last_activity", ""))
            if datetime.now() - last_activity > timedelta(hours=24):
                self.logger.warning(f"Session {session_id} expired")
                return False
        except:
            pass
        
        return True
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session_data in self.sessions.items():
            try:
                last_activity = datetime.fromisoformat(session_data.get("last_activity", ""))
                if current_time - last_activity > timedelta(hours=24):
                    expired_sessions.append(session_id)
            except:
                expired_sessions.append(session_id)  # Invalid timestamp
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            self.logger.info(f"Cleaned up expired session: {session_id}")
        
        return len(expired_sessions)
    
    def get_customer_context(self, session_id: str) -> Dict[str, Any]:
        """Extract customer context from session"""
        session_data = self.get_session_data(session_id)
        
        return {
            "customer_id": session_data.get("customer_id"),
            "authenticated": session_data.get("authenticated", False),
            "preferences": session_data.get("preferences", {}),
            "last_activity": session_data.get("last_activity"),
            "conversation_count": len(session_data.get("conversation_history", [])),
            "session_duration": self._calculate_session_duration(session_data)
        }
    
    def _calculate_session_duration(self, session_data: Dict[str, Any]) -> Optional[str]:
        """Calculate session duration"""
        try:
            created_at = datetime.fromisoformat(session_data.get("created_at", ""))
            current_time = datetime.now()
            duration = current_time - created_at
            
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            return f"{hours:02d}:{minutes:02d}"
        except:
            return None


class AuthenticationManager:
    """Authentication manager for customer verification"""
    
    def __init__(self):
        self.name = "authentication_manager"
        self.description = "Handle customer authentication"
        self.logger = logging.getLogger(__name__)
    
    async def verify_customer(self, customer_id: str, verification_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Verify customer identity"""
        # Simplified verification for demo purposes
        # In production, this would integrate with identity provider
        
        if not customer_id:
            return {
                "success": False,
                "error": "Customer ID required",
                "authenticated": False
            }
        
        # Basic validation - customer ID should be numeric or valid format
        try:
            if customer_id.isdigit() or customer_id.startswith("CUST"):
                return {
                    "success": True,
                    "authenticated": True,
                    "customer_id": customer_id,
                    "verification_method": "customer_id",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid customer ID format",
                    "authenticated": False
                }
                
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return {
                "success": False,
                "error": "Authentication system error",
                "authenticated": False
            }
    
    async def check_authorization(self, customer_id: str, resource: str) -> bool:
        """Check if customer is authorized to access resource"""
        # Simplified authorization - in production would check permissions
        if not customer_id:
            return False
        
        # For demo purposes, all authenticated customers can access basic resources
        allowed_resources = ["policies", "payments", "coverage", "agent", "deductibles"]
        return resource in allowed_resources


# Factory functions
def create_session_manager() -> SessionManager:
    """Create session manager instance"""
    return SessionManager()


def create_auth_manager() -> AuthenticationManager:
    """Create authentication manager instance"""
    return AuthenticationManager() 