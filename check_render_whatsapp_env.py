#!/usr/bin/env python3
"""Check WhatsApp environment on Render."""

import httpx
import asyncio

async def check_render():
    """Check WhatsApp configuration on Render."""
    base_url = "https://syb-offline-alarm.onrender.com"
    
    print("🔍 Checking WhatsApp Configuration on Render")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check the debug endpoint
        print("\n📋 WhatsApp Debug Info:")
        try:
            response = await client.get(f"{base_url}/api/whatsapp/debug")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Service Available: {data.get('service_available')}")
                print(f"Environment Phone ID: {data.get('env_phone_id')}")
                print(f"Environment Enabled: {data.get('env_enabled')}")
                print(f"Token Exists: {data.get('token_exists')}")
                
                if data.get('service_available'):
                    print(f"\nService Details:")
                    print(f"Service Enabled: {data.get('service_enabled')}")
                    print(f"Service Phone ID: {data.get('service_phone_id')}")
                    print(f"Token Preview: {data.get('token_preview')}")
                    
                    # Check if using correct phone ID
                    correct_phone_id = "742462142273418"
                    if data.get('service_phone_id') == correct_phone_id:
                        print(f"\n✅ Using CORRECT Phone Number ID!")
                    else:
                        print(f"\n❌ Using WRONG Phone Number ID!")
                        print(f"   Expected: {correct_phone_id}")
                        print(f"   Got: {data.get('service_phone_id')}")
            else:
                print(f"❌ Debug endpoint not available yet (status: {response.status_code})")
                print("   Render may still be deploying...")
        except Exception as e:
            print(f"❌ Error checking debug endpoint: {e}")

asyncio.run(check_render())