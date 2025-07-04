"""Optimized zone monitoring with better rate limit handling."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import random

import httpx

from config import Config
try:
    from database import get_database
except ImportError:
    # Fallback to compatible version
    from database_compat import get_database


class ZoneMonitor:
    """Monitors SYB zones with optimized rate limit handling."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Zone tracking - now with detailed status
        self.zone_states: Dict[str, str] = {}  # zone_id -> status
        self.zone_names: Dict[str, str] = {}    # zone_id -> zone_name
        self.zone_details: Dict[str, Dict] = {} # zone_id -> detailed info
        self.offline_since: Dict[str, datetime] = {}  # zone_id -> offline_start_time
        self.last_check_time: Optional[datetime] = None
        self.db = None  # Database instance
        
        # Status stabilization - prevent flickering
        self.pending_status_changes: Dict[str, Tuple[str, datetime]] = {}  # zone_id -> (new_status, first_seen)
        self.status_confirmation_count: Dict[str, int] = {}  # zone_id -> count of consistent readings
        self.STABILIZATION_THRESHOLD = 1  # Temporarily reduced to 1 for immediate updates
        
        # Make zone_ids mutable for dynamic updates
        self.zone_ids = list(config.zone_ids) if hasattr(config, 'zone_ids') else []
        
        # Priority queue for zones that need more frequent checking
        self.priority_zones: set = set()  # Zones that went offline recently
        self.last_priority_check: Optional[datetime] = None
        
        # Rate limiting
        self.rate_limit_reset = datetime.now()
        self.available_tokens = 100  # Start with assumed tokens
        
        # HTTP client with retry logic
        self.client = httpx.AsyncClient(
            timeout=self.config.request_timeout,
            headers={
                "Authorization": f"Basic {self.config.syb_api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def initialize(self):
        """Initialize database and load saved states."""
        self.db = await get_database()
        
        if self.db:
            # Load saved states from database
            saved_states = await self.db.load_all_zone_states()
            
            for zone_id, state_data in saved_states.items():
                # Restore state from database
                self.zone_states[zone_id] = state_data['status']
                self.zone_names[zone_id] = state_data['zone_name']
                self.zone_details[zone_id] = state_data['details'] or {}
                
                # Restore offline tracking
                if state_data['status'] == 'offline' and state_data['offline_since']:
                    self.offline_since[zone_id] = state_data['offline_since']
            
            self.logger.info(f"Loaded {len(saved_states)} zone states from database")
            
            # Initialize any new zones that aren't in the database yet
            new_zones = set(self.zone_ids) - set(saved_states.keys())
            if new_zones:
                self.logger.info(f"Found {len(new_zones)} new zones not in database")
                # Mark them as pending initial check
                for zone_id in new_zones:
                    self.zone_states[zone_id] = "checking"
                    self.zone_names[zone_id] = zone_id  # Use ID as temporary name
    
    async def check_zones(self) -> None:
        """Check status of all configured zones with smart rate limiting."""
        self.last_check_time = datetime.now()
        
        # Check priority zones first if it's been more than 2 minutes
        if self.priority_zones and (not self.last_priority_check or 
                                   (datetime.now() - self.last_priority_check).total_seconds() > 120):
            await self.check_priority_zones()
        
        # Dynamic batch size based on available tokens
        # Each query costs 16 tokens, so batch size = available_tokens / 16
        batch_size = max(1, min(20, self.available_tokens // 16))  # Max 20, min 1
        
        zone_ids = list(self.zone_ids)  # Use instance variable
        total_zones = len(zone_ids)
        
        # Prioritize offline zones at the beginning of the check cycle
        offline_zones = [z for z in zone_ids if self.zone_states.get(z) == 'offline']
        online_zones = [z for z in zone_ids if z not in offline_zones]
        
        # Check offline zones first, then online zones
        zone_ids = offline_zones + online_zones
        
        self.logger.info(f"Starting to check {total_zones} zones ({len(offline_zones)} offline first) in batches of {batch_size}")
        
        checked_count = 0
        
        for i in range(0, total_zones, batch_size):
            batch = zone_ids[i:i + batch_size]
            
            # Check if we need to wait for rate limit reset
            if self.available_tokens < len(batch) * 16:
                wait_time = max(0, (self.rate_limit_reset - datetime.now()).total_seconds())
                if wait_time > 0:
                    self.logger.info(f"Rate limit reached. Waiting {wait_time:.1f}s for reset...")
                    await asyncio.sleep(wait_time + 1)  # Add 1s buffer
                    self.available_tokens = 100  # Reset tokens
            
            tasks = []
            for zone_id in batch:
                task = self._check_single_zone(zone_id)
                tasks.append(task)
            
            # Wait for all tasks in this batch to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful checks
            successful = sum(1 for r in results if not isinstance(r, Exception))
            checked_count += successful
            
            # Log progress
            self.logger.info(f"Checked {checked_count}/{total_zones} zones ({checked_count*100//total_zones}%)")
            
            # Adaptive delay based on success rate
            if successful < len(batch) / 2:  # More than half failed
                await asyncio.sleep(2)  # Longer delay
            elif i + batch_size < total_zones:
                await asyncio.sleep(0.5)  # Normal delay between batches
    
    async def check_priority_zones(self) -> None:
        """Check priority zones (recently offline) more frequently."""
        if not self.priority_zones:
            return
            
        self.logger.info(f"Checking {len(self.priority_zones)} priority zones")
        self.last_priority_check = datetime.now()
        
        # Check priority zones in small batches
        priority_list = list(self.priority_zones)
        batch_size = min(5, len(priority_list))  # Smaller batches for priority zones
        
        for i in range(0, len(priority_list), batch_size):
            batch = priority_list[i:i + batch_size]
            
            tasks = []
            for zone_id in batch:
                task = self._check_single_zone(zone_id)
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            if i + batch_size < len(priority_list):
                await asyncio.sleep(0.5)
        
        # Remove zones that have been online for a while from priority list
        zones_to_remove = []
        for zone_id in self.priority_zones:
            if self.zone_states.get(zone_id) == 'online':
                zones_to_remove.append(zone_id)
        
        for zone_id in zones_to_remove:
            self.priority_zones.discard(zone_id)
            self.logger.info(f"Removed {self.zone_names.get(zone_id, zone_id)} from priority queue (back online)")
    
    async def _check_single_zone(self, zone_id: str) -> None:
        """Check a single zone and update its state."""
        try:
            status, zone_name, details = await self._check_zone_status(zone_id)
            await self._update_zone_state(zone_id, status, zone_name, details)
        except Exception as e:
            self.logger.error(f"Failed to check zone {zone_id}: {e}")
            # Don't mark as offline if it's a rate limit error
            if "rate limited" not in str(e).lower():
                await self._update_zone_state(zone_id, "offline", self.zone_names.get(zone_id, zone_id), {})
    
    async def _check_zone_status(self, zone_id: str) -> Tuple[str, str, Dict]:
        """Check detailed status of a specific zone using simplified query."""
        # Query with nowPlaying information
        query = """
        query GetZoneStatus($zoneId: ID!) {
            soundZone(id: $zoneId) {
                id
                name
                isPaired
                online
                subscription {
                    state
                }
                nowPlaying {
                    track {
                        id
                        title
                        artists {
                            name
                        }
                        album {
                            name
                        }
                        duration
                    }
                    startedAt
                    playFrom {
                        __typename
                        ... on Playlist {
                            id
                            name
                        }
                        ... on Schedule {
                            id
                            name
                        }
                    }
                }
            }
        }
        """
        
        variables = {"zoneId": zone_id}
        
        # Single retry with exponential backoff
        for attempt in range(2):
            try:
                response = await self.client.post(
                    self.config.syb_api_url,
                    json={"query": query, "variables": variables},
                    timeout=10.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                if "errors" in data:
                    error_msg = str(data['errors'])
                    
                    # Parse rate limit info
                    if "rate limited" in error_msg.lower():
                        # Extract token info if available
                        import re
                        tokens_match = re.search(r'costs (\d+) tokens.*have (\d+) available', error_msg)
                        if tokens_match:
                            cost = int(tokens_match.group(1))
                            available = int(tokens_match.group(2))
                            self.available_tokens = available
                            
                            # Set rate limit reset (usually 1 minute)
                            self.rate_limit_reset = datetime.now() + timedelta(seconds=60)
                        
                        # Don't retry rate limit errors immediately
                        if attempt == 0:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                    
                    raise Exception(f"GraphQL errors: {data['errors']}")
                
                zone_data = data.get("data", {}).get("soundZone")
                if not zone_data:
                    raise Exception(f"Zone {zone_id} not found")
                
                zone_name = zone_data.get("name", zone_id)
                is_paired = zone_data.get("isPaired", False)
                online = zone_data.get("online", False)
                subscription = zone_data.get("subscription", {})
                subscription_state = subscription.get("state") if subscription else None
                now_playing = zone_data.get("nowPlaying")
                
                # Simplified status determination
                if not is_paired:
                    status = "unpaired"
                elif subscription_state is None:
                    status = "no_subscription"
                elif subscription_state in ["EXPIRED", "CANCELLED"]:
                    status = "expired"
                elif online:
                    status = "online"
                else:
                    status = "offline"
                
                details = {
                    "isPaired": is_paired,
                    "online": online,
                    "subscriptionState": subscription_state
                }
                
                # Add nowPlaying information if available
                if now_playing and now_playing.get("track"):
                    track = now_playing["track"]
                    details["nowPlaying"] = {
                        "track": {
                            "title": track.get("title", "Unknown"),
                            "artists": ", ".join([artist.get("name", "") for artist in track.get("artists", [])]),
                            "album": track.get("album", {}).get("name", "Unknown") if track.get("album") else "Unknown",
                            "duration": track.get("duration", 0)
                        },
                        "startedAt": now_playing.get("startedAt"),
                        "playFrom": None
                    }
                    
                    # Add playlist/schedule info if available
                    if now_playing.get("playFrom"):
                        play_from = now_playing["playFrom"]
                        details["nowPlaying"]["playFrom"] = {
                            "type": play_from.get("__typename", "Unknown"),
                            "name": play_from.get("name", "Unknown"),
                            "id": play_from.get("id")
                        }
                else:
                    details["nowPlaying"] = None
                
                # Update available tokens on success
                # NowPlaying query costs more tokens
                self.available_tokens = max(0, self.available_tokens - 15)
                
                return status, zone_name, details
                
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for zone {zone_id}: {e}")
                if attempt < 1 and "rate limited" not in str(e).lower():
                    await asyncio.sleep(1)
                else:
                    raise
    
    
    async def _update_zone_state(self, zone_id: str, status: str, zone_name: str, details: Dict) -> None:
        """Update the internal state for a zone with status stabilization."""
        self.zone_names[zone_id] = zone_name
        self.zone_details[zone_id] = details
        previous_state = self.zone_states.get(zone_id)
        
        # Status stabilization logic
        if zone_id in self.zone_states and self.zone_states[zone_id] != status:
            # Status is changing - apply stabilization
            
            if zone_id in self.pending_status_changes:
                pending_status, first_seen = self.pending_status_changes[zone_id]
                
                if pending_status == status:
                    # Same pending status seen again
                    self.status_confirmation_count[zone_id] = self.status_confirmation_count.get(zone_id, 1) + 1
                    
                    if self.status_confirmation_count[zone_id] >= self.STABILIZATION_THRESHOLD:
                        # Enough confirmations - apply the change
                        self.logger.info(f"Zone {zone_name} status stabilized from {self.zone_states[zone_id]} to {status} after {self.status_confirmation_count[zone_id]} confirmations")
                        self.zone_states[zone_id] = status
                        
                        # Clean up stabilization tracking
                        del self.pending_status_changes[zone_id]
                        del self.status_confirmation_count[zone_id]
                    else:
                        # Still pending - keep current status
                        self.logger.debug(f"Zone {zone_name} pending status change to {status} ({self.status_confirmation_count[zone_id]}/{self.STABILIZATION_THRESHOLD} confirmations)")
                        return  # Don't update the status yet
                else:
                    # Different status - reset stabilization
                    self.logger.debug(f"Zone {zone_name} status changed from pending {pending_status} to {status}, resetting stabilization")
                    self.pending_status_changes[zone_id] = (status, datetime.now())
                    self.status_confirmation_count[zone_id] = 1
                    return  # Don't update the status yet
            else:
                # First time seeing this status change
                self.logger.debug(f"Zone {zone_name} starting status stabilization from {self.zone_states[zone_id]} to {status}")
                self.pending_status_changes[zone_id] = (status, datetime.now())
                self.status_confirmation_count[zone_id] = 1
                return  # Don't update the status yet
        else:
            # No status change or new zone - apply immediately
            self.zone_states[zone_id] = status
            
            # Clear any pending changes since status is stable
            if zone_id in self.pending_status_changes:
                del self.pending_status_changes[zone_id]
            if zone_id in self.status_confirmation_count:
                del self.status_confirmation_count[zone_id]
        
        # Extract account name from zone name pattern
        account_name = self._determine_account_name(zone_name)
        
        # Only track offline timing for zones that should be working (paired with active subscription)
        should_track_offline = status in ["online", "offline"]
        
        if status == "online":
            # Zone is online and working
            if zone_id in self.offline_since:
                offline_duration = datetime.now() - self.offline_since[zone_id]
                self.logger.info(f"Zone {zone_name} back online after {offline_duration}")
                del self.offline_since[zone_id]
        elif should_track_offline and status == "offline":
            # Zone should be working but is offline
            if previous_state == "online":  # Was online, now offline
                self.offline_since[zone_id] = datetime.now()
                self.logger.warning(f"Zone {zone_name} went offline")
                # Add to priority queue for more frequent checking
                self.priority_zones.add(zone_id)
                self.logger.info(f"Added {zone_name} to priority queue for frequent checking")
            elif zone_id not in self.offline_since:
                # First time checking this zone and it's offline
                self.offline_since[zone_id] = datetime.now()
                self.logger.warning(f"Zone {zone_name} detected as offline")
                # Also add to priority queue
                self.priority_zones.add(zone_id)
        else:
            # Zone has subscription/pairing issues - don't track as "offline"
            if zone_id in self.offline_since:
                del self.offline_since[zone_id]
            
            if previous_state != status:
                if status == "expired":
                    self.logger.warning(f"Zone {zone_name} subscription expired")
                elif status == "unpaired":
                    self.logger.warning(f"Zone {zone_name} has no paired device")
                elif status == "no_subscription":
                    self.logger.warning(f"Zone {zone_name} has no subscription")
        
        # Save to database if available
        if self.db:
            offline_since = self.offline_since.get(zone_id) if status == "offline" else None
            await self.db.save_zone_status(
                zone_id=zone_id,
                zone_name=zone_name,
                status=status,
                details=details,
                offline_since=offline_since,
                account_name=account_name
            )
    
    def get_offline_zones(self) -> Dict[str, timedelta]:
        """Get zones that are currently offline with their offline duration."""
        offline_zones = {}
        current_time = datetime.now()
        
        for zone_id, offline_start in self.offline_since.items():
            offline_duration = current_time - offline_start
            offline_zones[zone_id] = offline_duration
            
        return offline_zones
    
    def get_zone_name(self, zone_id: str) -> str:
        """Get the display name for a zone."""
        return self.zone_names.get(zone_id, zone_id)
    
    def get_zone_status_summary(self) -> str:
        """Get a summary of zone statuses."""
        status_counts = {"online": 0, "offline": 0, "expired": 0, "unpaired": 0, "no_subscription": 0, "checking": 0}
        for status in self.zone_states.values():
            status_counts[status] = status_counts.get(status, 0) + 1
        
        parts = []
        if status_counts['online'] > 0:
            parts.append(f"{status_counts['online']} online")
        if status_counts['offline'] > 0:
            parts.append(f"{status_counts['offline']} offline")
        if status_counts['expired'] > 0:
            parts.append(f"{status_counts['expired']} expired")
        if status_counts['no_subscription'] > 0:
            parts.append(f"{status_counts['no_subscription']} no subscription")
        if status_counts['unpaired'] > 0:
            parts.append(f"{status_counts['unpaired']} unpaired")
        if status_counts['checking'] > 0:
            parts.append(f"{status_counts['checking']} checking")
        
        return ", ".join(parts) if parts else "No zones"
    
    def get_detailed_status(self) -> Dict:
        """Get detailed status information for all zones."""
        status = {}
        current_time = datetime.now()
        
        for zone_id in self.config.zone_ids:
            zone_name = self.zone_names.get(zone_id, zone_id)
            zone_status = self.zone_states.get(zone_id, "checking")  # Default to "checking" instead of "offline"
            zone_details = self.zone_details.get(zone_id, {})
            
            # Map old 'online' field for backward compatibility
            is_online = zone_status == "online"
            
            zone_info = {
                "name": zone_name,
                "online": is_online,  # For backward compatibility
                "status": zone_status,  # New detailed status
                "status_label": self._get_status_label(zone_status),
                "offline_since": None,
                "offline_duration_seconds": None,
                "details": zone_details
            }
            
            # Add pending status information if in stabilization
            if zone_id in self.pending_status_changes:
                pending_status, first_seen = self.pending_status_changes[zone_id]
                confirmations = self.status_confirmation_count.get(zone_id, 0)
                zone_info["pending_status"] = {
                    "status": pending_status,
                    "confirmations": confirmations,
                    "required": self.STABILIZATION_THRESHOLD,
                    "first_seen": first_seen.isoformat()
                }
            
            if zone_id in self.offline_since:
                offline_start = self.offline_since[zone_id]
                offline_duration = current_time - offline_start
                zone_info.update({
                    "offline_since": offline_start.isoformat(),
                    "offline_duration_seconds": int(offline_duration.total_seconds())
                })
            
            status[zone_id] = zone_info
        
        return status
    
    def _get_status_label(self, status: str) -> str:
        """Get human-readable status label."""
        labels = {
            "online": "Online",
            "offline": "Offline",
            "expired": "Subscription Expired",
            "unpaired": "No Device Paired",
            "no_subscription": "No Subscription",
            "checking": "Checking..."
        }
        return labels.get(status, status.title())
    
    def _determine_account_name(self, zone_name: str) -> str:
        """Extract account name from zone name."""
        # Common patterns: "Account - Zone" or just use first part
        if " - " in zone_name:
            return zone_name.split(" - ")[0].strip()
        return zone_name.split()[0] if zone_name else "Unknown"
    
    async def close(self):
        """Clean up resources."""
        await self.client.aclose()
        if self.db:
            await self.db.close()