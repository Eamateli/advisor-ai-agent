# backend/app/core/middleware.py
"""
Custom middleware for error handling and request logging
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import traceback
from app.core.config import settings

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            # Add request ID for tracing
            request.state.request_id = f"{time.time()}"
            
            # Time the request
            start_time = time.time()
            
            response = await call_next(request)
            
            # Log request
            process_time = time.time() - start_time
            logger.info(
                f"{request.method} {request.url.path} "
                f"completed in {process_time:.3f}s"
            )
            
            # Add custom headers
            response.headers["X-Request-ID"] = request.state.request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        
        except HTTPException as exc:
            # Let FastAPI handle HTTP exceptions normally
            raise exc
        
        except Exception as exc:
            # Log the full traceback
            logger.error(
                f"Unhandled exception: {exc}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            
            # Don't leak sensitive info in production
            if settings.ENVIRONMENT == "production":
                error_detail = "An internal error occurred"
            else:
                error_detail = str(exc)
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "detail": error_detail,
                    "request_id": getattr(request.state, "request_id", None)
                }
            )

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize incoming requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            max_size = 10 * 1024 * 1024  # 10MB
            if int(content_length) > max_size:
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request too large"}
                )
        
        # Security headers
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' wss: https:;"
            )
        
        return response

# ============================================================================
# Update backend/app/main.py to use middleware
"""
Add to your main.py after creating the FastAPI app:
"""

# from app.core.middleware import ErrorHandlingMiddleware, RequestValidationMiddleware

# app.add_middleware(ErrorHandlingMiddleware)
# app.add_middleware(RequestValidationMiddleware)

# ============================================================================
# backend/app/core/exceptions.py
"""
Custom exceptions and handlers
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)

class BusinessLogicError(Exception):
    """Custom exception for business logic errors"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class InsufficientPermissionsError(Exception):
    """Raised when user lacks required permissions"""
    def __init__(self, message: str = "Insufficient permissions"):
        self.message = message
        super().__init__(self.message)

class ExternalAPIError(Exception):
    """Raised when external API calls fail"""
    def __init__(self, service: str, message: str):
        self.service = service
        self.message = message
        super().__init__(f"{service} API error: {message}")

# Exception handlers to register in FastAPI
async def business_logic_exception_handler(request: Request, exc: BusinessLogicError):
    """Handle business logic errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Business Logic Error",
            "detail": exc.message,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with clean messages"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"][1:]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": "Invalid input data",
            "errors": errors,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

async def permission_exception_handler(request: Request, exc: InsufficientPermissionsError):
    """Handle permission errors"""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "Permission Denied",
            "detail": exc.message,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

async def external_api_exception_handler(request: Request, exc: ExternalAPIError):
    """Handle external API errors"""
    logger.error(f"External API error: {exc.service} - {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": "External Service Error",
            "service": exc.service,
            "detail": exc.message,
            "request_id": getattr(request.state, "request_id", None)
        }
    )