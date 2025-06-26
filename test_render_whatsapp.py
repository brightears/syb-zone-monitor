#!/usr/bin/env python3
"""Test WhatsApp on Render deployment."""

import httpx
import asyncio
from datetime import datetime

async def test_render():
    """Test WhatsApp via Render API."""
    # Your Render deployment URL
    base_url = "https://syb-offline-alarm.onrender.com"
    
    print("🔍 Testing WhatsApp on Render")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First, get accounts
        print("\n1️⃣ Getting accounts...")
        response = await client.get(f"{base_url}/zones")
        
        if response.status_code != 200:
            print(f"❌ Failed to get zones: {response.status_code}")
            return
        
        data = response.json()
        accounts = data.get('accounts', {})
        
        if not accounts:
            print("❌ No accounts found")
            return
        
        # Use BMAsia account
        bm_account = None
        for acc_id, acc_data in accounts.items():
            if 'BMAsia' in acc_data.get('name', ''):
                bm_account = (acc_id, acc_data['name'])
                break
        
        if not bm_account:
            # Use first account
            acc_id = list(accounts.keys())[0]
            bm_account = (acc_id, accounts[acc_id]['name'])
        
        print(f"Using account: {bm_account[1]}")
        
        # Send WhatsApp notification
        print(f"\n2️⃣ Sending WhatsApp notification to +66856644142...")
        
        notify_data = {
            'account_id': bm_account[0],
            'whatsapp_numbers': ['+66856644142'],
            'whatsapp_message': f'Test from Render at {datetime.now().strftime("%H:%M:%S")} - Please confirm receipt'
        }
        
        response = await client.post(
            f"{base_url}/notify",
            json=notify_data
        )
        
        print(f"\nResponse Status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            print("✅ API call successful!")
            print(f"Result: {result}")
            
            # Check WhatsApp specific result
            whatsapp_result = result.get('whatsapp', {})
            if whatsapp_result.get('success'):
                print(f"\n✅ WhatsApp message sent!")
                print(f"Message ID: {whatsapp_result.get('message_id', 'N/A')}")
            else:
                print(f"\n❌ WhatsApp failed: {whatsapp_result.get('error', 'Unknown error')}")
        else:
            print(f"❌ API error: {result}")

# Run the test
asyncio.run(test_render())