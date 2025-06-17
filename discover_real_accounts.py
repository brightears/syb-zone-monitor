#!/usr/bin/env python3
"""Discover the real account names and structure from SYB API."""

import asyncio
import json
import base64
from datetime import datetime

import httpx


async def discover_real_accounts():
    """Discover the actual account structure and names."""
    
    api_token = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
    api_url = "https://api.soundtrackyourbrand.com/v2"
    
    headers = {
        "Authorization": f"Basic {api_token}",
        "Content-Type": "application/json"
    }
    
    # First, get all accounts with their actual business names
    accounts_query = """
    {
        me {
            ... on PublicAPIClient {
                id
                accounts(first: 50) {
                    edges {
                        node {
                            id
                            businessName
                            soundZones(first: 50) {
                                edges {
                                    node {
                                        id
                                        isPaired
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
    
    async with httpx.AsyncClient(timeout=30) as client:
        print("🔍 Discovering Real Account Structure")
        print(f"Timestamp: {datetime.now()}")
        
        try:
            response = await client.post(
                api_url,
                json={"query": accounts_query},
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print("❌ GraphQL Errors:")
                    for error in data["errors"]:
                        print(f"  - {error.get('message', error)}")
                
                if "data" in data and data["data"]:
                    # Extract account data
                    me_data = data["data"].get("me", {})
                    accounts_data = me_data.get("accounts", {})
                    account_edges = accounts_data.get("edges", [])
                    
                    print(f"\n🏨 Found {len(account_edges)} Real Accounts:")
                    
                    account_mapping = {}
                    total_zones = 0
                    
                    for account_edge in account_edges:
                        account = account_edge.get("node", {})
                        account_id = account.get("id")
                        business_name = account.get("businessName", "Unknown").strip()
                        
                        # Get zones for this account
                        zones = account.get("soundZones", {}).get("edges", [])
                        zone_count = len(zones)
                        total_zones += zone_count
                        
                        # Count online/offline
                        online_count = sum(1 for z in zones if z.get("node", {}).get("isPaired"))
                        offline_count = zone_count - online_count
                        
                        print(f"\n📊 Account: {business_name}")
                        print(f"   ID: {account_id}")
                        print(f"   Zones: {zone_count} total ({online_count} online, {offline_count} offline)")
                        
                        # Store mapping
                        account_mapping[account_id] = {
                            "name": business_name,
                            "zone_count": zone_count,
                            "zones": []
                        }
                        
                        # Get detailed zone info
                        for zone_edge in zones:
                            zone = zone_edge.get("node", {})
                            zone_id = zone.get("id")
                            is_paired = zone.get("isPaired")
                            
                            if zone_id:
                                account_mapping[account_id]["zones"].append({
                                    "id": zone_id,
                                    "paired": is_paired
                                })
                    
                    print(f"\n📈 Summary:")
                    print(f"   Total Accounts: {len(account_edges)}")
                    print(f"   Total Zones: {total_zones}")
                    
                    # Now get zone names by querying each zone individually (sample)
                    print(f"\n🔍 Getting Zone Names (sampling first few)...")
                    
                    zone_names = {}
                    sample_count = 0
                    max_samples = 10
                    
                    for account_id, account_info in account_mapping.items():
                        if sample_count >= max_samples:
                            break
                            
                        business_name = account_info["name"]
                        print(f"\n   Zones in {business_name}:")
                        
                        for zone_info in account_info["zones"][:3]:  # First 3 zones per account
                            if sample_count >= max_samples:
                                break
                                
                            zone_id = zone_info["id"]
                            
                            # Query individual zone for name
                            zone_query = f'''
                            query {{
                                soundZone(id: "{zone_id}") {{
                                    id
                                    isPaired
                                }}
                            }}
                            '''
                            
                            try:
                                zone_response = await client.post(
                                    api_url,
                                    json={"query": zone_query},
                                    headers=headers
                                )
                                
                                if zone_response.status_code == 200:
                                    zone_data = zone_response.json()
                                    zone_result = zone_data.get("data", {}).get("soundZone")
                                    
                                    if zone_result:
                                        # Try to get zone name (might not be available in this version)
                                        zone_name = zone_result.get("name", f"Zone_{sample_count}")
                                        is_paired = zone_result.get("isPaired")
                                        
                                        print(f"     - {zone_name} ({'ONLINE' if is_paired else 'OFFLINE'})")
                                        zone_names[zone_id] = zone_name
                                        sample_count += 1
                                        
                            except Exception as e:
                                print(f"     - {zone_id} (Error getting name: {e})")
                                sample_count += 1
                    
                    # Create corrected mapping file
                    corrected_mapping = {
                        "accounts": {},
                        "zones": zone_names,
                        "total_accounts": len(account_edges),
                        "total_zones": total_zones
                    }
                    
                    for account_id, account_info in account_mapping.items():
                        corrected_mapping["accounts"][account_id] = account_info["name"]
                    
                    # Save to file
                    with open("account_mapping.json", "w") as f:
                        json.dump(corrected_mapping, f, indent=2)
                    
                    print(f"\n✅ Account mapping saved to account_mapping.json")
                    print(f"\n🎯 Use this data to fix the dashboard account grouping!")
                    
            else:
                print(f"❌ HTTP {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")


if __name__ == "__main__":
    asyncio.run(discover_real_accounts())