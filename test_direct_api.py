#!/usr/bin/env python3
"""Test WhatsApp API directly."""

import httpx
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

async def test_direct():
    """Test the API directly without our wrapper."""
    phone_id = "742462142273418"
    token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    
    # Your test number
    to_number = "66856644142"  # Without + for API
    
    print(f"📱 Direct API Test")
    print(f"From: +66 63 237 7765 (ID: {phone_id})")
    print(f"To: +{to_number}")
    
    url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": "Direct API test - if you see this, WhatsApp is working!"
        }
    }
    
    print("\n🔍 Request details:")
    print(f"URL: {url}")
    print(f"Phone format: {to_number}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        
        print(f"\n📊 Response:")
        print(f"Status: {response.status_code}")
        print(f"Body: {response.json()}")
        
        if response.status_code == 200:
            print("\n✅ Message sent via direct API!")
        else:
            print("\n❌ API error")

asyncio.run(test_direct())