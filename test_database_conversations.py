#!/usr/bin/env python3
"""Test script to check WhatsApp conversations in the database."""

import asyncio
import os
import sys
from datetime import datetime
import json
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_database

async def check_conversations():
    """Check all WhatsApp conversations in the database."""
    print("🔍 Checking WhatsApp conversations in database...\n")
    
    # Load environment variables
    load_dotenv()
    
    # Get database connection
    db = await get_database()
    if not db:
        print("❌ Error: Could not connect to database")
        print("Make sure DATABASE_URL is set in your environment")
        return
    
    try:
        # Get all conversations
        conversations = await db.get_conversations(limit=100)
        
        if not conversations:
            print("📭 No conversations found in database")
            print("\nThis could mean:")
            print("  - No WhatsApp messages have been received yet")
            print("  - The webhook is not properly receiving messages")
            print("  - Messages are not being saved to the database")
        else:
            print(f"📬 Found {len(conversations)} conversation(s):\n")
            
            for conv in conversations:
                print(f"Conversation ID: {conv['id']}")
                print(f"  WhatsApp ID: {conv['wa_id']}")
                print(f"  Phone Number: {conv['phone_number']}")
                print(f"  Profile Name: {conv['profile_name'] or 'Unknown'}")
                print(f"  Status: {conv['status']}")
                print(f"  Created: {conv['created_at']}")
                print(f"  Last Message: {conv['last_message_at']}")
                print(f"  Unread Count: {conv['unread_count']}")
                print(f"  Total Messages: {conv['message_count']}")
                
                # Get messages for this conversation
                messages = await db.get_conversation_messages(conv['id'])
                if messages:
                    print(f"\n  Messages ({len(messages)}):")
                    for msg in messages[:5]:  # Show first 5 messages
                        direction = "📥" if msg['direction'] == 'inbound' else "📤"
                        print(f"    {direction} {msg['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"       Type: {msg['message_type']}")
                        if msg['message_text']:
                            print(f"       Text: {msg['message_text'][:100]}...")
                        print(f"       Status: {msg['status'] or 'N/A'}")
                    
                    if len(messages) > 5:
                        print(f"    ... and {len(messages) - 5} more messages")
                
                print("\n" + "-" * 50 + "\n")
        
        # Check database tables
        print("\n📊 Database Statistics:")
        async with db.pool.acquire() as conn:
            # Count conversations
            conv_count = await conn.fetchval("SELECT COUNT(*) FROM whatsapp_conversations")
            print(f"  Total Conversations: {conv_count}")
            
            # Count messages
            msg_count = await conn.fetchval("SELECT COUNT(*) FROM whatsapp_messages")
            print(f"  Total Messages: {msg_count}")
            
            # Count by direction
            inbound_count = await conn.fetchval(
                "SELECT COUNT(*) FROM whatsapp_messages WHERE direction = 'inbound'"
            )
            outbound_count = await conn.fetchval(
                "SELECT COUNT(*) FROM whatsapp_messages WHERE direction = 'outbound'"
            )
            print(f"  Inbound Messages: {inbound_count}")
            print(f"  Outbound Messages: {outbound_count}")
            
            # Recent messages
            recent = await conn.fetch("""
                SELECT created_at, direction, message_type 
                FROM whatsapp_messages 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            if recent:
                print("\n  Recent Message Activity:")
                for row in recent:
                    direction = "📥" if row['direction'] == 'inbound' else "📤"
                    print(f"    {direction} {row['created_at'].strftime('%Y-%m-%d %H:%M:%S')} - {row['message_type']}")
    
    except Exception as e:
        print(f"\n❌ Error checking conversations: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db.close()
        print("\n✅ Database check complete")

if __name__ == "__main__":
    asyncio.run(check_conversations())