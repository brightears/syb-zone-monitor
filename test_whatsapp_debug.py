#\!/usr/bin/env python3
"""Debug WhatsApp delivery issues."""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv(override=True)

from whatsapp_service import WhatsAppService

async def debug_whatsapp():
    """Debug WhatsApp message delivery."""
    print("\n🔍 WhatsApp Delivery Debug")
    print("=" * 60)
    
    service = WhatsAppService()
    
    # Test with your number
    TEST_NUMBER = "+66856644142"
    
    print(f"📱 Sending to: {TEST_NUMBER}")
    print(f"🏢 From business: +66 63 237 7765")
    print(f"🔑 Phone ID: {service.phone_number_id}")
    
    # Simple test message
    msg = f"WhatsApp test at {datetime.now().strftime('%H:%M:%S')}"
    
    print(f"\n📤 Sending: {msg}")
    result = await service.send_message(TEST_NUMBER, msg)
    
    if result['success']:
        print(f"✅ API Success - Message ID: {result.get('message_id', 'N/A')}")
        print(f"   Sent to: {result.get('to')}")
    else:
        print(f"❌ API Failed: {result.get('error')}")
    
    print("\n" + "=" * 60)
    print("📋 Please check:")
    print("1. WhatsApp > Settings > Privacy > Message Requests")
    print("2. WhatsApp > Chats > Archived or Spam")
    print("3. Add +66632377765 to your contacts")
    print("4. Check Meta Business Suite > WhatsApp Manager > Insights")

if __name__ == "__main__":
    asyncio.run(debug_whatsapp())
EOF < /dev/null