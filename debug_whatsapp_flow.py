#!/usr/bin/env python3
"""Debug script to test the complete WhatsApp flow."""

import asyncio
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_database
from whatsapp_service import WhatsAppService

async def test_whatsapp_flow():
    """Test the complete WhatsApp flow: webhook -> database -> UI."""
    print("🔍 WhatsApp Flow Debugger")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    print("\n1️⃣ Checking Environment Variables:")
    whatsapp_token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")
    webhook_token = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")
    
    print(f"  WHATSAPP_TOKEN: {'✅ Set' if whatsapp_token else '❌ Not set'}")
    print(f"  WHATSAPP_PHONE_ID: {'✅ Set' if phone_id else '❌ Not set'} ({phone_id if phone_id else 'N/A'})")
    print(f"  WHATSAPP_WEBHOOK_VERIFY_TOKEN: {'✅ Set' if webhook_token else '❌ Not set'}")
    
    # Check database connection
    print("\n2️⃣ Checking Database Connection:")
    db = await get_database()
    if not db:
        print("  ❌ Could not connect to database")
        return
    else:
        print("  ✅ Database connected successfully")
    
    try:
        # Check WhatsApp service
        print("\n3️⃣ Checking WhatsApp Service:")
        wa_service = WhatsAppService()
        
        # Test sending a message (if credentials are available)
        if whatsapp_token and phone_id:
            print("  Testing WhatsApp API connection...")
            # This is just to test the connection, not actually send
            print("  ✅ WhatsApp service initialized")
        else:
            print("  ⚠️  WhatsApp credentials not fully configured")
        
        # Check database tables
        print("\n4️⃣ Checking Database Tables:")
        async with db.pool.acquire() as conn:
            # Check if tables exist
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('whatsapp_conversations', 'whatsapp_messages')
            """)
            
            table_names = [t['table_name'] for t in tables]
            
            if 'whatsapp_conversations' in table_names:
                print("  ✅ whatsapp_conversations table exists")
            else:
                print("  ❌ whatsapp_conversations table missing")
                
            if 'whatsapp_messages' in table_names:
                print("  ✅ whatsapp_messages table exists")
            else:
                print("  ❌ whatsapp_messages table missing")
        
        # Test creating a conversation
        print("\n5️⃣ Testing Database Operations:")
        test_wa_id = "60123456789"
        test_phone = "+60123456789"
        
        print(f"  Creating test conversation for {test_phone}...")
        conv_id = await db.get_or_create_conversation(
            wa_id=test_wa_id,
            phone_number=test_phone,
            profile_name="Test User"
        )
        
        if conv_id:
            print(f"  ✅ Created/retrieved conversation ID: {conv_id}")
            
            # Save a test message
            print("  Saving test message...")
            success = await db.save_whatsapp_message(
                conversation_id=conv_id,
                wa_message_id=f"test_{int(datetime.now().timestamp())}",
                direction="inbound",
                message_text="Test message from debug script",
                message_type="text",
                status="received"
            )
            
            if success:
                print("  ✅ Test message saved successfully")
            else:
                print("  ❌ Failed to save test message")
        else:
            print("  ❌ Failed to create conversation")
        
        # Check webhook endpoint
        print("\n6️⃣ Webhook Information:")
        print("  Local webhook URL: http://localhost:8000/webhook/whatsapp")
        print("  Production webhook URL: https://your-domain.com/webhook/whatsapp")
        print("\n  To configure in Meta/WhatsApp:")
        print("  1. Go to Meta Business Manager")
        print("  2. Navigate to WhatsApp > Configuration > Webhooks")
        print("  3. Set callback URL to your production URL")
        print(f"  4. Set verify token to: {webhook_token or 'your-verify-token-here'}")
        print("  5. Subscribe to 'messages' webhook field")
        
        # Summary
        print("\n7️⃣ Troubleshooting Summary:")
        print("\nIf messages aren't showing in the UI:")
        print("  1. Verify webhook is receiving messages (check server logs)")
        print("  2. Ensure webhook URL is correctly configured in Meta")
        print("  3. Check that webhook verification token matches")
        print("  4. Confirm database tables exist and are accessible")
        print("  5. Verify conversations and messages are being saved")
        print("  6. Check browser console for any JavaScript errors")
        print("  7. Ensure the dashboard is polling for updates")
        
        print("\n📝 Recommended next steps:")
        print("  1. Run: python test_webhook_simulator.py")
        print("  2. Check server logs for webhook activity")
        print("  3. Run: python test_database_conversations.py")
        print("  4. Open dashboard and check WhatsApp tab")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db.close()
        print("\n✅ Debug complete")

if __name__ == "__main__":
    asyncio.run(test_whatsapp_flow())