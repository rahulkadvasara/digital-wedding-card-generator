"""
Authentication routes for Digital Audio Wedding Cards
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.user import UserCreate, UserLogin, UserResponse
from services.auth_service import AuthService
import jwt
from datetime import datetime, timedelta
import os

router = APIRouter()
security = HTTPBearer(auto_error=False)

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

auth_service = AuthService()

def create_access_token(user_id: str, username: str) -> str:
    """Create JWT access token"""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

@router.post("/login")
async def login(user_data: UserLogin):
    """Authenticate user and return token"""
    try:
        # Validate input
        if not user_data.username or not user_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required"
            )
        
        # Authenticate user
        user = await auth_service.authenticate_user(user_data.username, user_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create access token
        access_token = create_access_token(user.id, user.username)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse(
                id=user.id,
                username=user.username,
                created_at=user.created_at,
                cards=user.cards
            )
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

@router.post("/register")
async def register(user_data: UserCreate):
    """Register new user account"""
    try:
        # Validate input
        if not user_data.username or not user_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required"
            )
        
        # Basic validation
        if len(user_data.username) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username must be at least 3 characters long"
            )
        
        if len(user_data.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long"
            )
        
        # Create user
        user = await auth_service.create_user(user_data)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists"
            )
        
        # Create access token
        access_token = create_access_token(user.id, user.username)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse(
                id=user.id,
                username=user.username,
                created_at=user.created_at,
                cards=user.cards
            ),
            "message": "User registered successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.get("/verify")
async def verify_token_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verify authentication token and return user info"""
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        current_user = await auth_service.get_current_user_from_token(credentials)
        user = await auth_service.get_user_by_id(current_user["id"])
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return {
            "valid": True,
            "user": UserResponse(
                id=user.id,
                username=user.username,
                created_at=user.created_at,
                cards=user.cards
            )
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token verification failed: {str(e)}"
        )

@router.post("/logout")
async def logout():
    """Logout user (client-side token removal)"""
    return {"message": "Logged out successfully"}