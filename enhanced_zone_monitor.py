"""Enhanced Zone Monitor that discovers zones from all configured accounts.

This module extends the basic zone_monitor.py to automatically discover
all zones from the configured account IDs instead of using hardcoded zone IDs.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime
import httpx
from zone_monitor import ZoneMonitor, ZoneStatus
from account_config import get_account_config
import json

logger = logging.getLogger(__name__)


class EnhancedZoneMonitor(ZoneMonitor):
    """Zone monitor that discovers zones from account IDs."""
    
    def __init__(self, api_key: str, api_url: str = "https://api.soundtrackyourbrand.com/v2"):
        # Initialize without zone IDs first
        super().__init__(api_key, [], api_url)
        self.account_config = get_account_config()
        self.discovered_zones: Dict[str, Dict] = {}
        self.account_zone_mapping: Dict[str, List[str]] = {}
        
    async def discover_zones_from_accounts(self) -> Dict[str, List[str]]:
        """Discover all zones from configured accounts."""
        logger.info(f"Discovering zones from {self.account_config.account_count} accounts...")
        
        discovered = {}
        failed_accounts = []
        
        # Process accounts in batches to avoid overwhelming the API
        batch_size = 10
        account_ids = self.account_config.account_ids
        
        for i in range(0, len(account_ids), batch_size):
            batch = account_ids[i:i + batch_size]
            tasks = [self._discover_account_zones(acc_id) for acc_id in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for acc_id, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to discover zones for account {acc_id}: {result}")
                    failed_accounts.append(acc_id)
                else:
                    if result:
                        discovered[acc_id] = result
                        logger.info(f"Discovered {len(result)} zones for account {acc_id}")
            
            # Brief pause between batches
            if i + batch_size < len(account_ids):
                await asyncio.sleep(1)
        
        # Update internal zone list
        all_zone_ids = []
        for acc_id, zones in discovered.items():
            all_zone_ids.extend(zones)
            self.account_zone_mapping[acc_id] = zones
        
        self.zone_ids = list(set(all_zone_ids))  # Remove duplicates
        logger.info(f"Total zones discovered: {len(self.zone_ids)} from {len(discovered)} accounts")
        
        if failed_accounts:
            logger.warning(f"Failed to discover zones from {len(failed_accounts)} accounts")
        
        return discovered
    
    async def _discover_account_zones(self, account_id: str) -> List[str]:
        """Discover zones for a single account."""
        query = """
        query($accountId: ID!) {
            account(id: $accountId) {
                id
                name
                locations {
                    edges {
                        node {
                            id
                            name
                            soundZones {
                                edges {
                                    node {
                                        id
                                        name
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
            result = await self._query_graphql(query, {"accountId": account_id})
            
            if not result or 'data' not in result:
                return []
            
            account_data = result['data'].get('account')
            if not account_data:
                return []
            
            zone_ids = []
            locations = account_data.get('locations', {}).get('edges', [])
            
            for loc_edge in locations:
                location = loc_edge.get('node', {})
                zones = location.get('soundZones', {}).get('edges', [])
                
                for zone_edge in zones:
                    zone = zone_edge.get('node', {})
                    if zone.get('id'):
                        zone_ids.append(zone['id'])
                        # Store zone metadata
                        self.discovered_zones[zone['id']] = {
                            'id': zone['id'],
                            'name': zone.get('name', 'Unknown'),
                            'account_id': account_id,
                            'account_name': account_data.get('name', 'Unknown'),
                            'location_name': location.get('name', 'Unknown')
                        }
            
            return zone_ids
            
        except Exception as e:
            logger.error(f"Error discovering zones for account {account_id}: {e}")
            return []
    
    async def initialize(self) -> None:
        """Initialize the monitor by discovering all zones."""
        await self.discover_zones_from_accounts()
        logger.info(f"Enhanced zone monitor initialized with {len(self.zone_ids)} zones")
    
    def get_zones_by_account(self, account_id: str) -> List[Dict]:
        """Get all zones for a specific account."""
        zone_ids = self.account_zone_mapping.get(account_id, [])
        zones = []
        
        for zone_id in zone_ids:
            zone_info = self.discovered_zones.get(zone_id, {})
            status = self.zone_status.get(zone_id)
            
            if zone_info:
                zone_data = zone_info.copy()
                if status:
                    zone_data['status'] = status.status
                    zone_data['offline_duration'] = status.offline_duration
                    zone_data['last_seen'] = status.last_seen.isoformat() if status.last_seen else None
                zones.append(zone_data)
        
        return zones
    
    def get_all_accounts(self) -> Dict[str, Dict]:
        """Get all accounts with their zone counts and status summary."""
        accounts = {}
        
        for acc_id in self.account_config.account_ids:
            zones = self.get_zones_by_account(acc_id)
            
            # Calculate status summary
            status_counts = {
                'online': 0,
                'offline': 0,
                'no_device': 0,
                'expired': 0,
                'unknown': 0
            }
            
            for zone in zones:
                status = zone.get('status', 'unknown').lower()
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts['unknown'] += 1
            
            account_name = self.account_config.get_account_name(acc_id)
            if not account_name:
                # Try to get from discovered zones
                for zone in zones:
                    if zone.get('account_name'):
                        account_name = zone['account_name']
                        break
            
            accounts[acc_id] = {
                'id': acc_id,
                'name': account_name or 'Unknown',
                'total_zones': len(zones),
                'status_counts': status_counts,
                'has_issues': status_counts['offline'] > 0 or status_counts['no_device'] > 0
            }
        
        return accounts
    
    def save_discovery_results(self, filename: str = "discovered_zones.json") -> None:
        """Save discovered zones to a JSON file."""
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_accounts': self.account_config.account_count,
            'total_zones': len(self.zone_ids),
            'account_zone_mapping': self.account_zone_mapping,
            'zones': self.discovered_zones,
            'accounts': self.get_all_accounts()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Discovery results saved to {filename}")


async def test_enhanced_monitor():
    """Test the enhanced zone monitor."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("SYB_API_KEY")
    
    if not api_key:
        logger.error("SYB_API_KEY not found in environment")
        return
    
    monitor = EnhancedZoneMonitor(api_key)
    
    # Initialize and discover zones
    await monitor.initialize()
    
    # Save discovery results
    monitor.save_discovery_results()
    
    # Get some statistics
    accounts = monitor.get_all_accounts()
    total_issues = sum(1 for acc in accounts.values() if acc['has_issues'])
    
    print(f"\n=== Enhanced Zone Monitor Summary ===")
    print(f"Total accounts: {len(accounts)}")
    print(f"Total zones: {len(monitor.zone_ids)}")
    print(f"Accounts with issues: {total_issues}")
    
    # Show a few accounts with issues
    print("\nAccounts with offline zones:")
    for acc_id, acc_data in list(accounts.items())[:10]:
        if acc_data['has_issues']:
            print(f"- {acc_data['name']}: {acc_data['status_counts']['offline']} offline, "
                  f"{acc_data['status_counts']['no_device']} no device")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_enhanced_monitor())