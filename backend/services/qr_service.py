"""
QR code generation service for Digital Audio Wedding Cards
"""
import os
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from fastapi import HTTPException


class QRService:
    """Service class for QR code generation"""
    
    def __init__(self):
        # Point to main directory structure (not backend subdirectory)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.qr_codes_dir = os.path.join(base_dir, "data", "qr_codes")
        self.base_url = "http://localhost:3000"  # Frontend server URL
        
        # Ensure directory exists
        os.makedirs(self.qr_codes_dir, exist_ok=True)
    
    def generate_qr_code(self, card_id: str) -> str:
        """Generate QR code for a wedding card"""
        try:
            # Create the URL that the QR code will point to
            card_url = f"{self.base_url}/view-card.html?id={card_id}"
            
            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,  # Controls the size of the QR code
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            # Add data to QR code
            qr.add_data(card_url)
            qr.make(fit=True)
            
            # Create QR code image with styling
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
                fill_color="black",
                back_color="white"
            )
            
            # Save QR code image
            filename = f"{card_id}_qr.png"
            filepath = os.path.join(self.qr_codes_dir, filename)
            img.save(filepath)
            
            # Return relative path for consistency
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            relative_path = os.path.relpath(filepath, base_dir).replace('\\', '/')
            return relative_path
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate QR code: {str(e)}")
    
    def get_qr_code_url(self, card_id: str) -> str:
        """Get the URL that a QR code points to"""
        return f"{self.base_url}/view-card.html?id={card_id}"
    
    def update_base_url(self, new_base_url: str):
        """Update the base URL for QR code generation"""
        self.base_url = new_base_url