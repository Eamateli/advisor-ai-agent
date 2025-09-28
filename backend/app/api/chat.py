# backend/app/api/chat.py
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import json
import logging
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.security import verify_token
from app.core.rate_limit import rate_limiter
from app.core.websocket import manager
from app.models.user import User
from app.models.chat import ChatMessage, MessageRole
from app.agents.agent import create_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatHistoryResponse(BaseModel):
    messages: List[dict]
    total: int

class ConsentRequest(BaseModel):
    action_type: str
    scope: str = "all"
    conditions: Optional[dict] = None

# ============================================================================
# Dependencies
# ============================================================================

async def check_chat_rate_limit(
    request: Request,
    user: User = Depends(get_current_user)
):
    """Check rate limits for chat endpoint"""
    await rate_limiter.check_request(
        request=request,
        user_id=user.id,
        max_per_minute=10,
        max_per_hour=100
    )

# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    req: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_chat_rate_limit)
):
    """
    Stream chat responses with SSE (Rate Limited: 10/min, 100/hour)
    
    Returns Server-Sent Events stream with:
    - type: "content" - Streaming text content
    - type: "tool_use_start" - Tool execution started
    - type: "tool_result" - Tool execution completed
    - type: "done" - Stream completed
    - type: "error" - Error occurred
    """
    
    async def event_generator():
        try:
            agent = create_agent(db, user, request=req)
            
            async for event in agent.chat_stream(user_message=request.message):
                event_data = json.dumps(event)
                yield f"data: {event_data}\n\n"
            
            # Notify via WebSocket if connected
            try:
                await manager.broadcast_to_user(
                    user.id,
                    "chat_message",
                    {"message": request.message, "response_complete": True}
                )
            except:
                pass  # WebSocket notification is optional
        
        except HTTPException as he:
            error_event = json.dumps({
                "type": "error",
                "error": he.detail,
                "status_code": he.status_code
            })
            yield f"data: {error_event}\n\n"
        
        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            error_event = json.dumps({"type": "error", "error": str(e)})
            yield f"data: {error_event}\n\n"
    
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"
    }
    
    if hasattr(req.state, 'rate_limit_headers'):
        headers.update(req.state.rate_limit_headers)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=headers
    )

@router.websocket("/ws/{token}")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time updates
    
    Client connects with JWT token in path
    Receives real-time notifications about:
    - Task updates
    - Sync completions
    - Proactive agent actions
    - Chat events
    
    Send "ping" to receive "pong" for keepalive
    """
    try:
        # Verify JWT token
        try:
            payload = verify_token(token)
            user_id = int(payload.get("sub"))
        except Exception as e:
            logger.warning(f"WebSocket auth failed: {e}")
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.close(code=1008, reason="User not found")
            return
        
        # Connect
        await manager.connect(websocket, user_id)
        logger.info(f"WebSocket connected for user {user_id}")
        
        try:
            while True:
                # Keep connection alive and handle any incoming messages
                data = await websocket.receive_text()
                
                # Handle ping/pong for keepalive
                if data == "ping":
                    await websocket.send_text("pong")
                    continue
                
                # Handle JSON messages
                try:
                    message = json.loads(data)
                    message_type = message.get("type")
                    
                    if message_type == "subscribe":
                        # Handle subscription to specific events
                        events = message.get("events", [])
                        await manager.send_personal_message(
                            {"type": "subscribed", "events": events},
                            websocket
                        )
                    
                    elif message_type == "status":
                        # Send current status
                        await manager.send_personal_message(
                            {"type": "status", "connected": True, "user_id": user_id},
                            websocket
                        )
                    
                    else:
                        # Echo unknown messages back
                        await manager.send_personal_message(
                            {"type": "echo", "data": message},
                            websocket
                        )
                
                except json.JSONDecodeError:
                    # Handle plain text messages (echo back)
                    await manager.send_personal_message(
                        {"type": "echo", "data": data},
                        websocket
                    )
        
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
            logger.info(f"WebSocket disconnected for user {user_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass
        finally:
            manager.disconnect(websocket, user_id)

@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get chat history with pagination"""
    total = db.query(ChatMessage).filter(ChatMessage.user_id == user.id).count()
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == user.id
    ).order_by(ChatMessage.created_at.desc()).limit(limit).offset(offset).all()
    
    # Reverse to get chronological order
    messages = list(reversed(messages))
    
    formatted_messages = [
        {
            "id": msg.id,
            "role": msg.role.value,
            "content": msg.content,
            "tool_calls": msg.tool_calls,
            "created_at": msg.created_at.isoformat()
        }
        for msg in messages
    ]
    
    return ChatHistoryResponse(messages=formatted_messages, total=total)

@router.delete("/history")
async def clear_chat_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Clear all chat history for the current user"""
    deleted_count = db.query(ChatMessage).filter(ChatMessage.user_id == user.id).delete()
    db.commit()
    
    # Notify via WebSocket
    await manager.broadcast_to_user(
        user.id,
        "chat_cleared",
        {"deleted_messages": deleted_count}
    )
    
    return {"message": "Chat history cleared", "deleted_count": deleted_count}

# ============================================================================
# INSTRUCTIONS ENDPOINTS
# ============================================================================

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
    
    # Notify via WebSocket
    await manager.broadcast_to_user(
        user.id,
        "instruction_deleted",
        {"instruction_id": instruction_id}
    )
    
    return {"message": "Instruction deleted"}

# ============================================================================
# TASKS ENDPOINTS
# ============================================================================

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

@router.patch("/tasks/{task_id}/status")
async def update_task_status(
    task_id: int,
    status: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Update task status"""
    from app.models.task import Task, TaskStatus
    
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        task.status = TaskStatus[status.upper()]
        if status.upper() == "COMPLETED":
            task.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(task)
        
        # Notify via WebSocket
        await manager.notify_task_update(user.id, task_id, status)
        
        return {"message": f"Task {task_id} status updated to {status}"}
    
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

# ============================================================================
# CONSENT MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/consent")
async def get_user_consents(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get user's consent settings"""
    from app.models.consent import UserConsent
    
    consents = db.query(UserConsent).filter(UserConsent.user_id == user.id).all()
    
    return {
        "consents": [
            {
                "id": c.id,
                "action_type": c.action_type,
                "scope": c.scope,
                "is_granted": c.is_granted,
                "conditions": c.conditions,
                "granted_at": c.granted_at.isoformat() if c.granted_at else None,
                "last_used_at": c.last_used_at.isoformat() if c.last_used_at else None,
                "use_count": c.use_count
            }
            for c in consents
        ]
    }

@router.post("/consent/grant")
async def grant_consent(
    request: ConsentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Grant consent for autonomous actions"""
    from app.models.consent import consent_manager
    
    consent = consent_manager.grant_consent(
        db=db,
        user_id=user.id,
        action_type=request.action_type,
        scope=request.scope,
        conditions=request.conditions
    )
    
    # Notify via WebSocket
    await manager.broadcast_to_user(
        user.id,
        "consent_granted",
        {
            "action_type": request.action_type,
            "consent_id": consent.id
        }
    )
    
    return {
        "message": f"Consent granted for {request.action_type}",
        "consent_id": consent.id
    }

@router.post("/consent/revoke/{action_type}")
async def revoke_consent(
    action_type: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Revoke consent for an action"""
    from app.models.consent import consent_manager
    
    success = consent_manager.revoke_consent(
        db=db,
        user_id=user.id,
        action_type=action_type
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Consent not found")
    
    # Notify via WebSocket
    await manager.broadcast_to_user(
        user.id,
        "consent_revoked",
        {"action_type": action_type}
    )
    
    return {"message": f"Consent revoked for {action_type}"}

# ============================================================================
# AUDIT LOGS ENDPOINTS
# ============================================================================

@router.get("/audit")
async def get_audit_logs(
    limit: int = 50,
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get audit logs for current user"""
    from app.core.audit import AuditLog
    
    query = db.query(AuditLog).filter(AuditLog.user_id == user.id)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    return {
        "audit_logs": [
            {
                "id": log.id,
                "action": log.action,
                "resource_type": log.resource_type,
                "status": log.status,
                "details": log.details,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    }