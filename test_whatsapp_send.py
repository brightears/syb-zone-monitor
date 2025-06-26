#!/usr/bin/env python3
"""Test WhatsApp sending directly."""

import asyncio
import os
from dotenv import load_dotenv
from whatsapp_service import get_whatsapp_service

load_dotenv()

async def test_send():
    """Test sending a WhatsApp message."""
    whatsapp = get_whatsapp_service()
    
    if not whatsapp or not whatsapp.enabled:
        print("❌ WhatsApp service not available or not enabled")
        return
    
    print("✅ WhatsApp service initialized")
    print(f"   Phone ID: {whatsapp.phone_number_id}")
    print(f"   Token preview: {whatsapp.access_token[:20]}...{whatsapp.access_token[-20:]}")
    
    # Test phone number - replace with your test number
    test_number = "+66856644142"  # Your test number from the logs
    test_message = "Test message from debugging script - checking if WhatsApp sending works"
    
    print(f"\nSending test message to {test_number}")
    result = await whatsapp.send_message(test_number, test_message)
    
    print(f"\nResult: {result}")
    
    if result['success']:
        print("✅ Message sent successfully!")
        print(f"   Message ID: {result.get('message_id')}")
    else:
        print("❌ Failed to send message")
        print(f"   Error: {result.get('error')}")
        print(f"   Details: {result.get('details')}")

if __name__ == "__main__":
    asyncio.run(test_send())