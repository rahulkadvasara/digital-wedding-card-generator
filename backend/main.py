"""
FastAPI main application for Digital Audio Wedding Cards
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn

# Import route modules
from routes import auth, cards, voice

app = FastAPI(title="Digital Audio Wedding Cards API")

# Basic error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (only if directories exist)
import os
if os.path.exists("../frontend"):
    app.mount("/static", StaticFiles(directory="../frontend"), name="static")
if os.path.exists("../data"):
    app.mount("/data", StaticFiles(directory="../data"), name="data")

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "Digital Audio Wedding Cards API is running"}

# Route registration
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(cards.router, prefix="/cards", tags=["cards"])
app.include_router(voice.router, prefix="/voice", tags=["voice"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )