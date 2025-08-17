"""
Card management API routes for Digital Audio Wedding Cards
"""
import os
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.card import CardCreate, CardResponse, CardView
from services.card_service import CardService
from services.qr_service import QRService
from services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()
card_service = CardService()
qr_service = QRService()
auth_service = AuthService()
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    return await auth_service.get_current_user_from_token(credentials)


@router.post("/create", response_model=CardResponse)
async def create_card(
    request: Request,
    message: str = Form(...),
    voice_file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    """Create a new wedding card with message and optional voice sample"""
    from utils.error_handler import (
        validate_string_length,
        validate_file_upload,
        sanitize_input,
        ValidationError,
        log_api_call,
        ErrorHandler
    )
    
    try:
        # Log API call
        log_api_call(request, "cards/create", user_id=current_user.get("id"))
        
        # Validate message
        if not message or not message.strip():
            raise ValidationError("Message is required", field="message")
        
        # Sanitize and validate message
        sanitized_message = sanitize_input(message.strip())
        validate_string_length(sanitized_message, "message", min_length=10, max_length=1000)
        
        # Validate voice file if provided
        if voice_file:
            validate_file_upload(
                voice_file,
                allowed_types=['wav', 'mp3', 'webm', 'ogg', 'm4a'],
                max_size=10 * 1024 * 1024  # 10MB
            )
        
        # Create card data object
        card_data = CardCreate(message=sanitized_message)
        
        # Create the card
        card_response = await card_service.create_card(
            user_id=current_user["id"],
            card_data=card_data,
            voice_file=voice_file
        )
        
        # Generate QR code for the card
        qr_code_path = qr_service.generate_qr_code(card_response.id)
        
        # Update card with QR code path
        await card_service._update_card_qr_path(card_response.id, qr_code_path)
        card_response.qr_code_path = qr_code_path
        
        # Log successful creation
        log_api_call(
            request, 
            "cards/create", 
            user_id=current_user["id"], 
            additional_data={"card_id": card_response.id, "status": "success"}
        )
        
        return card_response
        
    except ValidationError:
        raise
    except HTTPException:
        # Re-raise HTTP exceptions (like voice generation errors) without modification
        raise
    except Exception as e:
        # Log the actual error for debugging
        logger.error(f"Unexpected error in card creation: {str(e)}", exc_info=True)
        raise ErrorHandler.handle_database_error("create card", e)


@router.get("/{card_id}", response_model=CardView)
async def get_card(card_id: str, recipient_name: str = None):
    """Get card data for public viewing (no authentication required)"""
    try:
        # Increment view count
        await card_service.update_card_views(card_id)
        
        # Return personalized card data if recipient name is provided
        if recipient_name:
            return await card_service.get_personalized_card(card_id, recipient_name)
        else:
            return await card_service.get_card(card_id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve card: {str(e)}")


@router.get("/user/{user_id}", response_model=List[CardResponse])
async def get_user_cards(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all cards created by a specific user (authentication required)"""
    try:
        # Verify user can only access their own cards
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied. You can only view your own cards.")
        
        return await card_service.get_user_cards(user_id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user cards: {str(e)}")


@router.get("/my-cards", response_model=List[CardResponse])
async def get_my_cards(current_user: dict = Depends(get_current_user)):
    """Get all cards created by the current authenticated user"""
    try:
        return await card_service.get_user_cards(current_user["id"])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cards: {str(e)}")


@router.get("/{card_id}/qr-code")
async def get_qr_code(card_id: str):
    """Get QR code image for a specific card"""
    try:
        # Check if card exists
        await card_service.get_card(card_id)
        
        # Return QR code file - use absolute path to main assets directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        qr_code_path = os.path.join(base_dir, "data", "qr_codes", f"{card_id}_qr.png")
        
        if not os.path.exists(qr_code_path):
            # Generate QR code if it doesn't exist
            qr_code_path = qr_service.generate_qr_code(card_id)
        
        return FileResponse(
            qr_code_path,
            media_type="image/png",
            filename=f"{card_id}_qr.png"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve QR code: {str(e)}")


@router.get("/{card_id}/audio")
async def get_card_audio(card_id: str, recipient_name: str):
    """Get personalized AI-generated audio for a specific card and recipient"""
    try:
        # Get the personalized card which will generate the audio
        card_view = await card_service.get_personalized_card(card_id, recipient_name)
        
        if not card_view.ai_voice_path or not os.path.exists(card_view.ai_voice_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            card_view.ai_voice_path,
            media_type="audio/mpeg",
            filename=f"{card_id}_{recipient_name}_audio.mp3"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audio: {str(e)}")


@router.put("/{card_id}/views")
async def increment_card_views(card_id: str):
    """Increment view count for a card (public endpoint)"""
    try:
        success = await card_service.update_card_views(card_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Card not found")
        
        return {"message": "View count updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update view count: {str(e)}")