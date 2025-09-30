"""
Background agent tasks for proactive actions and long-running operations
"""
from app.tasks.celery_app import celery_app
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.agents.agent import create_agent
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.agent_tasks.process_webhook")
def process_webhook(self, user_id: int, webhook_type: str, webhook_data: dict):
    """Process incoming webhook and trigger proactive agent actions"""
    import asyncio
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Create agent and check for proactive actions
        agent = create_agent(db, user)
        # Run async function in sync context
        action_taken = asyncio.run(agent.proactive_check(webhook_type, webhook_data))
        
        return {"success": True, "action_taken": action_taken}
        
    except Exception as e:
        logger.error(f"Webhook processing failed for user {user_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, name="app.tasks.agent_tasks.execute_task")
def execute_task(self, task_id: int):
    """Execute a specific task"""
    import asyncio
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"success": False, "error": "Task not found"}
        
        user = db.query(User).filter(User.id == task.user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        db.commit()
        
        # Create agent and execute task
        agent = create_agent(db, user)
        result = asyncio.run(agent.chat(task.description))
        
        # Update task with result
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        if task.memory:
            task.memory["result"] = result
        else:
            task.memory = {"result": result}
        db.commit()
        
        return {"success": True, "result": result}
        
    except Exception as e:
        logger.error(f"Task execution failed for task {task_id}: {e}")
        
        # Update task status to failed
        if task:
            task.status = TaskStatus.FAILED
            if task.memory:
                task.memory["error"] = str(e)
            else:
                task.memory = {"error": str(e)}
            db.commit()
        
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, name="app.tasks.agent_tasks.cleanup_old_tasks")
def cleanup_old_tasks(self):
    """Clean up old completed tasks"""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Delete old completed tasks
        deleted_count = db.query(Task).filter(
            Task.status == TaskStatus.COMPLETED,
            Task.completed_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old tasks")
        return {"success": True, "deleted_count": deleted_count}
        
    except Exception as e:
        logger.error(f"Task cleanup failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, name="app.tasks.agent_tasks.process_email")
def process_email(self, user_id: int, email_id: str):
    """Process a new email and check for proactive actions"""
    import asyncio
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Create agent and check for proactive actions
        agent = create_agent(db, user)
        action_taken = asyncio.run(agent.proactive_check("email_received", {"email_id": email_id}))
        
        return {"success": True, "action_taken": action_taken}
        
    except Exception as e:
        logger.error(f"Email processing failed for user {user_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, name="app.tasks.agent_tasks.process_calendar_event")
def process_calendar_event(self, user_id: int, event_id: str):
    """Process a calendar event and check for proactive actions"""
    import asyncio
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Create agent and check for proactive actions
        agent = create_agent(db, user)
        action_taken = asyncio.run(agent.proactive_check("calendar_event", {"event_id": event_id}))
        
        return {"success": True, "action_taken": action_taken}
        
    except Exception as e:
        logger.error(f"Calendar event processing failed for user {user_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()
