"""
Voice generation API routes for Digital Audio Wedding Cards
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os
import logging

from services.voice_service import VoiceService, VoiceGenerationError
from services.auth_service import AuthService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
voice_service = VoiceService()
auth_service = AuthService()
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_data = await auth_service.get_current_user_from_token(credentials)
    return {"user_id": user_data["id"], "username": user_data["username"]}


@router.post("/clone")
async def clone_voice(
    request: Request,
    voice_sample: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Clone user's voice from uploaded sample
    
    - **voice_sample**: Audio file containing voice sample (WAV format recommended)
    - Returns: Voice model ID for future synthesis
    """
    from utils.error_handler import (
        validate_file_upload,
        ValidationError,
        ExternalServiceError,
        log_api_call,
        ErrorHandler
    )
    
    try:
        user_id = current_user["user_id"]
        
        # Log API call
        log_api_call(request, "voice/clone", user_id=user_id)
        
        # Validate file upload
        validate_file_upload(
            voice_sample,
            allowed_types=['wav', 'mp3', 'webm', 'ogg', 'm4a'],
            max_size=25 * 1024 * 1024  # 25MB for voice samples
        )
        
        # Additional validation for voice files
        if not voice_sample.content_type or not voice_sample.content_type.startswith('audio/'):
            raise ValidationError("Invalid file type. Please upload an audio file.")
        
        # Read voice sample data
        voice_data = await voice_sample.read()
        
        if len(voice_data) == 0:
            raise ValidationError("Empty audio file")
        
        # Check minimum file size (at least 1KB)
        if len(voice_data) < 1024:
            raise ValidationError("Audio file is too small. Please upload a longer voice sample.")
        
        # Save voice sample
        sample_path = await voice_service.save_voice_sample(user_id, voice_data)
        
        # Clone voice
        voice_id = await voice_service.clone_voice(user_id, sample_path)
        
        # Log successful cloning
        log_api_call(
            request, 
            "voice/clone", 
            user_id=user_id, 
            additional_data={"voice_id": voice_id, "status": "success"}
        )
        
        return {
            "success": True,
            "message": "Voice cloned successfully",
            "voice_id": voice_id,
            "sample_path": sample_path
        }
        
    except ValidationError:
        raise
    except VoiceGenerationError as e:
        logger.error(f"Voice cloning error: {e}")
        raise ExternalServiceError(str(e), service_name="voice_cloning")
    except Exception as e:
        logger.error(f"Unexpected error in voice cloning: {e}")
        raise ErrorHandler.handle_external_api_error("voice_cloning", e)


@router.post("/synthesize")
async def synthesize_message(
    message: str = Form(...),
    recipient_name: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate personalized audio message using cloned voice
    
    - **message**: Text message to synthesize (can include {name} placeholder)
    - **recipient_name**: Name of the recipient for personalization
    - Returns: Path to generated audio file
    """
    try:
        user_id = current_user["user_id"]
        
        # Validate inputs
        logger.info(f"Synthesize request - message: '{message}', recipient: '{recipient_name}'")
        
        if not message or not message.strip():
            logger.info("Message validation failed - empty message")
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if not recipient_name or not recipient_name.strip():
            logger.info("Recipient name validation failed - empty name")
            raise HTTPException(status_code=400, detail="Recipient name cannot be empty")
        
        # Check if user has a voice model
        voice_model = await voice_service.get_voice_model_info(user_id)
        if not voice_model:
            raise HTTPException(
                status_code=400, 
                detail="No voice model found. Please clone your voice first."
            )
        
        # Synthesize message
        audio_path = await voice_service.synthesize_message(user_id, message, recipient_name)
        
        return {
            "success": True,
            "message": "Audio synthesized successfully",
            "audio_path": audio_path,
            "recipient_name": recipient_name
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors)
        raise
    except VoiceGenerationError as e:
        logger.error(f"Voice synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in voice synthesis: {e}")
        raise HTTPException(status_code=500, detail="Voice synthesis failed")


@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """
    Serve generated audio files
    
    - **filename**: Name of the audio file to retrieve
    - Returns: Audio file for playback
    """
    try:
        audio_path = os.path.join(voice_service.generated_audio_dir, filename)
        
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Determine media type based on file extension
        media_type = "audio/mpeg" if filename.endswith('.mp3') else "audio/wav"
        
        return FileResponse(
            path=audio_path,
            media_type=media_type,
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"Error serving audio file: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve audio file")


@router.get("/model/info")
async def get_voice_model_info(current_user: dict = Depends(get_current_user)):
    """
    Get voice model information for current user
    
    - Returns: Voice model details if available
    """
    try:
        user_id = current_user["user_id"]
        voice_model = await voice_service.get_voice_model_info(user_id)
        
        if not voice_model:
            return {
                "success": False,
                "message": "No voice model found",
                "has_voice_model": False
            }
        
        return {
            "success": True,
            "message": "Voice model found",
            "has_voice_model": True,
            "voice_model": {
                "voice_id": voice_model["voice_id"],
                "voice_name": voice_model["voice_name"],
                "provider": voice_model["provider"],
                "created_at": voice_model["created_at"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting voice model info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get voice model info")


@router.delete("/model")
async def delete_voice_model(current_user: dict = Depends(get_current_user)):
    """
    Delete voice model for current user
    
    - Returns: Success status
    """
    try:
        user_id = current_user["user_id"]
        success = await voice_service.delete_voice_model(user_id)
        
        if success:
            return {
                "success": True,
                "message": "Voice model deleted successfully"
            }
        else:
            return {
                "success": False,
                "message": "No voice model found to delete"
            }
        
    except Exception as e:
        logger.error(f"Error deleting voice model: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete voice model")


@router.post("/test-synthesis")
async def test_voice_synthesis(
    message: str = Form("Hello {name}, welcome to our wedding!"),
    recipient_name: str = Form("Test User"),
    current_user: dict = Depends(get_current_user)
):
    """
    Test voice synthesis with default message (for development/testing)
    
    - **message**: Test message (optional, has default)
    - **recipient_name**: Test recipient name (optional, has default)
    - Returns: Test audio file
    """
    try:
        user_id = current_user["user_id"]
        
        # Use real voice synthesis for testing
        audio_path = await voice_service.synthesize_message(user_id, message, recipient_name)
        
        return {
            "success": True,
            "message": "Test audio generated successfully",
            "audio_path": audio_path,
            "note": "This is a real AI-generated audio file"
        }
        
    except Exception as e:
        logger.error(f"Error in test synthesis: {e}")
        raise HTTPException(status_code=500, detail="Test synthesis failed")