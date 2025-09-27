from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"  # Waiting for external response
    COMPLETED = "completed"
    FAILED = "failed"

class Task(Base):
    """Store agent tasks with memory"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Task details
    description = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    
    # Task memory - stores conversation state
    memory = Column(JSON)  # Store task execution history
    # Example:
    # {
    #   "steps": [
    #     {"action": "searched_calendar", "result": "found 3 slots"},
    #     {"action": "sent_email", "to": "client@example.com", "message_id": "123"}
    #   ],
    #   "waiting_for": "email_response",
    #   "context": {...}
    # }
    
    # Related entities
    related_email_id = Column(String)  # Gmail ID if triggered by email
    related_contact_id = Column(Integer, ForeignKey("hubspot_contacts.id"))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    
    def __repr__(self):
        return f"<Task {self.id}: {self.status} - {self.description[:50]}>"

class Instruction(Base):
    """Store ongoing user instructions for proactive behavior"""
    __tablename__ = "instructions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Instruction details
    instruction = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    
    # Trigger conditions
    trigger_type = Column(String)  # 'email', 'calendar', 'hubspot_contact', 'hubspot_note'
    trigger_conditions = Column(JSON)  # Conditions for when to apply
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="instructions")
    
    def __repr__(self):
        return f"<Instruction {self.id}: {self.instruction[:50]}>"