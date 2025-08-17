"""
FastAPI main application entry point for Digital Audio Wedding Cards

This is the central application file that configures and starts the FastAPI server.
It handles:
- Application initialization and configuration
- Middleware setup (CORS, request tracking, error handling)
- Route registration for all API endpoints
- Static file serving for frontend assets
- Comprehensive logging and monitoring
- Health check endpoints

The application follows a modular architecture with separate route modules
for different functional areas (auth, cards, voice, analytics).
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
import uuid
import time
import logging

# Import route modules - each handles a specific functional area
from routes import auth, cards, voice  # Core functionality routes
from routes import analytics           # Analytics and tracking routes

# Import comprehensive error handling system
from utils.error_handler import (
    APIError,                          # Custom API exception class
    api_error_handler,                 # Handler for custom API errors
    http_exception_handler,            # Handler for HTTP exceptions
    validation_exception_handler,      # Handler for request validation errors
    general_exception_handler          # Catch-all error handler
)

# Configure application-wide logging
# This ensures all operations are properly logged for debugging and monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Digital Audio Wedding Cards API",
    description="API for creating and managing personalized digital wedding cards with AI-generated audio",
    version="1.0.0"
)

# Add request ID middleware for tracking
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID for tracking and logging"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"Request started: {request.method} {request.url.path}", extra={
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host,
        "user_agent": request.headers.get("user-agent")
    })
    
    try:
        response = await call_next(request)
        
        # Log request completion
        process_time = time.time() - start_time
        logger.info(f"Request completed: {request.method} {request.url.path}", extra={
            "request_id": request_id,
            "status_code": response.status_code,
            "process_time": f"{process_time:.3f}s"
        })
        
        response.headers["X-Request-ID"] = request_id
        return response
        
    except Exception as e:
        # Log request error
        process_time = time.time() - start_time
        logger.error(f"Request failed: {request.method} {request.url.path}", extra={
            "request_id": request_id,
            "error": str(e),
            "process_time": f"{process_time:.3f}s"
        })
        raise

# Add error handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:8080",
        "http://localhost:5500",  # Live Server default port
        "http://127.0.0.1:5500",
        "file://",  # Allow file:// protocol for local HTML files
        "*"  # Allow all origins for development (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving frontend assets with error handling
try:
    app.mount("/static", StaticFiles(directory="../frontend"), name="static")
    app.mount("/data", StaticFiles(directory="../data"), name="data")
except Exception as e:
    logger.warning(f"Could not mount static directories: {e}")

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "Digital Audio Wedding Cards API is running",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "digital-audio-wedding-cards",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

# Route registration
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(cards.router, prefix="/cards", tags=["cards"])
app.include_router(voice.router, prefix="/voice", tags=["voice"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )