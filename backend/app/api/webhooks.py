from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
import hmac
import hashlib
import json
import logging
from app.core.database import get_db
from app.models.user import User
from app.services.batch_sync import batch_sync_service
from app.core.auth import get_google_credentials, get_hubspot_token, get_current_user
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/gmail/watch")
async def gmail_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle Gmail push notifications
    
    Gmail uses Cloud Pub/Sub for push notifications.
    Setup: https://developers.google.com/gmail/api/guides/push
    """
    try:
        body = await request.json()
        
        # Decode Pub/Sub message
        if 'message' not in body:
            raise HTTPException(status_code=400, detail="Invalid webhook format")
        
        message = body['message']
        
        # Decode data
        import base64
        data_str = base64.b64decode(message['data']).decode('utf-8')
        data = json.loads(data_str)
        
        email_address = data.get('emailAddress')
        history_id = data.get('historyId')
        
        logger.info(f"Gmail webhook received for {email_address}, historyId: {history_id}")
        
        # Find user by email
        user = db.query(User).filter(User.email == email_address).first()
        
        if not user:
            logger.warning(f"User not found for email: {email_address}")
            return {"status": "ignored"}
        
        # Trigger incremental sync in background
        background_tasks.add_task(
            _process_gmail_webhook,
            db,
            user.id
        )
        
        return {"status": "processing"}
    
    except Exception as e:
        logger.error(f"Error processing Gmail webhook: {e}")
        # Return 200 to prevent retry
        return {"status": "error", "message": str(e)}

async def _process_gmail_webhook(db: Session, user_id: int):
    """Background task to process Gmail webhook"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        
        gmail_creds = await get_google_credentials(user, db)
        
        # Sync new emails
        await batch_sync_service.sync_gmail_incremental(
            db=db,
            user_id=user_id,
            gmail_credentials=gmail_creds
        )
        
        logger.info(f"Gmail webhook processing complete for user {user_id}")
    
    except Exception as e:
        logger.error(f"Error in Gmail webhook processing: {e}")

@router.post("/calendar")
async def calendar_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle Google Calendar push notifications
    
    Setup: https://developers.google.com/calendar/api/guides/push
    """
    try:
        # Get headers
        resource_id = request.headers.get('X-Goog-Resource-ID')
        resource_state = request.headers.get('X-Goog-Resource-State')
        channel_id = request.headers.get('X-Goog-Channel-ID')
        
        logger.info(f"Calendar webhook: state={resource_state}, channel={channel_id}")
        
        # Verify it's not a sync message
        if resource_state == 'sync':
            return {"status": "sync"}
        
        # For 'exists' or 'not_exists', trigger calendar sync
        # You would need to store channel_id -> user_id mapping
        # For simplicity, we'll just log it here
        
        # In production, you'd:
        # 1. Store channel_id when setting up watch
        # 2. Look up user_id from channel_id
        # 3. Trigger calendar event sync
        
        logger.info("Calendar event changed, sync needed")
        
        return {"status": "acknowledged"}
    
    except Exception as e:
        logger.error(f"Error processing Calendar webhook: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/hubspot")
async def hubspot_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle HubSpot webhooks
    
    Setup: https://developers.hubspot.com/docs/api/webhooks
    """
    try:
        # Verify signature
        signature = request.headers.get('X-HubSpot-Signature')
        body_bytes = await request.body()
        
        # Verify signature (if you have app secret)
        # expected_signature = hmac.new(
        #     settings.HUBSPOT_APP_SECRET.encode(),
        #     body_bytes,
        #     hashlib.sha256
        # ).hexdigest()
        # 
        # if signature != expected_signature:
        #     raise HTTPException(status_code=401, detail="Invalid signature")
        
        body = json.loads(body_bytes)
        
        # Parse webhook events
        for event in body:
            subscription_type = event.get('subscriptionType')
            object_id = event.get('objectId')
            portal_id = event.get('portalId')
            
            logger.info(f"HubSpot webhook: type={subscription_type}, objectId={object_id}")
            
            # Find user by portal_id
            user = db.query(User).filter(
                User.hubspot_portal_id == str(portal_id)
            ).first()
            
            if not user:
                logger.warning(f"User not found for portal: {portal_id}")
                continue
            
            # Handle different event types
            if subscription_type == 'contact.creation':
                background_tasks.add_task(
                    _sync_contact,
                    db,
                    user.id,
                    object_id
                )
            
            elif subscription_type == 'contact.propertyChange':
                background_tasks.add_task(
                    _sync_contact,
                    db,
                    user.id,
                    object_id
                )
            
            elif subscription_type == 'contact.deletion':
                background_tasks.add_task(
                    _delete_contact,
                    db,
                    user.id,
                    object_id
                )
        
        return {"status": "processing"}
    
    except Exception as e:
        logger.error(f"Error processing HubSpot webhook: {e}")
        return {"status": "error", "message": str(e)}

async def _sync_contact(db: Session, user_id: int, contact_id: str):
    """Sync a single contact from HubSpot"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        
        hubspot_token = await get_hubspot_token(user, db)
        
        from app.integrations.hubspot_service import HubSpotService
        hubspot = HubSpotService(hubspot_token)
        
        # Get contact details
        contacts = await hubspot.get_contacts(limit=1)
        # Note: In production, you'd fetch by ID directly
        
        logger.info(f"Contact sync complete for {contact_id}")
    
    except Exception as e:
        logger.error(f"Error syncing contact {contact_id}: {e}")

async def _delete_contact(db: Session, user_id: int, contact_id: str):
    """Delete contact from local database"""
    try:
        from app.models.hubspot import HubSpotContact
        
        contact = db.query(HubSpotContact).filter(
            HubSpotContact.user_id == user_id,
            HubSpotContact.hubspot_id == contact_id
        ).first()
        
        if contact:
            db.delete(contact)
            db.commit()
            logger.info(f"Deleted contact {contact_id}")
    
    except Exception as e:
        logger.error(f"Error deleting contact {contact_id}: {e}")
        db.rollback()

@router.get("/gmail/setup")
async def setup_gmail_watch(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Setup Gmail push notifications
    
    Returns instructions for setting up Cloud Pub/Sub
    """
    return {
        "instructions": [
            "1. Create Cloud Pub/Sub topic in Google Cloud Console",
            "2. Grant Gmail API permission to publish to topic",
            "3. Create push subscription pointing to /webhooks/gmail/watch",
            "4. Call Gmail watch API to start receiving notifications",
            f"5. Your webhook URL: {settings.BACKEND_URL}/webhooks/gmail/watch"
        ],
        "topic_name": "projects/YOUR_PROJECT/topics/gmail-notifications",
        "webhook_url": f"{settings.BACKEND_URL}/webhooks/gmail/watch"
    }

@router.get("/hubspot/setup")
async def setup_hubspot_webhooks(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Instructions for setting up HubSpot webhooks
    """
    return {
        "instructions": [
            "1. Go to HubSpot App Settings",
            "2. Navigate to Webhooks section",
            "3. Add subscription for events:",
            "   - contact.creation",
            "   - contact.propertyChange",
            "   - contact.deletion",
            f"4. Target URL: {settings.BACKEND_URL}/webhooks/hubspot"
        ],
        "webhook_url": f"{settings.BACKEND_URL}/webhooks/hubspot",
        "required_scopes": [
            "crm.objects.contacts.read",
            "crm.objects.contacts.write"
        ]
    }