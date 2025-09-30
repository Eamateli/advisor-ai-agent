"""
Celery application configuration for background tasks
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "financial_advisor_agent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.sync_tasks",
        "app.tasks.agent_tasks", 
        "app.tasks.webhook_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    task_routes={
        "app.tasks.sync_tasks.*": {"queue": "sync"},
        "app.tasks.agent_tasks.*": {"queue": "agent"},
        "app.tasks.webhook_tasks.*": {"queue": "webhooks"},
    },
    beat_schedule={
        "periodic-sync": {
            "task": "app.tasks.sync_tasks.periodic_sync",
            "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        },
        "cleanup-old-tasks": {
            "task": "app.tasks.agent_tasks.cleanup_old_tasks",
            "schedule": crontab(minute=0, hour=2),  # Daily at 2 AM
        },
    }
)

# Health check
@celery_app.task(bind=True)
def debug_task(self):
    logger.info(f"Request: {self.request!r}")
    return "Celery is working!"
