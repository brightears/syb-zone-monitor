#!/usr/bin/env python3
"""Simple WhatsApp test - edit the TEST_NUMBER below."""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from whatsapp_service import WhatsAppService

load_dotenv()

# EDIT THIS: Put your test phone number here (with country code)
TEST_NUMBER = "+66632377765"  # You can change this to test with a different number

async def test_whatsapp():
    """Test sending a WhatsApp message."""
    print("Testing WhatsApp Business API...")
    print("-" * 50)
    
    # Initialize WhatsApp service
    service = WhatsAppService()
    
    print(f"WhatsApp Service Status: {'Enabled' if service.enabled else 'Disabled'}")
    if service.enabled:
        print(f"Phone Number ID: {service.phone_number_id}")
        print(f"Access Token: {'Set' if service.access_token else 'Not set'}")
        print(f"API Version: {service.api_version}")
    else:
        print("❌ WhatsApp service is not enabled!")
        return
    
    # Test message
    test_message = f"""🎉 WhatsApp Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is a test from SYB Zone Monitor.

Your WhatsApp Business integration is working!

Sent from: +66 63 237 7765"""
    
    print(f"\n📱 Sending test message to: {TEST_NUMBER}")
    
    # Send the message
    result = await service.send_message(TEST_NUMBER, test_message)
    
    print(f"\nAPI Response: {result}")
    
    if result['success']:
        print(f"\n✅ Success! Message sent to {TEST_NUMBER}")
        print(f"Message ID: {result.get('message_id', 'N/A')}")
    else:
        print(f"\n❌ Failed to send message!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        print(f"Details: {result.get('details', 'No details available')}")

if __name__ == "__main__":
    # First check environment variables
    print("Environment Check:")
    print(f"WHATSAPP_PHONE_NUMBER_ID: {os.getenv('WHATSAPP_PHONE_NUMBER_ID', 'Not set')}")
    print(f"WHATSAPP_ACCESS_TOKEN: {'Set' if os.getenv('WHATSAPP_ACCESS_TOKEN') else 'Not set'}")
    print(f"WHATSAPP_ENABLED: {os.getenv('WHATSAPP_ENABLED', 'Not set')}")
    print()
    
    asyncio.run(test_whatsapp())