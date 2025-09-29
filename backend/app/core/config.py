# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Pydantic automatically loads from .env file in the working directory.
    """
    
    # ============================================================================
    # APPLICATION SETTINGS
    # ============================================================================
    APP_NAME: str = "Financial Advisor AI Agent"
    SECRET_KEY: str  # REQUIRED - generate with: openssl rand -base64 32
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENVIRONMENT: str = "development"  # development | production
    
    # ============================================================================
    # DATABASE SETTINGS
    # ============================================================================
    DATABASE_URL: str  # REQUIRED - postgresql://user:pass@host:port/dbname
    REDIS_URL: str = "redis://localhost:6379"
    
    # ============================================================================
    # GOOGLE OAUTH SETTINGS
    # ============================================================================
    GOOGLE_CLIENT_ID: str  # REQUIRED
    GOOGLE_CLIENT_SECRET: str  # REQUIRED
    GOOGLE_REDIRECT_URI: str  # REQUIRED
    GOOGLE_SCOPES: List[str] = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events"
    ]
    
    # ============================================================================
    # HUBSPOT OAUTH SETTINGS
    # ============================================================================
    HUBSPOT_CLIENT_ID: str  # REQUIRED
    HUBSPOT_CLIENT_SECRET: str  # REQUIRED
    HUBSPOT_REDIRECT_URI: str  # REQUIRED
    HUBSPOT_SCOPES: str = "crm.objects.contacts.read crm.objects.contacts.write crm.schemas.contacts.read oauth"
    
    # ============================================================================
    # FRONTEND & CORS SETTINGS
    # ============================================================================
    FRONTEND_URL: str  # REQUIRED - http://localhost:5173 or https://yourdomain.com
    ALLOWED_ORIGINS: str = "http://localhost:5173"  # Comma-separated if multiple
    
    # ============================================================================
    # ENCRYPTION SETTINGS
    # ============================================================================
    ENCRYPTION_KEY: str  # REQUIRED - generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    
    # ============================================================================
    # AI/ML API KEYS
    # ============================================================================
    OPENAI_API_KEY: str  # REQUIRED - for embeddings
    ANTHROPIC_API_KEY: str  # REQUIRED - for Claude AI agent
    
    # ============================================================================
    # RAG PIPELINE CONFIGURATION
    # ============================================================================
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    MAX_CONTEXT_DOCUMENTS: int = 10
    SIMILARITY_THRESHOLD: float = 0.7
    
    # ============================================================================
    # SECURITY & RATE LIMITING
    # ============================================================================
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Webhook Security (Optional but HIGHLY recommended for production)
    HUBSPOT_WEBHOOK_SECRET: Optional[str] = None
    GMAIL_WEBHOOK_TOKEN: Optional[str] = None
    
    # Backend URL (for webhook callbacks)
    BACKEND_URL: Optional[str] = "http://localhost:8000"
    
    # ============================================================================
    # COMPUTED PROPERTIES
    # ============================================================================
    
    @property
    def ALLOWED_HOSTS(self) -> List[str]:
        """Allowed hosts for TrustedHostMiddleware"""
        if self.ENVIRONMENT == "production":
            # In production, extract host from BACKEND_URL
            if self.BACKEND_URL:
                from urllib.parse import urlparse
                parsed = urlparse(self.BACKEND_URL)
                return [parsed.hostname or "localhost", "*.onrender.com"]
            return ["*.onrender.com"]
        return ["localhost", "127.0.0.1", "*"]
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list"""
        origins = []
        
        # Split comma-separated origins
        if isinstance(self.ALLOWED_ORIGINS, str):
            origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        
        # Always include FRONTEND_URL
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        
        return origins
    
    @property
    def IS_PRODUCTION(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def IS_DEVELOPMENT(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT.lower() == "development"
    
    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    
    def validate_production_settings(self) -> None:
        """Validate that all required production settings are configured"""
        if not self.IS_PRODUCTION:
            return
        
        errors = []
        
        # Check webhook secrets are set in production
        if not self.HUBSPOT_WEBHOOK_SECRET:
            errors.append("HUBSPOT_WEBHOOK_SECRET must be set in production")
        
        if not self.GMAIL_WEBHOOK_TOKEN:
            errors.append("GMAIL_WEBHOOK_TOKEN must be set in production")
        
        # Check HTTPS is used
        if self.FRONTEND_URL and not self.FRONTEND_URL.startswith("https://"):
            errors.append("FRONTEND_URL must use HTTPS in production")
        
        if self.BACKEND_URL and not self.BACKEND_URL.startswith("https://"):
            errors.append("BACKEND_URL must use HTTPS in production")
        
        if errors:
            raise ValueError(f"Production configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    # ============================================================================
    # PYDANTIC CONFIGURATION
    # ============================================================================
    
    class Config:
        # Auto-discover .env file in current working directory
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env
        
        # Optional: Customize .env file name for different environments
        # env_file = ".env"  # Not needed - auto-discovery works!
        # env_file_encoding = "utf-8"


# ============================================================================
# SETTINGS SINGLETON WITH CACHING
# ============================================================================

@lru_cache()
def get_settings() -> Settings:
    """
    Create cached settings instance.
    This ensures settings are loaded only once and reused across the app.
    
    Usage:
        from app.core.config import get_settings
        settings = get_settings()
    """
    _settings = Settings()
    
    # Validate production settings on startup
    try:
        _settings.validate_production_settings()
    except ValueError as e:
        if _settings.IS_PRODUCTION:
            raise  # Fail fast in production
        else:
            print(f"⚠️  Warning: {e}")  # Just warn in development
    
    return _settings


# Default settings instance for backward compatibility
settings = get_settings()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def reload_settings() -> Settings:
    """
    Force reload settings (clears cache).
    Useful for testing or dynamic config updates.
    """
    get_settings.cache_clear()
    return get_settings()


def print_settings_summary() -> None:
    """Print a summary of loaded settings (without secrets)"""
    _settings = get_settings()
    
    print("\n" + "="*60)
    print("🔧 CONFIGURATION SUMMARY")
    print("="*60)
    print(f"Environment: {_settings.ENVIRONMENT}")
    print(f"App Name: {_settings.APP_NAME}")
    print(f"Backend URL: {_settings.BACKEND_URL}")
    print(f"Frontend URL: {_settings.FRONTEND_URL}")
    print(f"Database: {_settings.DATABASE_URL.split('@')[1] if '@' in _settings.DATABASE_URL else 'configured'}")
    print(f"Redis: {_settings.REDIS_URL}")
    print(f"AI Models: Claude + {_settings.EMBEDDING_MODEL}")
    print(f"Google OAuth: {'✓ Configured' if _settings.GOOGLE_CLIENT_ID else '✗ Missing'}")
    print(f"HubSpot OAuth: {'✓ Configured' if _settings.HUBSPOT_CLIENT_ID else '✗ Missing'}")
    print(f"Webhook Security: {'✓ Enabled' if _settings.HUBSPOT_WEBHOOK_SECRET else '⚠ Optional'}")
    print("="*60 + "\n")


# ============================================================================
# STARTUP VALIDATION (Optional - uncomment to enable)
# ============================================================================

# Uncomment to validate settings on import
# print_settings_summary()