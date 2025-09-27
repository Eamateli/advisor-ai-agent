from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.auth import get_current_user, get_google_credentials, get_hubspot_token
from app.models.user import User
from app.services.batch_sync import batch_sync_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["Sync"])

class SyncRequest(BaseModel):
    days_back: int = 30
    include_gmail: bool = True
    include_hubspot: bool = True

class SyncResponse(BaseModel):
    status: str
    message: str
    summary: dict

@router.post("/full", response_model=SyncResponse)
async def full_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Trigger full batch sync from Gmail and HubSpot
    
    This runs in the background to avoid timeout
    """
    try:
        # Check if user has connected accounts
        if request.include_gmail and not user.google_access_token:
            raise HTTPException(
                status_code=400,
                detail="Google account not connected"
            )
        
        if request.include_hubspot and not user.hubspot_access_token:
            raise HTTPException(
                status_code=400,
                detail="HubSpot account not connected"
            )
        
        # Get credentials
        gmail_creds = None
        hubspot_token = None
        
        if request.include_gmail:
            gmail_creds = await get_google_credentials(user, db)
        
        if request.include_hubspot:
            hubspot_token = await get_hubspot_token(user, db)
        
        # Run sync in background
        background_tasks.add_task(
            _run_full_sync,
            db,
            user.id,
            gmail_creds,
            hubspot_token,
            request.days_back
        )
        
        return SyncResponse(
            status="started",
            message="Full sync started in background",
            summary={}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _run_full_sync(
    db: Session,
    user_id: int,
    gmail_creds,
    hubspot_token: str,
    days_back: int
):
    """Background task for full sync"""
    try:
        summary = await batch_sync_service.sync_all(
            db=db,
            user_id=user_id,
            gmail_credentials=gmail_creds,
            hubspot_token=hubspot_token,
            days_back=days_back
        )
        logger.info(f"Full sync complete for user {user_id}: {summary}")
    except Exception as e:
        logger.error(f"Full sync failed for user {user_id}: {e}")

@router.post("/gmail/incremental")
async def sync_gmail_incremental(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Sync new Gmail messages since last sync"""
    try:
        if not user.google_access_token:
            raise HTTPException(
                status_code=400,
                detail="Google account not connected"
            )
        
        gmail_creds = await get_google_credentials(user, db)
        
        # Run in background
        background_tasks.add_task(
            _run_gmail_incremental,
            db,
            user.id,
            gmail_creds
        )
        
        return {
            "status": "started",
            "message": "Gmail incremental sync started"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting Gmail sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _run_gmail_incremental(db: Session, user_id: int, gmail_creds):
    """Background task for Gmail incremental sync"""
    try:
        new_count = await batch_sync_service.sync_gmail_incremental(
            db=db,
            user_id=user_id,
            gmail_credentials=gmail_creds
        )
        logger.info(f"Gmail incremental sync complete: {new_count} new emails")
    except Exception as e:
        logger.error(f"Gmail incremental sync failed: {e}")

@router.post("/hubspot/incremental")
async def sync_hubspot_incremental(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Sync updated HubSpot contacts since last sync"""
    try:
        if not user.hubspot_access_token:
            raise HTTPException(
                status_code=400,
                detail="HubSpot account not connected"
            )
        
        hubspot_token = await get_hubspot_token(user, db)
        
        # Run in background
        background_tasks.add_task(
            _run_hubspot_incremental,
            db,
            user.id,
            hubspot_token
        )
        
        return {
            "status": "started",
            "message": "HubSpot incremental sync started"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting HubSpot sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _run_hubspot_incremental(db: Session, user_id: int, hubspot_token: str):
    """Background task for HubSpot incremental sync"""
    try:
        result = await batch_sync_service.sync_hubspot_incremental(
            db=db,
            user_id=user_id,
            hubspot_token=hubspot_token
        )
        logger.info(f"HubSpot incremental sync complete: {result}")
    except Exception as e:
        logger.error(f"HubSpot incremental sync failed: {e}")

@router.get("/status")
async def get_sync_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get sync status and statistics"""
    from app.models.email import Email
    from app.models.hubspot import HubSpotContact, HubSpotNote
    from app.models.document import Document
    
    # Get counts
    email_count = db.query(Email).filter(Email.user_id == user.id).count()
    email_processed = db.query(Email).filter(
        Email.user_id == user.id,
        Email.is_processed == True
    ).count()
    
    contact_count = db.query(HubSpotContact).filter(
        HubSpotContact.user_id == user.id
    ).count()
    contact_processed = db.query(HubSpotContact).filter(
        HubSpotContact.user_id == user.id,
        HubSpotContact.is_processed == True
    ).count()
    
    note_count = db.query(HubSpotNote).filter(
        HubSpotNote.user_id == user.id
    ).count()
    
    document_count = db.query(Document).filter(
        Document.user_id == user.id
    ).count()
    
    # Get last sync times
    last_email = db.query(Email).filter(
        Email.user_id == user.id
    ).order_by(Email.created_at.desc()).first()
    
    last_contact = db.query(HubSpotContact).filter(
        HubSpotContact.user_id == user.id
    ).order_by(HubSpotContact.created_at.desc()).first()
    
    return {
        "gmail": {
            "total_emails": email_count,
            "processed": email_processed,
            "pending": email_count - email_processed,
            "last_synced": last_email.created_at if last_email else None
        },
        "hubspot": {
            "total_contacts": contact_count,
            "processed_contacts": contact_processed,
            "total_notes": note_count,
            "last_synced": last_contact.created_at if last_contact else None
        },
        "rag": {
            "total_documents": document_count
        }
    }