#!/usr/bin/env python3
"""Test email notification through the dashboard API."""

import asyncio
import httpx
import json

async def test_notification():
    """Test sending notification through the API."""
    print("Testing Email Notification via Dashboard API...")
    
    # First, get the list of accounts
    async with httpx.AsyncClient() as client:
        # Get zones data to find an account
        response = await client.get("http://127.0.0.1:8080/api/zones")
        if response.status_code != 200:
            print("❌ Failed to get zones data. Is the dashboard running?")
            print("  Run: python enhanced_dashboard.py")
            return
        
        data = response.json()
        accounts = data.get('accounts', {})
        
        if not accounts:
            print("❌ No accounts found")
            return
        
        # Use the first account with issues for testing
        test_account = None
        for account_id, account_info in accounts.items():
            if account_info.get('hasIssues'):
                test_account = (account_id, account_info)
                break
        
        if not test_account:
            # Use first account if no issues found
            test_account = list(accounts.items())[0]
        
        account_id, account_info = test_account
        print(f"\n📍 Using account: {account_info['name']}")
        print(f"   Zones: {len(account_info['zones'])}")
        
        # Get email contacts for this account
        response = await client.get(f"http://127.0.0.1:8080/api/email/{account_id}")
        if response.status_code == 200:
            email_data = response.json()
            contacts = email_data.get('contacts', [])
            print(f"   Email contacts: {len(contacts)}")
            for contact in contacts[:3]:  # Show first 3
                print(f"     - {contact['contact_name']} ({contact['email']}) [{contact['source']}]")
        
        # Prepare test notification
        test_emails = []
        if contacts:
            # Use first contact for testing
            test_emails = [contacts[0]['email']]
        else:
            print("   No email contacts found - using test email")
            test_emails = ['test@example.com']
        
        # Send test notification
        print(f"\n📧 Sending test notification to: {test_emails}")
        
        notification_data = {
            'account_id': account_id,
            'emails': test_emails,
            'whatsapp_numbers': [],
            'email_message': (
                f"This is a test notification for {account_info['name']}.\n\n"
                "This message was sent to verify the email notification system "
                "is working correctly with both API and manual email contacts.\n\n"
                "If you receive this, the integration is successful!"
            )
        }
        
        response = await client.post(
            "http://127.0.0.1:8080/api/notify",
            json=notification_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Notification sent successfully!")
            print(f"   Emails sent: {result.get('email_sent', 0)}")
            print(f"   WhatsApp sent: {result.get('whatsapp_sent', 0)}")
        else:
            print(f"❌ Failed to send notification: {response.status_code}")
            print(f"   Response: {response.text}")

if __name__ == "__main__":
    print("=" * 60)
    print("Email Notification Integration Test")
    print("=" * 60)
    print("\nMake sure:")
    print("1. The dashboard is running (python enhanced_dashboard.py)")
    print("2. Email service is configured in .env file")
    print("3. You have some accounts with email contacts")
    print()
    
    asyncio.run(test_notification())