#!/usr/bin/env python3
"""Test the email service functionality."""

import asyncio
from email_service import get_email_service
import os
from dotenv import load_dotenv

load_dotenv()

async def test_email_service():
    """Test email service functionality."""
    print("Testing Email Service...")
    
    # Get the email service instance
    email_service = get_email_service()
    
    # Check if service is configured
    if not email_service.enabled:
        print("❌ Email service is not configured!")
        print(f"  SMTP_HOST: {email_service.smtp_host}")
        print(f"  SMTP_USERNAME: {'*' * len(email_service.smtp_username) if email_service.smtp_username else 'Not set'}")
        print(f"  SMTP_PASSWORD: {'Set' if email_service.smtp_password else 'Not set'}")
        return
    
    print("✅ Email service is configured")
    print(f"  SMTP Host: {email_service.smtp_host}:{email_service.smtp_port}")
    print(f"  From: {email_service.email_from}")
    
    # Test zone alert formatting
    print("\n📧 Testing zone alert email formatting...")
    zones_info = {
        'offline_zones': [
            {'name': 'Dining Area', 'offline_duration': '2h 30m'},
            {'name': 'Lobby', 'offline_duration': '45m'}
        ],
        'expired_zones': [
            {'name': 'Rooftop Bar'}
        ],
        'unpaired_zones': []
    }
    
    email_data = email_service.format_zone_alert_email(
        account_name="Test Restaurant",
        zones_info=zones_info
    )
    
    print(f"\nSubject: {email_data['subject']}")
    print(f"\nBody:\n{'-' * 50}")
    print(email_data['body'])
    print('-' * 50)
    
    # Test sending email (if you want to actually send)
    test_email = os.getenv('TEST_EMAIL_ADDRESS')
    if test_email:
        print(f"\n📮 Sending test email to: {test_email}")
        result = await email_service.send_email(
            to_addresses=[test_email],
            subject=email_data['subject'],
            body=email_data['body'],
            is_html=False
        )
        
        if result['success']:
            print(f"✅ Email sent successfully to {result['sent_to']}")
        else:
            print(f"❌ Failed to send email: {result.get('error')}")
            if result.get('failed'):
                print(f"   Failed recipients: {result['failed']}")
    else:
        print("\n⚠️  No TEST_EMAIL_ADDRESS set in .env - skipping actual send test")

if __name__ == "__main__":
    asyncio.run(test_email_service())