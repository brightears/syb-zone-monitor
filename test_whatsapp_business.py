#!/usr/bin/env python3
"""Test WhatsApp Business API with the real business number."""

import asyncio
import os
from dotenv import load_dotenv
from whatsapp_service import WhatsAppService

load_dotenv()

async def test_whatsapp():
    """Test sending a WhatsApp message."""
    print("Testing WhatsApp Business API...")
    print("-" * 50)
    
    # Initialize WhatsApp service
    service = WhatsAppService()
    
    print(f"WhatsApp Service Status: {'Enabled' if service.enabled else 'Disabled'}")
    if service.enabled:
        print(f"Phone Number ID: {service.phone_number_id}")
        print(f"Using business number: +66 63 237 7765")
    else:
        print("❌ WhatsApp service is not enabled!")
        print("Check that WHATSAPP_ENABLED=true in .env")
        return
    
    # Test number - you can change this to your number
    test_number = input("\nEnter phone number to test (with country code, e.g., +66123456789): ").strip()
    
    if not test_number.startswith('+'):
        print("❌ Phone number must include country code (e.g., +66123456789)")
        return
    
    # Test message
    test_message = """🎉 WhatsApp Business API Test Success!

This is a test message from the SYB Zone Monitor system using your business number +66 63 237 7765.

If you receive this message, your WhatsApp integration is working correctly!

Time: {}""".format(asyncio.get_event_loop().time())
    
    print(f"\n📱 Sending test message to: {test_number}")
    print("Message preview:")
    print("-" * 50)
    print(test_message)
    print("-" * 50)
    
    # Send the message
    result = await service.send_message(test_number, test_message)
    
    if result['success']:
        print(f"\n✅ Success! Message sent to {test_number}")
        print(f"Message ID: {result.get('message_id', 'N/A')}")
        print("\nWhatsApp integration is working correctly!")
    else:
        print(f"\n❌ Failed to send message!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        print(f"Details: {result.get('details', 'No details available')}")
        
        if 'Invalid parameter' in str(result.get('error', '')):
            print("\n💡 This might mean the number hasn't been fully activated yet.")
            print("   Wait a bit more and try again.")

if __name__ == "__main__":
    print("=" * 60)
    print("WhatsApp Business API Test")
    print("=" * 60)
    asyncio.run(test_whatsapp())