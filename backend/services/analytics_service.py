"""
Analytics service for Digital Audio Wedding Cards
"""
import os
from datetime import datetime
from typing import List, Dict, Any
from fastapi import HTTPException

from models.analytics import ViewTrack, CardAnalytics, CardView
from utils.file_handler import FileHandler


class AnalyticsService:
    """Service class for analytics operations"""
    
    def __init__(self):
        self.file_handler = FileHandler()
        # Point to main directory structure (not backend subdirectory)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.analytics_file = os.path.join(base_dir, "data", "analytics.json")
    
    async def track_view(self, view_data: ViewTrack) -> bool:
        """Record a card view event"""
        try:
            # Create view record
            view_record = CardView(
                card_id=view_data.card_id,
                viewer_name=view_data.viewer_name,
                viewed_at=datetime.now(),
                ip_address=view_data.ip_address
            )
            
            # Save to analytics file
            view_dict = view_record.dict()
            success = await self.file_handler.append_json(self.analytics_file, view_dict)
            
            return success
            
        except Exception as e:
            print(f"Error tracking view: {e}")
            return False
    
    async def get_card_analytics(self, card_id: str) -> CardAnalytics:
        """Get analytics for a specific card"""
        try:
            analytics_data = await self.file_handler.read_json(self.analytics_file)
            
            # Filter views for this card
            card_views = [
                CardView(**view) for view in analytics_data 
                if view["card_id"] == card_id
            ]
            
            # Calculate analytics
            total_views = len(card_views)
            viewer_names = list(set([view.viewer_name for view in card_views]))
            unique_viewers = len(viewer_names)
            
            # Get recent views (last 10)
            recent_views = sorted(card_views, key=lambda x: x.viewed_at, reverse=True)[:10]
            
            return CardAnalytics(
                card_id=card_id,
                total_views=total_views,
                unique_viewers=unique_viewers,
                viewer_names=viewer_names,
                recent_views=recent_views
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")
    
    async def get_user_analytics(self, user_id: str) -> List[Dict[str, Any]]:
        """Get analytics for all cards belonging to a user"""
        try:
            # Get user's cards
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cards_file = os.path.join(base_dir, "data", "cards.json")
            cards_data = await self.file_handler.read_json(cards_file)
            user_cards = [card for card in cards_data if card["user_id"] == user_id]
            
            # Get analytics for each card
            analytics_data = await self.file_handler.read_json(self.analytics_file)
            
            result = []
            for card in user_cards:
                card_id = card["id"]
                
                # Filter views for this card
                card_views = [
                    view for view in analytics_data 
                    if view["card_id"] == card_id
                ]
                
                # Calculate analytics
                total_views = len(card_views)
                viewer_names = list(set([view["viewer_name"] for view in card_views]))
                unique_viewers = len(viewer_names)
                
                # Get recent views (last 5 for summary)
                recent_views = sorted(card_views, key=lambda x: x["viewed_at"], reverse=True)[:5]
                
                result.append({
                    "card_id": card_id,
                    "message": card["message"],
                    "created_at": card["created_at"],
                    "total_views": total_views,
                    "unique_viewers": unique_viewers,
                    "viewer_names": viewer_names,
                    "recent_views": recent_views
                })
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get user analytics: {str(e)}")