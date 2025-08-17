"""
Authentication service for Digital Audio Wedding Cards
"""
from datetime import datetime
from typing import Optional
import uuid
import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.user import User, UserCreate
from utils.file_handler import FileHandler
import os

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"


class AuthService:
    """Service for handling user authentication"""
    
    def __init__(self):
        self.file_handler = FileHandler()
        # Point to main directory structure (not backend subdirectory)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.users_file = os.path.join(base_dir, "data", "users.json")
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        try:
            users_data = await self.file_handler.read_json(self.users_file)
            
            for user_dict in users_data:
                if user_dict.get("username") == username and user_dict.get("password") == password:
                    # Convert datetime string back to datetime object
                    user_dict["created_at"] = datetime.fromisoformat(user_dict["created_at"])
                    return User(**user_dict)
            
            return None
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None
    
    async def create_user(self, user_data: UserCreate) -> Optional[User]:
        """Create new user account"""
        try:
            # Check if username already exists
            existing_user = await self.get_user_by_username(user_data.username)
            if existing_user:
                return None
            
            # Create new user
            new_user = User(
                id=f"user_{uuid.uuid4().hex[:8]}",
                username=user_data.username,
                password=user_data.password,
                created_at=datetime.now(),
                cards=[]
            )
            
            # Convert to dict for JSON storage
            user_dict = new_user.dict()
            user_dict["created_at"] = user_dict["created_at"].isoformat()
            
            # Save to file
            success = await self.file_handler.append_json(self.users_file, user_dict)
            
            return new_user if success else None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve user by ID"""
        try:
            users_data = await self.file_handler.read_json(self.users_file)
            
            for user_dict in users_data:
                if user_dict.get("id") == user_id:
                    # Convert datetime string back to datetime object
                    user_dict["created_at"] = datetime.fromisoformat(user_dict["created_at"])
                    return User(**user_dict)
            
            return None
        except Exception as e:
            print(f"Error retrieving user by ID: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve user by username"""
        try:
            users_data = await self.file_handler.read_json(self.users_file)
            
            for user_dict in users_data:
                if user_dict.get("username") == username:
                    # Convert datetime string back to datetime object
                    user_dict["created_at"] = datetime.fromisoformat(user_dict["created_at"])
                    return User(**user_dict)
            
            return None
        except Exception as e:
            print(f"Error retrieving user by username: {e}")
            return None
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    async def get_current_user_from_token(self, credentials: HTTPAuthorizationCredentials = None):
        """Get current authenticated user from token"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        payload = self.verify_token(credentials.credentials)
        user = await self.get_user_by_id(payload["user_id"])
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return {"id": user.id, "username": user.username}