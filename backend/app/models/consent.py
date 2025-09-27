from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from typing import Optional
from datetime import datetime

class UserConsent(Base):
    """Track user consent for autonomous actions"""
    __tablename__ = "user_consents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # What action is consented
    action_type = Column(String, nullable=False, index=True)  # e.g., "send_email", "create_contact"
    scope = Column(String)  # e.g., "all", "specific_contact", "work_hours_only"
    
    # Consent status
    is_granted = Column(Boolean, default=False, nullable=False)
    
    # Conditions
    conditions = Column(JSON)  # e.g., {"max_emails_per_day": 10}
    
    # Metadata
    granted_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))  # Optional expiration
    
    # Tracking
    last_used_at = Column(DateTime(timezone=True))
    use_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="consents")
    
    def __repr__(self):
        return f"<UserConsent {self.action_type} - {'Granted' if self.is_granted else 'Revoked'}>"
    
    def is_valid(self) -> bool:
        """Check if consent is currently valid"""
        if not self.is_granted:
            return False
        
        if self.revoked_at:
            return False
        
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        
        return True
    
    def check_conditions(self, context: dict = None) -> bool:
        """Check if conditions are met for using this consent"""
        if not self.conditions:
            return True
        
        # Check max usage per day
        if "max_per_day" in self.conditions:
            # Would need to query usage count for today
            # Simplified here
            pass
        
        # Check time-based conditions
        if "allowed_hours" in self.conditions:
            current_hour = datetime.utcnow().hour
            allowed = self.conditions["allowed_hours"]
            if current_hour < allowed["start"] or current_hour > allowed["end"]:
                return False
        
        return True

class ConsentManager:
    """Service for managing user consent"""
    
    @staticmethod
    def check_consent(
        db,
        user_id: int,
        action_type: str,
        context: dict = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user has consented to an action
        
        Returns:
            (is_allowed, reason_if_denied)
        """
        consent = db.query(UserConsent).filter(
            UserConsent.user_id == user_id,
            UserConsent.action_type == action_type,
            UserConsent.is_granted == True
        ).first()
        
        if not consent:
            return False, f"No consent granted for {action_type}"
        
        if not consent.is_valid():
            return False, f"Consent for {action_type} has expired or been revoked"
        
        if not consent.check_conditions(context):
            return False, f"Consent conditions not met for {action_type}"
        
        # Update usage
        consent.last_used_at = datetime.utcnow()
        consent.use_count += 1
        db.commit()
        
        return True, None
    
    @staticmethod
    def grant_consent(
        db,
        user_id: int,
        action_type: str,
        scope: str = "all",
        conditions: dict = None,
        expires_at: Optional[datetime] = None
    ) -> UserConsent:
        """Grant consent for an action"""
        
        # Check if consent already exists
        existing = db.query(UserConsent).filter(
            UserConsent.user_id == user_id,
            UserConsent.action_type == action_type
        ).first()
        
        if existing:
            # Update existing
            existing.is_granted = True
            existing.scope = scope
            existing.conditions = conditions
            existing.granted_at = datetime.utcnow()
            existing.revoked_at = None
            existing.expires_at = expires_at
            db.commit()
            return existing
        
        # Create new consent
        consent = UserConsent(
            user_id=user_id,
            action_type=action_type,
            scope=scope,
            is_granted=True,
            conditions=conditions,
            granted_at=datetime.utcnow(),
            expires_at=expires_at
        )
        
        db.add(consent)
        db.commit()
        db.refresh(consent)
        
        return consent
    
    @staticmethod
    def revoke_consent(
        db,
        user_id: int,
        action_type: str
    ) -> bool:
        """Revoke consent for an action"""
        consent = db.query(UserConsent).filter(
            UserConsent.user_id == user_id,
            UserConsent.action_type == action_type
        ).first()
        
        if not consent:
            return False
        
        consent.is_granted = False
        consent.revoked_at = datetime.utcnow()
        db.commit()
        
        return True

consent_manager = ConsentManager()