"""Pushover notification provider."""

from datetime import timedelta
import httpx

from .base import BaseNotifier


class PushoverNotifier(BaseNotifier):
    """Sends notifications via Pushover service."""
    
    PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"
    
    async def send_notification(self, zone_name: str, offline_duration: timedelta) -> bool:
        """Send a push notification via Pushover."""
        try:
            message = self._format_message(zone_name, offline_duration)
            
            payload = {
                "token": self.config.pushover_token,
                "user": self.config.pushover_user_key,
                "message": message,
                "title": "SYB Zone Offline Alert",
                "priority": 1,  # High priority
                "sound": "alarm"
            }
            
            async with httpx.AsyncClient(timeout=self.config.request_timeout) as client:
                response = await client.post(self.PUSHOVER_API_URL, data=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == 1:
                        self.logger.info(f"Pushover notification sent for zone {zone_name}")
                        return True
                    else:
                        self.logger.error(f"Pushover API error: {result.get('errors', [])}")
                        return False
                else:
                    self.logger.error(f"Pushover HTTP error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to send Pushover notification: {e}")
            return False