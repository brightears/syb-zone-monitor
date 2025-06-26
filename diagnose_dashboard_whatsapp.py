#!/usr/bin/env python3
"""Diagnose why dashboard WhatsApp isn't working."""

import asyncio
import httpx
import os
from datetime import datetime

print("🔍 Dashboard WhatsApp Diagnosis")
print("=" * 60)

# Test 1: Check environment variables
print("\n1️⃣ Environment Variables:")
from dotenv import load_dotenv
load_dotenv()

phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
token = os.getenv('WHATSAPP_ACCESS_TOKEN')
enabled = os.getenv('WHATSAPP_ENABLED')

print(f"WHATSAPP_ENABLED: {enabled}")
print(f"WHATSAPP_PHONE_NUMBER_ID: {phone_id}")
print(f"Token exists: {'Yes' if token else 'No'}")
print(f"Token preview: {token[:20]}...{token[-20:] if token else 'NOT SET'}")

# Test 2: Test via dashboard endpoint
print("\n2️⃣ Testing via Dashboard API:")

async def test_dashboard():
    # First, get an account
    async with httpx.AsyncClient() as client:
        response = await client.get("http://127.0.0.1:8080/api/zones")
        if response.status_code != 200:
            print("❌ Dashboard not running!")
            return
        
        data = response.json()
        accounts = data.get('accounts', {})
        if not accounts:
            print("❌ No accounts found")
            return
        
        # Get first account
        account_id = list(accounts.keys())[0]
        account_name = accounts[account_id]['name']
        print(f"Using account: {account_name}")
        
        # Send notification
        print("\n3️⃣ Sending notification via dashboard...")
        notify_data = {
            'account_id': account_id,
            'whatsapp_numbers': ['+66856644142'],
            'whatsapp_message': f'Dashboard test at {datetime.now().strftime("%H:%M:%S")}'
        }
        
        response = await client.post(
            "http://127.0.0.1:8080/api/notify",
            json=notify_data
        )
        
        print(f"Response: {response.status_code}")
        result = response.json()
        print(f"Result: {result}")

# Test 3: Check WhatsApp service initialization
print("\n4️⃣ Testing WhatsApp Service directly:")
from whatsapp_service import WhatsAppService

service = WhatsAppService()
print(f"Service enabled: {service.enabled}")
print(f"Phone ID in service: {service.phone_number_id}")
print(f"Token in service: {service.access_token[:20]}...{service.access_token[-20:] if service.access_token else 'NOT SET'}")

# Run dashboard test
asyncio.run(test_dashboard())