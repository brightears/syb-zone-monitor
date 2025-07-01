#!/usr/bin/env python3
"""
Add a single account to the existing accounts discovery results.
This script queries the SYB API for a specific account and merges it into the existing data.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import httpx


class SingleAccountProcessor:
    """Process a single SYB account and add it to existing data."""
    
    def __init__(self, api_key: str, api_url: str = "https://api.soundtrackyourbrand.com/v2"):
        self.api_key = api_key
        self.api_url = api_url
        self.logger = logging.getLogger(__name__)
        
        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=30,
            headers={
                "Authorization": f"Basic {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def query_account(self, account_id: str) -> Optional[Dict]:
        """Query account information including zones and contacts."""
        query = """
        query GetAccountDetails($accountId: ID!) {
            account(id: $accountId) {
                id
                businessName
                businessType
                country
                createdAt
                settings {
                    filterExplicit
                    restrictBlockTracks
                }
                locations(first: 100) {
                    edges {
                        node {
                            id
                            name
                            soundZones(first: 100) {
                                edges {
                                    node {
                                        id
                                        name
                                        isPaired
                                        online
                                        device {
                                            id
                                            name
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                access {
                    users(first: 100) {
                        edges {
                            node {
                                id
                                name
                                email
                            }
                            role
                        }
                    }
                }
            }
        }
        """
        
        variables = {"accountId": account_id}
        
        try:
            response = await self.client.post(
                self.api_url,
                json={"query": query, "variables": variables}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    self.logger.error(f"GraphQL errors: {data['errors']}")
                    return None
                
                return data.get("data", {}).get("account")
            else:
                self.logger.error(f"HTTP error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to query account: {e}")
            return None
    
    def process_account_data(self, account_data: Dict) -> Dict:
        """Process account data into the expected format."""
        processed_data = {
            "id": account_data.get("id"),
            "name": account_data.get("businessName", "Unknown"),
            "businessType": account_data.get("businessType"),
            "country": account_data.get("country"),
            "createdAt": account_data.get("createdAt"),
            "locations": [],
            "users": [],
            "zone_count": 0,
            "online_zones": 0,
            "offline_zones": 0,
            "unpaired_zones": 0
        }
        
        # Process locations and zones
        locations_data = account_data.get("locations", {}).get("edges", [])
        for location_edge in locations_data:
            location = location_edge.get("node", {})
            location_info = {
                "id": location.get("id"),
                "name": location.get("name"),
                "zones": []
            }
            
            zones_data = location.get("soundZones", {}).get("edges", [])
            for zone_edge in zones_data:
                zone = zone_edge.get("node", {})
                zone_info = {
                    "id": zone.get("id"),
                    "name": zone.get("name"),
                    "isPaired": zone.get("isPaired", False),
                    "online": zone.get("online", False),
                    "device": zone.get("device", {}).get("name") if zone.get("device") else None
                }
                
                location_info["zones"].append(zone_info)
                processed_data["zone_count"] += 1
                
                if zone_info["isPaired"]:
                    if zone_info["online"]:
                        processed_data["online_zones"] += 1
                    else:
                        processed_data["offline_zones"] += 1
                else:
                    processed_data["unpaired_zones"] += 1
            
            processed_data["locations"].append(location_info)
        
        # Process users/contacts
        users_data = account_data.get("access", {}).get("users", {}).get("edges", [])
        for user_edge in users_data:
            user = user_edge.get("node", {})
            user_info = {
                "id": user.get("id"),
                "name": user.get("name"),
                "email": user.get("email"),
                "role": user_edge.get("role")
            }
            processed_data["users"].append(user_info)
        
        return processed_data
    
    async def add_account(self, account_id: str):
        """Add a single account to the existing discovery results."""
        self.logger.info(f"Querying account: {account_id}")
        
        # Query the account
        account_data = await self.query_account(account_id)
        
        if not account_data:
            self.logger.error(f"Failed to retrieve account data for {account_id}")
            return False
        
        # Process the account data
        processed_data = self.process_account_data(account_data)
        
        # Load existing results
        results_file = Path("accounts_discovery_results.json")
        if results_file.exists():
            with open(results_file, "r", encoding="utf-8") as f:
                existing_results = json.load(f)
        else:
            existing_results = {
                "accounts": {},
                "processing_errors": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # Add/update the account
        existing_results["accounts"][account_id] = processed_data
        existing_results["timestamp"] = datetime.now().isoformat()
        
        # Save updated results
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(existing_results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Successfully added account: {processed_data['name']}")
        self.logger.info(f"  - Zones: {processed_data['zone_count']}")
        self.logger.info(f"  - Online: {processed_data['online_zones']}")
        self.logger.info(f"  - Offline: {processed_data['offline_zones']}")
        self.logger.info(f"  - Users: {len(processed_data['users'])}")
        
        # Extract zone IDs for ZONE_IDS environment variable
        zone_ids = []
        for location in processed_data["locations"]:
            for zone in location["zones"]:
                zone_ids.append(zone["id"])
        
        if zone_ids:
            self.logger.info(f"\nZone IDs for this account:")
            for zone_id in zone_ids:
                self.logger.info(f"  {zone_id}")
        
        return True


async def main():
    """Main function."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python add_single_account.py <account_id>")
        print("Example: python add_single_account.py QWNjb3VudCwsMWs3bHVkeGY1czAv")
        sys.exit(1)
    
    account_id = sys.argv[1]
    
    # API key (same as in process_all_accounts.py)
    api_key = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
    
    # Create processor and run
    processor = SingleAccountProcessor(api_key)
    
    try:
        success = await processor.add_account(account_id)
        
        if success:
            logger.info(f"\n✅ Account {account_id} has been successfully added!")
            logger.info("The dashboard will use the updated data on next restart.")
        else:
            logger.error(f"\n❌ Failed to add account {account_id}")
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        await processor.close()


if __name__ == "__main__":
    asyncio.run(main())