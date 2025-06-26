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
            
            # WhatsApp contacts table
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
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_contacts_account_id 
                ON whatsapp_contacts(account_id)
            """)
            
            # Email contacts table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS email_contacts (
                    id SERIAL PRIMARY KEY,
                    account_id VARCHAR(255) NOT NULL,
                    account_name VARCHAR(255) NOT NULL,
                    contact_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    role VARCHAR(100) DEFAULT 'Manager',
                    is_active BOOLEAN DEFAULT TRUE,
                    source VARCHAR(50) DEFAULT 'manual',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(account_id, email)
                )
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_email_contacts_account_id 
                ON email_contacts(account_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_email_contacts_email 
                ON email_contacts(email)
            """)
            
            # WhatsApp conversations table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS whatsapp_conversations (
                    id SERIAL PRIMARY KEY,
                    wa_id VARCHAR(50) NOT NULL,  -- WhatsApp ID of the customer
                    phone_number VARCHAR(50) NOT NULL,
                    profile_name VARCHAR(255),
                    account_id VARCHAR(255),  -- Link to which account this conversation relates to
                    account_name VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'active',  -- active, archived, resolved
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    unread_count INTEGER DEFAULT 0,
                    UNIQUE(wa_id)
                )
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_wa_id 
                ON whatsapp_conversations(wa_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_account_id 
                ON whatsapp_conversations(account_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_status 
                ON whatsapp_conversations(status)
            """)
            
            # WhatsApp messages table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS whatsapp_messages (
                    id SERIAL PRIMARY KEY,
                    conversation_id INTEGER REFERENCES whatsapp_conversations(id) ON DELETE CASCADE,
                    wa_message_id VARCHAR(255) UNIQUE,  -- WhatsApp's message ID
                    direction VARCHAR(10) NOT NULL,  -- 'inbound' or 'outbound'
                    message_type VARCHAR(50) DEFAULT 'text',  -- text, image, document, etc.
                    message_text TEXT,
                    media_url TEXT,
                    media_mime_type VARCHAR(100),
                    status VARCHAR(50),  -- sent, delivered, read, failed
                    error_message TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    delivered_at TIMESTAMP WITH TIME ZONE,
                    read_at TIMESTAMP WITH TIME ZONE
                )
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_conversation_id 
                ON whatsapp_messages(conversation_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_wa_message_id 
                ON whatsapp_messages(wa_message_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_created_at 
                ON whatsapp_messages(created_at)
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
    
    async def add_whatsapp_contact(self, account_id: str, account_name: str, 
                                  contact_name: str, whatsapp_number: str) -> bool:
        """Add a WhatsApp contact for an account."""
        if not self.pool:
            return False
            
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO whatsapp_contacts 
                    (account_id, account_name, contact_name, whatsapp_number)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (account_id, whatsapp_number) 
                    DO UPDATE SET
                        contact_name = EXCLUDED.contact_name,
                        updated_at = NOW()
                """, account_id, account_name, contact_name, whatsapp_number)
                
                logger.info(f"Added WhatsApp contact for {account_name}: {whatsapp_number}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding WhatsApp contact: {e}")
            return False
    
    async def get_whatsapp_contacts(self, account_id: str) -> List[Dict]:
        """Get WhatsApp contacts for an account."""
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, contact_name, whatsapp_number, created_at
                    FROM whatsapp_contacts
                    WHERE account_id = $1
                    ORDER BY contact_name, whatsapp_number
                """, account_id)
                
                contacts = []
                for row in rows:
                    contacts.append({
                        'id': row['id'],
                        'contact_name': row['contact_name'],
                        'whatsapp_number': row['whatsapp_number'],
                        'created_at': row['created_at'].isoformat()
                    })
                
                return contacts
                
        except Exception as e:
            logger.error(f"Error getting WhatsApp contacts: {e}")
            return []
    
    async def delete_whatsapp_contact(self, contact_id: int) -> bool:
        """Delete a WhatsApp contact."""
        if not self.pool:
            return False
            
        try:
            async with self.pool.acquire() as conn:
                deleted = await conn.fetchval("""
                    DELETE FROM whatsapp_contacts
                    WHERE id = $1
                    RETURNING id
                """, contact_id)
                
                if deleted:
                    logger.info(f"Deleted WhatsApp contact ID: {contact_id}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error deleting WhatsApp contact: {e}")
            return False
    
    # Email contact methods
    async def add_email_contact(self, account_id: str, account_name: str,
                               contact_name: str, email: str, role: str = 'Manager') -> bool:
        """Add email contact for an account."""
        if not self.pool:
            return False
            
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO email_contacts 
                    (account_id, account_name, contact_name, email, role)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (account_id, email) 
                    DO UPDATE SET
                        contact_name = EXCLUDED.contact_name,
                        role = EXCLUDED.role,
                        updated_at = NOW()
                """, account_id, account_name, contact_name, email, role)
                
                logger.info(f"Added email contact for {account_name}: {email}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding email contact: {e}")
            return False
    
    async def get_email_contacts(self, account_id: str) -> List[Dict]:
        """Get email contacts for an account."""
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, contact_name, email, role, is_active, source, created_at
                    FROM email_contacts
                    WHERE account_id = $1 AND is_active = TRUE
                    ORDER BY contact_name, email
                """, account_id)
                
                contacts = []
                for row in rows:
                    contacts.append({
                        'id': row['id'],
                        'contact_name': row['contact_name'],
                        'email': row['email'],
                        'role': row['role'],
                        'source': row['source'],
                        'created_at': row['created_at'].isoformat()
                    })
                
                return contacts
                
        except Exception as e:
            logger.error(f"Error getting email contacts: {e}")
            return []
    
    async def delete_email_contact(self, contact_id: int) -> bool:
        """Delete email contact."""
        if not self.pool:
            return False
            
        try:
            async with self.pool.acquire() as conn:
                deleted = await conn.fetchval("""
                    DELETE FROM email_contacts
                    WHERE id = $1
                    RETURNING id
                """, contact_id)
                
                if deleted:
                    logger.info(f"Deleted email contact ID: {contact_id}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error deleting email contact: {e}")
            return False
    
    async def update_email_contact(self, contact_id: int, contact_name: str, 
                                  email: str, role: str) -> bool:
        """Update email contact."""
        if not self.pool:
            return False
            
        try:
            async with self.pool.acquire() as conn:
                updated = await conn.fetchval("""
                    UPDATE email_contacts
                    SET contact_name = $2, email = $3, role = $4, updated_at = NOW()
                    WHERE id = $1
                    RETURNING id
                """, contact_id, contact_name, email, role)
                
                if updated:
                    logger.info(f"Updated email contact ID: {contact_id}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error updating email contact: {e}")
            return False
    
    # WhatsApp conversation methods
    async def get_or_create_conversation(self, wa_id: str, phone_number: str, 
                                       profile_name: str = None) -> int:
        """Get or create a WhatsApp conversation."""
        if not self.pool:
            return None
            
        try:
            async with self.pool.acquire() as conn:
                # Try to get existing conversation
                conversation_id = await conn.fetchval("""
                    SELECT id FROM whatsapp_conversations
                    WHERE wa_id = $1
                """, wa_id)
                
                if conversation_id:
                    # Update last message time
                    await conn.execute("""
                        UPDATE whatsapp_conversations
                        SET last_message_at = NOW(),
                            updated_at = NOW()
                        WHERE id = $1
                    """, conversation_id)
                else:
                    # Create new conversation
                    conversation_id = await conn.fetchval("""
                        INSERT INTO whatsapp_conversations 
                        (wa_id, phone_number, profile_name)
                        VALUES ($1, $2, $3)
                        RETURNING id
                    """, wa_id, phone_number, profile_name)
                    
                return conversation_id
                
        except Exception as e:
            logger.error(f"Error managing conversation: {e}")
            return None
    
    async def save_whatsapp_message(self, conversation_id: int, wa_message_id: str,
                                   direction: str, message_text: str = None,
                                   message_type: str = 'text', status: str = None) -> bool:
        """Save a WhatsApp message."""
        if not self.pool:
            return False
            
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO whatsapp_messages 
                    (conversation_id, wa_message_id, direction, message_type, 
                     message_text, status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (wa_message_id) DO NOTHING
                """, conversation_id, wa_message_id, direction, message_type,
                    message_text, status)
                
                # Update unread count if inbound
                if direction == 'inbound':
                    await conn.execute("""
                        UPDATE whatsapp_conversations
                        SET unread_count = unread_count + 1,
                            last_message_at = NOW()
                        WHERE id = $1
                    """, conversation_id)
                    
                return True
                
        except Exception as e:
            logger.error(f"Error saving WhatsApp message: {e}")
            return False
    
    async def get_conversations(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Get WhatsApp conversations."""
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT c.*, 
                           (SELECT COUNT(*) FROM whatsapp_messages m 
                            WHERE m.conversation_id = c.id) as message_count
                    FROM whatsapp_conversations c
                """
                params = []
                
                if status:
                    query += " WHERE c.status = $1"
                    params.append(status)
                    
                query += " ORDER BY c.last_message_at DESC LIMIT $" + str(len(params) + 1)
                params.append(limit)
                
                rows = await conn.fetch(query, *params)
                # Convert datetime objects to ISO format strings
                conversations = []
                for row in rows:
                    conv = dict(row)
                    for key, value in conv.items():
                        if isinstance(value, datetime):
                            conv[key] = value.isoformat()
                    conversations.append(conv)
                return conversations
                
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return []
    
    async def get_conversation_messages(self, conversation_id: int) -> List[Dict]:
        """Get messages for a conversation."""
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM whatsapp_messages
                    WHERE conversation_id = $1
                    ORDER BY created_at ASC
                """, conversation_id)
                
                # Mark messages as read
                await conn.execute("""
                    UPDATE whatsapp_conversations
                    SET unread_count = 0
                    WHERE id = $1
                """, conversation_id)
                
                # Convert datetime objects to ISO format strings
                messages = []
                for row in rows:
                    msg = dict(row)
                    for key, value in msg.items():
                        if isinstance(value, datetime):
                            msg[key] = value.isoformat()
                    messages.append(msg)
                return messages
                
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    async def update_message_status(self, wa_message_id: str, status: str,
                                   timestamp: datetime = None) -> bool:
        """Update WhatsApp message status."""
        if not self.pool:
            return False
            
        try:
            async with self.pool.acquire() as conn:
                if status == 'delivered' and timestamp:
                    await conn.execute("""
                        UPDATE whatsapp_messages
                        SET status = $2, delivered_at = $3
                        WHERE wa_message_id = $1
                    """, wa_message_id, status, timestamp)
                elif status == 'read' and timestamp:
                    await conn.execute("""
                        UPDATE whatsapp_messages
                        SET status = $2, read_at = $3
                        WHERE wa_message_id = $1
                    """, wa_message_id, status, timestamp)
                else:
                    await conn.execute("""
                        UPDATE whatsapp_messages
                        SET status = $2
                        WHERE wa_message_id = $1
                    """, wa_message_id, status)
                    
                return True
                
        except Exception as e:
            logger.error(f"Error updating message status: {e}")
            return False
    
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