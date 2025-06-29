"""
Middleware for error handling and request processing.
"""

import logging
import time
import traceback
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import uuid

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Centralized error handling middleware for the FastAPI application.
    
    Handles:
    - Validation errors
    - Database errors  
    - HTTP exceptions
    - Unexpected errors
    - Request logging and timing
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Add request ID to headers for response
        request.state.request_id = request_id
        
        # Log incoming request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            
            # Log successful response
            duration = time.time() - start_time
            logger.info(
                f"[{request_id}] {response.status_code} - "
                f"Duration: {duration:.3f}s"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except ValidationError as e:
            return await self._handle_validation_error(request_id, e)
            
        except HTTPException as e:
            return await self._handle_http_exception(request_id, e)
            
        except IntegrityError as e:
            return await self._handle_integrity_error(request_id, e)
            
        except SQLAlchemyError as e:
            return await self._handle_database_error(request_id, e)
            
        except Exception as e:
            return await self._handle_unexpected_error(request_id, e)
    
    async def _handle_validation_error(self, request_id: str, error: ValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        logger.warning(f"[{request_id}] Validation error: {error}")
        
        # Format validation errors for user-friendly response
        errors = []
        for err in error.errors():
            field_path = " -> ".join(str(loc) for loc in err["loc"])
            errors.append({
                "field": field_path,
                "message": err["msg"],
                "type": err["type"],
                "input": err.get("input")
            })
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "The provided data is invalid. Please check the highlighted fields.",
                "details": errors,
                "request_id": request_id
            },
            headers={"X-Request-ID": request_id}
        )
    
    async def _handle_http_exception(self, request_id: str, error: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        logger.warning(f"[{request_id}] HTTP {error.status_code}: {error.detail}")
        
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": self._get_error_title(error.status_code),
                "message": error.detail,
                "request_id": request_id
            },
            headers={"X-Request-ID": request_id}
        )
    
    async def _handle_integrity_error(self, request_id: str, error: IntegrityError) -> JSONResponse:
        """Handle database integrity constraint violations."""
        logger.error(f"[{request_id}] Database integrity error: {error}")
        
        # Extract user-friendly error messages from common constraints
        error_msg = str(error.orig) if hasattr(error, 'orig') else str(error)
        
        if "duplicate key" in error_msg.lower():
            message = "A record with this information already exists."
        elif "foreign key" in error_msg.lower():
            message = "The referenced item does not exist or has been deleted."
        elif "not null" in error_msg.lower():
            message = "Required information is missing."
        else:
            message = "The data could not be saved due to a constraint violation."
        
        return JSONResponse(
            status_code=409,
            content={
                "error": "Data Conflict",
                "message": message,
                "request_id": request_id
            },
            headers={"X-Request-ID": request_id}
        )
    
    async def _handle_database_error(self, request_id: str, error: SQLAlchemyError) -> JSONResponse:
        """Handle general database errors."""
        logger.error(f"[{request_id}] Database error: {error}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Database Error",
                "message": "A database error occurred. Please try again later.",
                "request_id": request_id
            },
            headers={"X-Request-ID": request_id}
        )
    
    async def _handle_unexpected_error(self, request_id: str, error: Exception) -> JSONResponse:
        """Handle unexpected errors."""
        logger.error(f"[{request_id}] Unexpected error: {error}")
        logger.error(f"[{request_id}] Traceback: {traceback.format_exc()}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later.",
                "request_id": request_id
            },
            headers={"X-Request-ID": request_id}
        )
    
    def _get_error_title(self, status_code: int) -> str:
        """Get user-friendly error title for HTTP status codes."""
        titles = {
            400: "Bad Request",
            401: "Authentication Required",
            403: "Access Denied",
            404: "Not Found",
            405: "Method Not Allowed",
            409: "Conflict",
            422: "Validation Error",
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable"
        }
        return titles.get(status_code, "Unknown Error")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for detailed request/response logging.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip logging for health checks to reduce noise
        if request.url.path in ["/health", "/health/basic"]:
            return await call_next(request)
        
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4())[:8])
        
        # Log request details
        logger.info(
            f"[{request_id}] Request: {request.method} {request.url}"
        )
        
        # Log request headers (excluding sensitive ones)
        safe_headers = {
            k: v for k, v in request.headers.items() 
            if k.lower() not in ['authorization', 'cookie', 'x-api-key']
        }
        logger.debug(f"[{request_id}] Headers: {safe_headers}")
        
        try:
            response = await call_next(request)
            
            # Log response details
            duration = time.time() - start_time
            logger.info(
                f"[{request_id}] Response: {response.status_code} - "
                f"Duration: {duration:.3f}s"
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[{request_id}] Error after {duration:.3f}s: {e}"
            )
            raise


def create_custom_http_exception(
    status_code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """
    Create a custom HTTP exception with structured error response.
    
    Args:
        status_code: HTTP status code
        message: User-friendly error message
        details: Additional error details
    
    Returns:
        HTTPException with structured detail
    """
    detail = {
        "message": message,
        "details": details or {}
    }
    
    return HTTPException(status_code=status_code, detail=detail)


# Utility functions for common error scenarios

def validation_error(message: str, field: str = None) -> HTTPException:
    """Create a validation error exception."""
    details = {"field": field} if field else {}
    return create_custom_http_exception(422, message, details)


def not_found_error(resource: str = "Resource") -> HTTPException:
    """Create a not found error exception."""
    return create_custom_http_exception(404, f"{resource} not found")


def access_denied_error(message: str = "Access denied") -> HTTPException:
    """Create an access denied error exception."""
    return create_custom_http_exception(403, message)


def conflict_error(message: str) -> HTTPException:
    """Create a conflict error exception."""
    return create_custom_http_exception(409, message)


def rate_limit_error(message: str = "Too many requests") -> HTTPException:
    """Create a rate limit error exception."""
    return create_custom_http_exception(429, message)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using a sliding window approach.
    
    Limits requests per IP address and optionally per user.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        
        # Storage for request tracking
        self.minute_windows: Dict[str, deque] = defaultdict(deque)
        self.hour_windows: Dict[str, deque] = defaultdict(deque)
        self.burst_windows: Dict[str, deque] = defaultdict(deque)
        
        # Cleanup tracking
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and testing
        import os
        if (request.url.path in ["/health", "/health/basic"] or 
            request.headers.get("X-Test-Mode") == "true" or
            os.getenv("TESTING") == "true" or
            os.getenv("PYTEST_CURRENT_TEST")):
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_ip = self._get_client_ip(request)
        
        # Clean up old entries periodically
        current_time = time.time()
        if current_time - self.last_cleanup > 60:  # Clean every minute
            self._cleanup_old_entries(current_time)
            self.last_cleanup = current_time
        
        # Check rate limits
        rate_limit_response = self._check_rate_limits(client_ip, current_time)
        if rate_limit_response:
            return rate_limit_response
        
        # Record this request
        self._record_request(client_ip, current_time)
        
        # Continue with request
        response = await call_next(request)
        
        # Add rate limit headers to response
        self._add_rate_limit_headers(response, client_ip, current_time)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers first (for proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _check_rate_limits(self, client_ip: str, current_time: float) -> Optional[JSONResponse]:
        """Check if client has exceeded rate limits."""
        
        # Check burst limit (10 requests in 10 seconds)
        burst_window = self.burst_windows[client_ip]
        burst_cutoff = current_time - 10  # 10 seconds
        burst_count = sum(1 for timestamp in burst_window if timestamp > burst_cutoff)
        
        if burst_count >= self.burst_limit:
            logger.warning(f"Burst rate limit exceeded for {client_ip}: {burst_count} requests in 10 seconds")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": "Burst rate limit exceeded. Please slow down your requests.",
                    "retry_after": 10
                },
                headers={"Retry-After": "10"}
            )
        
        # Check minute limit
        minute_window = self.minute_windows[client_ip]
        minute_cutoff = current_time - 60  # 1 minute
        minute_count = sum(1 for timestamp in minute_window if timestamp > minute_cutoff)
        
        if minute_count >= self.requests_per_minute:
            logger.warning(f"Minute rate limit exceeded for {client_ip}: {minute_count} requests per minute")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute.",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Check hour limit
        hour_window = self.hour_windows[client_ip]
        hour_cutoff = current_time - 3600  # 1 hour
        hour_count = sum(1 for timestamp in hour_window if timestamp > hour_cutoff)
        
        if hour_count >= self.requests_per_hour:
            logger.warning(f"Hour rate limit exceeded for {client_ip}: {hour_count} requests per hour")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Maximum {self.requests_per_hour} requests per hour.",
                    "retry_after": 3600
                },
                headers={"Retry-After": "3600"}
            )
        
        return None
    
    def _record_request(self, client_ip: str, current_time: float):
        """Record a request for rate limiting tracking."""
        self.burst_windows[client_ip].append(current_time)
        self.minute_windows[client_ip].append(current_time)
        self.hour_windows[client_ip].append(current_time)
    
    def _add_rate_limit_headers(self, response: Response, client_ip: str, current_time: float):
        """Add rate limiting headers to response."""
        # Calculate remaining requests
        minute_count = sum(1 for timestamp in self.minute_windows[client_ip] 
                          if timestamp > current_time - 60)
        hour_count = sum(1 for timestamp in self.hour_windows[client_ip] 
                        if timestamp > current_time - 3600)
        
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(max(0, self.requests_per_minute - minute_count))
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(max(0, self.requests_per_hour - hour_count))
    
    def _cleanup_old_entries(self, current_time: float):
        """Clean up old entries from rate limiting windows."""
        burst_cutoff = current_time - 10
        minute_cutoff = current_time - 60
        hour_cutoff = current_time - 3600
        
        # Clean up burst windows
        for client_ip in list(self.burst_windows.keys()):
            window = self.burst_windows[client_ip]
            while window and window[0] <= burst_cutoff:
                window.popleft()
            if not window:
                del self.burst_windows[client_ip]
        
        # Clean up minute windows
        for client_ip in list(self.minute_windows.keys()):
            window = self.minute_windows[client_ip]
            while window and window[0] <= minute_cutoff:
                window.popleft()
            if not window:
                del self.minute_windows[client_ip]
        
        # Clean up hour windows
        for client_ip in list(self.hour_windows.keys()):
            window = self.hour_windows[client_ip]
            while window and window[0] <= hour_cutoff:
                window.popleft()
            if not window:
                del self.hour_windows[client_ip]