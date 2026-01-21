"""
Card management routes for Digital Audio Wedding Cards
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from models.card import CardCreate, CardResponse
from services.card_service import CardService
from services.auth_service import AuthService

router = APIRouter()
card_service = CardService()
auth_service = AuthService()
security = HTTPBearer()

@router.post("/create", response_model=CardResponse)
async def create_card(
    card_data: CardCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new wedding card"""
    try:
        current_user = await auth_service.get_current_user_from_token(credentials)
        card = await card_service.create_card(card_data, current_user["id"])
        return card
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{card_id}", response_model=CardResponse)
async def get_card(card_id: str):
    """Get a specific card by ID (public endpoint for viewing)"""
    card = await card_service.get_card(card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    return card

@router.get("/my-cards", response_model=List[CardResponse])
async def get_my_cards(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all cards for the current user"""
    try:
        current_user = await auth_service.get_current_user_from_token(credentials)
        cards = await card_service.get_user_cards(current_user["id"])
        return cards
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{card_id}")
async def delete_card(
    card_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a card (only by owner)"""
    try:
        current_user = await auth_service.get_current_user_from_token(credentials)
        success = await card_service.delete_card(card_id, current_user["id"])
        if success:
            return {"message": "Card deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete card"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )