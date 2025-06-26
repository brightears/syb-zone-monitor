#!/usr/bin/env python3
"""Check WhatsApp delivery."""

import asyncio
from datetime import datetime
from dotenv import load_dotenv
load_dotenv(override=True)

from whatsapp_service import WhatsAppService

async def check():
    service = WhatsAppService()
    TEST_NUMBER = "+66856644142"
    
    print(f"\n📱 Testing WhatsApp delivery to: {TEST_NUMBER}")
    print(f"🔑 Using Phone ID: {service.phone_number_id}")
    
    msg = f"Test from SYB Monitor at {datetime.now().strftime('%H:%M:%S')}"
    result = await service.send_message(TEST_NUMBER, msg)
    
    print(f"\nAPI Response: {result}")
    
    if result['success']:
        print("\n✅ API accepted the message")
        print("\n⚠️  If you don't see the message, please check:")
        print("1. WhatsApp > Settings > Privacy > Others > Message Requests")
        print("2. Your WhatsApp archived chats")
        print("3. Try adding +66632377765 to your contacts first")
        print("4. Check if the number shows as 'BMAsia' or similar")
    else:
        print(f"\n❌ API Error: {result.get('error')}")

asyncio.run(check())