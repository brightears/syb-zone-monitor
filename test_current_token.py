#!/usr/bin/env python3
"""Test with the current token."""

import os
from dotenv import load_dotenv
load_dotenv(override=True)

import httpx
import asyncio

async def test():
    token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_id = "742462142273418"
    
    print(f"Testing with current token...")
    print(f"Token preview: {token[:30]}...{token[-20:]}")
    
    # Test the token
    url = f"https://graph.facebook.com/v17.0/{phone_id}"
    params = {"access_token": token}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        print(f"\nAPI Response: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200:
            print("✅ Token is valid!")
            print(f"Phone: {data.get('display_phone_number')}")
            print(f"Name: {data.get('verified_name')}")
            
            # Try sending a message
            print("\n📱 Sending test message...")
            msg_url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
            msg_data = {
                "messaging_product": "whatsapp",
                "to": "66856644142",
                "type": "text",
                "text": {"body": "Test from current token"}
            }
            
            msg_response = await client.post(msg_url, json=msg_data, params=params)
            print(f"Message API: {msg_response.status_code}")
            print(f"Response: {msg_response.json()}")
        else:
            print(f"❌ Token error: {data}")

asyncio.run(test())