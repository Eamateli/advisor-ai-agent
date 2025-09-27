from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(Base):
    """Store chat conversation history"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Message content
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # Context used for this message
    context_documents = Column(JSON)  # List of document IDs used for RAG
    
    # Tool calls if any
    tool_calls = Column(JSON)  # Store tool invocations
    tool_results = Column(JSON)  # Store tool results
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_messages")
    
    def __repr__(self):
        return f"<ChatMessage {self.role}: {self.content[:50]}...>"