#!/usr/bin/env python3
"""Test database connection and tables."""

import asyncio
import os
from dotenv import load_dotenv
from database import get_database

load_dotenv()

async def test_db():
    """Test database connection and tables."""
    print("Testing database connection...")
    
    db = await get_database()
    if not db:
        print("❌ No database connection!")
        return
    
    print("✅ Database connected")
    
    # Test conversations table
    try:
        conversations = await db.get_conversations()
        print(f"\nConversations in database: {len(conversations)}")
        for conv in conversations:
            print(f"  - {conv.get('phone_number')} ({conv.get('profile_name')})")
    except Exception as e:
        print(f"❌ Error reading conversations: {e}")
    
    # Test creating a test conversation
    try:
        print("\nTesting conversation creation...")
        conv_id = await db.get_or_create_conversation(
            wa_id="66856644142",
            phone_number="66856644142",
            profile_name="Test User"
        )
        print(f"✅ Created/found conversation ID: {conv_id}")
        
        # Test saving a message
        success = await db.save_whatsapp_message(
            conversation_id=conv_id,
            wa_message_id="test_msg_123",
            direction="inbound",
            message_text="Test message from webhook test"
        )
        print(f"✅ Message saved: {success}")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")

asyncio.run(test_db())