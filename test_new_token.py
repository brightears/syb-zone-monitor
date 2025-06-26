#!/usr/bin/env python3
"""Test the new WhatsApp token directly."""

import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_new_token():
    """Test WhatsApp with the new token."""
    token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_id = "742462142273418"  # Your business number ID
    
    if not token:
        print("❌ No token found in .env")
        return
    
    print("🔍 Testing WhatsApp with new token")
    print("=" * 60)
    print(f"Phone Number ID: {phone_id}")
    print(f"Token preview: {token[:20]}...{token[-20:]}")
    
    # Test 1: Verify phone number
    print("\n1️⃣ Verifying phone number...")
    
    async with httpx.AsyncClient() as client:
        url = f"https://graph.facebook.com/v17.0/{phone_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Phone verified: {data.get('display_phone_number')}")
            print(f"Account name: {data.get('verified_name')}")
            
            # Test 2: Send message
            print("\n2️⃣ Sending test message to +66856644142...")
            
            msg_url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
            msg_data = {
                "messaging_product": "whatsapp",
                "to": "66856644142",
                "type": "text",
                "text": {
                    "body": "Test message with new token - If you receive this, WhatsApp is working correctly!"
                }
            }
            
            msg_response = await client.post(
                msg_url, 
                json=msg_data, 
                headers=headers
            )
            
            print(f"Message status: {msg_response.status_code}")
            result = msg_response.json()
            
            if msg_response.status_code == 200:
                print(f"✅ Message sent! ID: {result.get('messages', [{}])[0].get('id', 'N/A')}")
            else:
                print(f"❌ Error: {result}")
        else:
            error_data = response.json()
            print(f"❌ Error: {error_data}")

asyncio.run(test_new_token())