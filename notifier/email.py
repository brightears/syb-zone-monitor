"""Email notification provider using SMTP."""

import smtplib
from datetime import timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .base import BaseNotifier


class EmailNotifier(BaseNotifier):
    """Sends notifications via email using SMTP."""
    
    async def send_notification(self, zone_name: str, offline_duration: timedelta) -> bool:
        """Send an email notification."""
        try:
            # Create email content
            subject = f"SYB Zone Offline Alert: {zone_name}"
            body = self._format_message(zone_name, offline_duration)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.email_from
            msg['To'] = self.config.email_to
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                if self.config.smtp_password:
                    server.login(self.config.smtp_username, self.config.smtp_password)
                
                text = msg.as_string()
                server.sendmail(self.config.email_from, self.config.email_to, text)
            
            self.logger.info(f"Email notification sent for zone {zone_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            return False