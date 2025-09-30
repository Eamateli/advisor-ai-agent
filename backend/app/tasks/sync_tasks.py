"""
Background sync tasks for Gmail, Calendar, and HubSpot
"""
from app.tasks.celery_app import celery_app
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.services.batch_sync import batch_sync_service
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.sync_tasks.sync_user_data")
def sync_user_data(self, user_id: int, sync_options: dict = None):
    """Sync all data for a specific user"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            return {"success": False, "error": "User not found"}
        
        # Update task status
        self.update_state(state="PROGRESS", meta={"status": "Starting sync"})
        
        # Perform sync
        result = batch_sync_service.sync_user_data(
            db=db,
            user=user,
            options=sync_options or {}
        )
        
        logger.info(f"Sync completed for user {user_id}: {result}")
        return {"success": True, "result": result}
        
    except Exception as e:
        logger.error(f"Sync failed for user {user_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, name="app.tasks.sync_tasks.periodic_sync")
def periodic_sync(self):
    """Periodic sync for all active users"""
    db = SessionLocal()
    try:
        active_users = db.query(User).filter(User.is_active == True).all()
        
        for user in active_users:
            try:
                # Queue individual sync tasks
                sync_user_data.delay(user.id, {"days_back": 1})
            except Exception as e:
                logger.error(f"Failed to queue sync for user {user.id}: {e}")
        
        return {"success": True, "users_synced": len(active_users)}
        
    except Exception as e:
        logger.error(f"Periodic sync failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, name="app.tasks.sync_tasks.sync_gmail")
def sync_gmail(self, user_id: int, days_back: int = 30):
    """Sync Gmail data for a user"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        result = batch_sync_service.sync_gmail(db, user, days_back)
        return {"success": True, "result": result}
        
    except Exception as e:
        logger.error(f"Gmail sync failed for user {user_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, name="app.tasks.sync_tasks.sync_hubspot")
def sync_hubspot(self, user_id: int):
    """Sync HubSpot data for a user"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        result = batch_sync_service.sync_hubspot(db, user)
        return {"success": True, "result": result}
        
    except Exception as e:
        logger.error(f"HubSpot sync failed for user {user_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, name="app.tasks.sync_tasks.sync_calendar")
def sync_calendar(self, user_id: int, days_back: int = 30, days_forward: int = 90):
    """Sync Calendar data for a user"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        result = batch_sync_service.sync_calendar(db, user, days_back, days_forward)
        return {"success": True, "result": result}
        
    except Exception as e:
        logger.error(f"Calendar sync failed for user {user_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()
