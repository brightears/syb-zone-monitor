#!/usr/bin/env python3
"""Test with correct Phone ID."""

import asyncio
import os
from datetime import datetime

# Force the correct Phone ID
os.environ['WHATSAPP_PHONE_NUMBER_ID'] = '742462142273418'

from dotenv import load_dotenv
load_dotenv(override=True)

from whatsapp_service import WhatsAppService

async def test():
    service = WhatsAppService()
    
    print(f"🔍 Configuration Check:")
    print(f"Phone ID being used: {service.phone_number_id}")
    print(f"Should be: 742462142273418")
    print(f"Correct: {service.phone_number_id == '742462142273418'}")
    
    if service.phone_number_id != '742462142273418':
        print("\n❌ Wrong Phone ID is being used!")
        print("Forcing correct ID...")
        service.phone_number_id = '742462142273418'
    
    TEST_NUMBER = "+66856644142"
    msg = f"Test with correct Phone ID at {datetime.now().strftime('%H:%M')}"
    
    print(f"\n📱 Sending to: {TEST_NUMBER}")
    print(f"🔑 Using Phone ID: {service.phone_number_id}")
    
    result = await service.send_message(TEST_NUMBER, msg)
    print(f"\nResult: {result}")
    
    if result['success']:
        print("\n✅ Message sent! Check WhatsApp Manager > Insights in a few minutes")
    else:
        print(f"\n❌ Error: {result.get('error')}")

asyncio.run(test())