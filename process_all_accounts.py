#!/usr/bin/env python3
"""
Process all accounts to discover zones and contacts.
Reads account IDs from CSV files and queries SYB API for zone and contact information.
"""

import asyncio
import csv
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional, Set
from pathlib import Path

import httpx


class AccountProcessor:
    """Process SYB accounts to discover zones and contacts."""
    
    def __init__(self, api_key: str, api_url: str = "https://api.soundtrackyourbrand.com/v2"):
        self.api_key = api_key
        self.api_url = api_url
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.requests_per_minute = 30  # Conservative rate limit
        self.request_interval = 60.0 / self.requests_per_minute
        self.last_request_time = 0
        
        # Results storage
        self.results = {
            "accounts": {},
            "processing_errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
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
    
    async def _rate_limit(self):
        """Implement rate limiting."""
        current_time = asyncio.get_event_loop().time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.request_interval:
            await asyncio.sleep(self.request_interval - time_since_last_request)
        
        self.last_request_time = asyncio.get_event_loop().time()
    
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
        
        await self._rate_limit()
        
        try:
            response = await self.client.post(
                self.api_url,
                json={"query": query, "variables": variables}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    self.logger.error(f"GraphQL errors for account {account_id}: {data['errors']}")
                    return None
                
                return data.get("data", {}).get("account")
            else:
                self.logger.error(f"HTTP error {response.status_code} for account {account_id}: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to query account {account_id}: {e}")
            return None
    
    async def process_account(self, account_id: str) -> Dict:
        """Process a single account and extract relevant information."""
        self.logger.info(f"Processing account: {account_id}")
        
        account_data = await self.query_account(account_id)
        
        if not account_data:
            self.results["processing_errors"].append({
                "account_id": account_id,
                "error": "Failed to retrieve account data",
                "timestamp": datetime.now().isoformat()
            })
            return {}
        
        # Extract relevant information
        processed_data = {
            "id": account_id,
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
                "role": user_edge.get("role")  # role is on the edge, not the node
            }
            processed_data["users"].append(user_info)
        
        return processed_data
    
    async def process_all_accounts(self, account_ids: List[str]):
        """Process all accounts from the list."""
        total = len(account_ids)
        self.logger.info(f"Starting to process {total} accounts")
        
        for i, account_id in enumerate(account_ids, 1):
            self.logger.info(f"Processing account {i}/{total}: {account_id}")
            
            try:
                account_data = await self.process_account(account_id)
                if account_data:
                    self.results["accounts"][account_id] = account_data
            except Exception as e:
                self.logger.error(f"Error processing account {account_id}: {e}")
                self.results["processing_errors"].append({
                    "account_id": account_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            # Progress update every 10 accounts
            if i % 10 == 0:
                self.logger.info(f"Progress: {i}/{total} accounts processed ({i/total*100:.1f}%)")
                await self.save_results()  # Save intermediate results
        
        self.logger.info(f"Completed processing {total} accounts")
    
    async def save_results(self):
        """Save results to JSON files."""
        # Save main results
        output_file = "accounts_discovery_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Results saved to {output_file}")
        
        # Save summary statistics
        summary = {
            "timestamp": self.results["timestamp"],
            "total_accounts": len(self.results["accounts"]),
            "successful_accounts": len([a for a in self.results["accounts"].values() if a]),
            "failed_accounts": len(self.results["processing_errors"]),
            "total_zones": sum(a.get("zone_count", 0) for a in self.results["accounts"].values()),
            "total_online_zones": sum(a.get("online_zones", 0) for a in self.results["accounts"].values()),
            "total_offline_zones": sum(a.get("offline_zones", 0) for a in self.results["accounts"].values()),
            "total_unpaired_zones": sum(a.get("unpaired_zones", 0) for a in self.results["accounts"].values()),
            "total_users": sum(len(a.get("users", [])) for a in self.results["accounts"].values())
        }
        
        summary_file = "accounts_discovery_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        self.logger.info(f"Summary saved to {summary_file}")


def load_account_ids() -> List[str]:
    """Load account IDs from JSON file or CSV files."""
    # First try to load from JSON file
    json_file = Path("account_ids.json")
    if json_file.exists():
        with open(json_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Otherwise, extract from CSV files
    account_ids = set()
    
    # Read from new_token_soundtrack_accounts.csv
    csv_file1 = Path("new_token_soundtrack_accounts.csv")
    if csv_file1.exists():
        with open(csv_file1, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "account_id" in row and row["account_id"]:
                    account_ids.add(row["account_id"])
    
    # Read from new_token_soundtrack_accounts_with_zones.csv
    csv_file2 = Path("new_token_soundtrack_accounts_with_zones.csv")
    if csv_file2.exists():
        with open(csv_file2, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "account_id" in row and row["account_id"]:
                    account_ids.add(row["account_id"])
    
    return sorted(list(account_ids))


async def main():
    """Main function."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("process_accounts.log")
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # API key (same as in discover_zones.py)
    api_key = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
    
    # Load account IDs
    account_ids = load_account_ids()
    if not account_ids:
        logger.error("No account IDs found!")
        return
    
    logger.info(f"Loaded {len(account_ids)} account IDs")
    
    # Create processor and run
    processor = AccountProcessor(api_key)
    
    try:
        await processor.process_all_accounts(account_ids)
        await processor.save_results()
        
        # Print summary
        summary = {
            "total_accounts": len(processor.results["accounts"]),
            "successful": len([a for a in processor.results["accounts"].values() if a]),
            "failed": len(processor.results["processing_errors"])
        }
        
        logger.info(f"\nProcessing complete!")
        logger.info(f"Total accounts: {summary['total_accounts']}")
        logger.info(f"Successful: {summary['successful']}")
        logger.info(f"Failed: {summary['failed']}")
        
    except KeyboardInterrupt:
        logger.info("\nProcessing interrupted by user")
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
    finally:
        await processor.close()


if __name__ == "__main__":
    asyncio.run(main())