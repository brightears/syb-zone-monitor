"""Database integration for persistent zone status storage."""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, List
import asyncpg
import json
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ZoneDatabase:
    """Handle database operations for zone status persistence."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self):
        """Initialize database connection and create tables if needed."""
        try:
            # Parse DATABASE_URL for asyncpg
            parsed = urlparse(self.database_url)
            
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:],  # Remove leading '/'
                min_size=1,
                max_size=10
            )
            
            # Create tables if they don't exist
            await self._create_tables()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _create_tables(self):
        """Create necessary tables if they don't exist."""
        async with self.pool.acquire() as conn:
            # Zone status table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS zone_status (
                    zone_id VARCHAR(255) PRIMARY KEY,
                    zone_name VARCHAR(255),
                    account_name VARCHAR(255),
                    status VARCHAR(50),
                    last_checked TIMESTAMP DEFAULT NOW(),
                    offline_since TIMESTAMP,
                    details JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create indexes for performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_zone_status_account 
                ON zone_status(account_name)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_zone_status_status 
                ON zone_status(status)
            """)
            
            # Historical data table (for tracking status changes)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS zone_history (
                    id SERIAL PRIMARY KEY,
                    zone_id VARCHAR(255),
                    zone_name VARCHAR(255),
                    old_status VARCHAR(50),
                    new_status VARCHAR(50),
                    changed_at TIMESTAMP DEFAULT NOW(),
                    offline_duration_seconds INTEGER
                )
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_zone_history_zone_id 
                ON zone_history(zone_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_zone_history_changed_at 
                ON zone_history(changed_at)
            """)
    
    async def save_zone_status(self, zone_id: str, zone_name: str, status: str, 
                              details: Dict, offline_since: Optional[datetime] = None,
                              account_name: Optional[str] = None):
        """Save or update zone status in database."""
        if not self.pool:
            return
            
        try:
            async with self.pool.acquire() as conn:
                # Check if zone exists and get previous status
                row = await conn.fetchrow(
                    "SELECT status, offline_since FROM zone_status WHERE zone_id = $1",
                    zone_id
                )
                
                previous_status = row['status'] if row else None
                previous_offline_since = row['offline_since'] if row else None
                
                # Upsert zone status
                await conn.execute("""
                    INSERT INTO zone_status 
                    (zone_id, zone_name, account_name, status, offline_since, details, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, NOW())
                    ON CONFLICT (zone_id) 
                    DO UPDATE SET
                        zone_name = EXCLUDED.zone_name,
                        account_name = EXCLUDED.account_name,
                        status = EXCLUDED.status,
                        offline_since = EXCLUDED.offline_since,
                        details = EXCLUDED.details,
                        last_checked = NOW(),
                        updated_at = NOW()
                """, zone_id, zone_name, account_name, status, offline_since, 
                    json.dumps(details) if details else None)
                
                # Log status change to history if status changed
                if previous_status and previous_status != status:
                    offline_duration = None
                    if previous_status == 'offline' and previous_offline_since:
                        offline_duration = int((datetime.now() - previous_offline_since).total_seconds())
                    
                    await conn.execute("""
                        INSERT INTO zone_history 
                        (zone_id, zone_name, old_status, new_status, offline_duration_seconds)
                        VALUES ($1, $2, $3, $4, $5)
                    """, zone_id, zone_name, previous_status, status, offline_duration)
                    
        except Exception as e:
            logger.error(f"Error saving zone status for {zone_id}: {e}")
    
    async def load_all_zone_states(self) -> Dict[str, Dict]:
        """Load all zone states from database."""
        if not self.pool:
            return {}
            
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT zone_id, zone_name, account_name, status, 
                           offline_since, details, last_checked
                    FROM zone_status
                    ORDER BY zone_name
                """)
                
                states = {}
                for row in rows:
                    states[row['zone_id']] = {
                        'zone_name': row['zone_name'],
                        'account_name': row['account_name'],
                        'status': row['status'],
                        'offline_since': row['offline_since'],
                        'details': json.loads(row['details']) if row['details'] else {},
                        'last_checked': row['last_checked']
                    }
                
                logger.info(f"Loaded {len(states)} zone states from database")
                return states
                
        except Exception as e:
            logger.error(f"Error loading zone states: {e}")
            return {}
    
    async def get_zone_history(self, zone_id: str, days: int = 7) -> List[Dict]:
        """Get status change history for a zone."""
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT zone_name, old_status, new_status, changed_at, 
                           offline_duration_seconds
                    FROM zone_history
                    WHERE zone_id = $1 
                    AND changed_at > NOW() - INTERVAL '%s days'
                    ORDER BY changed_at DESC
                """, zone_id, days)
                
                history = []
                for row in rows:
                    history.append({
                        'zone_name': row['zone_name'],
                        'old_status': row['old_status'],
                        'new_status': row['new_status'],
                        'changed_at': row['changed_at'].isoformat(),
                        'offline_duration_seconds': row['offline_duration_seconds']
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Error getting zone history: {e}")
            return []
    
    async def get_account_summary(self) -> Dict[str, Dict]:
        """Get summary of zones by account."""
        if not self.pool:
            return {}
            
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        account_name,
                        COUNT(*) as total_zones,
                        SUM(CASE WHEN status = 'online' THEN 1 ELSE 0 END) as online_zones,
                        SUM(CASE WHEN status = 'offline' THEN 1 ELSE 0 END) as offline_zones,
                        SUM(CASE WHEN status = 'expired' THEN 1 ELSE 0 END) as expired_zones,
                        SUM(CASE WHEN status = 'unpaired' THEN 1 ELSE 0 END) as unpaired_zones,
                        SUM(CASE WHEN status = 'no_subscription' THEN 1 ELSE 0 END) as no_subscription_zones,
                        SUM(CASE WHEN status = 'checking' THEN 1 ELSE 0 END) as checking_zones
                    FROM zone_status
                    GROUP BY account_name
                    ORDER BY account_name
                """)
                
                summary = {}
                for row in rows:
                    account = row['account_name'] or 'Unknown'
                    summary[account] = {
                        'total_zones': row['total_zones'],
                        'online_zones': row['online_zones'],
                        'offline_zones': row['offline_zones'],
                        'expired_zones': row['expired_zones'],
                        'unpaired_zones': row['unpaired_zones'],
                        'no_subscription_zones': row['no_subscription_zones'],
                        'checking_zones': row['checking_zones']
                    }
                
                return summary
                
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return {}
    
    async def cleanup_old_history(self, days_to_keep: int = 30):
        """Clean up old history records."""
        if not self.pool:
            return
            
        try:
            async with self.pool.acquire() as conn:
                deleted = await conn.fetchval("""
                    DELETE FROM zone_history
                    WHERE changed_at < NOW() - INTERVAL '%s days'
                    RETURNING COUNT(*)
                """, days_to_keep)
                
                if deleted:
                    logger.info(f"Cleaned up {deleted} old history records")
                    
        except Exception as e:
            logger.error(f"Error cleaning up history: {e}")
    
    async def close(self):
        """Close database connections."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection closed")


# Helper function to get database instance
_db_instance: Optional[ZoneDatabase] = None

async def get_database() -> Optional[ZoneDatabase]:
    """Get or create database instance."""
    global _db_instance
    
    if _db_instance:
        return _db_instance
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.warning("DATABASE_URL not set, running without database")
        return None
    
    _db_instance = ZoneDatabase(database_url)
    await _db_instance.initialize()
    return _db_instance