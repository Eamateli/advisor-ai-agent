from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from app.core.database import Base
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class AuditLog(Base):
    """Audit trail for security-sensitive operations"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Who
    user_id = Column(Integer, index=True)
    user_email = Column(String)
    
    # What
    action = Column(String, nullable=False, index=True)  # e.g., "tool_execution", "email_sent"
    resource_type = Column(String, index=True)  # e.g., "email", "calendar", "hubspot"
    resource_id = Column(String)  # ID of affected resource
    
    # Details
    details = Column(JSON)  # Action-specific data
    input_data = Column(JSON)  # Tool inputs (sanitized)
    output_data = Column(JSON)  # Tool outputs (sanitized)
    
    # Outcome
    status = Column(String, index=True)  # "success", "failure", "unauthorized"
    error_message = Column(Text)
    
    # Context
    ip_address = Column(String)
    user_agent = Column(String)
    endpoint = Column(String)
    
    # When
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.action} by user {self.user_id}>"

class AuditLogger:
    """Service for creating audit logs"""
    
    @staticmethod
    def _sanitize_data(data: Any, sensitive_keys: list = None) -> Any:
        """Remove sensitive information from data before logging"""
        if sensitive_keys is None:
            sensitive_keys = [
                'password', 'token', 'secret', 'api_key', 'access_token',
                'refresh_token', 'authorization', 'credit_card', 'ssn'
            ]
        
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Check if key contains sensitive terms
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = AuditLogger._sanitize_data(value, sensitive_keys)
            return sanitized
        
        elif isinstance(data, list):
            return [AuditLogger._sanitize_data(item, sensitive_keys) for item in data]
        
        else:
            return data
    
    @staticmethod
    def log_tool_execution(
        db: Session,
        user_id: int,
        user_email: str,
        tool_name: str,
        tool_input: Dict,
        result: Dict,
        status: str = "success",
        error: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log tool execution for audit trail"""
        try:
            # Determine resource type from tool name
            resource_type = "unknown"
            if "email" in tool_name.lower():
                resource_type = "email"
            elif "calendar" in tool_name.lower():
                resource_type = "calendar"
            elif "hubspot" in tool_name.lower():
                resource_type = "hubspot"
            elif "knowledge" in tool_name.lower():
                resource_type = "rag"
            elif "task" in tool_name.lower():
                resource_type = "task"
            elif "instruction" in tool_name.lower():
                resource_type = "instruction"
            
            # Sanitize input/output
            sanitized_input = AuditLogger._sanitize_data(tool_input)
            sanitized_output = AuditLogger._sanitize_data(result)
            
            audit_log = AuditLog(
                user_id=user_id,
                user_email=user_email,
                action="tool_execution",
                resource_type=resource_type,
                resource_id=result.get("result", {}).get("task_id") or result.get("result", {}).get("message_id"),
                details={
                    "tool_name": tool_name,
                    "execution_time": datetime.utcnow().isoformat()
                },
                input_data=sanitized_input,
                output_data=sanitized_output,
                status=status,
                error_message=error,
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint="/chat/stream"
            )
            
            db.add(audit_log)
            db.commit()
            
            logger.info(f"Audit: {user_email} executed {tool_name} - {status}")
        
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't fail the request if audit logging fails
    
    @staticmethod
    def log_proactive_action(
        db: Session,
        user_id: int,
        user_email: str,
        action: str,
        details: Dict,
        trigger_event: str
    ):
        """Log proactive agent actions"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                user_email=user_email,
                action="proactive_action",
                resource_type="agent",
                details={
                    "action_taken": action,
                    "trigger": trigger_event,
                    **details
                },
                status="success",
                endpoint="/webhooks"
            )
            
            db.add(audit_log)
            db.commit()
            
            logger.info(f"Audit: Proactive action for {user_email} - {action}")
        
        except Exception as e:
            logger.error(f"Failed to log proactive action: {e}")
    
    @staticmethod
    def log_oauth_event(
        db: Session,
        user_id: int,
        user_email: str,
        provider: str,
        action: str,  # "connected", "disconnected", "token_refreshed"
        ip_address: Optional[str] = None
    ):
        """Log OAuth events"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                user_email=user_email,
                action=f"oauth_{action}",
                resource_type="oauth",
                details={
                    "provider": provider,
                    "action": action
                },
                status="success",
                ip_address=ip_address,
                endpoint="/auth"
            )
            
            db.add(audit_log)
            db.commit()
            
            logger.info(f"Audit: OAuth {action} for {user_email} - {provider}")
        
        except Exception as e:
            logger.error(f"Failed to log OAuth event: {e}")
    
    @staticmethod
    def log_unauthorized_attempt(
        db: Session,
        user_id: Optional[int],
        action: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log unauthorized access attempts"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action="unauthorized_attempt",
                resource_type="security",
                details={
                    "attempted_action": action,
                    "reason": reason
                },
                status="unauthorized",
                error_message=reason,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(audit_log)
            db.commit()
            
            logger.warning(f"Audit: Unauthorized attempt - {action} - {reason}")
        
        except Exception as e:
            logger.error(f"Failed to log unauthorized attempt: {e}")

audit_logger = AuditLogger()