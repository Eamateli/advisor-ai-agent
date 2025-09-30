from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta
import secrets
from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.core.encryption import token_encryption
from app.models.user import User
from app.services.google_oauth import google_oauth
from app.services.hubspot_oauth import hubspot_oauth
from app.core.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory state storage (use Redis in production)
oauth_states = {}

@router.get("/google/login")
async def google_login():
    """Initiate Google OAuth flow"""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"provider": "google"}
    
    auth_url = google_oauth.get_authorization_url(state)
    return {"authorization_url": auth_url}

@router.get("/google/callback")
async def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    # Verify state
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    del oauth_states[state]
    
    # Exchange code for tokens
    token_data = await google_oauth.exchange_code_for_tokens(code)
    user_info = token_data["user_info"]
    
    # Check if user exists
    user = db.query(User).filter(User.email == user_info["email"]).first()
    
    if not user:
        # Create new user
        user = User(
            email=user_info["email"],
            full_name=user_info.get("name"),
            profile_picture=user_info.get("picture"),
            google_id=user_info["id"],
            google_access_token=token_encryption.encrypt(token_data["access_token"]),
            google_refresh_token=token_encryption.encrypt(token_data["refresh_token"]),
            google_token_expiry=token_data["token_expiry"]
        )
        db.add(user)
    else:
        # Update existing user
        user.google_id = user_info["id"]
        user.google_access_token = token_encryption.encrypt(token_data["access_token"])
        user.google_refresh_token = token_encryption.encrypt(token_data["refresh_token"])
        user.google_token_expiry = token_data["token_expiry"]
        user.full_name = user_info.get("name", user.full_name)
        user.profile_picture = user_info.get("picture", user.profile_picture)
    
    db.commit()
    db.refresh(user)
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Redirect to frontend with token
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/callback?token={access_token}")

@router.get("/hubspot/login")
async def hubspot_login(user: User = Depends(get_current_user)):
    """Initiate HubSpot OAuth flow"""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"provider": "hubspot", "user_id": user.id}
    
    auth_url = hubspot_oauth.get_authorization_url(state)
    return {"authorization_url": auth_url}

@router.get("/hubspot/callback")
async def hubspot_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Handle HubSpot OAuth callback"""
    # Verify state
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    state_data = oauth_states[state]
    del oauth_states[state]
    
    user_id = state_data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in state")
    
    # Exchange code for tokens
    token_data = await hubspot_oauth.exchange_code_for_tokens(code)
    
    # Get account info
    account_info = await hubspot_oauth.get_account_info(token_data["access_token"])
    
    # Update user with HubSpot tokens
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hubspot_access_token = token_encryption.encrypt(token_data["access_token"])
    user.hubspot_refresh_token = token_encryption.encrypt(token_data["refresh_token"])
    user.hubspot_token_expiry = token_data["token_expiry"]
    user.hubspot_portal_id = account_info.get("hub_id")
    
    db.commit()
    
    # Redirect to frontend
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings?hubspot=connected")

@router.get("/me")
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "profile_picture": user.profile_picture,
        "google_connected": bool(user.google_access_token),
        "hubspot_connected": bool(user.hubspot_access_token)
    }

@router.post("/logout")
async def logout():
    """Logout user (client should delete token)"""
    return {"message": "Logged out successfully"}