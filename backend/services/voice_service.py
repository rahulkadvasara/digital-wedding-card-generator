"""
AI voice generation service for Digital Audio Wedding Cards

This service handles the integration with GenAI APIs (primarily ElevenLabs)
for voice cloning and text-to-speech synthesis. It provides reliable voice
generation with proper error handling when external APIs fail.

Key Features:
- Voice cloning from user-uploaded samples
- Personalized message synthesis with cloned voices
- Comprehensive error handling and logging
- Rate limiting and timeout management
- Strict API validation and error reporting
"""
from typing import Optional, Dict, Any
import os
import json
import httpx
import asyncio
import uuid
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging for voice service operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceGenerationError(Exception):
    """
    Custom exception for voice generation errors
    
    This exception is raised when voice cloning or synthesis operations fail,
    providing specific error messages to help with debugging and user feedback.
    """
    pass


class VoiceService:
    """
    Service for handling AI voice generation using ElevenLabs API
    
    This service manages the complete voice generation workflow:
    1. Saving user voice samples to disk
    2. Cloning voices using ElevenLabs API
    3. Synthesizing personalized messages with cloned voices
    4. Managing voice model registry and cleanup
    
    The service requires a valid ElevenLabs API key and will fail with clear
    error messages when the API is unavailable or misconfigured.
    """
    
    def __init__(self):
        # Directory structure for voice-related files - use absolute paths
        # Point to main directory structure (not backend subdirectory)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.voice_samples_dir = os.path.join(self.base_dir, "data", "audio", "samples")
        self.generated_audio_dir = os.path.join(self.base_dir, "data", "audio", "generated")
        self.voice_models_file = os.path.join(self.base_dir, "data", "voice_models.json")
        
        # Load environment variables from .env file
        env_path = os.path.join(self.base_dir, ".env")
        load_dotenv(env_path)
        
        # Ensure all required directories exist
        os.makedirs(self.voice_samples_dir, exist_ok=True)
        os.makedirs(self.generated_audio_dir, exist_ok=True)
        
        # ElevenLabs API configuration - load from .env file
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.elevenlabs_base_url = os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io/v1")
        
        # Validate API key - fail if not properly configured
        if not self.elevenlabs_api_key or self.elevenlabs_api_key == "your_elevenlabs_api_key_here":
            logger.warning("ElevenLabs API key not configured in .env file. Voice generation will fail until a valid API key is provided.")
            self.api_configured = False
        else:
            logger.info("ElevenLabs API key loaded from .env file successfully.")
            self.api_configured = True
        
        # Load existing voice models registry from disk
        self._load_voice_models()
    
    def _load_voice_models(self):
        """Load voice models registry from JSON file"""
        try:
            if os.path.exists(self.voice_models_file):
                with open(self.voice_models_file, 'r') as f:
                    self.voice_models = json.load(f)
            else:
                self.voice_models = {}
                self._save_voice_models()
        except Exception as e:
            logger.error(f"Error loading voice models: {e}")
            self.voice_models = {}
    
    def _save_voice_models(self):
        """Save voice models registry to JSON file"""
        try:
            with open(self.voice_models_file, 'w') as f:
                json.dump(self.voice_models, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving voice models: {e}")
    
    async def save_voice_sample(self, user_id: str, voice_data: bytes) -> str:
        """Save uploaded voice sample to disk"""
        try:
            sample_id = str(uuid.uuid4())
            sample_filename = f"{user_id}_{sample_id}.wav"
            sample_path = os.path.join(self.voice_samples_dir, sample_filename)
            
            with open(sample_path, 'wb') as f:
                f.write(voice_data)
            
            logger.info(f"Voice sample saved: {sample_path}")
            return sample_path
        except Exception as e:
            logger.error(f"Error saving voice sample: {e}")
            raise VoiceGenerationError(f"Failed to save voice sample: {str(e)}")
    
    async def clone_voice(self, user_id: str, voice_sample_path: str) -> str:
        """Generate AI voice model from uploaded sample"""
        # Check if API is configured
        if not self.api_configured:
            raise VoiceGenerationError("Voice generation service is not configured. Please contact administrator.")
        
        try:
            # Convert relative path to absolute path if needed
            if not os.path.isabs(voice_sample_path):
                voice_sample_path = os.path.join(self.base_dir, voice_sample_path)
            
            # Use ElevenLabs API for voice cloning
            return await self._elevenlabs_clone_voice(user_id, voice_sample_path)
            
        except VoiceGenerationError:
            # Re-raise voice generation errors
            raise
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            raise VoiceGenerationError(f"Voice cloning failed: {str(e)}")
    
    async def _elevenlabs_clone_voice(self, user_id: str, voice_sample_path: str) -> str:
        """Clone voice using ElevenLabs API with enhanced error handling"""
        try:
            voice_name = f"wedding_voice_{user_id}"
            
            # Validate API key
            if not self.elevenlabs_api_key or self.elevenlabs_api_key.startswith("sk_22b91f8de8e8b59a285ed112143c2e0fdfeb87578ea86674"):
                raise VoiceGenerationError("Voice generation service is not configured. Please contact administrator.")
            
            # Read the voice sample file
            try:
                with open(voice_sample_path, 'rb') as f:
                    voice_data = f.read()
            except FileNotFoundError:
                raise VoiceGenerationError(f"Voice sample file not found: {voice_sample_path}")
            except PermissionError:
                raise VoiceGenerationError("Permission denied accessing voice sample file")
            
            if len(voice_data) == 0:
                raise VoiceGenerationError("Voice sample file is empty")
            
            # Prepare the request to ElevenLabs
            headers = {
                "xi-api-key": self.elevenlabs_api_key
            }
            
            files = {
                "files": ("sample.wav", voice_data, "audio/wav")
            }
            
            data = {
                "name": voice_name,
                "description": f"Cloned voice for user {user_id}"
            }
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:  # Increased timeout
                    response = await client.post(
                        f"{self.elevenlabs_base_url}/voices/add",
                        headers=headers,
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        voice_id = result.get("voice_id")
                        
                        if not voice_id:
                            raise VoiceGenerationError("No voice ID returned from API")
                        
                        # Store voice model info
                        self.voice_models[user_id] = {
                            "voice_id": voice_id,
                            "voice_name": voice_name,
                            "sample_path": voice_sample_path,
                            "provider": "elevenlabs",
                            "created_at": str(asyncio.get_event_loop().time())
                        }
                        self._save_voice_models()
                        
                        logger.info(f"Voice cloned successfully for user {user_id}: {voice_id}")
                        return voice_id
                    
                    elif response.status_code == 401:
                        logger.error("ElevenLabs API authentication failed")
                        raise VoiceGenerationError("Voice cloning service authentication failed. Please try again later.")
                    
                    elif response.status_code == 429:
                        logger.error("ElevenLabs API rate limit exceeded")
                        raise VoiceGenerationError("Voice cloning service is busy. Please try again in a few minutes.")
                    
                    elif response.status_code == 400:
                        try:
                            error_data = response.json()
                            error_message = error_data.get("detail", {}).get("message", "Invalid voice sample")
                        except:
                            error_message = "Invalid voice sample format"
                        logger.error(f"ElevenLabs API validation error: {error_message}")
                        raise VoiceGenerationError(f"Voice sample validation failed: {error_message}")
                    
                    else:
                        logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                        raise VoiceGenerationError(f"Voice cloning service error: {response.status_code} - {response.text}")
                        
            except httpx.TimeoutException:
                logger.error("ElevenLabs API timeout")
                raise VoiceGenerationError("Voice cloning service timeout. Please try again.")
            
            except httpx.NetworkError as e:
                logger.error(f"ElevenLabs API network error: {e}")
                raise VoiceGenerationError("Network error connecting to voice cloning service. Please check your connection.")
                    
        except VoiceGenerationError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error in ElevenLabs voice cloning: {e}")
            raise VoiceGenerationError(f"Unexpected error in voice cloning: {str(e)}")
    

    
    async def synthesize_message(self, user_id: str, message: str, recipient_name: str) -> str:
        """Generate personalized audio message"""
        # Check if API is configured
        if not self.api_configured:
            raise VoiceGenerationError("Voice generation service is not configured. Please contact administrator.")
        
        # Check if user has a voice model
        if user_id not in self.voice_models:
            raise VoiceGenerationError("No voice model found for user. Please create a card with voice recording first.")
        
        try:
            # Personalize the message
            personalized_message = self._personalize_message(message, recipient_name)
            
            # Use ElevenLabs API for voice synthesis
            return await self._elevenlabs_synthesize_message(user_id, personalized_message, recipient_name)
            
        except VoiceGenerationError:
            # Re-raise voice generation errors
            raise
        except Exception as e:
            logger.error(f"Voice synthesis failed: {e}")
            raise VoiceGenerationError(f"Voice synthesis failed: {str(e)}")
    
    async def _elevenlabs_synthesize_message(self, user_id: str, message: str, recipient_name: str) -> str:
        """Synthesize message using ElevenLabs API"""
        try:
            voice_model = self.voice_models[user_id]
            voice_id = voice_model["voice_id"]
            
            headers = {
                "xi-api-key": self.elevenlabs_api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "text": message,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.elevenlabs_base_url}/text-to-speech/{voice_id}",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    # Save the generated audio - standardize to .mp3 extension
                    audio_filename = f"{user_id}_{recipient_name}_{uuid.uuid4().hex[:8]}.mp3"
                    audio_path = os.path.join(self.generated_audio_dir, audio_filename)
                    
                    with open(audio_path, 'wb') as f:
                        f.write(response.content)
                    
                    # Return relative path for consistency
                    relative_path = os.path.relpath(audio_path, self.base_dir).replace('\\', '/')
                    logger.info(f"Audio synthesized successfully: {relative_path}")
                    return relative_path
                else:
                    logger.error(f"ElevenLabs synthesis error: {response.status_code} - {response.text}")
                    raise VoiceGenerationError(f"Synthesis API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"ElevenLabs voice synthesis failed: {e}")
            raise VoiceGenerationError(f"Voice synthesis failed: {str(e)}")
    

    
    def _personalize_message(self, message: str, recipient_name: str) -> str:
        """Replace placeholder with recipient name"""
        # Replace common placeholders
        personalized = message.replace("{name}", recipient_name)
        personalized = personalized.replace("{NAME}", recipient_name.upper())
        personalized = personalized.replace("[name]", recipient_name)
        personalized = personalized.replace("[NAME]", recipient_name.upper())
        
        return personalized
    
    async def get_voice_model_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get voice model information for a user"""
        return self.voice_models.get(user_id)
    
    async def delete_voice_model(self, user_id: str) -> bool:
        """Delete voice model for a user"""
        try:
            if user_id in self.voice_models:
                voice_model = self.voice_models[user_id]
                
                # If using ElevenLabs, delete from their service too
                if self.api_configured and voice_model.get("provider") == "elevenlabs":
                    await self._delete_elevenlabs_voice(voice_model["voice_id"])
                
                # Remove from local registry
                del self.voice_models[user_id]
                self._save_voice_models()
                
                logger.info(f"Voice model deleted for user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting voice model: {e}")
            return False
    
    async def _delete_elevenlabs_voice(self, voice_id: str):
        """Delete voice from ElevenLabs"""
        try:
            headers = {
                "xi-api-key": self.elevenlabs_api_key
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.elevenlabs_base_url}/voices/{voice_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    logger.info(f"Voice deleted from ElevenLabs: {voice_id}")
                else:
                    logger.warning(f"Failed to delete voice from ElevenLabs: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error deleting ElevenLabs voice: {e}")