"""
Card data model for Digital Audio Wedding Cards
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Card(BaseModel):
    """Card model for wedding card data"""
    id: str
    user_id: str
    message: str
    voice_sample_path: Optional[str] = None
    ai_voice_path: Optional[str] = None
    qr_code_path: Optional[str] = None
    created_at: datetime
    views: int = 0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CardCreate(BaseModel):
    """Model for card creation"""
    message: str
    voice_sample: Optional[str] = None  # Base64 encoded audio data


class CardResponse(BaseModel):
    """Model for card response"""
    id: str
    user_id: str
    message: str
    qr_code_path: Optional[str] = None
    created_at: datetime
    views: int = 0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CardView(BaseModel):
    """Model for card viewing (public access)"""
    id: str
    message: str
    ai_voice_path: Optional[str] = None