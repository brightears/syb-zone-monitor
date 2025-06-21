#!/usr/bin/env python3
"""Direct WhatsApp API test with automatic number."""

import os
import httpx
import asyncio
from dotenv import load_dotenv
import sys

load_dotenv()

async def test_whatsapp(phone_number):
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
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'messaging_product': 'whatsapp',
        'to': phone_number.strip(),
        'type': 'text',
        'text': {
            'body': '🧪 Test message from SYB Zone Monitor - WhatsApp integration is working!'
        }
    }
    
    print(f"\nSending test message to: {phone_number}")
    
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
    # Use the number from the screenshot
    phone_number = "+66856644142"
    if len(sys.argv) > 1:
        phone_number = sys.argv[1]
    
    asyncio.run(test_whatsapp(phone_number))