#!/usr/bin/env python3
"""Test Facebook API directly with minimal configuration."""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
PHONE_NUMBER_ID = "704214529438627"
ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
TO_NUMBER = "66856644142"  # Without the +

print("=== Testing WhatsApp Business API ===\n")
print(f"Phone Number ID: {PHONE_NUMBER_ID}")
print(f"To Number: {TO_NUMBER}")
print(f"Access Token: ...{ACCESS_TOKEN[-20:] if ACCESS_TOKEN else 'NOT SET'}\n")

# Method 1: Try with template message (hello_world)
print("1. Testing with hello_world template...")
url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}
data = {
    "messaging_product": "whatsapp",
    "to": TO_NUMBER,
    "type": "template",
    "template": {
        "name": "hello_world",
        "language": {
            "code": "en_US"
        }
    }
}

response = requests.post(url, headers=headers, json=data)
print(f"Response: {response.status_code}")
print(f"Body: {response.text}\n")

# Method 2: Try checking if the number is registered
print("2. Checking if recipient number is registered on WhatsApp...")
check_url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/phone_numbers"
check_response = requests.get(check_url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}"})
print(f"Response: {check_response.status_code}")
print(f"Body: {check_response.text}\n")

# Method 3: Get app info
print("3. Getting app information...")
app_url = "https://graph.facebook.com/v17.0/me"
app_response = requests.get(app_url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}"})
print(f"Response: {app_response.status_code}")
print(f"Body: {app_response.text}\n")

print("=== Troubleshooting ===")
if response.status_code == 400:
    error_data = response.json()
    if "error" in error_data:
        error_code = error_data["error"].get("code")
        if error_code == 10:
            print("❌ Permission Error (Code 10)")
            print("   Possible causes:")
            print("   1. Phone number not added as test recipient")
            print("   2. Wrong access token type") 
            print("   3. App not properly configured")
            print("\n   Try this:")
            print("   1. Go to WhatsApp > API Setup in your app")
            print("   2. In 'To' section, remove and re-add +66856644142")
            print("   3. Make sure to complete the verification")
elif response.status_code == 200:
    print("✅ Success! Message sent.")
    print("   Check your WhatsApp!")