"""
Simple voice cloning service using ElevenLabs API
"""
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs import clone, generate, set_api_key
import logging

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Set up directories
        self.base_dir = Path(__file__).parent.parent.parent
        self.samples_dir = self.base_dir / "data" / "audio" / "samples"
        self.generated_dir = self.base_dir / "data" / "audio" / "generated"
        
        # Create directories if they don't exist
        try:
            self.samples_dir.mkdir(parents=True, exist_ok=True)
            self.generated_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create directories: {e}")
        
        # Set ElevenLabs API key
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            logger.warning("ELEVENLABS_API_KEY not found in environment variables")
            # Don't raise error during import, just log warning
        else:
            try:
                set_api_key(api_key)
                logger.info("ElevenLabs API key configured successfully")
            except Exception as e:
                logger.warning(f"Could not set ElevenLabs API key: {e}")
    
    async def save_voice_sample(self, user_id: str, audio_data: bytes) -> str:
        """Save user's voice sample to disk"""
        try:
            # Create unique filename
            sample_id = str(uuid.uuid4())[:8]
            filename = f"{user_id}_{sample_id}.wav"
            file_path = self.samples_dir / filename
            
            # Save audio data
            with open(file_path, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"Voice sample saved: {file_path}")
            return str(file_path)
        
        except Exception as e:
            logger.error(f"Error saving voice sample: {e}")
            raise Exception(f"Failed to save voice sample: {str(e)}")
    
    async def clone_and_generate(self, user_id: str, sample_path: str, message: str, recipient_name: str) -> str:
        """Clone voice from sample and generate message in one step"""
        try:
            # Personalize message (replace {name} with recipient name)
            personalized_message = message.replace("{name}", recipient_name)
            personalized_message = personalized_message.replace("{NAME}", recipient_name.upper())
            
            logger.info(f"Generating audio for message: '{personalized_message}'")
            
            # Clone voice and generate audio in one step
            voice = clone(
                name=f"voice_{user_id}",
                files=[sample_path],
                description=f"Cloned voice for user {user_id}"
            )
            
            # Generate audio with cloned voice
            audio = generate(
                text=personalized_message,
                voice=voice,
                model="eleven_multilingual_v2"
            )
            
            # Save generated audio
            output_filename = f"{user_id}_{recipient_name}_{uuid.uuid4().hex[:8]}.mp3"
            output_path = self.generated_dir / output_filename
            
            with open(output_path, 'wb') as f:
                f.write(audio)
            
            logger.info(f"Audio generated successfully: {output_path}")
            
            # Return relative path for API response
            return f"data/audio/generated/{output_filename}"
        
        except Exception as e:
            logger.error(f"Error in voice cloning/generation: {e}")
            raise Exception(f"Voice generation failed: {str(e)}")
    
    def get_audio_file_path(self, filename: str) -> str:
        """Get full path to generated audio file"""
        return str(self.generated_dir / filename)