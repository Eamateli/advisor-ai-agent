from fastapi import Request, HTTPException, status
from typing import Dict, Optional
import time
import redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting using Redis with sliding window"""
    
    def __init__(self):
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.redis_client.ping()  # Test connection
            self.enabled = True
            logger.info("[PASS] Rate limiter initialized with Redis")
        except Exception as e:
            # In production, Redis is required for security
            if settings.ENVIRONMENT == "production":
                logger.error(f"[FAIL] Redis connection REQUIRED in production: {e}")
                raise RuntimeError("Redis connection required for production rate limiting") from e
            else:
                logger.warning(f"⚠️  Redis not available in dev, rate limiting disabled: {e}")
                self.redis_client = None
                self.enabled = False
    
    def _get_key(self, identifier: str, endpoint: str) -> str:
        """Generate rate limit key"""
        return f"ratelimit:{endpoint}:{identifier}"
    
    async def check_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int
    ) -> Dict:
        """
        Check if request should be rate limited
        
        Returns:
            Dict with 'allowed' (bool) and metadata
        """
        if not self.enabled:
            return {"allowed": True, "remaining": max_requests}
        
        key = self._get_key(identifier, endpoint)
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        try:
            pipe = self.redis_client.pipeline()
            
            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiry
            pipe.expire(key, window_seconds)
            
            results = pipe.execute()
            request_count = results[1]
            
            # Check if limit exceeded
            if request_count >= max_requests:
                # Get oldest request time for reset calculation
                oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
                reset_time = int(oldest[0][1]) + window_seconds if oldest else current_time + window_seconds
                
                return {
                    "allowed": False,
                    "limit": max_requests,
                    "remaining": 0,
                    "reset": reset_time
                }
            
            return {
                "allowed": True,
                "limit": max_requests,
                "remaining": max_requests - request_count,
                "reset": current_time + window_seconds
            }
        
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # On error, allow request (fail open)
            return {"allowed": True, "remaining": max_requests}
    
    async def check_request(
        self,
        request: Request,
        user_id: Optional[int] = None,
        max_per_minute: int = None,
        max_per_hour: int = None
    ):
        """
        Check rate limits for a request
        
        Raises HTTPException if rate limited
        """
        if not self.enabled:
            return
        
        # Use defaults from config if not specified
        if max_per_minute is None:
            max_per_minute = settings.RATE_LIMIT_PER_MINUTE
        if max_per_hour is None:
            max_per_hour = settings.RATE_LIMIT_PER_HOUR
        
        # Identify user
        identifier = str(user_id) if user_id else request.client.host
        endpoint = request.url.path
        
        # Check per-minute limit
        minute_result = await self.check_rate_limit(
            identifier=identifier,
            endpoint=endpoint,
            max_requests=max_per_minute,
            window_seconds=60
        )
        
        if not minute_result["allowed"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": minute_result["limit"],
                    "reset": minute_result["reset"],
                    "retry_after": minute_result["reset"] - int(time.time())
                },
                headers={
                    "X-RateLimit-Limit": str(minute_result["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(minute_result["reset"]),
                    "Retry-After": str(minute_result["reset"] - int(time.time()))
                }
            )
        
        # Check per-hour limit
        hour_result = await self.check_rate_limit(
            identifier=identifier,
            endpoint=endpoint,
            max_requests=max_per_hour,
            window_seconds=3600
        )
        
        if not hour_result["allowed"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Hourly rate limit exceeded",
                    "limit": hour_result["limit"],
                    "reset": hour_result["reset"],
                    "retry_after": hour_result["reset"] - int(time.time())
                },
                headers={
                    "X-RateLimit-Limit": str(hour_result["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(hour_result["reset"]),
                    "Retry-After": str(hour_result["reset"] - int(time.time()))
                }
            )
        
        # Add rate limit headers
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit-Minute": str(max_per_minute),
            "X-RateLimit-Remaining-Minute": str(minute_result["remaining"]),
            "X-RateLimit-Limit-Hour": str(max_per_hour),
            "X-RateLimit-Remaining-Hour": str(hour_result["remaining"])
        }

rate_limiter = RateLimiter()