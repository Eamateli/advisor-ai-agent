# backend/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.middleware import ErrorHandlingMiddleware, RequestValidationMiddleware
from app.core.exceptions import (
    BusinessLogicError,
    InsufficientPermissionsError,
    ExternalAPIError,
    business_logic_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    permission_exception_handler,
    external_api_exception_handler
)

# Import all routers
from app.api import auth, rag, sync, webhooks, chat, profile

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME}...")

    # Add production validation
    if settings.ENVIRONMENT == "production":
        # Core required secrets (app won't work without these)
        required_secrets = {
            "SECRET_KEY": settings.SECRET_KEY,
            "ENCRYPTION_KEY": settings.ENCRYPTION_KEY,
            "ANTHROPIC_API_KEY": settings.ANTHROPIC_API_KEY,
            "OPENAI_API_KEY": settings.OPENAI_API_KEY,
            "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
            "GOOGLE_CLIENT_SECRET": settings.GOOGLE_CLIENT_SECRET,
        }
        
        # Optional integrations (app works without these)
        optional_integrations = {
            "HUBSPOT_CLIENT_ID": settings.HUBSPOT_CLIENT_ID,
            "HUBSPOT_CLIENT_SECRET": settings.HUBSPOT_CLIENT_SECRET,
        }
    
        missing = [name for name, value in required_secrets.items() if not value]
        
        if missing:
            error_msg = f"[FAIL] CRITICAL: Missing required secrets in production: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Check optional integrations
        missing_optional = [name for name, value in optional_integrations.items() if not value]
        if missing_optional:
            logger.warning(f"Optional integrations not configured: {', '.join(missing_optional)}")
            logger.info("App will work without these integrations")
        
        logger.info("[PASS] All required production secrets validated")
    
    # Initialize database tables (use Alembic migrations instead)
    # Note: pgvector extension must be enabled first via migrations
    # Run: alembic upgrade head
    try:
        from app.core.database import engine
        # Test database connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection successful")
    except Exception as e:
        logger.warning(f"Database connection issue: {e}")
    
    # Note: Tables should be created via Alembic migrations, not here
    # Uncomment below only for development without migrations:
    # from app.core.database import Base
    # Base.metadata.create_all(bind=engine)
    logger.info("Database ready (use 'alembic upgrade head' to create tables)")
    
    # Initialize vector indexes if needed
    try:
        from app.services.vector_index import create_vector_indexes
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            create_vector_indexes(db)
            logger.info("Vector indexes initialized")
        except Exception as e:
            logger.error(f"Error creating vector indexes: {e}")
        finally:
            db.close()
    except ImportError:
        logger.warning("Vector index module not found, skipping initialization")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")

# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.APP_NAME,
    description="AI Agent for Financial Advisors with Gmail, Calendar, and HubSpot integrations",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Add middleware (order matters - applied in reverse)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Only add custom middleware if modules exist
try:
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestValidationMiddleware)
except NameError:
    logger.warning("Custom middleware not found, using defaults only")

# Security Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS + ["*.onrender.com"] if settings.ENVIRONMENT == "production" else ["*"]
)

# CORS Configuration - Allow all origins in development
if settings.ENVIRONMENT == "development":
    origins = ["*"]  # Allow all origins in development
else:
    # Production CORS configuration
    if isinstance(settings.ALLOWED_ORIGINS, str):
        origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
    else:
        origins = [settings.ALLOWED_ORIGINS]

    if settings.FRONTEND_URL and settings.FRONTEND_URL not in origins:
        origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time", "X-RateLimit-*"]
)

# Register exception handlers (if custom exceptions module exists)
try:
    app.add_exception_handler(BusinessLogicError, business_logic_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(InsufficientPermissionsError, permission_exception_handler)
    app.add_exception_handler(ExternalAPIError, external_api_exception_handler)
except NameError:
    pass  # Custom exception handlers not available

# Include all routers with /api/v1 prefix for consistency
app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(rag.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")

# Root endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    """Detailed health check for monitoring"""
    from app.core.database import SessionLocal
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "database": "unknown",
        "services": {},
        "oauth": {
            "google": bool(settings.GOOGLE_CLIENT_ID),
            "hubspot": bool(settings.HUBSPOT_CLIENT_ID)
        },
        "apis": {
            "openai": bool(settings.OPENAI_API_KEY),
            "anthropic": bool(settings.ANTHROPIC_API_KEY)
        },
        "integrations": {
            "gmail": "configured" if settings.GOOGLE_CLIENT_ID else "not configured",
            "calendar": "configured" if settings.GOOGLE_CLIENT_ID else "not configured",
            "hubspot": "configured" if settings.HUBSPOT_CLIENT_ID else "not configured"
        },
        "agent": {
            "tools": "configured",
            "streaming": "enabled"
        }
    }
    
    # Check database
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["database"] = "connected"
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["database"] = "disconnected"
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis (if rate limiter is available)
    try:
        from app.core.rate_limit import rate_limiter
        if rate_limiter.enabled:
            rate_limiter.redis_client.ping()
            health_status["services"]["redis"] = "healthy"
        else:
            health_status["services"]["redis"] = "disabled"
    except ImportError:
        health_status["services"]["redis"] = "not configured"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint for monitoring"""
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.models.document import Document
    from app.models.chat import ChatMessage
    
    db = SessionLocal()
    
    try:
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        metrics_data = {
            "timestamp": now.isoformat(),
            "users": {
                "total": db.query(User).count(),
                "active": db.query(User).filter(User.is_active == True).count()
            },
            "documents": {
                "total": db.query(Document).count()
            },
            "messages": {
                "total": db.query(ChatMessage).count(),
                "last_hour": db.query(ChatMessage).filter(ChatMessage.created_at > last_hour).count(),
                "last_day": db.query(ChatMessage).filter(ChatMessage.created_at > last_day).count()
            }
        }
        
        # Try to add audit logs if available
        try:
            from app.core.audit import AuditLog
            metrics_data["audit_logs"] = {
                "last_hour": db.query(AuditLog).filter(AuditLog.created_at > last_hour).count(),
                "last_day": db.query(AuditLog).filter(AuditLog.created_at > last_day).count()
            }
        except ImportError:
            pass
        
        return metrics_data
    
    finally:
        db.close()

# Custom 404 handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": f"The requested URL {request.url.path} was not found",
            "request_id": getattr(request.state, "request_id", None)
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level="info",
        access_log=True
    )