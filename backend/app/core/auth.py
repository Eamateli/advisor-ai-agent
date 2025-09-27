from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.core.security import verify_token
from app.core.encryption import token_encryption
from app.models.user import User
from app.services.google_oauth import google_oauth
from app.services.hubspot_oauth import hubspot_oauth

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

async def get_google_credentials(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get valid Google credentials, refreshing if necessary"""
    if not user.google_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account not connected"
        )
    
    # Decrypt tokens
    access_token = token_encryption.decrypt(user.google_access_token)
    refresh_token = token_encryption.decrypt(user.google_refresh_token)
    
    # Check if token is expired
    if user.google_token_expiry < datetime.utcnow():
        # Refresh token
        token_data = await google_oauth.refresh_access_token(refresh_token)
        
        # Update database with new encrypted tokens
        user.google_access_token = token_encryption.encrypt(token_data["access_token"])
        user.google_token_expiry = token_data["token_expiry"]
        db.commit()
        
        access_token = token_data["access_token"]
    
    return google_oauth.get_credentials(access_token, refresh_token, user.google_token_expiry)

async def get_hubspot_token(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> str:
    """Get valid HubSpot access token, refreshing if necessary"""
    if not user.hubspot_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HubSpot account not connected"
        )
    
    # Decrypt tokens
    access_token = token_encryption.decrypt(user.hubspot_access_token)
    refresh_token = token_encryption.decrypt(user.hubspot_refresh_token)
    
    # Check if token is expired
    if user.hubspot_token_expiry < datetime.utcnow():
        # Refresh token
        token_data = await hubspot_oauth.refresh_access_token(refresh_token)
        
        # Update database with new encrypted tokens
        user.hubspot_access_token = token_encryption.encrypt(token_data["access_token"])
        user.hubspot_refresh_token = token_encryption.encrypt(token_data["refresh_token"])
        user.hubspot_token_expiry = token_data["token_expiry"]
        db.commit()
        
        access_token = token_data["access_token"]
    
    return access_token