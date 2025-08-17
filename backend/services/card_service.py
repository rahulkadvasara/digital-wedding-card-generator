"""
Card management service for Digital Audio Wedding Cards

This service handles the core business logic for wedding card operations,
including creation, retrieval, and management. It integrates with the
VoiceService for AI voice generation and maintains data persistence
through JSON file storage.

Key Responsibilities:
- Card creation with optional voice sample processing
- Voice sample upload and integration with AI voice cloning
- Card retrieval for both private (user dashboard) and public (QR viewing) access
- View count tracking for analytics
- User-card relationship management
"""
import os
import uuid
import base64
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, UploadFile
import aiofiles

from models.card import Card, CardCreate, CardResponse, CardView
from utils.file_handler import FileHandler
from services.voice_service import VoiceService, VoiceGenerationError
from services.qr_service import QRService

# Configure logging
logger = logging.getLogger(__name__)


class CardService:
    """
    Service class for card management operations
    
    This service orchestrates the complex workflow of wedding card creation,
    which involves:
    1. Processing user input (message text)
    2. Handling voice sample uploads
    3. Integrating with AI voice cloning services
    4. Managing file storage and data persistence
    5. Providing different views for different user types
    """
    
    def __init__(self):
        # Initialize dependencies
        self.file_handler = FileHandler()        # JSON file operations
        self.voice_service = VoiceService()      # AI voice generation
        self.qr_service = QRService()            # QR code generation
        
        # File paths for data persistence - use absolute paths to avoid issues
        # Point to main directory structure (not backend subdirectory)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.cards_file = os.path.join(self.base_dir, "data", "cards.json")
        self.users_file = os.path.join(self.base_dir, "data", "users.json")
        
        # Directory paths for file uploads
        self.voice_samples_dir = os.path.join(self.base_dir, "data", "audio", "samples")
        self.qr_codes_dir = os.path.join(self.base_dir, "data", "qr_codes")
        
        # Ensure all required directories exist
        # This prevents file operation errors during runtime
        os.makedirs(self.voice_samples_dir, exist_ok=True)
        os.makedirs(self.qr_codes_dir, exist_ok=True)
    
    async def create_card(self, user_id: str, card_data: CardCreate, voice_file: Optional[UploadFile] = None) -> CardResponse:
        """Create a new wedding card"""
        try:
            # Generate unique card ID
            card_id = f"card_{uuid.uuid4().hex[:8]}"
            
            # Handle voice sample upload and AI voice generation if provided
            voice_sample_path = None
            ai_voice_path = None
            
            if voice_file:
                # Save the voice sample
                voice_sample_path = await self._save_voice_sample(card_id, voice_file)
                
                # Generate AI voice model from the sample - FAIL if this fails
                try:
                    print(f"Starting voice cloning for user {user_id}...")
                    voice_model_id = await self.voice_service.clone_voice(user_id, voice_sample_path)
                    print(f"Voice cloning completed. Model ID: {voice_model_id}")
                    
                    # Set AI voice path for future synthesis
                    ai_voice_path = f"data/audio/generated/{card_id}_ai_voice.mp3"
                    print(f"AI voice path set: {ai_voice_path}")
                    
                except VoiceGenerationError as voice_error:
                    print(f"Voice cloning failed (VoiceGenerationError): {voice_error}")
                    # Remove the saved voice sample since card creation failed
                    try:
                        if voice_sample_path and os.path.exists(voice_sample_path):
                            os.remove(voice_sample_path)
                            print(f"Removed voice sample file: {voice_sample_path}")
                    except Exception as cleanup_error:
                        print(f"Failed to cleanup voice sample: {cleanup_error}")
                    
                    # Fail card creation completely with specific error
                    error_message = f"Failed to process voice recording: {str(voice_error)}"
                    print(f"Raising HTTPException with message: {error_message}")
                    raise HTTPException(status_code=400, detail=error_message)
                
                except Exception as voice_error:
                    print(f"Voice cloning failed (Generic Exception): {type(voice_error).__name__}: {voice_error}")
                    # Remove the saved voice sample since card creation failed
                    try:
                        if voice_sample_path and os.path.exists(voice_sample_path):
                            os.remove(voice_sample_path)
                            print(f"Removed voice sample file: {voice_sample_path}")
                    except Exception as cleanup_error:
                        print(f"Failed to cleanup voice sample: {cleanup_error}")
                    
                    # Fail card creation completely with generic error
                    error_message = f"Failed to process voice recording: {str(voice_error)}"
                    print(f"Raising HTTPException with message: {error_message}")
                    raise HTTPException(status_code=400, detail=error_message)
            
            # Generate QR code for the card
            qr_code_path = None
            try:
                print(f"Generating QR code for card {card_id}...")
                qr_code_path = self.qr_service.generate_qr_code(card_id)
                print(f"QR code generated: {qr_code_path}")
            except Exception as qr_error:
                print(f"QR code generation failed: {qr_error}")
                # Continue with card creation even if QR generation fails
            
            # Create card object
            card = Card(
                id=card_id,
                user_id=user_id,
                message=card_data.message,
                voice_sample_path=voice_sample_path,
                ai_voice_path=ai_voice_path,
                qr_code_path=qr_code_path,
                created_at=datetime.now(),
                views=0
            )
            
            # Save card to JSON file
            try:
                card_dict = card.dict()
                print(f"Attempting to save card to: {self.cards_file}")
                print(f"Card data: {card_dict}")
                
                success = await self.file_handler.append_json(self.cards_file, card_dict)
                
                if not success:
                    print("Failed to save card - file handler returned False")
                    raise HTTPException(status_code=500, detail="Failed to save card to database")
                
                print("Card saved successfully to database")
                    
            except Exception as db_error:
                print(f"Database error saving card: {db_error}")
                logger.error(f"Database error saving card: {db_error}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
            
            # Update user's cards list
            await self._add_card_to_user(user_id, card_id)
            
            # Return card response
            return CardResponse(
                id=card.id,
                user_id=card.user_id,
                message=card.message,
                qr_code_path=card.qr_code_path,
                created_at=card.created_at,
                views=card.views
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions (like voice generation errors) without modification
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create card: {str(e)}")
    
    async def get_card(self, card_id: str) -> CardView:
        """Get card data for public viewing"""
        try:
            cards = await self.file_handler.read_json(self.cards_file)
            
            for card_data in cards:
                if card_data["id"] == card_id:
                    return CardView(
                        id=card_data["id"],
                        message=card_data["message"],
                        ai_voice_path=card_data.get("ai_voice_path")
                    )
            
            raise HTTPException(status_code=404, detail="Card not found")
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve card: {str(e)}")
    
    async def get_personalized_card(self, card_id: str, recipient_name: str) -> CardView:
        """Get card data with personalized AI voice message"""
        try:
            cards = await self.file_handler.read_json(self.cards_file)
            
            for card_data in cards:
                if card_data["id"] == card_id:
                    # Get the base card data
                    card_view = CardView(
                        id=card_data["id"],
                        message=card_data["message"],
                        ai_voice_path=card_data.get("ai_voice_path")
                    )
                    
                    # Generate personalized AI voice if we have a voice model for this user
                    user_id = card_data["user_id"]
                    voice_model_info = await self.voice_service.get_voice_model_info(user_id)
                    
                    if voice_model_info:
                        try:
                            print(f"Generating personalized voice for {recipient_name}...")
                            personalized_audio_path = await self.voice_service.synthesize_message(
                                user_id, card_data["message"], recipient_name
                            )
                            card_view.ai_voice_path = personalized_audio_path
                            print(f"Personalized voice generated: {personalized_audio_path}")
                        except Exception as voice_error:
                            print(f"Failed to generate personalized voice: {voice_error}")
                            # Use the default AI voice path if personalization fails
                    
                    return card_view
            
            raise HTTPException(status_code=404, detail="Card not found")
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve personalized card: {str(e)}")
    
    async def get_user_cards(self, user_id: str) -> List[CardResponse]:
        """Get all cards created by a specific user"""
        try:
            cards = await self.file_handler.read_json(self.cards_file)
            user_cards = []
            
            for card_data in cards:
                if card_data["user_id"] == user_id:
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
    
    async def update_card_views(self, card_id: str) -> bool:
        """Increment card view count"""
        try:
            cards = await self.file_handler.read_json(self.cards_file)
            
            for i, card_data in enumerate(cards):
                if card_data["id"] == card_id:
                    cards[i]["views"] = card_data.get("views", 0) + 1
                    return await self.file_handler.write_json(self.cards_file, cards)
            
            return False
            
        except Exception as e:
            print(f"Error updating card views: {e}")
            return False
    
    async def _save_voice_sample(self, card_id: str, voice_file: UploadFile) -> str:
        """Save uploaded voice sample file"""
        try:
            # Validate file type
            if not voice_file.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail="Invalid file type. Only audio files are allowed.")
            
            # Generate filename - standardize to .webm for voice samples
            file_extension = voice_file.filename.split('.')[-1] if '.' in voice_file.filename else 'webm'
            filename = f"{card_id}_voice_sample.{file_extension}"
            filepath = os.path.join(self.voice_samples_dir, filename)
            
            # Save file
            async with aiofiles.open(filepath, 'wb') as f:
                content = await voice_file.read()
                await f.write(content)
            
            # Return relative path instead of absolute path for consistency
            relative_path = os.path.relpath(filepath, self.base_dir).replace('\\', '/')
            return relative_path
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save voice sample: {str(e)}")
    
    async def _add_card_to_user(self, user_id: str, card_id: str) -> bool:
        """Add card ID to user's cards list"""
        try:
            users = await self.file_handler.read_json(self.users_file)
            
            for i, user_data in enumerate(users):
                if user_data["id"] == user_id:
                    if "cards" not in users[i]:
                        users[i]["cards"] = []
                    users[i]["cards"].append(card_id)
                    return await self.file_handler.write_json(self.users_file, users)
            
            return False
            
        except Exception as e:
            print(f"Error adding card to user: {e}")
            return False
    
    async def _update_card_qr_path(self, card_id: str, qr_code_path: str) -> bool:
        """Update card with QR code path"""
        try:
            cards = await self.file_handler.read_json(self.cards_file)
            
            for i, card_data in enumerate(cards):
                if card_data["id"] == card_id:
                    cards[i]["qr_code_path"] = qr_code_path
                    return await self.file_handler.write_json(self.cards_file, cards)
            
            return False
            
        except Exception as e:
            print(f"Error updating card QR path: {e}")
            return False