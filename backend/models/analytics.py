"""
Analytics data model for Digital Audio Wedding Cards
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CardView(BaseModel):
    """Model for tracking card views"""
    card_id: str
    viewer_name: str
    viewed_at: datetime
    ip_address: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ViewTrack(BaseModel):
    """Model for tracking a new view"""
    card_id: str
    viewer_name: str
    ip_address: Optional[str] = None


class CardAnalytics(BaseModel):
    """Model for card analytics summary"""
    card_id: str
    total_views: int
    unique_viewers: int
    viewer_names: list[str]
    recent_views: list[CardView]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }