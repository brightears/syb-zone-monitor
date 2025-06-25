#!/usr/bin/env python3
"""Test script to verify email contact functionality."""

import asyncio
import httpx
import json

async def test_email_contacts():
    """Test email contact add and display."""
    base_url = "http://127.0.0.1:8080"
    
    print("Testing Email Contact Management...")
    
    async with httpx.AsyncClient() as client:
        # First get zones to find an account
        try:
            response = await client.get(f"{base_url}/api/zones")
            if response.status_code != 200:
                print("❌ Dashboard not running. Start with: python enhanced_dashboard.py")
                return
            
            data = response.json()
            accounts = data.get('accounts', {})
            
            if not accounts:
                print("❌ No accounts found")
                return
            
            # Use first account
            account_id, account_info = list(accounts.items())[0]
            account_name = account_info['name']
            
            print(f"\n📍 Testing with account: {account_name}")
            print(f"   Account ID: {account_id}")
            
            # Add test email contact
            print("\n➕ Adding test email contact...")
            response = await client.post(f"{base_url}/api/email", json={
                'account_id': account_id,
                'account_name': account_name,
                'contact_name': 'Test Contact',
                'email': 'test@example.com',
                'role': 'Manager'
            })
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ Email contact added successfully")
                else:
                    print(f"❌ Failed to add contact: {result.get('message')}")
            else:
                print(f"❌ HTTP error {response.status_code}: {response.text}")
            
            # Retrieve email contacts
            print("\n📋 Retrieving email contacts...")
            response = await client.get(f"{base_url}/api/email/{account_id}")
            
            if response.status_code == 200:
                data = response.json()
                contacts = data.get('contacts', [])
                print(f"   Found {len(contacts)} contacts:")
                for contact in contacts:
                    print(f"   - {contact['contact_name']} ({contact['email']}) [{contact['source']}]")
            else:
                print(f"❌ Failed to retrieve contacts: {response.status_code}")
            
            print("\n✅ Test complete!")
            print("\n📌 Next steps:")
            print("1. Open the dashboard in your browser")
            print("2. Click 'Notify' for the test account")
            print("3. Check that email contacts appear in the Email section")
            print("4. Try adding more contacts via 'Manage Contacts'")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Email Contact UI Test")
    print("=" * 60)
    asyncio.run(test_email_contacts())