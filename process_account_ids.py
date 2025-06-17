#!/usr/bin/env python3
"""Process a list of account IDs to discover zones and contacts."""

import asyncio
import json
from datetime import datetime
import httpx
from config import Config
import sys


async def process_account_ids(account_ids):
    """Process a list of account IDs to get zones and contacts."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"🔍 Processing {len(account_ids)} Account IDs")
    print(f"Timestamp: {datetime.now()}")
    print("="*80)
    
    all_zones = []
    all_accounts = []
    zone_to_account = {}
    account_contacts = []
    
    # Query to get account details, zones, and users
    query = """
    query GetAccountById($accountId: ID!) {
        node(id: $accountId) {
            ... on Account {
                id
                businessName
                businessType
                country
                createdAt
                access {
                    users(first: 50) {
                        edges {
                            node {
                                id
                                name
                                email
                                companyRole
                            }
                        }
                    }
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
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    async with httpx.AsyncClient() as client:
        for i, account_id in enumerate(account_ids, 1):
            print(f"\n📂 Processing account {i}/{len(account_ids)}")
            print(f"   ID: {account_id}")
            
            variables = {"accountId": account_id}
            
            try:
                response = await client.post(
                    config.syb_api_url,
                    headers=headers,
                    json={"query": query, "variables": variables},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data and "data" in data and data["data"] and data["data"].get("node"):
                        account = data["data"]["node"]
                        account_name = account.get("businessName", "Unknown")
                        
                        print(f"   ✅ {account_name}")
                        print(f"      Type: {account.get('businessType', 'N/A')}")
                        print(f"      Country: {account.get('country', 'N/A')}")
                        
                        # Store account info
                        all_accounts.append({
                            "id": account_id,
                            "name": account_name,
                            "type": account.get("businessType"),
                            "country": account.get("country")
                        })
                        
                        # Process users/contacts
                        users = account.get("access", {}).get("users", {}).get("edges", [])
                        if users:
                            print(f"      Users: {len(users)}")
                            contacts = []
                            for user_edge in users:
                                user = user_edge["node"]
                                contacts.append({
                                    "type": "active",
                                    "name": user.get("name", ""),
                                    "email": user.get("email", ""),
                                    "role": user.get("companyRole")
                                })
                            
                            account_contacts.append({
                                "business_name": account_name,
                                "account_id": account_id,
                                "active_users": len(users),
                                "pending_users": 0,
                                "contacts": contacts
                            })
                        
                        # Process zones
                        locations = account.get("locations", {}).get("edges", [])
                        zone_count = 0
                        
                        for location_edge in locations:
                            location = location_edge["node"]
                            location_name = location["name"]
                            
                            zones = location["soundZones"]["edges"]
                            for zone_edge in zones:
                                zone = zone_edge["node"]
                                zone_id = zone["id"]
                                zone_name = zone["name"]
                                
                                all_zones.append(zone_id)
                                zone_to_account[zone_id] = {
                                    "account_id": account_id,
                                    "account_name": account_name,
                                    "location_name": location_name,
                                    "zone_name": zone_name
                                }
                                zone_count += 1
                                
                        print(f"      Zones: {zone_count}")
                        
                    else:
                        print(f"   ❌ No access to this account")
                        
                else:
                    print(f"   ❌ HTTP Error: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                
        print(f"\n📊 Summary:")
        print(f"   Total accounts processed: {len(account_ids)}")
        print(f"   Successful accounts: {len(all_accounts)}")
        print(f"   Total zones discovered: {len(all_zones)}")
        print(f"   Accounts with contacts: {len(account_contacts)}")
        
        # Save all discovered data
        timestamp = datetime.now().isoformat()
        
        # Save zone data
        with open('account_id_zones_discovered.json', 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "total_accounts": len(all_accounts),
                "total_zones": len(all_zones),
                "accounts": all_accounts,
                "zone_ids": all_zones,
                "zone_details": zone_to_account
            }, f, indent=2)
        print(f"\n💾 Saved zone data to account_id_zones_discovered.json")
        
        # Save contact data
        with open('account_id_contacts_discovered.json', 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "analysis": {
                    "total_accounts": len(all_accounts),
                    "accounts_with_contacts": len(account_contacts),
                    "total_contacts": sum(len(a["contacts"]) for a in account_contacts)
                },
                "accounts_with_contacts": account_contacts
            }, f, indent=2)
        print(f"💾 Saved contact data to account_id_contacts_discovered.json")
        
        # Save zone IDs list
        with open('account_id_zone_list.txt', 'w') as f:
            f.write(','.join(all_zones))
        print(f"💾 Saved zone IDs to account_id_zone_list.txt")


if __name__ == "__main__":
    # Test with Hilton Pattaya
    test_account_ids = [
        "QWNjb3VudCwsMXN4N242NTZyeTgv"  # Hilton Pattaya
    ]
    
    # Check if account IDs were provided as command line argument
    if len(sys.argv) > 1:
        # Read account IDs from file
        with open(sys.argv[1], 'r') as f:
            account_ids = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(account_ids)} account IDs from {sys.argv[1]}")
    else:
        account_ids = test_account_ids
        print("Using test account ID (Hilton Pattaya)")
    
    asyncio.run(process_account_ids(account_ids))