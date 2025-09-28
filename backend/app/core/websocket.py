# backend/app/core/websocket.py
"""
WebSocket manager for real-time updates
"""
from typing import Dict, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept and track new WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}")
        
        # Send initial connection confirmation
        await self.send_personal_message(
            {"type": "connected", "message": "WebSocket connected"},
            websocket
        )
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def send_user_message(self, message: dict, user_id: int):
        """Send message to all connections for a user"""
        if user_id in self.active_connections:
            dead_connections = []
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to connection: {e}")
                    dead_connections.append(connection)
            
            # Clean up dead connections
            for conn in dead_connections:
                self.active_connections[user_id].discard(conn)
    
    async def broadcast_to_user(self, user_id: int, event_type: str, data: dict):
        """Broadcast event to all user's connections"""
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_user_message(message, user_id)
    
    async def notify_task_update(self, user_id: int, task_id: int, status: str):
        """Notify user of task status change"""
        await self.broadcast_to_user(
            user_id,
            "task_update",
            {"task_id": task_id, "status": status}
        )
    
    async def notify_sync_complete(self, user_id: int, sync_type: str, result: dict):
        """Notify user of sync completion"""
        await self.broadcast_to_user(
            user_id,
            "sync_complete",
            {"sync_type": sync_type, "result": result}
        )
    
    async def notify_proactive_action(self, user_id: int, action: str, details: dict):
        """Notify user of proactive agent action"""
        await self.broadcast_to_user(
            user_id,
            "proactive_action",
            {"action": action, "details": details}
        )

# Global instance
manager = ConnectionManager()