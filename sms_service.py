"""SMS notification service using Twilio."""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

logger = logging.getLogger(__name__)


class SMSService:
    """Handle SMS notifications via Twilio."""
    
    def __init__(self):
        self.enabled = os.getenv('SMS_ENABLED', 'false').lower() == 'true'
        if self.enabled:
            self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
            self.critical_threshold = int(os.getenv('SMS_CRITICAL_THRESHOLD', '1800'))  # 30 minutes
            self.quiet_hours_start = int(os.getenv('SMS_QUIET_HOURS_START', '22'))  # 10 PM
            self.quiet_hours_end = int(os.getenv('SMS_QUIET_HOURS_END', '7'))  # 7 AM
            
            if not all([self.account_sid, self.auth_token, self.from_number]):
                logger.warning("SMS enabled but Twilio credentials not fully configured")
                self.enabled = False
            else:
                try:
                    self.client = Client(self.account_sid, self.auth_token)
                    logger.info("SMS service initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Twilio client: {e}")
                    self.enabled = False
    
    def is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours."""
        current_hour = datetime.now().hour
        if self.quiet_hours_start > self.quiet_hours_end:
            # Quiet hours span midnight
            return current_hour >= self.quiet_hours_start or current_hour < self.quiet_hours_end
        else:
            return self.quiet_hours_start <= current_hour < self.quiet_hours_end
    
    def should_send_critical_sms(self, offline_duration: int) -> bool:
        """Determine if issue is critical enough for automatic SMS."""
        return (
            self.enabled and 
            offline_duration >= self.critical_threshold and 
            not self.is_quiet_hours()
        )
    
    async def send_sms(self, phone_number: str, message: str, force: bool = False) -> Dict:
        """Send SMS message."""
        if not self.enabled:
            return {'success': False, 'error': 'SMS service not enabled'}
        
        if not force and self.is_quiet_hours():
            return {'success': False, 'error': 'Cannot send SMS during quiet hours'}
        
        try:
            # Ensure phone number is in E.164 format
            if not phone_number.startswith('+'):
                # Assume US number if no country code
                if phone_number.startswith('1'):
                    phone_number = '+' + phone_number
                else:
                    phone_number = '+1' + phone_number
            
            # Truncate message if too long (SMS limit is 1600 chars)
            if len(message) > 1600:
                message = message[:1597] + '...'
            
            result = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone_number
            )
            
            logger.info(f"SMS sent successfully to {phone_number[:6]}... (SID: {result.sid})")
            
            return {
                'success': True,
                'message_sid': result.sid,
                'status': result.status,
                'to': result.to
            }
        except TwilioException as e:
            logger.error(f"Failed to send SMS to {phone_number[:6]}...: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {e}")
            return {'success': False, 'error': str(e)}
    
    async def send_bulk_sms(self, recipients: List[Dict[str, str]], message: str) -> List[Dict]:
        """Send SMS to multiple recipients."""
        results = []
        for recipient in recipients:
            phone = recipient.get('phone')
            if phone:
                result = await self.send_sms(phone, message)
                result['recipient'] = recipient
                results.append(result)
        return results
    
    def format_sms_alert(self, account_name: str, zones: List[Dict], alert_type: str = 'offline') -> str:
        """Format a concise SMS alert message."""
        if alert_type == 'offline':
            offline_zones = [z for z in zones if z.get('status') == 'offline']
            offline_count = len(offline_zones)
            
            if offline_count > 0:
                message = f"🚨 SYB ALERT: {account_name}\n"
                message += f"{offline_count} zone(s) offline:\n"
                
                # List first 3 offline zones
                for zone in offline_zones[:3]:
                    zone_name = zone['name'][:20]
                    if len(zone['name']) > 20:
                        zone_name += '...'
                    
                    duration = zone.get('offline_duration', 0)
                    if duration > 3600:
                        duration_str = f"{duration // 3600}h"
                    elif duration > 60:
                        duration_str = f"{duration // 60}m"
                    else:
                        duration_str = f"{duration}s"
                    
                    message += f"• {zone_name} ({duration_str})\n"
                
                if offline_count > 3:
                    message += f"...and {offline_count - 3} more\n"
                
                message += "\nCheck dashboard for details"
                return message
        
        elif alert_type == 'expired':
            expired_count = len([z for z in zones if z.get('status') == 'expired'])
            if expired_count > 0:
                message = f"⚠️ SYB: {account_name}\n"
                message += f"{expired_count} subscription(s) expired.\n"
                message += "Contact support to renew."
                return message
        
        elif alert_type == 'unpaired':
            unpaired_count = len([z for z in zones if z.get('status') == 'unpaired'])
            if unpaired_count > 0:
                message = f"📱 SYB: {account_name}\n"
                message += f"{unpaired_count} zone(s) need device pairing.\n"
                message += "Setup required to play music."
                return message
        
        return ""
    
    def format_custom_sms(self, message: str, max_length: int = 160) -> str:
        """Format a custom message for SMS, ensuring it fits in a single SMS if possible."""
        # Remove extra whitespace and newlines
        message = ' '.join(message.split())
        
        if len(message) <= max_length:
            return message
        
        # Try to truncate at a word boundary
        truncated = message[:max_length-3]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # If we find a space in the last 20%
            truncated = truncated[:last_space]
        
        return truncated + '...'


# Singleton instance
_sms_service: Optional[SMSService] = None

def get_sms_service() -> SMSService:
    """Get or create SMS service instance."""
    global _sms_service
    if _sms_service is None:
        _sms_service = SMSService()
    return _sms_service