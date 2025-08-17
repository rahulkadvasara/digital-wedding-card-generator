"""
Authentication routes for Digital Audio Wedding Cards
"""
from fastapi import APIRouter, HTTPException, status, Response, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.user import UserCreate, UserLogin, UserResponse
from services.auth_service import AuthService
import jwt
from datetime import datetime, timedelta
import os

router = APIRouter()
security = HTTPBearer(auto_error=False)

# Simple JWT secret - in production this should be environment variable
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

def verify_token(token: str) -> dict:
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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    payload = verify_token(credentials.credentials)
    user = await auth_service.get_user_by_id(payload["user_id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

@router.post("/login")
async def login(user_data: UserLogin, request: Request):
    """Authenticate user and return token"""
    from utils.error_handler import (
        validate_required_fields, 
        validate_string_length, 
        sanitize_input,
        AuthenticationError,
        ValidationError,
        log_api_call
    )
    
    try:
        # Log API call
        log_api_call(request, "auth/login")
        
        # Validate input data
        if not user_data.username or not user_data.password:
            raise ValidationError("Username and password are required")
        
        # Sanitize inputs
        username = sanitize_input(user_data.username.strip())
        password = user_data.password  # Don't sanitize password as it might contain special chars
        
        # Validate username format
        validate_string_length(username, "username", min_length=3, max_length=50)
        validate_string_length(password, "password", min_length=6, max_length=128)
        
        # Authenticate user
        user = await auth_service.authenticate_user(username, password)
        
        if not user:
            raise AuthenticationError("Invalid username or password")
        
        # Create access token
        access_token = create_access_token(user.id, user.username)
        
        # Log successful login
        log_api_call(request, "auth/login", user_id=user.id, additional_data={"status": "success"})
        
        # Return user data and token
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
    
    except (ValidationError, AuthenticationError):
        raise
    except Exception as e:
        from utils.error_handler import ErrorHandler
        raise ErrorHandler.handle_authentication_error(e)

@router.post("/register")
async def register(user_data: UserCreate, request: Request):
    """Register new user account"""
    from utils.error_handler import (
        validate_string_length, 
        sanitize_input,
        ValidationError,
        ConflictError,
        log_api_call
    )
    
    try:
        # Log API call
        log_api_call(request, "auth/register")
        
        # Validate input data
        if not user_data.username or not user_data.password:
            raise ValidationError("Username and password are required")
        
        # Sanitize inputs
        username = sanitize_input(user_data.username.strip())
        password = user_data.password  # Don't sanitize password
        
        # Validate username format
        validate_string_length(username, "username", min_length=3, max_length=50)
        validate_string_length(password, "password", min_length=6, max_length=128)
        
        # Additional username validation
        if not username.replace('_', '').replace('-', '').isalnum():
            raise ValidationError("Username can only contain letters, numbers, underscores, and hyphens", field="username")
        
        # Create user
        user = await auth_service.create_user(UserCreate(username=username, password=password))
        
        if not user:
            raise ConflictError("Username already exists", resource_type="user")
        
        # Create access token
        access_token = create_access_token(user.id, user.username)
        
        # Log successful registration
        log_api_call(request, "auth/register", user_id=user.id, additional_data={"status": "success"})
        
        # Return user data and token
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
    
    except (ValidationError, ConflictError):
        raise
    except Exception as e:
        from utils.error_handler import ErrorHandler
        raise ErrorHandler.handle_authentication_error(e)

@router.get("/verify")
async def verify_token_endpoint(current_user = Depends(get_current_user)):
    """Verify authentication token and return user info"""
    return {
        "valid": True,
        "user": UserResponse(
            id=current_user.id,
            username=current_user.username,
            created_at=current_user.created_at,
            cards=current_user.cards
        )
    }

@router.post("/logout")
async def logout():
    """Logout user (client-side token removal)"""
    return {"message": "Logged out successfully"}