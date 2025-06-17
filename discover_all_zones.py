#!/usr/bin/env python3
"""Discover ALL zones from ALL accounts accessible via the API."""

import asyncio
import json
from datetime import datetime
import httpx
from config import Config
import base64


async def discover_all_zones():
    """Discover all zones from all accounts."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Discovering ALL zones from ALL accounts")
    print(f"Timestamp: {datetime.now()}")
    print("="*80)
    
    # First, get all accounts
    accounts_query = """
    {
        me {
            ... on PublicAPIClient {
                accounts(first: 200) {
                    edges {
                        node {
                            id
                            businessName
                            businessType
                            country
                        }
                    }
                }
            }
        }
    }
    """
    
    all_zones = []
    zone_to_account = {}
    
    async with httpx.AsyncClient() as client:
        try:
            # Get all accounts
            response = await client.post(
                config.syb_api_url,
                headers=headers,
                json={"query": accounts_query},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data and "data" in data and data["data"]["me"]:
                    accounts = data["data"]["me"]["accounts"]["edges"]
                    print(f"\n✅ Found {len(accounts)} accounts")
                    
                    # Now get zones for each account
                    for i, account_edge in enumerate(accounts, 1):
                        account = account_edge["node"]
                        account_id = account["id"]
                        account_name = account["businessName"]
                        
                        print(f"\n📂 Account {i}/{len(accounts)}: {account_name}")
                        print(f"   ID: {account_id}")
                        
                        # Query zones for this specific account
                        zones_query = """
                        query GetAccountZones($accountId: ID!) {
                            node(id: $accountId) {
                                ... on Account {
                                    id
                                    businessName
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
                        
                        try:
                            zone_response = await client.post(
                                config.syb_api_url,
                                headers=headers,
                                json={"query": zones_query, "variables": {"accountId": account_id}},
                                timeout=30.0
                            )
                            
                            if zone_response.status_code == 200:
                                zone_data = zone_response.json()
                                
                                if zone_data and "data" in zone_data and zone_data["data"]["node"]:
                                    locations = zone_data["data"]["node"]["locations"]["edges"]
                                    
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
                                            
                                            print(f"      ✓ {location_name} - {zone_name}")
                                            
                                    print(f"   Total zones: {len([z for z in zone_to_account.values() if z['account_id'] == account_id])}")
                                    
                        except Exception as e:
                            print(f"   ❌ Error querying zones: {e}")
                            
                    print(f"\n📊 Summary:")
                    print(f"   Total accounts: {len(accounts)}")
                    print(f"   Total zones discovered: {len(all_zones)}")
                    
                    # Save the zone list
                    with open('all_zones_discovered.json', 'w') as f:
                        json.dump({
                            "timestamp": datetime.now().isoformat(),
                            "total_zones": len(all_zones),
                            "total_accounts": len(accounts),
                            "zone_ids": all_zones,
                            "zone_details": zone_to_account
                        }, f, indent=2)
                    
                    print(f"\n💾 Saved {len(all_zones)} zones to all_zones_discovered.json")
                    
                    # Also create a simple comma-separated list for easy use
                    with open('zone_ids_list.txt', 'w') as f:
                        f.write(','.join(all_zones))
                    
                    print(f"💾 Saved comma-separated zone IDs to zone_ids_list.txt")
                    
                    # Check if Hilton Pattaya is included
                    hilton_zones = [z for z in zone_to_account.values() if "Hilton Pattaya" in z["account_name"]]
                    if hilton_zones:
                        print(f"\n✅ Found {len(hilton_zones)} Hilton Pattaya zones:")
                        for zone in hilton_zones:
                            print(f"   - {zone['zone_name']} ({zone['location_name']})")
                    else:
                        print(f"\n❌ No Hilton Pattaya zones found")
                    
                else:
                    print("❌ No account data returned")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error discovering zones: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(discover_all_zones())