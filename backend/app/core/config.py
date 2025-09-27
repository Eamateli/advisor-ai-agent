from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Financial Advisor AI Agent"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    GOOGLE_SCOPES: list = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events"
    ]
    
    # HubSpot OAuth
    HUBSPOT_CLIENT_ID: str
    HUBSPOT_CLIENT_SECRET: str
    HUBSPOT_REDIRECT_URI: str
    HUBSPOT_SCOPES: str = "crm.objects.contacts.read crm.objects.contacts.write crm.schemas.contacts.read oauth"
    
    # Frontend
    FRONTEND_URL: str
    
    # Encryption for OAuth tokens
    ENCRYPTION_KEY: str
    
    # Security
    ALLOWED_HOSTS: list = ["localhost", "127.0.0.1"]
    
    class Config:
        env_file = "../.env"
        case_sensitive = True

settings = Settings()