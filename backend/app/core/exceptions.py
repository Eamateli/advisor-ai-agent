# backend/app/core/exceptions.py
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
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

# Exception handlers
async def business_logic_exception_handler(request: Request, exc: BusinessLogicError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Business Logic Error", "detail": exc.message}
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation Error", "detail": str(exc)}
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

async def permission_exception_handler(request: Request, exc: InsufficientPermissionsError):
    return JSONResponse(
        status_code=403,
        content={"error": "Permission Denied", "detail": exc.message}
    )

async def external_api_exception_handler(request: Request, exc: ExternalAPIError):
    return JSONResponse(
        status_code=502,
        content={"error": "External Service Error", "service": exc.service}
    )