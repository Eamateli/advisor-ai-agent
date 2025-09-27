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
    REDIS_URL: str = "redis://localhost:6379"
    
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
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    
    # Encryption for OAuth tokens
    ENCRYPTION_KEY: str

    # Environment
    ENVIRONMENT: str = "development"
    
    # OpenAI for Embeddings (RAG Pipeline)
    OPENAI_API_KEY: str
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    
    # Anthropic Claude for AI Agent
    ANTHROPIC_API_KEY: str
    
    # RAG Configuration
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    MAX_CONTEXT_DOCUMENTS: int = 10
    SIMILARITY_THRESHOLD: float = 0.7
    
    # Rate Limiting (Security)
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Webhook Security (Optional)
    HUBSPOT_WEBHOOK_SECRET: Optional[str] = None
    GMAIL_WEBHOOK_TOKEN: Optional[str] = None
    
    # Backend URL (for webhooks)
    BACKEND_URL: Optional[str] = "http://localhost:8000"
    
    # Security
    @property
    def ALLOWED_HOSTS(self) -> list:
        return ["localhost", "127.0.0.1"]
    
    class Config:
        env_file = "../.env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()