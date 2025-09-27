from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    profile_picture = Column(String)
    
    # Google OAuth
    google_id = Column(String, unique=True, index=True)
    google_access_token = Column(Text)  # Encrypted
    google_refresh_token = Column(Text)  # Encrypted
    google_token_expiry = Column(DateTime(timezone=True))
    
    # HubSpot OAuth
    hubspot_access_token = Column(Text)  # Encrypted
    hubspot_refresh_token = Column(Text)  # Encrypted
    hubspot_token_expiry = Column(DateTime(timezone=True))
    hubspot_portal_id = Column(String)
    
    # Account status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # messages = relationship("Message", back_populates="user")
    # tasks = relationship("Task", back_populates="user")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan", lazy="select")
    emails = relationship("Email", back_populates="user", cascade="all, delete-orphan", lazy="select")
    hubspot_contacts = relationship("HubSpotContact", back_populates="user", cascade="all, delete-orphan")
    hubspot_notes = relationship("HubSpotNote", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    instructions = relationship("Instruction", back_populates="user", cascade="all, delete-orphan")
    consents = relationship("UserConsent", back_populates="user", cascade="all, delete-orphan")