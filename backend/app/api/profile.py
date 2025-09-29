# backend/app/api/profile.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/profile", tags=["Profile"])

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

class ProfileResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    profile_picture: Optional[str]
    google_connected: bool
    hubspot_connected: bool
    created_at: str

@router.get("/", response_model=ProfileResponse)
async def get_profile(user: User = Depends(get_current_user)):
    """Get current user profile"""
    return ProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        profile_picture=user.profile_picture,
        google_connected=bool(user.google_access_token),
        hubspot_connected=bool(user.hubspot_access_token),
        created_at=user.created_at.isoformat()
    )

@router.post("/disconnect/google")
async def disconnect_google(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect Google account"""
    if not user.google_access_token:
        raise HTTPException(
            status_code=400,
            detail="Google account not connected"
        )
    
    # Clear Google tokens and related data
    user.google_id = None
    user.google_access_token = None
    user.google_refresh_token = None
    user.google_token_expiry = None
    
    db.commit()
    
    return {"message": "Google account disconnected successfully"}

@router.post("/disconnect/hubspot")
async def disconnect_hubspot(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect HubSpot account"""
    if not user.hubspot_access_token:
        raise HTTPException(
            status_code=400,
            detail="HubSpot account not connected"
        )
    
    # Clear HubSpot tokens and related data
    user.hubspot_access_token = None
    user.hubspot_refresh_token = None
    user.hubspot_token_expiry = None
    user.hubspot_portal_id = None
    
    db.commit()
    
    return {"message": "HubSpot account disconnected successfully"}

@router.patch("/", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    
    # Update fields if provided
    if profile_data.full_name is not None:
        user.full_name = profile_data.full_name
    
    if profile_data.email is not None:
        # Check if email already exists
        existing_user = db.query(User).filter(
            User.email == profile_data.email,
            User.id != user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        user.email = profile_data.email
    
    db.commit()
    db.refresh(user)
    
    return ProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        profile_picture=user.profile_picture,
        google_connected=bool(user.google_access_token),
        hubspot_connected=bool(user.hubspot_access_token),
        created_at=user.created_at.isoformat()
    )