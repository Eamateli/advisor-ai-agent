from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class Document(Base):
    """Universal document store with embeddings for RAG"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Document metadata
    doc_type = Column(String, nullable=False, index=True)  # 'email', 'hubspot_contact', 'hubspot_note'
    source_id = Column(String, nullable=False, index=True)  # Original ID from source system
    
    # Content
    title = Column(String)
    content = Column(Text, nullable=False)
    chunk_text = Column(Text)  # The actual chunk being embedded
    chunk_index = Column(Integer, default=0)  # Which chunk this is
    
    # Embedding
    embedding = Column(Vector(1536))  # OpenAI text-embedding-3-small dimension
    
    # Rich metadata for filtering
    metadata = Column(JSON)  # Store additional context
    # Example metadata:
    # {
    #   "email_from": "client@example.com",
    #   "email_to": ["advisor@example.com"],
    #   "email_subject": "Meeting request",
    #   "email_date": "2025-09-27T10:00:00Z",
    #   "contact_name": "John Smith",
    #   "contact_email": "john@example.com",
    #   "hubspot_id": "12345"
    # }
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="documents")
    
    def __repr__(self):
        return f"<Document {self.doc_type}:{self.source_id} chunk:{self.chunk_index}>"