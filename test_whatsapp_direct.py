#!/usr/bin/env python3
"""Direct WhatsApp API test to verify configuration."""

import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_whatsapp():
    """Test WhatsApp API directly."""
    
    # Get configuration
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    api_version = os.getenv('WHATSAPP_API_VERSION', 'v17.0')
    
    print(f"Phone Number ID: {phone_number_id}")
    print(f"Access Token: {'*' * 10 + access_token[-10:] if access_token else 'NOT SET'}")
    print(f"API Version: {api_version}")
    
    if not phone_number_id or not access_token:
        print("\nERROR: Missing WHATSAPP_PHONE_NUMBER_ID or WHATSAPP_ACCESS_TOKEN")
        return
    
    # API URL
    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
    print(f"\nAPI URL: {url}")
    
    # Test message
    to_number = input("\nEnter your WhatsApp number with country code (e.g., +60123456789): ")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'messaging_product': 'whatsapp',
        'to': to_number.strip(),
        'type': 'text',
        'text': {
            'body': '🧪 Test message from SYB Zone Monitor - WhatsApp integration is working!'
        }
    }
    
    print(f"\nSending test message to: {to_number}")
    print("Request data:", data)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=data,
                timeout=30.0
            )
            
            print(f"\nResponse status: {response.status_code}")
            print(f"Response body: {response.text}")
            
            if response.status_code == 200:
                print("\n✅ SUCCESS! Check your WhatsApp.")
            else:
                print("\n❌ FAILED! Check the error message above.")
                
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_whatsapp())