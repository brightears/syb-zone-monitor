#!/usr/bin/env python3
"""Check environment variables on Render."""

import httpx
import asyncio

async def check_render_env():
    """Check what environment Render is using."""
    base_url = "https://syb-offline-alarm.onrender.com"
    
    print("🔍 Checking Render Environment")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try the health endpoint
        print("\n1️⃣ Checking service health...")
        response = await client.get(f"{base_url}/")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Service is running")
            
            # Now try to send a WhatsApp message with direct API
            print("\n2️⃣ Testing WhatsApp directly...")
            
            # Get some account data first
            zones_response = await client.get(f"{base_url}/api/zones")
            if zones_response.status_code == 200:
                data = zones_response.json()
                accounts = data.get('accounts', {})
                if accounts:
                    account_id = list(accounts.keys())[0]
                    account_name = accounts[account_id]['name']
                    print(f"Using account: {account_name}")
                    
                    # Send notification
                    notify_data = {
                        'account_id': account_id,
                        'whatsapp_numbers': ['+66856644142'],
                        'whatsapp_message': 'Test from Render - checking environment'
                    }
                    
                    notify_response = await client.post(
                        f"{base_url}/api/notify",
                        json=notify_data
                    )
                    
                    print(f"\nNotify response: {notify_response.status_code}")
                    if notify_response.status_code == 200:
                        result = notify_response.json()
                        print(f"Result: {result}")
                    else:
                        print(f"Error: {notify_response.text}")

asyncio.run(check_render_env())