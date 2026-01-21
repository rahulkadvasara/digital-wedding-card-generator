"""
Simple card management service for Digital Audio Wedding Cards
"""
import os
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
from models.card import Card, CardCreate, CardResponse
from utils.file_handler import FileHandler

class CardService:
    def __init__(self):
        self.file_handler = FileHandler()
        
        # Set up file paths
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.cards_file = os.path.join(base_dir, "data", "cards.json")
        self.users_file = os.path.join(base_dir, "data", "users.json")
    
    async def create_card(self, card_data: CardCreate, user_id: str) -> CardResponse:
        """Create a new wedding card"""
        try:
            # Generate unique card ID
            card_id = f"card_{uuid.uuid4().hex[:8]}"
            
            # Create card object
            card = Card(
                id=card_id,
                user_id=user_id,
                message=card_data.message,
                voice_sample_path=None,
                ai_voice_path=None,
                qr_code_path=None,
                created_at=datetime.now(),
                views=0
            )
            
            # Save card to JSON file
            card_dict = card.dict()
            success = await self.file_handler.append_json(self.cards_file, card_dict)
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to save card")
            
            # Update user's card list
            await self._add_card_to_user(user_id, card_id)
            
            return CardResponse(
                id=card.id,
                user_id=card.user_id,
                message=card.message,
                qr_code_path=card.qr_code_path,
                created_at=card.created_at,
                views=card.views
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create card: {str(e)}")
    
    async def get_card(self, card_id: str) -> Optional[CardResponse]:
        """Get a card by ID"""
        try:
            cards = await self.file_handler.read_json(self.cards_file)
            
            for card_data in cards:
                if card_data.get("id") == card_id:
                    return CardResponse(
                        id=card_data["id"],
                        user_id=card_data["user_id"],
                        message=card_data["message"],
                        qr_code_path=card_data.get("qr_code_path"),
                        created_at=datetime.fromisoformat(card_data["created_at"]),
                        views=card_data.get("views", 0)
                    )
            
            return None
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve card: {str(e)}")
    
    async def get_user_cards(self, user_id: str) -> List[CardResponse]:
        """Get all cards for a user"""
        try:
            cards = await self.file_handler.read_json(self.cards_file)
            user_cards = []
            
            for card_data in cards:
                if card_data.get("user_id") == user_id:
                    user_cards.append(CardResponse(
                        id=card_data["id"],
                        user_id=card_data["user_id"],
                        message=card_data["message"],
                        qr_code_path=card_data.get("qr_code_path"),
                        created_at=datetime.fromisoformat(card_data["created_at"]),
                        views=card_data.get("views", 0)
                    ))
            
            return user_cards
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve user cards: {str(e)}")
    
    async def delete_card(self, card_id: str, user_id: str) -> bool:
        """Delete a card (only by owner)"""
        try:
            # First verify the card exists and belongs to the user
            card = await self.get_card(card_id)
            if not card:
                raise HTTPException(status_code=404, detail="Card not found")
            
            if card.user_id != user_id:
                raise HTTPException(status_code=403, detail="Not authorized to delete this card")
            
            # Delete the card from JSON file
            success = await self.file_handler.delete_json_item(self.cards_file, card_id)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to delete card")
            
            # Remove card from user's list
            await self._remove_card_from_user(user_id, card_id)
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete card: {str(e)}")
    
    async def _add_card_to_user(self, user_id: str, card_id: str):
        """Add card ID to user's card list"""
        try:
            users = await self.file_handler.read_json(self.users_file)
            for user in users:
                if user.get("id") == user_id:
                    if "cards" not in user:
                        user["cards"] = []
                    user["cards"].append(card_id)
                    break
            await self.file_handler.write_json(self.users_file, users)
        except Exception as e:
            print(f"Warning: Failed to update user card list: {e}")
    
    async def _remove_card_from_user(self, user_id: str, card_id: str):
        """Remove card ID from user's card list"""
        try:
            users = await self.file_handler.read_json(self.users_file)
            for user in users:
                if user.get("id") == user_id:
                    if "cards" in user and card_id in user["cards"]:
                        user["cards"].remove(card_id)
                    break
            await self.file_handler.write_json(self.users_file, users)
        except Exception as e:
            print(f"Warning: Failed to update user card list: {e}")