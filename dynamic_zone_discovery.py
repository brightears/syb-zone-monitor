#!/usr/bin/env python3
"""Dynamic zone discovery to handle added/removed zones without restart.

This module can be integrated into zone_monitor to periodically refresh
the list of zones from the SoundTrack API.
"""

import asyncio
import httpx
import logging
from typing import List, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class DynamicZoneDiscovery:
    """Dynamically discover zones to handle additions/removals."""
    
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Basic {api_key}",
                "Content-Type": "application/json"
            }
        )
        self.last_discovery = None
        self.discovered_zones: Set[str] = set()
    
    async def discover_all_zones(self) -> List[str]:
        """Discover all zones across all accounts."""
        try:
            # First, get all accounts
            accounts = await self._get_all_accounts()
            
            all_zones = []
            for account_id in accounts:
                # Get zones for each account
                zones = await self._get_account_zones(account_id)
                all_zones.extend(zones)
            
            self.last_discovery = datetime.now()
            self.discovered_zones = set(all_zones)
            
            logger.info(f"Discovered {len(all_zones)} total zones across {len(accounts)} accounts")
            return all_zones
            
        except Exception as e:
            logger.error(f"Error discovering zones: {e}")
            return []
    
    async def _get_all_accounts(self) -> List[str]:
        """Get all account IDs."""
        query = """
        query GetAccounts {
            accounts {
                edges {
                    node {
                        id
                    }
                }
            }
        }
        """
        
        try:
            response = await self.client.post(
                self.api_url,
                json={"query": query}
            )
            response.raise_for_status()
            
            data = response.json()
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []
            
            accounts = []
            edges = data.get("data", {}).get("accounts", {}).get("edges", [])
            for edge in edges:
                account_id = edge.get("node", {}).get("id")
                if account_id:
                    accounts.append(account_id)
            
            return accounts
            
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            return []
    
    async def _get_account_zones(self, account_id: str) -> List[str]:
        """Get all zone IDs for a specific account."""
        query = """
        query GetAccountZones($accountId: ID!) {
            account(id: $accountId) {
                locations {
                    edges {
                        node {
                            soundZones {
                                edges {
                                    node {
                                        id
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        try:
            response = await self.client.post(
                self.api_url,
                json={"query": query, "variables": {"accountId": account_id}}
            )
            response.raise_for_status()
            
            data = response.json()
            if "errors" in data:
                logger.warning(f"Error getting zones for account {account_id}: {data['errors']}")
                return []
            
            zones = []
            account = data.get("data", {}).get("account", {})
            locations = account.get("locations", {}).get("edges", [])
            
            for location in locations:
                sound_zones = location.get("node", {}).get("soundZones", {}).get("edges", [])
                for zone in sound_zones:
                    zone_id = zone.get("node", {}).get("id")
                    if zone_id:
                        zones.append(zone_id)
            
            return zones
            
        except Exception as e:
            logger.warning(f"Error getting zones for account {account_id}: {e}")
            return []
    
    def get_added_zones(self, current_zones: Set[str]) -> Set[str]:
        """Get zones that have been added since last discovery."""
        return self.discovered_zones - current_zones
    
    def get_removed_zones(self, current_zones: Set[str]) -> Set[str]:
        """Get zones that have been removed since last discovery."""
        return current_zones - self.discovered_zones
    
    async def close(self):
        """Clean up resources."""
        await self.client.aclose()


# Integration example for zone_monitor.py
async def update_zone_list(zone_monitor, discovery: DynamicZoneDiscovery):
    """Update zone monitor with dynamically discovered zones."""
    # Discover all zones
    new_zones = await discovery.discover_all_zones()
    
    if not new_zones:
        logger.warning("No zones discovered, keeping current zone list")
        return
    
    current_zones = set(zone_monitor.config.zone_ids)
    discovered_zones = set(new_zones)
    
    # Find changes
    added = discovered_zones - current_zones
    removed = current_zones - discovered_zones
    
    if added:
        logger.info(f"Found {len(added)} new zones to monitor")
        # Add new zones to config
        zone_monitor.config.zone_ids.extend(list(added))
    
    if removed:
        logger.info(f"Found {len(removed)} zones that were removed")
        # Remove zones from config
        zone_monitor.config.zone_ids = [z for z in zone_monitor.config.zone_ids if z not in removed]
        
        # Clean up state for removed zones
        for zone_id in removed:
            zone_monitor.zone_states.pop(zone_id, None)
            zone_monitor.zone_names.pop(zone_id, None)
            zone_monitor.zone_details.pop(zone_id, None)
            zone_monitor.offline_since.pop(zone_id, None)
    
    logger.info(f"Zone list updated: {len(zone_monitor.config.zone_ids)} total zones")


if __name__ == "__main__":
    # Test the discovery
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    async def test():
        discovery = DynamicZoneDiscovery(
            api_key=os.getenv("SYB_API_KEY"),
            api_url="https://api.soundtrackyourbrand.com/v2"
        )
        
        zones = await discovery.discover_all_zones()
        print(f"Discovered {len(zones)} zones")
        
        if zones:
            print(f"Sample zones: {zones[:5]}")
        
        await discovery.close()
    
    asyncio.run(test())