#!/usr/bin/env python3
"""Test WhatsApp notification on Render."""

import httpx
import asyncio
from datetime import datetime

async def test_notify():
    """Test the notify endpoint on Render."""
    base_url = "https://syb-offline-alarm.onrender.com"
    
    print("🔍 Testing WhatsApp Notification on Render")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First get zones to find an account
        print("\n1️⃣ Getting accounts...")
        try:
            response = await client.get(f"{base_url}/api/zones")
            
            if response.status_code != 200:
                print(f"❌ Failed to get zones: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return
            
            data = response.json()
            accounts = data.get('accounts', {})
            
            # Find BMAsia account
            bm_account = None
            for acc_id, acc_data in accounts.items():
                if 'BMAsia' in acc_data.get('name', ''):
                    bm_account = (acc_id, acc_data['name'])
                    break
            
            if not bm_account and accounts:
                # Use first account
                acc_id = list(accounts.keys())[0]
                bm_account = (acc_id, accounts[acc_id]['name'])
            
            if not bm_account:
                print("❌ No accounts found")
                return
            
            print(f"Using account: {bm_account[1]}")
            
            # Test WhatsApp
            print(f"\n2️⃣ Sending WhatsApp to +66856644142...")
            
            notify_data = {
                'account_id': bm_account[0],
                'whatsapp_numbers': ['+66856644142'],
                'whatsapp_message': f'Test from Render at {datetime.now().strftime("%H:%M:%S")} - Checking if correct phone ID is used'
            }
            
            response = await client.post(
                f"{base_url}/api/notify",
                json=notify_data
            )
            
            print(f"\nResponse Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Result: {result}")
                
                if result.get('whatsapp_sent'):
                    print(f"\n✅ WhatsApp message sent successfully!")
                else:
                    print(f"\n❌ WhatsApp not sent")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

asyncio.run(test_notify())