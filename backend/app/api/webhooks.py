from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session
import hmac
import hashlib
import json
import logging
import base64
from app.core.database import get_db
from app.models.user import User
from app.services.batch_sync import batch_sync_service
from app.core.auth import get_google_credentials, get_hubspot_token, get_current_user
from app.core.config import settings
from app.core.webhook_security import webhook_security
from app.core.audit import audit_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# ============================================================================
# GMAIL WEBHOOK (Cloud Pub/Sub)
# ============================================================================

@router.post("/gmail/watch")
async def gmail_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle Gmail push notifications with token verification
    
    Gmail uses Cloud Pub/Sub for push notifications.
    Setup: https://developers.google.com/gmail/api/guides/push
    
    Security:
    - Token verification (if GMAIL_WEBHOOK_TOKEN is set)
    - User validation
    - Proactive agent checks
    """
    try:
        # Get verification token if configured
        token = request.headers.get('X-Goog-Channel-Token')
        
        # Verify token if configured
        if hasattr(settings, 'GMAIL_WEBHOOK_TOKEN') and settings.GMAIL_WEBHOOK_TOKEN:
            if not webhook_security.verify_gmail_pubsub(token, settings.GMAIL_WEBHOOK_TOKEN):
                logger.error("Invalid Gmail webhook token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook token"
                )
        
        body = await request.json()
        
        # Decode Pub/Sub message
        if 'message' not in body:
            raise HTTPException(status_code=400, detail="Invalid webhook format")
        
        message = body['message']
        
        # Decode data
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
        
        # Trigger sync with proactive check
        background_tasks.add_task(
            _process_gmail_webhook_with_proactive,
            db,
            user.id,
            {
                "email_address": email_address,
                "history_id": history_id
            }
        )
        
        return {"status": "processing"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Gmail webhook: {e}")
        # Return 200 to prevent retry storms
        return {"status": "error", "message": str(e)}

async def _process_gmail_webhook_with_proactive(
    db: Session,
    user_id: int,
    event_data: dict
):
    """
    Process Gmail webhook with proactive agent check
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        
        # Sync new emails
        gmail_creds = await get_google_credentials(user, db)
        await batch_sync_service.sync_gmail_incremental(
            db=db,
            user_id=user_id,
            gmail_credentials=gmail_creds
        )
        
        logger.info(f"Gmail sync complete for user {user_id}")
        
        # Check if agent should respond proactively
        from app.agents.agent import create_agent
        
        agent = create_agent(db, user)
        
        action_taken = await agent.proactive_check(
            event_type="email",
            event_data=event_data
        )
        
        if action_taken:
            # Log proactive action
            audit_logger.log_proactive_action(
                db=db,
                user_id=user_id,
                user_email=user.email,
                action="proactive_email_response",
                details=event_data,
                trigger_event="email_received"
            )
            
            logger.info(f"Proactive action taken for Gmail webhook, user {user_id}")
    
    except Exception as e:
        logger.error(f"Error in Gmail webhook processing: {e}")

# ============================================================================
# GOOGLE CALENDAR WEBHOOK
# ============================================================================

@router.post("/calendar")
async def calendar_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle Google Calendar push notifications
    
    Setup: https://developers.google.com/calendar/api/guides/push
    
    Note: In production, you should store channel_id -> user_id mapping
    when setting up the watch, then look it up here.
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
        
        # TODO: In production, look up user_id from channel_id
        # For now, we'll just acknowledge
        # Example:
        # channel_mapping = db.query(ChannelMapping).filter(
        #     ChannelMapping.channel_id == channel_id
        # ).first()
        # if channel_mapping:
        #     background_tasks.add_task(
        #         _process_calendar_webhook,
        #         db,
        #         channel_mapping.user_id,
        #         {"resource_state": resource_state}
        #     )
        
        logger.info("Calendar event changed, sync needed")
        
        return {"status": "acknowledged"}
    
    except Exception as e:
        logger.error(f"Error processing Calendar webhook: {e}")
        return {"status": "error", "message": str(e)}

# ============================================================================
# HUBSPOT WEBHOOK
# ============================================================================

@router.post("/hubspot")
async def hubspot_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle HubSpot webhooks with signature verification
    
    Setup: https://developers.hubspot.com/docs/api/webhooks
    
    Security:
    - HMAC-SHA256 signature verification
    - User validation
    - Proactive agent checks
    """
    try:
        # Get signature from headers (v3 is current version)
        signature = request.headers.get('X-HubSpot-Signature-v3')
        
        # Get raw body for signature verification
        body_bytes = await request.body()
        
        # Verify signature if secret is configured
        if hasattr(settings, 'HUBSPOT_WEBHOOK_SECRET') and settings.HUBSPOT_WEBHOOK_SECRET:
            webhook_security.enforce_signature(
                signature=signature,
                body=body_bytes,
                secret=settings.HUBSPOT_WEBHOOK_SECRET,
                provider="hubspot"
            )
            logger.info("HubSpot webhook signature verified")
        else:
            logger.warning("HubSpot webhook secret not configured - signature verification skipped")
        
        # Parse body
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
            
            # Handle different event types with proactive checks
            if subscription_type == 'contact.creation':
                background_tasks.add_task(
                    _process_hubspot_webhook_with_proactive,
                    db,
                    user.id,
                    "hubspot_contact",
                    {
                        "event": "created",
                        "contact_id": object_id,
                        "portal_id": portal_id
                    }
                )
            
            elif subscription_type == 'contact.propertyChange':
                background_tasks.add_task(
                    _process_hubspot_webhook_with_proactive,
                    db,
                    user.id,
                    "hubspot_contact",
                    {
                        "event": "updated",
                        "contact_id": object_id,
                        "portal_id": portal_id,
                        "changed_properties": event.get('propertyName')
                    }
                )
            
            elif subscription_type == 'contact.deletion':
                background_tasks.add_task(
                    _delete_contact,
                    db,
                    user.id,
                    object_id
                )
        
        return {"status": "processing"}
    
    except HTTPException as he:
        # Signature verification failed
        logger.error(f"HubSpot webhook verification failed: {he.detail}")
        raise
    
    except Exception as e:
        logger.error(f"Error processing HubSpot webhook: {e}")
        return {"status": "error", "message": str(e)}

async def _process_hubspot_webhook_with_proactive(
    db: Session,
    user_id: int,
    event_type: str,
    event_data: dict
):
    """
    Process HubSpot webhook with proactive agent check
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        
        # Sync the contact if needed
        contact_id = event_data.get('contact_id')
        if contact_id and event_data.get('event') in ['created', 'updated']:
            hubspot_token = await get_hubspot_token(user, db)
            
            from app.integrations.hubspot_service import HubSpotService
            from app.services.batch_sync import batch_sync_service
            
            hubspot = HubSpotService(hubspot_token)
            
            # Fetch contact details
            # Note: HubSpot API doesn't have direct fetch by ID in v3
            # You'd need to search or use the contacts API
            # For simplicity, we'll trigger an incremental sync
            await batch_sync_service.sync_hubspot_incremental(
                db=db,
                user_id=user_id,
                hubspot_token=hubspot_token
            )
        
        # Check if agent should respond proactively
        from app.agents.agent import create_agent
        
        agent = create_agent(db, user)
        
        action_taken = await agent.proactive_check(
            event_type=event_type,
            event_data=event_data
        )
        
        if action_taken:
            # Log proactive action
            audit_logger.log_proactive_action(
                db=db,
                user_id=user_id,
                user_email=user.email,
                action=f"proactive_{event_type}",
                details=event_data,
                trigger_event=event_type
            )
            
            logger.info(f"Proactive action taken for HubSpot webhook, user {user_id}")
    
    except Exception as e:
        logger.error(f"Error in HubSpot webhook processing: {e}")

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
            
            # Log deletion
            audit_logger.log_proactive_action(
                db=db,
                user_id=user_id,
                user_email=contact.user.email if contact.user else "unknown",
                action="contact_deleted",
                details={"contact_id": contact_id},
                trigger_event="hubspot_contact_deletion"
            )
    
    except Exception as e:
        logger.error(f"Error deleting contact {contact_id}: {e}")
        db.rollback()

# ============================================================================
# WEBHOOK SETUP ENDPOINTS (Helper endpoints for users)
# ============================================================================

@router.get("/gmail/setup")
async def setup_gmail_watch(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Setup Gmail push notifications
    
    Returns instructions for setting up Cloud Pub/Sub
    """
    backend_url = settings.BACKEND_URL or "https://your-app.onrender.com"
    
    return {
        "instructions": [
            "1. Create Cloud Pub/Sub topic in Google Cloud Console",
            "   - Topic name: gmail-notifications",
            "",
            "2. Grant Gmail API permission to publish:",
            "   gcloud pubsub topics add-iam-policy-binding gmail-notifications \\",
            "     --member=serviceAccount:gmail-api-push@system.gserviceaccount.com \\",
            "     --role=roles/pubsub.publisher",
            "",
            "3. Create push subscription:",
            f"   - Endpoint URL: {backend_url}/webhooks/gmail/watch",
            "   - Add verification token (optional but recommended)",
            "",
            "4. Call Gmail watch API to start receiving notifications:",
            "   POST https://gmail.googleapis.com/gmail/v1/users/me/watch",
            "   {",
            "     'topicName': 'projects/YOUR_PROJECT/topics/gmail-notifications',",
            "     'labelIds': ['INBOX']",
            "   }",
            "",
            "5. Add webhook token to your .env:",
            "   GMAIL_WEBHOOK_TOKEN=your-token-here"
        ],
        "webhook_url": f"{backend_url}/webhooks/gmail/watch",
        "topic_name": "projects/YOUR_PROJECT/topics/gmail-notifications",
        "user_email": user.email
    }

@router.get("/hubspot/setup")
async def setup_hubspot_webhooks(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Instructions for setting up HubSpot webhooks
    """
    backend_url = settings.BACKEND_URL or "https://your-app.onrender.com"
    
    return {
        "instructions": [
            "1. Go to HubSpot Developer Account",
            "   https://developers.hubspot.com/",
            "",
            "2. Navigate to your app → Webhooks section",
            "",
            "3. Configure webhook settings:",
            f"   - Target URL: {backend_url}/webhooks/hubspot",
            "   - Click 'Create subscription'",
            "",
            "4. Subscribe to these events:",
            "   ✓ contact.creation",
            "   ✓ contact.propertyChange",
            "   ✓ contact.deletion",
            "",
            "5. Copy webhook signature secret",
            "   - Go to app settings",
            "   - Find 'Client secret' under webhook settings",
            "",
            "6. Add to your .env:",
            "   HUBSPOT_WEBHOOK_SECRET=your-secret-here",
            "",
            "7. Test webhook:",
            "   - Create a test contact in HubSpot",
            "   - Check your logs for webhook event"
        ],
        "webhook_url": f"{backend_url}/webhooks/hubspot",
        "required_scopes": [
            "crm.objects.contacts.read",
            "crm.objects.contacts.write"
        ],
        "portal_id": user.hubspot_portal_id
    }

@router.get("/calendar/setup")
async def setup_calendar_watch(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Instructions for setting up Calendar webhooks
    """
    backend_url = settings.BACKEND_URL or "https://your-app.onrender.com"
    
    return {
        "instructions": [
            "1. Calendar webhooks use Google Cloud Pub/Sub (similar to Gmail)",
            "",
            "2. In your application code, call:",
            "   POST https://www.googleapis.com/calendar/v3/calendars/primary/events/watch",
            "   {",
            "     'id': 'unique-channel-id',",
            "     'type': 'web_hook',",
            f"     'address': '{backend_url}/webhooks/calendar'",
            "   }",
            "",
            "3. Store channel_id → user_id mapping in database",
            "",
            "4. Webhook will receive notifications for:",
            "   - Event creation",
            "   - Event updates",
            "   - Event deletion",
            "",
            "Note: Channel expires after ~1 week, need to renew"
        ],
        "webhook_url": f"{backend_url}/webhooks/calendar",
        "user_id": user.id
    }

# ============================================================================
# WEBHOOK TESTING ENDPOINTS (Development only)
# ============================================================================

@router.post("/test/gmail")
async def test_gmail_webhook(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Test Gmail webhook manually (development only)
    """
    if settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=403, detail="Only available in development")
    
    # Simulate Gmail webhook
    background_tasks.add_task(
        _process_gmail_webhook_with_proactive,
        db,
        user.id,
        {
            "email_address": user.email,
            "history_id": "test_history_123",
            "test": True
        }
    )
    
    return {"message": "Test webhook triggered"}

@router.post("/test/hubspot")
async def test_hubspot_webhook(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Test HubSpot webhook manually (development only)
    """
    if settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=403, detail="Only available in development")
    
    # Simulate HubSpot webhook
    background_tasks.add_task(
        _process_hubspot_webhook_with_proactive,
        db,
        user.id,
        "hubspot_contact",
        {
            "event": "created",
            "contact_id": "test_contact_123",
            "portal_id": user.hubspot_portal_id,
            "test": True
        }
    )
    
    return {"message": "Test webhook triggered"}