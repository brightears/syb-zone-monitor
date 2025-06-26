#!/usr/bin/env python3
"""Interactive WhatsApp test."""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Force reload of .env file
load_dotenv(override=True)

from whatsapp_service import WhatsAppService

async def test_whatsapp():
    """Test sending a WhatsApp message."""
    print("\n🚀 WhatsApp Business API Test")
    print("=" * 50)
    
    service = WhatsAppService()
    
    if not service.enabled:
        print("❌ WhatsApp service is not enabled!")
        return
    
    print("✅ WhatsApp Service is enabled")
    print(f"📱 Using business number: +66 63 237 7765")
    print(f"🔑 Phone Number ID: {service.phone_number_id}")
    
    print("\n" + "=" * 50)
    print("Please enter a phone number to test.")
    print("Note: You cannot send to your own business number.")
    print("Format: +CountryCode Number (e.g., +66812345678)")
    print("=" * 50)
    
    # Some test suggestions
    print("\nSuggested test numbers:")
    print("- Your personal WhatsApp number")
    print("- A colleague's WhatsApp number")
    
    # Hardcode a test number here if you want
    TEST_NUMBER = "+66812345678"  # Change this to your personal number
    
    print(f"\n📱 Sending test message to: {TEST_NUMBER}")
    print("(Edit TEST_NUMBER in the script to change)")
    
    # Test message
    test_message = f"""🎉 WhatsApp Business Test

Hello! This is a test message from the SYB Zone Monitor system.

✅ Your WhatsApp integration is working!
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📱 Sent from: +66 63 237 7765

This confirms that automated zone alerts can be sent via WhatsApp."""
    
    print("\nSending message...")
    
    # Send the message
    result = await service.send_message(TEST_NUMBER, test_message)
    
    if result['success']:
        print(f"\n✅ SUCCESS! Message sent to {TEST_NUMBER}")
        print(f"📬 Message ID: {result.get('message_id', 'N/A')}")
        print("\n🎉 WhatsApp Business API is working correctly!")
        print("You can now:")
        print("- Send manual notifications via the 'Notify' button")
        print("- Set up automated alerts via the 'Auto' button")
    else:
        print(f"\n❌ Failed to send message!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        if 'Invalid parameter' in str(result.get('error', '')):
            print("\n💡 Tips:")
            print("- Make sure the number has WhatsApp")
            print("- Use correct format: +66812345678")
            print("- Cannot send to your own business number")
            print("- The recipient should have your business number in contacts")

if __name__ == "__main__":
    asyncio.run(test_whatsapp())