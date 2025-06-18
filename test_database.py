#!/usr/bin/env python3
"""Test database connection and functionality."""

import asyncio
import os
from dotenv import load_dotenv
from database import ZoneDatabase

load_dotenv()

async def test_database():
    """Test database operations."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not set!")
        return
    
    print(f"Testing database connection...")
    print(f"URL: {db_url[:30]}...")
    
    try:
        db = ZoneDatabase(db_url)
        await db.initialize()
        print("✓ Database connected successfully!")
        
        # Test saving a zone
        await db.save_zone_status(
            zone_id="test_zone_1",
            zone_name="Test Zone 1",
            status="online",
            details={"test": True},
            account_name="Test Account"
        )
        print("✓ Saved test zone status")
        
        # Test loading zones
        states = await db.load_all_zone_states()
        print(f"✓ Loaded {len(states)} zone states")
        
        # Test account summary
        summary = await db.get_account_summary()
        print(f"✓ Got summary for {len(summary)} accounts")
        
        await db.close()
        print("✓ All database tests passed!")
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database())