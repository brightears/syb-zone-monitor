"""Database integration using databases library for better compatibility."""

import os
import logging
from datetime import datetime
from typing import Dict, Optional, List
import json
import databases
import sqlalchemy

logger = logging.getLogger(__name__)


class ZoneDatabase:
    """Handle database operations for zone status persistence."""
    
    def __init__(self, database_url: str):
        # Convert postgres:// to postgresql:// for compatibility
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        self.database_url = database_url
        self.database = databases.Database(database_url)
        
        # Create SQLAlchemy metadata
        metadata = sqlalchemy.MetaData()
        
        # Define tables
        self.zone_status = sqlalchemy.Table(
            "zone_status",
            metadata,
            sqlalchemy.Column("zone_id", sqlalchemy.String(255), primary_key=True),
            sqlalchemy.Column("zone_name", sqlalchemy.String(255)),
            sqlalchemy.Column("account_name", sqlalchemy.String(255)),
            sqlalchemy.Column("status", sqlalchemy.String(50)),
            sqlalchemy.Column("last_checked", sqlalchemy.DateTime, default=datetime.now),
            sqlalchemy.Column("offline_since", sqlalchemy.DateTime, nullable=True),
            sqlalchemy.Column("details", sqlalchemy.JSON, nullable=True),
            sqlalchemy.Column("created_at", sqlalchemy.DateTime, default=datetime.now),
            sqlalchemy.Column("updated_at", sqlalchemy.DateTime, default=datetime.now)
        )
        
        self.zone_history = sqlalchemy.Table(
            "zone_history",
            metadata,
            sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
            sqlalchemy.Column("zone_id", sqlalchemy.String(255)),
            sqlalchemy.Column("zone_name", sqlalchemy.String(255)),
            sqlalchemy.Column("old_status", sqlalchemy.String(50)),
            sqlalchemy.Column("new_status", sqlalchemy.String(50)),
            sqlalchemy.Column("changed_at", sqlalchemy.DateTime, default=datetime.now),
            sqlalchemy.Column("offline_duration_seconds", sqlalchemy.Integer, nullable=True)
        )
        
        # Create engine for table creation
        self.engine = sqlalchemy.create_engine(database_url)
        self.metadata = metadata
        
    async def initialize(self):
        """Initialize database connection and create tables if needed."""
        try:
            # Connect to database
            await self.database.connect()
            
            # Create tables if they don't exist
            self.metadata.create_all(self.engine)
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def save_zone_status(self, zone_id: str, zone_name: str, status: str, 
                              details: Dict, offline_since: Optional[datetime] = None,
                              account_name: Optional[str] = None):
        """Save or update zone status in database."""
        try:
            # Check if zone exists and get previous status
            query = self.zone_status.select().where(self.zone_status.c.zone_id == zone_id)
            row = await self.database.fetch_one(query)
            
            previous_status = row['status'] if row else None
            previous_offline_since = row['offline_since'] if row else None
            
            # Prepare values
            values = {
                "zone_id": zone_id,
                "zone_name": zone_name,
                "account_name": account_name,
                "status": status,
                "offline_since": offline_since,
                "details": details,
                "last_checked": datetime.now(),
                "updated_at": datetime.now()
            }
            
            # Insert or update
            if row:
                query = self.zone_status.update().where(
                    self.zone_status.c.zone_id == zone_id
                ).values(**values)
            else:
                values["created_at"] = datetime.now()
                query = self.zone_status.insert().values(**values)
            
            await self.database.execute(query)
            
            # Log status change to history if status changed
            if previous_status and previous_status != status:
                offline_duration = None
                if previous_status == 'offline' and previous_offline_since:
                    offline_duration = int((datetime.now() - previous_offline_since).total_seconds())
                
                history_query = self.zone_history.insert().values(
                    zone_id=zone_id,
                    zone_name=zone_name,
                    old_status=previous_status,
                    new_status=status,
                    offline_duration_seconds=offline_duration,
                    changed_at=datetime.now()
                )
                await self.database.execute(history_query)
                
        except Exception as e:
            logger.error(f"Error saving zone status for {zone_id}: {e}")
    
    async def load_all_zone_states(self) -> Dict[str, Dict]:
        """Load all zone states from database."""
        try:
            query = self.zone_status.select().order_by(self.zone_status.c.zone_name)
            rows = await self.database.fetch_all(query)
            
            states = {}
            for row in rows:
                states[row['zone_id']] = {
                    'zone_name': row['zone_name'],
                    'account_name': row['account_name'],
                    'status': row['status'],
                    'offline_since': row['offline_since'],
                    'details': row['details'] or {},
                    'last_checked': row['last_checked']
                }
            
            logger.info(f"Loaded {len(states)} zone states from database")
            return states
                
        except Exception as e:
            logger.error(f"Error loading zone states: {e}")
            return {}
    
    async def get_zone_history(self, zone_id: str, days: int = 7) -> List[Dict]:
        """Get status change history for a zone."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = self.zone_history.select().where(
                (self.zone_history.c.zone_id == zone_id) &
                (self.zone_history.c.changed_at > cutoff_date)
            ).order_by(self.zone_history.c.changed_at.desc())
            
            rows = await self.database.fetch_all(query)
            
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
        try:
            # Use raw SQL for aggregation
            query = """
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
            """
            
            rows = await self.database.fetch_all(query)
            
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
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            query = self.zone_history.delete().where(
                self.zone_history.c.changed_at < cutoff_date
            )
            result = await self.database.execute(query)
            
            if result:
                logger.info(f"Cleaned up old history records")
                
        except Exception as e:
            logger.error(f"Error cleaning up history: {e}")
    
    async def close(self):
        """Close database connections."""
        await self.database.disconnect()
        logger.info("Database connection closed")


# Import missing timedelta
from datetime import timedelta

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