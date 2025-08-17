"""
Comprehensive error handling utilities for Digital Audio Wedding Cards backend
"""
import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Custom API error with structured error information"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """Validation error with field-specific details"""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details or {}
        )
        if field:
            self.details["field"] = field


class AuthenticationError(APIError):
    """Authentication error"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(APIError):
    """Authorization error"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR"
        )


class NotFoundError(APIError):
    """Resource not found error"""
    
    def __init__(self, message: str = "Resource not found", resource_type: str = None):
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND_ERROR"
        )
        if resource_type:
            self.details["resource_type"] = resource_type


class ConflictError(APIError):
    """Resource conflict error"""
    
    def __init__(self, message: str = "Resource conflict", resource_type: str = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT_ERROR"
        )
        if resource_type:
            self.details["resource_type"] = resource_type


class RateLimitError(APIError):
    """Rate limit exceeded error"""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_ERROR"
        )


class ExternalServiceError(APIError):
    """External service error (e.g., GenAI API failures)"""
    
    def __init__(self, message: str, service_name: str = None):
        super().__init__(
            message=message,
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR"
        )
        if service_name:
            self.details["service"] = service_name


def create_error_response(
    message: str,
    status_code: int = 500,
    error_code: str = "INTERNAL_ERROR",
    details: Optional[Dict[str, Any]] = None,
    request_id: str = None
) -> JSONResponse:
    """Create standardized error response"""
    
    error_response = {
        "error": True,
        "message": message,
        "error_code": error_code,
        "status_code": status_code
    }
    
    if details:
        error_response["details"] = details
    
    if request_id:
        error_response["request_id"] = request_id
    
    # Log error for debugging
    logger.error(f"API Error: {error_code} - {message}", extra={
        "status_code": status_code,
        "details": details,
        "request_id": request_id
    })
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors"""
    return create_error_response(
        message=exc.message,
        status_code=exc.status_code,
        error_code=exc.error_code,
        details=exc.details,
        request_id=getattr(request.state, 'request_id', None)
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    
    # Map status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE"
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    return create_error_response(
        message=exc.detail,
        status_code=exc.status_code,
        error_code=error_code,
        request_id=getattr(request.state, 'request_id', None)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors"""
    
    # Extract field-specific validation errors
    validation_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        validation_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return create_error_response(
        message="Validation failed",
        status_code=422,
        error_code="VALIDATION_ERROR",
        details={"validation_errors": validation_errors},
        request_id=getattr(request.state, 'request_id', None)
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    
    # Log the full traceback for debugging
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    # Don't expose internal error details in production
    return create_error_response(
        message="An unexpected error occurred. Please try again later.",
        status_code=500,
        error_code="INTERNAL_ERROR",
        request_id=getattr(request.state, 'request_id', None)
    )


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """Validate that required fields are present and not empty"""
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Field '{field}' is required", field=field)
        
        value = data[field]
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"Field '{field}' cannot be empty", field=field)


def validate_string_length(
    value: str,
    field_name: str,
    min_length: int = None,
    max_length: int = None
) -> None:
    """Validate string length constraints"""
    
    if not isinstance(value, str):
        raise ValidationError(f"Field '{field_name}' must be a string", field=field_name)
    
    if min_length is not None and len(value) < min_length:
        raise ValidationError(
            f"Field '{field_name}' must be at least {min_length} characters long",
            field=field_name
        )
    
    if max_length is not None and len(value) > max_length:
        raise ValidationError(
            f"Field '{field_name}' must be no more than {max_length} characters long",
            field=field_name
        )


def validate_file_upload(file, allowed_types: list = None, max_size: int = None) -> None:
    """Validate file upload constraints"""
    
    if not file:
        raise ValidationError("File is required")
    
    if not file.filename:
        raise ValidationError("File must have a filename")
    
    if allowed_types:
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in allowed_types:
            raise ValidationError(
                f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
            )
    
    if max_size and hasattr(file, 'size') and file.size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise ValidationError(f"File size must be less than {max_size_mb:.1f}MB")


def sanitize_input(value: str) -> str:
    """Basic input sanitization"""
    
    if not isinstance(value, str):
        return value
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    sanitized = value
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()


def log_api_call(
    request: Request,
    endpoint: str,
    user_id: str = None,
    additional_data: Dict[str, Any] = None
) -> None:
    """Log API call for monitoring and debugging"""
    
    log_data = {
        "endpoint": endpoint,
        "method": request.method,
        "client_ip": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "user_id": user_id
    }
    
    if additional_data:
        log_data.update(additional_data)
    
    logger.info(f"API Call: {endpoint}", extra=log_data)


class ErrorHandler:
    """Centralized error handling utility class"""
    
    @staticmethod
    def handle_file_operation_error(operation: str, filepath: str, error: Exception) -> APIError:
        """Handle file operation errors"""
        
        if isinstance(error, FileNotFoundError):
            return NotFoundError(f"File not found: {filepath}")
        elif isinstance(error, PermissionError):
            return APIError(f"Permission denied for file operation: {operation}", 403)
        elif isinstance(error, OSError):
            return APIError(f"File system error during {operation}", 500)
        else:
            return APIError(f"Failed to {operation}: {str(error)}", 500)
    
    @staticmethod
    def handle_database_error(operation: str, error: Exception) -> APIError:
        """Handle database operation errors"""
        
        logger.error(f"Database error during {operation}: {str(error)}")
        return APIError(f"Database operation failed: {operation}", 500)
    
    @staticmethod
    def handle_external_api_error(service: str, error: Exception) -> APIError:
        """Handle external API errors"""
        
        logger.error(f"External API error ({service}): {str(error)}")
        return ExternalServiceError(
            f"External service temporarily unavailable: {service}",
            service_name=service
        )
    
    @staticmethod
    def handle_authentication_error(error: Exception) -> APIError:
        """Handle authentication errors"""
        
        logger.warning(f"Authentication error: {str(error)}")
        return AuthenticationError("Invalid credentials or session expired")
    
    @staticmethod
    def handle_validation_error(field: str, message: str) -> APIError:
        """Handle validation errors"""
        
        return ValidationError(message, field=field)