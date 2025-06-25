"""Email service for sending notifications to multiple recipients."""

import os
import smtplib
import asyncio
import logging
from typing import List, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class EmailService:
    """Handle email notifications to multiple recipients."""
    
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.email_from = os.getenv('EMAIL_FROM', 'noreply@bmasia.com')
        self.enabled = all([self.smtp_host, self.smtp_username, self.smtp_password])
        
        if not self.enabled:
            logger.warning("Email service is not properly configured. Missing SMTP credentials.")
    
    async def send_email(self, to_addresses: List[str], subject: str, body: str, 
                        is_html: bool = False) -> Dict[str, Any]:
        """
        Send email to multiple recipients.
        
        Args:
            to_addresses: List of email addresses
            subject: Email subject
            body: Email body (text or HTML)
            is_html: Whether the body is HTML
            
        Returns:
            Dict with success status and details
        """
        if not self.enabled:
            return {
                'success': False,
                'error': 'Email service is not configured',
                'sent_to': []
            }
        
        if not to_addresses:
            return {
                'success': False,
                'error': 'No recipients provided',
                'sent_to': []
            }
        
        try:
            # Create message
            msg = MIMEMultipart('alternative' if is_html else 'mixed')
            msg['From'] = self.email_from
            msg['To'] = ', '.join(to_addresses)
            msg['Subject'] = subject
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            sent_to = []
            failed = []
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                
                # Send to each recipient individually for better tracking
                for email in to_addresses:
                    try:
                        server.send_message(msg, from_addr=self.email_from, to_addrs=[email])
                        sent_to.append(email)
                        logger.info(f"Email sent successfully to {email}")
                    except Exception as e:
                        failed.append({'email': email, 'error': str(e)})
                        logger.error(f"Failed to send email to {email}: {e}")
            
            return {
                'success': len(sent_to) > 0,
                'sent_to': sent_to,
                'failed': failed,
                'total': len(to_addresses)
            }
            
        except Exception as e:
            logger.error(f"Email service error: {e}")
            return {
                'success': False,
                'error': str(e),
                'sent_to': []
            }
    
    def format_zone_alert_email(self, account_name: str, zones_info: Dict[str, Any]) -> Dict[str, str]:
        """
        Format a zone alert email.
        
        Args:
            account_name: Name of the account
            zones_info: Dictionary with zone status information
            
        Returns:
            Dict with subject and body
        """
        offline_zones = zones_info.get('offline_zones', [])
        expired_zones = zones_info.get('expired_zones', [])
        unpaired_zones = zones_info.get('unpaired_zones', [])
        
        subject = f"🚨 Zone Alert - {account_name}"
        
        body = f"""
Zone Alert for {account_name}

This is an automated notification from the BMAsia Zone Monitoring System.

"""
        
        if offline_zones:
            body += f"⚠️ OFFLINE ZONES ({len(offline_zones)}):\n"
            body += "-" * 40 + "\n"
            for zone in offline_zones:
                body += f"• {zone['name']}\n"
                if zone.get('offline_duration'):
                    body += f"  Offline for: {zone['offline_duration']}\n"
            body += "\n"
        
        if expired_zones:
            body += f"⚠️ EXPIRED SUBSCRIPTIONS ({len(expired_zones)}):\n"
            body += "-" * 40 + "\n"
            for zone in expired_zones:
                body += f"• {zone['name']}\n"
            body += "\n"
        
        if unpaired_zones:
            body += f"⚠️ NO PAIRED DEVICE ({len(unpaired_zones)}):\n"
            body += "-" * 40 + "\n"
            for zone in unpaired_zones:
                body += f"• {zone['name']}\n"
            body += "\n"
        
        body += """
Need assistance? Contact BMAsia Support:
- Email: support@bmasia.com
- Phone: +66 63 237 7765

Best regards,
BMAsia Support Team
"""
        
        return {
            'subject': subject,
            'body': body
        }


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get or create email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service