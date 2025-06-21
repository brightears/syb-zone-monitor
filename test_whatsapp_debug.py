#!/usr/bin/env python3
"""Debug WhatsApp configuration and permissions."""

import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def debug_whatsapp():
    """Debug WhatsApp configuration."""
    
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    
    if not access_token:
        print("ERROR: No WHATSAPP_ACCESS_TOKEN found")
        return
    
    print("=== WhatsApp Configuration Debug ===\n")
    
    # Test 1: Check token permissions
    print("1. Checking access token permissions...")
    url = f"https://graph.facebook.com/v17.0/debug_token?input_token={access_token}&access_token={access_token}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            data = response.json()
            
            if 'data' in data:
                token_data = data['data']
                print(f"   App ID: {token_data.get('app_id')}")
                print(f"   Type: {token_data.get('type')}")
                print(f"   Valid: {token_data.get('is_valid')}")
                print(f"   Expires: {token_data.get('expires_at', 'Never')}")
                print(f"   Scopes: {token_data.get('scopes', [])}")
            else:
                print(f"   Error: {data}")
                
    except Exception as e:
        print(f"   Failed: {e}")
    
    # Test 2: Check WhatsApp Business Account
    print("\n2. Checking WhatsApp Business Account...")
    waba_id = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID', 'not_set')
    print(f"   WABA ID: {waba_id}")
    
    # Test 3: List phone numbers
    print("\n3. Checking phone numbers...")
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    print(f"   Phone Number ID: {phone_number_id}")
    
    if phone_number_id:
        url = f"https://graph.facebook.com/v17.0/{phone_number_id}?access_token={access_token}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                data = response.json()
                
                if 'error' not in data:
                    print(f"   Display Number: {data.get('display_phone_number')}")
                    print(f"   Verified Name: {data.get('verified_name')}")
                    print(f"   Quality Rating: {data.get('quality_rating')}")
                else:
                    print(f"   Error: {data['error']['message']}")
                    
        except Exception as e:
            print(f"   Failed: {e}")
    
    print("\n=== Troubleshooting Steps ===")
    print("1. Go to https://developers.facebook.com")
    print("2. Select your app")
    print("3. Go to WhatsApp > API Setup")
    print("4. In the 'To' section, add your phone number as a test recipient")
    print("5. Verify with the code sent to your WhatsApp")
    print("\nAlternatively, if your app is in Development mode:")
    print("- You can only send to verified test numbers")
    print("- Consider applying for Business Verification to send to any number")

if __name__ == "__main__":
    asyncio.run(debug_whatsapp())