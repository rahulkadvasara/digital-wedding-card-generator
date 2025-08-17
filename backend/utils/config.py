"""
Configuration settings for Digital Audio Wedding Cards
"""
import os
from typing import Optional


class Config:
    """Application configuration"""
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # File paths
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    USERS_FILE: str = os.path.join(DATA_DIR, "users.json")
    CARDS_FILE: str = os.path.join(DATA_DIR, "cards.json")
    ANALYTICS_FILE: str = os.path.join(DATA_DIR, "analytics.json")
    
    # Upload directories
    VOICE_SAMPLES_DIR: str = os.path.join(DATA_DIR, "voice_samples")
    GENERATED_AUDIO_DIR: str = os.path.join(DATA_DIR, "generated_audio")
    QR_CODES_DIR: str = os.path.join(DATA_DIR, "qr_codes")
    
    # Frontend settings
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    STATIC_FILES_DIR: str = os.getenv("STATIC_FILES_DIR", "../frontend")
    
    # GenAI API settings (to be configured in later tasks)
    ELEVENLABS_API_KEY: Optional[str] = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_BASE_URL: str = "https://api.elevenlabs.io/v1"
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        directories = [
            cls.DATA_DIR,
            cls.VOICE_SAMPLES_DIR,
            cls.GENERATED_AUDIO_DIR,
            cls.QR_CODES_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)


# Initialize configuration
config = Config()
config.ensure_directories()