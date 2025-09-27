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