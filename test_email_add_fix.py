#!/usr/bin/env python3
"""Test the email contact add functionality after fix."""

import asyncio
import httpx

async def test_add_email():
    """Test adding an email contact."""
    print("Testing Email Contact Add Fix...")
    
    async with httpx.AsyncClient() as client:
        # First, get zones to find an account
        response = await client.get("http://127.0.0.1:8080/api/zones")
        if response.status_code != 200:
            print("❌ Dashboard not running")
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
        
        # Test data
        test_contact = {
            'account_id': account_id,
            'account_name': account_name,
            'contact_name': 'Norbert',
            'email': 'platzer.norbert@gmail.com',
            'role': 'Admin'
        }
        
        print(f"\n➕ Adding email contact: {test_contact['contact_name']} ({test_contact['email']})")
        
        # Add the contact
        response = await client.post(
            "http://127.0.0.1:8080/api/email",
            json=test_contact
        )
        
        print(f"   Response status: {response.status_code}")
        print(f"   Response body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Contact added successfully!")
                
                # Verify by retrieving contacts
                response = await client.get(f"http://127.0.0.1:8080/api/email/{account_id}")
                if response.status_code == 200:
                    data = response.json()
                    contacts = data.get('contacts', [])
                    print(f"\n📋 Current contacts ({len(contacts)}):")
                    for contact in contacts:
                        print(f"   - {contact['contact_name']} ({contact['email']}) [{contact['source']}]")
            else:
                print(f"❌ Failed: {result.get('message')}")
        else:
            print(f"❌ HTTP error: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_add_email())