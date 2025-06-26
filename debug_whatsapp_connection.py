#!/usr/bin/env python3
"""Debug WhatsApp connection issues."""

import asyncio
import httpx
import os
from dotenv import load_dotenv
load_dotenv(override=True)

async def debug_connection():
    """Debug the WhatsApp connection."""
    print("🔍 WhatsApp Connection Debug")
    print("=" * 60)
    
    # Check configuration
    phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    
    print(f"Phone Number ID: {phone_id}")
    print(f"Access Token: {'Set' if token else 'Not set'}")
    
    if not token:
        print("❌ No access token!")
        return
    
    # Test 1: Get phone number details
    print("\n📱 Test 1: Getting phone number details...")
    url = f"https://graph.facebook.com/v17.0/{phone_id}"
    params = {"access_token": token}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200:
            print(f"\n✅ Phone number details:")
            print(f"   Display number: {data.get('display_phone_number', 'N/A')}")
            print(f"   Verified name: {data.get('verified_name', 'N/A')}")
            print(f"   Quality rating: {data.get('quality_rating', 'N/A')}")
            print(f"   Status: {data.get('account_mode', 'N/A')}")
        
        # Test 2: Check WhatsApp Business Account
        print("\n🏢 Test 2: Checking WhatsApp Business Account...")
        waba_id = data.get('wa_id')
        if waba_id:
            waba_url = f"https://graph.facebook.com/v17.0/{waba_id}"
            waba_response = await client.get(waba_url, params=params)
            print(f"WABA Status: {waba_response.status_code}")
            if waba_response.status_code == 200:
                waba_data = waba_response.json()
                print(f"Business Account: {waba_data.get('name', 'N/A')}")

asyncio.run(debug_connection())