"""
Voice generation routes for Digital Audio Wedding Cards
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.voice_service import VoiceService
from services.auth_service import AuthService
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter()
voice_service = VoiceService()
auth_service = AuthService()
security = HTTPBearer()

@router.post("/generate")
async def generate_voice_message(
    message: str = Form(...),
    recipient_name: str = Form(...),
    voice_sample: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Generate personalized voice message from text and voice sample
    """
    try:
        # Get current user
        current_user = await auth_service.get_current_user_from_token(credentials)
        user_id = current_user["id"]
        
        # Validate inputs
        if not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if not recipient_name.strip():
            raise HTTPException(status_code=400, detail="Recipient name cannot be empty")
        
        # Validate audio file
        if not voice_sample.content_type or not voice_sample.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Please upload a valid audio file")
        
        # Read audio data
        audio_data = await voice_sample.read()
        if len(audio_data) < 1024:  # At least 1KB
            raise HTTPException(status_code=400, detail="Audio file is too small")
        
        # Save voice sample
        sample_path = await voice_service.save_voice_sample(user_id, audio_data)
        
        # Clone voice and generate message
        audio_path = await voice_service.clone_and_generate(
            user_id=user_id,
            sample_path=sample_path,
            message=message,
            recipient_name=recipient_name
        )
        
        return {
            "success": True,
            "message": "Voice message generated successfully",
            "audio_path": audio_path,
            "recipient_name": recipient_name
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating voice message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """
    Serve generated audio files
    """
    try:
        file_path = voice_service.get_audio_file_path(filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            path=file_path,
            media_type="audio/mpeg",
            filename=filename
        )
    
    except Exception as e:
        logger.error(f"Error serving audio file: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve audio file")