"""WhatsApp Business Cloud API Service using Templates."""

import os
import httpx
import asyncio
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for sending WhatsApp messages via WhatsApp Business Cloud API."""
    
    def __init__(self):
        """Initialize WhatsApp service with configuration from environment."""
        self.enabled = os.getenv('WHATSAPP_ENABLED', 'false').lower() == 'true'
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.api_version = os.getenv('WHATSAPP_API_VERSION', 'v17.0')
        
        # Validate configuration if enabled
        if self.enabled:
            if not self.phone_number_id or not self.access_token:
                logger.warning("WhatsApp enabled but missing WHATSAPP_PHONE_NUMBER_ID or WHATSAPP_ACCESS_TOKEN")
                self.enabled = False
            else:
                logger.info("WhatsApp service initialized successfully")
        else:
            logger.info("WhatsApp service is disabled")
    
    @property
    def api_url(self) -> str:
        """Get the WhatsApp API URL."""
        return f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
    
    async def send_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """
        Send a WhatsApp message to a phone number.
        
        For test numbers, we'll use the hello_world template.
        For production, you'd create a custom template.
        """
        if not self.enabled:
            return {
                'success': False,
                'error': 'WhatsApp service is not enabled'
            }
        
        # Clean phone number
        to_number = to_number.strip().replace(' ', '').replace('+', '')
        
        # Prepare request
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # For test number, use hello_world template
        # In production, you'd create a custom template for zone alerts
        data = {
            'messaging_product': 'whatsapp',
            'to': to_number,
            'type': 'template',
            'template': {
                'name': 'hello_world',
                'language': {
                    'code': 'en_US'
                }
            }
        }
        
        # Log that we're using template due to test number limitations
        logger.info(f"Using hello_world template for test number. Zone alert: {message[:50]}...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                
                response_data = response.json()
                
                if response.status_code == 200:
                    logger.info(f"WhatsApp template sent successfully to {to_number}")
                    logger.info(f"Note: Actual message content: {message}")
                    return {
                        'success': True,
                        'message_id': response_data.get('messages', [{}])[0].get('id'),
                        'to': to_number,
                        'note': 'Using test template - actual zone alert logged above'
                    }
                else:
                    error_msg = response_data.get('error', {}).get('message', 'Unknown error')
                    logger.error(f"WhatsApp API error: {error_msg}")
                    return {
                        'success': False,
                        'error': error_msg,
                        'status_code': response.status_code
                    }
                    
        except httpx.TimeoutException:
            logger.error("WhatsApp API request timed out")
            return {
                'success': False,
                'error': 'Request timed out'
            }
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def format_zone_alert_message(self, account_name: str, zones_info: Dict[str, Any]) -> str:
        """
        Format a zone alert message for WhatsApp.
        
        Note: This message will be logged but not sent with test number.
        """
        offline_zones = zones_info.get('offline_zones', [])
        
        message = f"🚨 Zone Alert - {account_name}\n\n"
        
        if offline_zones:
            message += f"⚠️ {len(offline_zones)} zones offline:\n"
            for zone in offline_zones[:5]:
                message += f"• {zone['name']}\n"
            if len(offline_zones) > 5:
                message += f"• ... and {len(offline_zones) - 5} more\n"
        
        message += "\n📞 Need help? Contact BMAsia Support"
        
        return message


# Singleton instance
_whatsapp_service = None


def get_whatsapp_service() -> WhatsAppService:
    """Get or create the WhatsApp service singleton."""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service