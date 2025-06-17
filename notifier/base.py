"""Base notification classes and notification chain logic."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from config import Config


class BaseNotifier(ABC):
    """Abstract base class for notification providers."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def send_notification(self, zone_name: str, offline_duration: timedelta) -> bool:
        """
        Send a notification about an offline zone.
        
        Args:
            zone_name: Name of the offline zone
            offline_duration: How long the zone has been offline
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        pass
    
    def _format_message(self, zone_name: str, offline_duration: timedelta) -> str:
        """Format the notification message."""
        minutes = int(offline_duration.total_seconds() // 60)
        offline_since = datetime.now() - offline_duration
        time_str = offline_since.strftime("%H:%M")
        
        return (
            f"🌐 Zone \"{zone_name}\" offline since {time_str} (>{minutes} min)\n"
            f"Dashboard: {self.config.dashboard_url}"
        )


class NotificationChain:
    """Manages the notification chain with fallback logic."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.notifiers: List[BaseNotifier] = []
        self.alert_history: Dict[str, datetime] = {}  # zone_id -> last_alert_time
        
        # Initialize available notifiers
        self._setup_notifiers()
    
    def _setup_notifiers(self):
        """Setup available notification providers in priority order."""
        from .pushover import PushoverNotifier
        from .email import EmailNotifier
        
        # Primary: Pushover (if configured)
        if self.config.pushover_token and self.config.pushover_user_key:
            self.notifiers.append(PushoverNotifier(self.config))
            self.logger.info("Pushover notifier enabled")
        
        # Fallback: Email (if configured)
        if (self.config.smtp_host and self.config.smtp_username and 
            self.config.email_from and self.config.email_to):
            self.notifiers.append(EmailNotifier(self.config))
            self.logger.info("Email notifier enabled")
        
        if not self.notifiers:
            self.logger.warning("No notification providers configured!")
    
    async def send_alert(self, zone_name: str, offline_duration: timedelta) -> bool:
        """
        Send alert through notification chain with fallback logic.
        
        Args:
            zone_name: Name of the offline zone
            offline_duration: How long the zone has been offline
            
        Returns:
            True if any notification was sent successfully
        """
        # Check if we already sent an alert for this zone recently
        zone_id = zone_name  # Using zone_name as key for simplicity
        last_alert = self.alert_history.get(zone_id)
        
        if last_alert:
            time_since_last_alert = datetime.now() - last_alert
            # Don't spam alerts - minimum 30 minutes between alerts for same zone
            if time_since_last_alert < timedelta(minutes=30):
                self.logger.debug(f"Skipping alert for {zone_name} - too soon since last alert")
                return False
        
        success = False
        
        for i, notifier in enumerate(self.notifiers):
            try:
                self.logger.info(f"Sending alert via {notifier.__class__.__name__} for zone {zone_name}")
                
                if await notifier.send_notification(zone_name, offline_duration):
                    self.logger.info(f"Alert sent successfully via {notifier.__class__.__name__}")
                    success = True
                    
                    # If this is the primary notifier, we're done
                    if i == 0:
                        break
                    
                    # For fallback notifiers, add a delay to see if primary succeeds
                    await asyncio.sleep(60)
                    break
                else:
                    self.logger.warning(f"Failed to send alert via {notifier.__class__.__name__}")
                    
            except Exception as e:
                self.logger.error(f"Error sending alert via {notifier.__class__.__name__}: {e}")
        
        if success:
            self.alert_history[zone_id] = datetime.now()
        
        return success