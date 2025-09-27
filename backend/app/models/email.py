from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Email(Base):
    """Store Gmail messages"""
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Gmail metadata
    gmail_id = Column(String, unique=True, nullable=False, index=True)
    thread_id = Column(String, index=True)
    
    # Email fields
    subject = Column(String)
    from_email = Column(String, index=True)
    from_name = Column(String)
    to_emails = Column(JSON)  # List of recipient emails
    cc_emails = Column(JSON)  # List of CC emails
    
    # Content
    body_text = Column(Text)
    body_html = Column(Text)
    snippet = Column(Text)  # Gmail snippet
    
    # Metadata
    date = Column(DateTime(timezone=True), index=True)
    labels = Column(JSON)  # Gmail labels
    is_read = Column(Boolean, default=False)
    is_important = Column(Boolean, default=False)
    
    # Processing status
    is_processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="emails")
    
    def __repr__(self):
        return f"<Email {self.gmail_id}: {self.subject}>"