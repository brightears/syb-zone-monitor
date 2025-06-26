#!/usr/bin/env python3
"""Test with fresh token load."""

import os
import sys

# Clear any cached environment
for key in ['WHATSAPP_ACCESS_TOKEN', 'WHATSAPP_PHONE_NUMBER_ID']:
    if key in os.environ:
        del os.environ[key]

# Force reload
from dotenv import load_dotenv
load_dotenv(override=True, verbose=True)

import httpx
import asyncio

async def test():
    token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_id = "742462142273418"
    
    print("🔍 Testing WhatsApp with fresh environment")
    print("=" * 60)
    print(f"Phone Number ID: {phone_id}")
    print(f"Token preview: {token[:30]}...{token[-20:]}")
    
    # Direct test
    url = f"https://graph.facebook.com/v17.0/{phone_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Token is valid!")
            print(f"Phone: {data.get('display_phone_number')}")
            
            # Send message
            print("\n📱 Sending message...")
            msg_url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
            msg_data = {
                "messaging_product": "whatsapp",
                "to": "66856644142",
                "type": "text",
                "text": {"body": "Test with new token - this should work now!"}
            }
            
            msg_response = await client.post(msg_url, json=msg_data, headers=headers)
            print(f"Message status: {msg_response.status_code}")
            
            if msg_response.status_code == 200:
                result = msg_response.json()
                print(f"✅ Message sent! ID: {result.get('messages', [{}])[0].get('id', 'N/A')}")
            else:
                print(f"❌ Error: {msg_response.json()}")
        else:
            print(f"❌ Error: {response.json()}")

asyncio.run(test())