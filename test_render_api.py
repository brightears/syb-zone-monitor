#!/usr/bin/env python3
"""Test Render API endpoints."""

import httpx
import asyncio

async def test_api():
    """Test various API endpoints."""
    base_url = "https://syb-offline-alarm.onrender.com"
    
    endpoints = [
        "/",
        "/health",
        "/api/zones",
        "/api/status",
        "/api/whatsapp/debug",
        "/zones",
        "/notify"
    ]
    
    print("🔍 Testing Render API Endpoints")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                response = await client.get(url)
                print(f"\n{endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    if endpoint == "/api/whatsapp/debug":
                        print(f"WhatsApp Debug: {response.json()}")
                    elif response.status_code < 400:
                        print(f"Response preview: {response.text[:100]}...")
                        
            except Exception as e:
                print(f"{endpoint}: ERROR - {e}")

asyncio.run(test_api())