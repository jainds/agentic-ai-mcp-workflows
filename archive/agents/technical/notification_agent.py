"""
Notification Agent - Technical agent providing MCP tools for notifications and communications.
Handles email, SMS, webhooks, and other notification mechanisms.
"""

import os
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from agents.shared.mcp_base import MCPServer, MCPToolDef
import structlog

logger = structlog.get_logger(__name__)


class NotificationAgent(MCPServer):
    """Technical agent providing notification and communication tools via MCP"""
    
    def __init__(self, port: int = 8003):
        super().__init__(
            name="NotificationAgent",
            description="MCP server providing notification and communication tools",
            port=port
        )
        
        # Notification state
        self.notification_queue: List[Dict[str, Any]] = []
        self.sent_notifications: List[Dict[str, Any]] = []
        self.delivery_settings = {
            "email_enabled": True,
            "sms_enabled": True,
            "webhook_enabled": True,
            "retry_attempts": 3,
            "retry_delay": 30  # seconds
        }
        
        logger.info("Notification Agent initialized", port=port)
    
    def setup_tools_and_resources(self):
        """Setup notification-specific MCP tools"""
        
        # Email notification tool
        email_tool = MCPToolDef(
            name="send_email",
            description="Send email notifications to users or teams",
            handler=self._send_email,
            parameters={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body content"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
                    "notification_type": {"type": "string", "description": "Type of notification"}
                },
                "required": ["to", "subject", "body"]
            }
        )
        self.add_tool(email_tool)
        
        # SMS notification tool
        sms_tool = MCPToolDef(
            name="send_sms",
            description="Send SMS notifications to mobile numbers",
            handler=self._send_sms,
            parameters={
                "type": "object",
                "properties": {
                    "phone": {"type": "string", "description": "Phone number with country code"},
                    "message": {"type": "string", "description": "SMS message content (max 160 chars)"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"}
                },
                "required": ["phone", "message"]
            }
        )
        self.add_tool(sms_tool)
        
        # Webhook notification tool
        webhook_tool = MCPToolDef(
            name="send_webhook",
            description="Send webhook notifications to external systems",
            handler=self._send_webhook,
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Webhook URL"},
                    "payload": {"type": "object", "description": "JSON payload to send"},
                    "headers": {"type": "object", "description": "Additional HTTP headers"},
                    "method": {"type": "string", "enum": ["POST", "PUT"], "default": "POST"}
                },
                "required": ["url", "payload"]
            }
        )
        self.add_tool(webhook_tool)
        
        # Bulk notification tool
        bulk_notification_tool = MCPToolDef(
            name="send_bulk_notification",
            description="Send notifications to multiple recipients",
            handler=self._send_bulk_notification,
            parameters={
                "type": "object",
                "properties": {
                    "notification_type": {"type": "string", "enum": ["email", "sms", "webhook"]},
                    "recipients": {"type": "array", "items": {"type": "string"}},
                    "message": {"type": "string", "description": "Message content"},
                    "subject": {"type": "string", "description": "Subject (for email)"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"}
                },
                "required": ["notification_type", "recipients", "message"]
            }
        )
        self.add_tool(bulk_notification_tool)
        
        # Notification status tool
        status_tool = MCPToolDef(
            name="get_notification_status",
            description="Get status of sent notifications",
            handler=self._get_notification_status,
            parameters={
                "type": "object",
                "properties": {
                    "notification_id": {"type": "string", "description": "Specific notification ID"},
                    "limit": {"type": "integer", "description": "Number of recent notifications", "default": 10}
                }
            }
        )
        self.add_tool(status_tool)
        
        # Alert tools
        alert_tool = MCPToolDef(
            name="send_alert",
            description="Send high-priority alerts to operations teams",
            handler=self._send_alert,
            parameters={
                "type": "object",
                "properties": {
                    "alert_type": {"type": "string", "enum": ["fraud", "system", "security", "business"]},
                    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "message": {"type": "string", "description": "Alert message"},
                    "details": {"type": "object", "description": "Additional alert details"},
                    "escalation_path": {"type": "array", "items": {"type": "string"}, "description": "Escalation contacts"}
                },
                "required": ["alert_type", "severity", "message"]
            }
        )
        self.add_tool(alert_tool)
        
        # Template-based notification tool
        template_tool = MCPToolDef(
            name="send_template_notification",
            description="Send notifications using predefined templates",
            handler=self._send_template_notification,
            parameters={
                "type": "object",
                "properties": {
                    "template_name": {"type": "string", "description": "Template identifier"},
                    "recipients": {"type": "array", "items": {"type": "string"}},
                    "variables": {"type": "object", "description": "Template variables"},
                    "delivery_method": {"type": "string", "enum": ["email", "sms", "both"], "default": "email"}
                },
                "required": ["template_name", "recipients", "variables"]
            }
        )
        self.add_tool(template_tool)
    
    async def _send_email(self, to: str, subject: str, body: str, priority: str = "medium", notification_type: str = "general") -> Dict[str, Any]:
        """Send email notification"""
        notification_id = f"email_{datetime.utcnow().timestamp()}"
        
        notification = {
            "id": notification_id,
            "type": "email",
            "to": to,
            "subject": subject,
            "body": body,
            "priority": priority,
            "notification_type": notification_type,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "attempts": 0
        }
        
        self.notification_queue.append(notification)
        
        try:
            # Simulate email sending (integrate with actual email service)
            await self._simulate_email_delivery(notification)
            
            notification["status"] = "sent"
            notification["sent_at"] = datetime.utcnow().isoformat()
            self.sent_notifications.append(notification)
            
            logger.info("Email sent successfully", notification_id=notification_id, to=to, subject=subject)
            
            return {
                "notification_id": notification_id,
                "status": "sent",
                "message": f"Email sent to {to}",
                "sent_at": notification["sent_at"]
            }
            
        except Exception as e:
            notification["status"] = "failed"
            notification["error"] = str(e)
            logger.error("Email sending failed", notification_id=notification_id, error=str(e))
            
            return {
                "notification_id": notification_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def _send_sms(self, phone: str, message: str, priority: str = "medium") -> Dict[str, Any]:
        """Send SMS notification"""
        notification_id = f"sms_{datetime.utcnow().timestamp()}"
        
        # Validate message length
        if len(message) > 160:
            return {
                "notification_id": notification_id,
                "status": "failed",
                "error": "SMS message exceeds 160 character limit"
            }
        
        notification = {
            "id": notification_id,
            "type": "sms",
            "phone": phone,
            "message": message,
            "priority": priority,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "attempts": 0
        }
        
        self.notification_queue.append(notification)
        
        try:
            # Simulate SMS sending (integrate with SMS service like Twilio)
            await self._simulate_sms_delivery(notification)
            
            notification["status"] = "sent"
            notification["sent_at"] = datetime.utcnow().isoformat()
            self.sent_notifications.append(notification)
            
            logger.info("SMS sent successfully", notification_id=notification_id, phone=phone)
            
            return {
                "notification_id": notification_id,
                "status": "sent",
                "message": f"SMS sent to {phone}",
                "sent_at": notification["sent_at"]
            }
            
        except Exception as e:
            notification["status"] = "failed"
            notification["error"] = str(e)
            logger.error("SMS sending failed", notification_id=notification_id, error=str(e))
            
            return {
                "notification_id": notification_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def _send_webhook(self, url: str, payload: Dict[str, Any], headers: Dict[str, str] = None, method: str = "POST") -> Dict[str, Any]:
        """Send webhook notification"""
        notification_id = f"webhook_{datetime.utcnow().timestamp()}"
        
        notification = {
            "id": notification_id,
            "type": "webhook",
            "url": url,
            "payload": payload,
            "headers": headers or {},
            "method": method,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "attempts": 0
        }
        
        self.notification_queue.append(notification)
        
        try:
            # Simulate webhook sending (integrate with httpx for actual HTTP calls)
            await self._simulate_webhook_delivery(notification)
            
            notification["status"] = "sent"
            notification["sent_at"] = datetime.utcnow().isoformat()
            self.sent_notifications.append(notification)
            
            logger.info("Webhook sent successfully", notification_id=notification_id, url=url)
            
            return {
                "notification_id": notification_id,
                "status": "sent",
                "message": f"Webhook sent to {url}",
                "sent_at": notification["sent_at"]
            }
            
        except Exception as e:
            notification["status"] = "failed"
            notification["error"] = str(e)
            logger.error("Webhook sending failed", notification_id=notification_id, error=str(e))
            
            return {
                "notification_id": notification_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def _send_bulk_notification(self, notification_type: str, recipients: List[str], message: str, subject: str = None, priority: str = "medium") -> Dict[str, Any]:
        """Send bulk notifications to multiple recipients"""
        bulk_id = f"bulk_{datetime.utcnow().timestamp()}"
        results = []
        
        for recipient in recipients:
            try:
                if notification_type == "email":
                    if not subject:
                        subject = "Notification"
                    result = await self._send_email(recipient, subject, message, priority)
                elif notification_type == "sms":
                    result = await self._send_sms(recipient, message, priority)
                elif notification_type == "webhook":
                    result = await self._send_webhook(recipient, {"message": message}, method="POST")
                else:
                    result = {"status": "failed", "error": f"Unsupported notification type: {notification_type}"}
                
                results.append({"recipient": recipient, "result": result})
                
            except Exception as e:
                results.append({"recipient": recipient, "result": {"status": "failed", "error": str(e)}})
        
        # Summary statistics
        sent_count = sum(1 for r in results if r["result"]["status"] == "sent")
        failed_count = len(results) - sent_count
        
        logger.info("Bulk notification completed", bulk_id=bulk_id, sent=sent_count, failed=failed_count)
        
        return {
            "bulk_id": bulk_id,
            "total_recipients": len(recipients),
            "sent_count": sent_count,
            "failed_count": failed_count,
            "results": results
        }
    
    async def _get_notification_status(self, notification_id: str = None, limit: int = 10) -> Dict[str, Any]:
        """Get notification status"""
        if notification_id:
            # Find specific notification
            for notification in self.sent_notifications + self.notification_queue:
                if notification["id"] == notification_id:
                    return notification
            return {"error": f"Notification {notification_id} not found"}
        else:
            # Return recent notifications
            recent = sorted(
                self.sent_notifications + self.notification_queue,
                key=lambda x: x["created_at"],
                reverse=True
            )[:limit]
            
            return {
                "recent_notifications": recent,
                "total_sent": len(self.sent_notifications),
                "queue_size": len(self.notification_queue)
            }
    
    async def _send_alert(self, alert_type: str, severity: str, message: str, details: Dict[str, Any] = None, escalation_path: List[str] = None) -> Dict[str, Any]:
        """Send high-priority alert"""
        alert_id = f"alert_{datetime.utcnow().timestamp()}"
        
        alert = {
            "id": alert_id,
            "type": alert_type,
            "severity": severity,
            "message": message,
            "details": details or {},
            "escalation_path": escalation_path or [],
            "status": "active",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Determine notification channels based on severity
        if severity == "critical":
            # Send immediate notifications via multiple channels
            notifications = []
            
            # Email alerts
            for contact in escalation_path or ["ops@insurance.com"]:
                email_result = await self._send_email(
                    contact,
                    f"CRITICAL ALERT: {alert_type.upper()}",
                    f"Alert: {message}\n\nDetails: {details}\n\nAlert ID: {alert_id}",
                    priority="high",
                    notification_type="alert"
                )
                notifications.append(email_result)
            
            # SMS for critical alerts
            ops_phone = os.getenv("OPS_PHONE", "+1234567890")
            sms_result = await self._send_sms(
                ops_phone,
                f"CRITICAL: {message[:100]}... Alert ID: {alert_id}",
                priority="high"
            )
            notifications.append(sms_result)
            
        elif severity == "high":
            # Email notifications
            notifications = []
            for contact in escalation_path or ["ops@insurance.com"]:
                email_result = await self._send_email(
                    contact,
                    f"HIGH ALERT: {alert_type.upper()}",
                    f"Alert: {message}\n\nDetails: {details}\n\nAlert ID: {alert_id}",
                    priority="high",
                    notification_type="alert"
                )
                notifications.append(email_result)
        else:
            # Standard email notification
            email_result = await self._send_email(
                escalation_path[0] if escalation_path else "ops@insurance.com",
                f"Alert: {alert_type.upper()}",
                f"Alert: {message}\n\nDetails: {details}\n\nAlert ID: {alert_id}",
                priority="medium",
                notification_type="alert"
            )
            notifications = [email_result]
        
        logger.info("Alert sent", alert_id=alert_id, severity=severity, type=alert_type)
        
        return {
            "alert_id": alert_id,
            "status": "sent",
            "notifications": notifications,
            "created_at": alert["created_at"]
        }
    
    async def _send_template_notification(self, template_name: str, recipients: List[str], variables: Dict[str, Any], delivery_method: str = "email") -> Dict[str, Any]:
        """Send notifications using predefined templates"""
        
        # Template registry (in production, store in database)
        templates = {
            "claim_approved": {
                "subject": "Claim {claim_id} Approved",
                "email_body": "Dear {customer_name},\n\nYour claim {claim_id} has been approved for ${amount}.\n\nBest regards,\nInsurance Team",
                "sms_body": "Claim {claim_id} approved for ${amount}. Payment processing."
            },
            "claim_rejected": {
                "subject": "Claim {claim_id} - Additional Information Required",
                "email_body": "Dear {customer_name},\n\nWe need additional information for claim {claim_id}.\n\nReason: {reason}\n\nPlease contact us.",
                "sms_body": "Claim {claim_id} needs more info. Please call us."
            },
            "fraud_alert": {
                "subject": "FRAUD ALERT - Claim {claim_id}",
                "email_body": "Fraud detected on claim {claim_id}.\n\nRisk Level: {risk_level}\n\nRequires immediate review.",
                "sms_body": "FRAUD ALERT: Claim {claim_id} flagged for review."
            }
        }
        
        if template_name not in templates:
            return {"error": f"Template {template_name} not found"}
        
        template = templates[template_name]
        results = []
        
        for recipient in recipients:
            try:
                if delivery_method in ["email", "both"]:
                    subject = template["subject"].format(**variables)
                    body = template["email_body"].format(**variables)
                    
                    email_result = await self._send_email(recipient, subject, body, priority="medium", notification_type="template")
                    results.append({"recipient": recipient, "method": "email", "result": email_result})
                
                if delivery_method in ["sms", "both"]:
                    sms_message = template["sms_body"].format(**variables)
                    
                    sms_result = await self._send_sms(recipient, sms_message, priority="medium")
                    results.append({"recipient": recipient, "method": "sms", "result": sms_result})
                    
            except Exception as e:
                results.append({"recipient": recipient, "error": str(e)})
        
        logger.info("Template notification sent", template=template_name, recipients=len(recipients))
        
        return {
            "template_name": template_name,
            "recipients_count": len(recipients),
            "delivery_method": delivery_method,
            "results": results
        }
    
    async def _simulate_email_delivery(self, notification: Dict[str, Any]):
        """Simulate email delivery (replace with actual email service integration)"""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Simulate occasional failures
        import random
        if random.random() < 0.05:  # 5% failure rate
            raise Exception("Email service temporarily unavailable")
    
    async def _simulate_sms_delivery(self, notification: Dict[str, Any]):
        """Simulate SMS delivery (replace with actual SMS service integration)"""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Simulate occasional failures
        import random
        if random.random() < 0.03:  # 3% failure rate
            raise Exception("SMS service temporarily unavailable")
    
    async def _simulate_webhook_delivery(self, notification: Dict[str, Any]):
        """Simulate webhook delivery (replace with actual HTTP client)"""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Simulate occasional failures
        import random
        if random.random() < 0.02:  # 2% failure rate
            raise Exception("Webhook endpoint unreachable")


# Main execution
if __name__ == "__main__":
    port = int(os.getenv("NOTIFICATION_AGENT_PORT", "8003"))
    agent = NotificationAgent(port=port)
    
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("Notification Agent shutting down") 