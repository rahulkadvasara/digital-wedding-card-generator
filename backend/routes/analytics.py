"""
Analytics routes for Digital Audio Wedding Cards
"""
from fastapi import APIRouter, HTTPException, status, Request
from models.analytics import ViewTrack, CardAnalytics
from services.analytics_service import AnalyticsService

router = APIRouter()
analytics_service = AnalyticsService()

@router.get("/user/{user_id}")
async def get_user_analytics(user_id: str):
    """Get analytics for all cards belonging to a user"""
    try:
        return await analytics_service.get_user_analytics(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user analytics: {str(e)}")

@router.get("/{card_id}")
async def get_card_analytics(card_id: str):
    """Get analytics for a specific card"""
    try:
        return await analytics_service.get_card_analytics(card_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.post("/track")
async def track_view(view_data: ViewTrack, request: Request):
    """Record a card view event"""
    try:
        # Get client IP address
        client_ip = request.client.host
        view_data.ip_address = client_ip
        
        success = await analytics_service.track_view(view_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to track view")
        
        return {"message": "View tracked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track view: {str(e)}")