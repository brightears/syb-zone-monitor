#!/usr/bin/env python3
"""Test script to simulate WhatsApp webhook messages."""

import requests
import json
import time
from datetime import datetime
import sys
import argparse

def send_test_message(webhook_url, phone_number="+60123456789", message_text="Hello, I need help with my zones"):
    """Send a test WhatsApp message to the webhook."""
    
    # Create a realistic WhatsApp webhook payload
    # This matches the format that Meta sends
    webhook_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789012345",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "60123456789",
                                "phone_number_id": "123456789012345"
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Test User"
                                    },
                                    "wa_id": phone_number.replace("+", "")
                                }
                            ],
                            "messages": [
                                {
                                    "from": phone_number.replace("+", ""),
                                    "id": f"wamid.{int(time.time())}",
                                    "timestamp": str(int(time.time())),
                                    "text": {
                                        "body": message_text
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    print(f"📤 Sending test webhook to: {webhook_url}")
    print(f"📱 From phone number: {phone_number}")
    print(f"💬 Message: {message_text}")
    print("\nPayload:")
    print(json.dumps(webhook_payload, indent=2))
    
    try:
        # Send the webhook
        response = requests.post(
            webhook_url,
            json=webhook_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n✅ Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\n🎉 Webhook delivered successfully!")
            print("Check your database to see if the message was saved.")
        else:
            print(f"\n❌ Webhook failed with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Could not reach the webhook URL")
        print("Make sure your server is running and accessible")
    except Exception as e:
        print(f"\n❌ Error sending webhook: {e}")

def send_status_update(webhook_url, message_id="wamid.123456789", status="delivered"):
    """Send a message status update webhook."""
    
    webhook_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789012345",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "60123456789",
                                "phone_number_id": "123456789012345"
                            },
                            "statuses": [
                                {
                                    "id": message_id,
                                    "status": status,
                                    "timestamp": str(int(time.time())),
                                    "recipient_id": "60123456789"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    print(f"\n📊 Sending status update: {status}")
    print(f"Message ID: {message_id}")
    
    try:
        response = requests.post(
            webhook_url,
            json=webhook_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"✅ Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
    except Exception as e:
        print(f"❌ Error sending status update: {e}")

def main():
    parser = argparse.ArgumentParser(description="Simulate WhatsApp webhook messages")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/webhook/whatsapp",
        help="Webhook URL (default: http://localhost:8000/webhook/whatsapp)"
    )
    parser.add_argument(
        "--phone",
        default="+60123456789",
        help="Phone number to simulate (default: +60123456789)"
    )
    parser.add_argument(
        "--message",
        default="Hello, I need help with my zones",
        help="Message text to send"
    )
    parser.add_argument(
        "--type",
        choices=["message", "status", "both"],
        default="message",
        help="Type of webhook to send"
    )
    
    args = parser.parse_args()
    
    print("🚀 WhatsApp Webhook Simulator")
    print("=" * 50)
    
    if args.type in ["message", "both"]:
        send_test_message(args.url, args.phone, args.message)
    
    if args.type in ["status", "both"]:
        # Wait a bit before sending status
        if args.type == "both":
            time.sleep(2)
        send_status_update(args.url)
    
    print("\n✅ Simulation complete!")
    print("\nNext steps:")
    print("1. Run test_database_conversations.py to check if messages were saved")
    print("2. Check the server logs for webhook processing details")
    print("3. Visit the dashboard UI to see if conversations appear")

if __name__ == "__main__":
    main()