#!/usr/bin/env python3
"""Add WhatsApp contacts table to the database."""

import asyncio
import os
import asyncpg
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

async def add_whatsapp_contacts_table():
    """Add table for storing WhatsApp contacts."""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set in .env file")
        return
    
    # Parse DATABASE_URL for asyncpg
    parsed = urlparse(database_url)
    
    try:
        # Create connection
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:]  # Remove leading '/'
        )
        
        # Create WhatsApp contacts table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_contacts (
                id SERIAL PRIMARY KEY,
                account_id VARCHAR(255) NOT NULL,
                account_name VARCHAR(255) NOT NULL,
                contact_name VARCHAR(255),
                whatsapp_number VARCHAR(50) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(account_id, whatsapp_number)
            )
        """)
        
        # Create index for faster lookups
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_whatsapp_contacts_account_id 
            ON whatsapp_contacts(account_id)
        """)
        
        print("✅ WhatsApp contacts table created successfully!")
        
        # Close connection
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")

if __name__ == "__main__":
    asyncio.run(add_whatsapp_contacts_table())