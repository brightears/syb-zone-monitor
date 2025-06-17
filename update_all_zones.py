#!/usr/bin/env python3
"""Update .env to monitor ALL zones from ALL accounts."""

import asyncio
import json
from datetime import datetime

import httpx


async def get_all_zones():
    """Get ALL zones from ALL accounts."""
    
    api_token = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
    api_url = "https://api.soundtrackyourbrand.com/v2"
    
    headers = {
        "Authorization": f"Basic {api_token}",
        "Content-Type": "application/json"
    }
    
    # Query to get ALL zones from ALL accounts
    query = """
    {
        me {
            ... on PublicAPIClient {
                accounts(first: 100) {
                    edges {
                        node {
                            id
                            businessName
                            soundZones(first: 100) {
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
    
    async with httpx.AsyncClient(timeout=60) as client:
        print("🔍 Getting ALL zones from ALL accounts...")
        print(f"Timestamp: {datetime.now()}")
        
        try:
            response = await client.post(
                api_url,
                json={"query": query},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print("❌ GraphQL Errors:")
                    for error in data["errors"]:
                        print(f"  - {error.get('message', error)}")
                
                if "data" in data and data["data"]:
                    # Extract all zone IDs
                    me_data = data["data"].get("me", {})
                    accounts_data = me_data.get("accounts", {})
                    account_edges = accounts_data.get("edges", [])
                    
                    all_zone_ids = []
                    account_summary = []
                    total_zones = 0
                    total_online = 0
                    total_offline = 0
                    
                    for account_edge in account_edges:
                        account = account_edge.get("node", {})
                        account_name = account.get("businessName", "Unknown")
                        zones = account.get("soundZones", {}).get("edges", [])
                        
                        account_zones = 0
                        account_online = 0
                        account_offline = 0
                        
                        for zone_edge in zones:
                            zone = zone_edge.get("node", {})
                            zone_id = zone.get("id")
                            is_paired = zone.get("isPaired")
                            
                            if zone_id:
                                all_zone_ids.append(zone_id)
                                account_zones += 1
                                total_zones += 1
                                
                                if is_paired:
                                    account_online += 1
                                    total_online += 1
                                else:
                                    account_offline += 1
                                    total_offline += 1
                        
                        if account_zones > 0:
                            account_summary.append({
                                "name": account_name,
                                "zones": account_zones,
                                "online": account_online,
                                "offline": account_offline
                            })
                    
                    print(f"\n🎯 DISCOVERY COMPLETE!")
                    print(f"   Total Accounts: {len(account_summary)}")
                    print(f"   Total Zones: {total_zones}")
                    print(f"   Online: {total_online}")
                    print(f"   Offline: {total_offline}")
                    
                    print(f"\n📊 Top Accounts by Zone Count:")
                    sorted_accounts = sorted(account_summary, key=lambda x: x['zones'], reverse=True)
                    for i, account in enumerate(sorted_accounts[:10]):
                        status = f"{account['online']}/{account['zones']} online"
                        print(f"   {i+1:2d}. {account['name']}: {status}")
                    
                    if len(sorted_accounts) > 10:
                        print(f"   ... and {len(sorted_accounts) - 10} more accounts")
                    
                    # Update .env file
                    print(f"\n🔧 Updating .env file...")
                    
                    try:
                        # Read current .env
                        with open('.env', 'r') as f:
                            lines = f.readlines()
                        
                        # Update ZONE_IDS line
                        updated_lines = []
                        for line in lines:
                            if line.startswith('ZONE_IDS='):
                                zone_ids_str = ','.join(all_zone_ids)
                                updated_lines.append(f'ZONE_IDS={zone_ids_str}\n')
                                print(f"✅ Updated ZONE_IDS with {len(all_zone_ids)} zones")
                            else:
                                updated_lines.append(line)
                        
                        # Write back to .env
                        with open('.env', 'w') as f:
                            f.writelines(updated_lines)
                        
                        print(f"✅ .env file updated successfully!")
                        print(f"\n🚀 Your monitor will now track ALL {total_zones} zones across {len(account_summary)} accounts!")
                        
                        # Save summary for reference
                        summary_data = {
                            "timestamp": datetime.now().isoformat(),
                            "total_accounts": len(account_summary),
                            "total_zones": total_zones,
                            "total_online": total_online,
                            "total_offline": total_offline,
                            "accounts": sorted_accounts,
                            "zone_count": len(all_zone_ids)
                        }
                        
                        with open("zones_summary.json", "w") as f:
                            json.dump(summary_data, f, indent=2)
                        
                        print(f"📄 Summary saved to zones_summary.json")
                        
                    except Exception as e:
                        print(f"❌ Failed to update .env file: {e}")
                        print(f"\n⚠️  Manual update needed:")
                        print(f"   Add this to your .env file:")
                        print(f"   ZONE_IDS={','.join(all_zone_ids[:5])}...") # Show first 5 as sample
                        
            else:
                print(f"❌ HTTP {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")


if __name__ == "__main__":
    asyncio.run(get_all_zones())