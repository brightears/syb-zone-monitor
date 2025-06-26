#!/usr/bin/env python3
"""Final WhatsApp test with business number."""

import asyncio
import os
from datetime import datetime

# Clear any cached modules
import sys
for module in list(sys.modules.keys()):
    if 'whatsapp' in module:
        del sys.modules[module]

# Fresh load
from dotenv import load_dotenv
load_dotenv(override=True)

# Import after env is loaded
from whatsapp_service import WhatsAppService

async def test_whatsapp():
    """Test WhatsApp with business number."""
    print("\n🚀 WhatsApp Business API Test - Final Check")
    print("=" * 60)
    
    # Show raw environment variable
    phone_id_env = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    print(f"Environment WHATSAPP_PHONE_NUMBER_ID: {phone_id_env}")
    
    # Create service
    service = WhatsAppService()
    
    print(f"\nService Configuration:")
    print(f"- Enabled: {service.enabled}")
    print(f"- Phone Number ID: {service.phone_number_id}")
    print(f"- Expected ID: 742462142273418")
    print(f"- IDs Match: {service.phone_number_id == '742462142273418'}")
    
    if not service.enabled:
        print("\n❌ Service not enabled!")
        return
    
    # IMPORTANT: Change this to a number that can receive messages
    # Cannot be the same as the business number
    TEST_RECIPIENT = "+66856644142"  # Test recipient number
    
    print(f"\n📱 Test Details:")
    print(f"- From (Business): +66 63 237 7765")
    print(f"- To (Recipient): {TEST_RECIPIENT}")
    print(f"- Phone ID Used: {service.phone_number_id}")
    
    message = f"""✅ WhatsApp Business Test - {datetime.now().strftime('%H:%M:%S')}

This confirms your business number +66 63 237 7765 is working!

You can now send automated zone alerts via WhatsApp."""
    
    print("\nSending message...")
    result = await service.send_message(TEST_RECIPIENT, message)
    
    print(f"\nResult: {result}")
    
    if result['success']:
        print("\n✅ SUCCESS! Your business WhatsApp number is working!")
        print(f"Message ID: {result.get('message_id')}")
    else:
        print("\n❌ Failed!")
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    print("NOTE: Edit TEST_RECIPIENT on line 44 to your personal WhatsApp number!")
    print("      You cannot send to the same number as the business number.")
    asyncio.run(test_whatsapp())