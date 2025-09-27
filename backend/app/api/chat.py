from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import json
import logging
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.chat import ChatMessage, MessageRole
from app.agents.agent import create_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatHistoryResponse(BaseModel):
    messages: List[dict]
    total: int

# Endpoints
@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Stream chat responses with Server-Sent Events (SSE)
    
    Event types:
    - content: Text chunks from Claude
    - tool_use_start: Tool execution started
    - tool_result: Tool execution completed
    - done: Response complete
    - error: Error occurred
    """
    
    async def event_generator():
        try:
            # Create agent
            agent = create_agent(db, user)
            
            # Stream responses
            async for event in agent.chat_stream(
                user_message=request.message
            ):
                # Format as SSE
                event_data = json.dumps(event)
                yield f"data: {event_data}\n\n"
        
        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            error_event = json.dumps({
                "type": "error",
                "error": str(e)
            })
            yield f"data: {error_event}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable proxy buffering
        }
    )

@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get chat history for current user"""
    
    # Get total count
    total = db.query(ChatMessage).filter(
        ChatMessage.user_id == user.id
    ).count()
    
    # Get messages
    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == user.id
    ).order_by(ChatMessage.created_at.desc()).limit(limit).offset(offset).all()
    
    messages = list(reversed(messages))  # Oldest first
    
    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            "id": msg.id,
            "role": msg.role.value,
            "content": msg.content,
            "tool_calls": msg.tool_calls,
            "created_at": msg.created_at.isoformat()
        })
    
    return ChatHistoryResponse(
        messages=formatted_messages,
        total=total
    )

@router.delete("/history")
async def clear_chat_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Clear chat history"""
    
    db.query(ChatMessage).filter(
        ChatMessage.user_id == user.id
    ).delete()
    
    db.commit()
    
    return {"message": "Chat history cleared"}

@router.get("/instructions")
async def get_instructions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get user's ongoing instructions"""
    from app.models.task import Instruction
    
    instructions = db.query(Instruction).filter(
        Instruction.user_id == user.id,
        Instruction.is_active == True
    ).all()
    
    return {
        "instructions": [
            {
                "id": inst.id,
                "instruction": inst.instruction,
                "trigger_type": inst.trigger_type,
                "created_at": inst.created_at.isoformat()
            }
            for inst in instructions
        ]
    }

@router.delete("/instructions/{instruction_id}")
async def delete_instruction(
    instruction_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Delete an ongoing instruction"""
    from app.models.task import Instruction
    
    instruction = db.query(Instruction).filter(
        Instruction.id == instruction_id,
        Instruction.user_id == user.id
    ).first()
    
    if not instruction:
        raise HTTPException(status_code=404, detail="Instruction not found")
    
    db.delete(instruction)
    db.commit()
    
    return {"message": "Instruction deleted"}

@router.get("/tasks")
async def get_active_tasks(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get active tasks"""
    from app.models.task import Task, TaskStatus
    
    tasks = db.query(Task).filter(
        Task.user_id == user.id,
        Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING])
    ).order_by(Task.created_at.desc()).all()
    
    return {
        "tasks": [
            {
                "id": task.id,
                "description": task.description,
                "status": task.status.value,
                "memory": task.memory,
                "created_at": task.created_at.isoformat()
            }
            for task in tasks
        ]
    }