#!/usr/bin/env python3
"""Test webhook verification endpoint."""

import httpx
import asyncio

async def test_webhook():
    """Test the webhook verification endpoint."""
    url = "https://syb-zone-monitor.onrender.com/webhook/whatsapp"
    
    # Test parameters that Meta will send
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "syb-whatsapp-verify-2025",
        "hub.challenge": "test_challenge_123"
    }
    
    print("Testing webhook verification...")
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=30.0)
            print(f"\nStatus: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200 and response.text == "test_challenge_123":
                print("\n✅ Webhook verification is working correctly!")
            else:
                print("\n❌ Webhook verification failed")
                print("Expected: 200 status and 'test_challenge_123' response")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")

asyncio.run(test_webhook())