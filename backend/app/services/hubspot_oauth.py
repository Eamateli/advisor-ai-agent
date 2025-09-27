from typing import Optional
from datetime import datetime, timedelta
import httpx
from app.core.config import settings

class HubSpotOAuthService:
    """Handles HubSpot OAuth flow and token management"""
    
    def __init__(self):
        self.auth_url = "https://app.hubspot.com/oauth/authorize"
        self.token_url = "https://api.hubapi.com/oauth/v1/token"
    
    def get_authorization_url(self, state: str) -> str:
        """Generate HubSpot OAuth authorization URL"""
        params = {
            "client_id": settings.HUBSPOT_CLIENT_ID,
            "redirect_uri": settings.HUBSPOT_REDIRECT_URI,
            "scope": settings.HUBSPOT_SCOPES,
            "state": state
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_url}?{query_string}"
    
    async def exchange_code_for_tokens(self, code: str) -> dict:
        """Exchange authorization code for access and refresh tokens"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.HUBSPOT_CLIENT_ID,
                    "client_secret": settings.HUBSPOT_CLIENT_SECRET,
                    "redirect_uri": settings.HUBSPOT_REDIRECT_URI,
                    "code": code
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Calculate expiry
            expiry = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 21600))
            
            return {
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
                "token_expiry": expiry
            }
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh an expired access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "client_id": settings.HUBSPOT_CLIENT_ID,
                    "client_secret": settings.HUBSPOT_CLIENT_SECRET,
                    "refresh_token": refresh_token
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Calculate expiry
            expiry = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 21600))
            
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", refresh_token),  # HubSpot may not return new refresh token
                "token_expiry": expiry
            }
    
    async def get_account_info(self, access_token: str) -> dict:
        """Get HubSpot account information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.hubapi.com/oauth/v1/access-tokens/" + access_token
            )
            response.raise_for_status()
            return response.json()

hubspot_oauth = HubSpotOAuthService()