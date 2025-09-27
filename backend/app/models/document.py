from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB  # Changed from JSON
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
    doc_type = Column(String, nullable=False, index=True)
    source_id = Column(String, nullable=False, index=True)
    
    # Content
    title = Column(String)
    content = Column(Text, nullable=False)
    chunk_text = Column(Text)
    chunk_index = Column(Integer, default=0)
    
    # Embedding
    embedding = Column(Vector(1536))
    
    # Rich metadata - Changed to JSONB
    doc_metadata = Column(JSONB)  # Changed from JSON to JSONB
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="documents")
    
    def __repr__(self):
        return f"<Document {self.doc_type}:{self.source_id} chunk:{self.chunk_index}>"