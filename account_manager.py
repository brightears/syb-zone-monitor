"""
Account management module for adding and removing accounts from the monitoring system.
Provides functions to add new accounts, remove accounts, and update the discovery results.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import httpx
import asyncio


class AccountManager:
    """Manage accounts in the SYB monitoring system."""
    
    def __init__(self, api_key: str, api_url: str = "https://api.soundtrackyourbrand.com/v2"):
        self.api_key = api_key
        self.api_url = api_url
        self.logger = logging.getLogger(__name__)
        self.discovery_file = Path("accounts_discovery_results.json")
        
        # HTTP client for API queries
        self.client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(
            timeout=30,
            headers={
                "Authorization": f"Basic {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    def load_discovery_results(self) -> Dict:
        """Load existing discovery results."""
        if self.discovery_file.exists():
            with open(self.discovery_file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {
                "accounts": {},
                "processing_errors": [],
                "timestamp": datetime.now().isoformat()
            }
    
    def save_discovery_results(self, results: Dict) -> None:
        """Save discovery results to file."""
        results["timestamp"] = datetime.now().isoformat()
        with open(self.discovery_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Saved discovery results with {len(results['accounts'])} accounts")
    
    async def query_account(self, account_id: str) -> Optional[Dict]:
        """Query account information from SYB API."""
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
        """Process raw account data into the expected format."""
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
    
    async def add_account(self, account_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Add a new account to the monitoring system.
        
        Returns:
            Tuple of (success, message, account_data)
        """
        self.logger.info(f"Adding account: {account_id}")
        
        # Load existing results
        results = self.load_discovery_results()
        
        # Check if account already exists
        if account_id in results["accounts"]:
            return False, f"Account {account_id} already exists", results["accounts"][account_id]
        
        # Query the account
        account_data = await self.query_account(account_id)
        
        if not account_data:
            return False, f"Failed to retrieve account data for {account_id}", None
        
        # Process the account data
        processed_data = self.process_account_data(account_data)
        
        # Add the account
        results["accounts"][account_id] = processed_data
        
        # Save updated results
        self.save_discovery_results(results)
        
        message = f"Successfully added account: {processed_data['name']} with {processed_data['zone_count']} zones"
        self.logger.info(message)
        
        return True, message, processed_data
    
    def remove_account(self, account_id: str) -> Tuple[bool, str]:
        """
        Remove an account from the monitoring system.
        
        Returns:
            Tuple of (success, message)
        """
        self.logger.info(f"Removing account: {account_id}")
        
        # Load existing results
        results = self.load_discovery_results()
        
        # Check if account exists
        if account_id not in results["accounts"]:
            return False, f"Account {account_id} not found"
        
        # Get account name for message
        account_name = results["accounts"][account_id].get("name", "Unknown")
        
        # Remove the account
        del results["accounts"][account_id]
        
        # Save updated results
        self.save_discovery_results(results)
        
        message = f"Successfully removed account: {account_name}"
        self.logger.info(message)
        
        return True, message
    
    def list_accounts(self) -> List[Dict]:
        """Get a list of all accounts with basic info."""
        results = self.load_discovery_results()
        
        accounts = []
        for account_id, account_data in results["accounts"].items():
            accounts.append({
                "id": account_id,
                "name": account_data.get("name", "Unknown"),
                "country": account_data.get("country"),
                "zone_count": account_data.get("zone_count", 0),
                "online_zones": account_data.get("online_zones", 0),
                "user_count": len(account_data.get("users", []))
            })
        
        # Sort by name
        accounts.sort(key=lambda x: x["name"])
        
        return accounts
    
    def get_zone_ids(self) -> List[str]:
        """Get all zone IDs from all accounts."""
        results = self.load_discovery_results()
        
        zone_ids = []
        for account_data in results["accounts"].values():
            for location in account_data.get("locations", []):
                for zone in location.get("zones", []):
                    zone_ids.append(zone["id"])
        
        return zone_ids
    
    async def refresh_account(self, account_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Refresh data for an existing account.
        
        Returns:
            Tuple of (success, message, account_data)
        """
        self.logger.info(f"Refreshing account: {account_id}")
        
        # Load existing results
        results = self.load_discovery_results()
        
        # Check if account exists
        if account_id not in results["accounts"]:
            return False, f"Account {account_id} not found", None
        
        # Query the account
        account_data = await self.query_account(account_id)
        
        if not account_data:
            return False, f"Failed to retrieve updated data for {account_id}", None
        
        # Process the account data
        processed_data = self.process_account_data(account_data)
        
        # Update the account
        results["accounts"][account_id] = processed_data
        
        # Save updated results
        self.save_discovery_results(results)
        
        message = f"Successfully refreshed account: {processed_data['name']}"
        self.logger.info(message)
        
        return True, message, processed_data