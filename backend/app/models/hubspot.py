from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class HubSpotContact(Base):
    """Store HubSpot contacts"""
    __tablename__ = "hubspot_contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # HubSpot metadata
    hubspot_id = Column(String, unique=True, nullable=False, index=True)
    
    # Contact info
    email = Column(String, index=True)
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String)
    company = Column(String)
    
    # Additional properties
    properties = Column(JSON)  # All HubSpot properties
    
    # Processing status
    is_processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="hubspot_contacts")
    notes = relationship("HubSpotNote", back_populates="contact", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<HubSpotContact {self.hubspot_id}: {self.first_name} {self.last_name}>"

class HubSpotNote(Base):
    """Store HubSpot contact notes"""
    __tablename__ = "hubspot_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("hubspot_contacts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # HubSpot metadata
    hubspot_id = Column(String, unique=True, nullable=False, index=True)
    
    # Note content
    body = Column(Text)
    
    # Metadata
    created_by = Column(String)
    
    # Processing status
    is_processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    contact = relationship("HubSpotContact", back_populates="notes")
    user = relationship("User", back_populates="hubspot_notes")
    
    def __repr__(self):
        return f"<HubSpotNote {self.hubspot_id}>"