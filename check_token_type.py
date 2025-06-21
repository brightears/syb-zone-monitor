#!/usr/bin/env python3
"""Check WhatsApp token type and configuration."""

import os
from dotenv import load_dotenv

load_dotenv()

print("=== WhatsApp Token Check ===\n")

access_token = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')

print(f"Token length: {len(access_token)} characters")
print(f"Token prefix: {access_token[:10]}...")
print(f"Token suffix: ...{access_token[-10:]}")
print(f"Phone Number ID: {phone_id}")

print("\n=== Token Types ===")
print("There are different token types for WhatsApp Business API:\n")
print("1. Temporary Access Token (from Graph API Explorer)")
print("   - Valid for 1 hour")
print("   - Good for testing")
print("   - Starts with random characters")
print("\n2. System User Access Token")
print("   - Long-lived token")
print("   - For production use")
print("   - Requires Business Manager setup")
print("\n3. Page Access Token")
print("   - Not used for WhatsApp Cloud API")

print("\n=== Possible Issues ===")
print("1. Using wrong token type")
print("2. Token expired")
print("3. Phone number not properly verified")
print("4. App still in Development mode")
print("5. Missing WhatsApp Business verification")

print("\n=== Quick Fix ===")
print("1. Go to https://developers.facebook.com/tools/explorer/")
print("2. Select your app")
print("3. Add permissions: whatsapp_business_messaging, whatsapp_business_management")
print("4. Click 'Generate Access Token'")
print("5. Copy the new token and update your .env file")