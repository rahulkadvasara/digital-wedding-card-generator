"""
User data model for Digital Audio Wedding Cards
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class User(BaseModel):
    """User model for authentication and card management"""
    id: str
    username: str
    password: str  # Plain text storage as per requirements
    created_at: datetime
    cards: List[str] = []  # List of card IDs owned by user

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserCreate(BaseModel):
    """Model for user registration"""
    username: str
    password: str


class UserLogin(BaseModel):
    """Model for user login"""
    username: str
    password: str


class UserResponse(BaseModel):
    """Model for user response (without password)"""
    id: str
    username: str
    created_at: datetime
    cards: List[str] = []

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }