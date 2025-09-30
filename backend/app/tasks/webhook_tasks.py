"""
Webhook processing tasks
"""
from app.tasks.celery_app import celery_app
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
import logging
import json

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.webhook_tasks.process_gmail_webhook")
def process_gmail_webhook(self, user_id: int, webhook_data: dict):
    """Process Gmail webhook"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Process Gmail webhook data
        # This would trigger email sync and proactive agent actions
        logger.info(f"Processing Gmail webhook for user {user_id}")
        
        # Queue email processing task
        from app.tasks.agent_tasks import process_email
        process_email.delay(user_id, webhook_data.get("email_id"))
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Gmail webhook processing failed for user {user_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, name="app.tasks.webhook_tasks.process_hubspot_webhook")
def process_hubspot_webhook(self, user_id: int, webhook_data: dict):
    """Process HubSpot webhook"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Process HubSpot webhook data
        logger.info(f"Processing HubSpot webhook for user {user_id}")
        
        # Queue sync task
        from app.tasks.sync_tasks import sync_hubspot
        sync_hubspot.delay(user_id)
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"HubSpot webhook processing failed for user {user_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, name="app.tasks.webhook_tasks.process_calendar_webhook")
def process_calendar_webhook(self, user_id: int, webhook_data: dict):
    """Process Calendar webhook"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Process Calendar webhook data
        logger.info(f"Processing Calendar webhook for user {user_id}")
        
        # Queue calendar event processing
        from app.tasks.agent_tasks import process_calendar_event
        process_calendar_event.delay(user_id, webhook_data.get("event_id"))
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Calendar webhook processing failed for user {user_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()
