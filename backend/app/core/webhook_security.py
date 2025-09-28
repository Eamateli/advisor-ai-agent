import hmac
import hashlib
from fastapi import HTTPException, status
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class WebhookSecurity:
    """Webhook signature verification"""
    
    @staticmethod
    def verify_hubspot_signature(
        signature: str,
        body: bytes,
        secret: str
    ) -> bool:
        """
        Verify HubSpot webhook signature
        
        HubSpot uses SHA-256 HMAC
        """
        if not signature or not secret:
            logger.warning("Missing signature or secret for HubSpot webhook")
            return False
        
        try:
            # Calculate expected signature
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures (timing-safe)
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            if not is_valid:
                logger.warning("Invalid HubSpot webhook signature")
            
            return is_valid
        
        except Exception as e:
            logger.error(f"Error verifying HubSpot signature: {e}")
            return False
    
    @staticmethod
    def verify_gmail_pubsub(
        token: Optional[str],
        expected_token: Optional[str]
    ) -> bool:
        """
        Verify Gmail Pub/Sub webhook token
        
        Gmail/Google Cloud Pub/Sub can include a verification token
        """
        if not expected_token:
            # If no token configured, skip verification (not recommended for prod)
            logger.warning("No Gmail webhook token configured")
            return True
        
        if not token:
            logger.warning("No token in Gmail webhook request")
            return False
        
        is_valid = hmac.compare_digest(token, expected_token)
        
        if not is_valid:
            logger.warning("Invalid Gmail webhook token")
        
        return is_valid
    
    @staticmethod
    def verify_request_origin(
        origin: Optional[str],
        allowed_origins: list
    ) -> bool:
        """Verify request comes from allowed origin"""
        if not origin:
            return False
        
        return origin in allowed_origins
    
    @staticmethod
    def enforce_signature(
        signature: Optional[str],
        body: bytes,
        secret: str,
        provider: str = "hubspot"
    ):
        """
        Enforce webhook signature verification
        
        Raises HTTPException if invalid
        """
        is_valid = False
        
        if provider == "hubspot":
            is_valid = WebhookSecurity.verify_hubspot_signature(signature, body, secret)
        
        if not is_valid:
            logger.error(f"Webhook signature verification failed for {provider}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

webhook_security = WebhookSecurity()