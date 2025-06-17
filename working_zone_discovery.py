#!/usr/bin/env python3
"""Working zone discovery script with proper pagination."""

import asyncio
import json
from datetime import datetime

import httpx


async def discover_zones():
    """Discover zones with proper GraphQL connection handling."""
    
    api_token = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
    api_url = "https://api.soundtrackyourbrand.com/v2"
    
    headers = {
        "Authorization": f"Basic {api_token}",
        "Content-Type": "application/json"
    }
    
    # Query with proper pagination
    query = """
    {
        me {
            ... on PublicAPIClient {
                id
                accounts(first: 10) {
                    edges {
                        node {
                            id
                            businessName
                            soundZones(first: 20) {
                                edges {
                                    node {
                                        id
                                        isPaired
                                    }
                                }
                            }
                            locations(first: 10) {
                                edges {
                                    node {
                                        id
                                        soundZones(first: 20) {
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
            }
        }
    }
    """
    
    async with httpx.AsyncClient(timeout=30) as client:
        print("🔍 Discovering zones...")
        
        try:
            response = await client.post(
                api_url,
                json={"query": query},
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
                    print("✅ Raw Response:")
                    print(json.dumps(data["data"], indent=2))
                    
                    # Extract zone information
                    me_data = data["data"].get("me", {})
                    accounts_data = me_data.get("accounts", {})
                    account_edges = accounts_data.get("edges", [])
                    
                    all_zone_ids = []
                    
                    print(f"\n🎯 Found {len(account_edges)} account(s):")
                    
                    for account_edge in account_edges:
                        account = account_edge.get("node", {})
                        account_id = account.get("id")
                        account_name = account.get("businessName", "Unknown")
                        
                        print(f"\nAccount: {account_name} ({account_id})")
                        
                        # Get zones directly from account
                        account_zones = account.get("soundZones", {}).get("edges", [])
                        print(f"  Direct zones: {len(account_zones)}")
                        
                        for zone_edge in account_zones:
                            zone = zone_edge.get("node", {})
                            zone_id = zone.get("id")
                            is_paired = zone.get("isPaired")
                            
                            if zone_id:
                                print(f"    Zone: {zone_id} (Paired: {is_paired})")
                                all_zone_ids.append(zone_id)
                        
                        # Get zones from locations
                        locations = account.get("locations", {}).get("edges", [])
                        print(f"  Locations: {len(locations)}")
                        
                        for location_edge in locations:
                            location = location_edge.get("node", {})
                            location_id = location.get("id")
                            location_zones = location.get("soundZones", {}).get("edges", [])
                            
                            print(f"    Location {location_id}: {len(location_zones)} zones")
                            
                            for zone_edge in location_zones:
                                zone = zone_edge.get("node", {})
                                zone_id = zone.get("id")
                                is_paired = zone.get("isPaired")
                                
                                if zone_id and zone_id not in all_zone_ids:
                                    print(f"      Zone: {zone_id} (Paired: {is_paired})")
                                    all_zone_ids.append(zone_id)
                    
                    if all_zone_ids:
                        print(f"\n🎉 ALL ZONE IDS: {','.join(all_zone_ids)}")
                        
                        # Test a zone query
                        await test_zone_monitoring(client, api_url, headers, all_zone_ids[0])
                        
                        # Update .env file
                        await update_env_file(all_zone_ids)
                    else:
                        print("\n❌ No zones found in this account")
            
            else:
                print(f"❌ HTTP {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")


async def test_zone_monitoring(client, api_url, headers, zone_id):
    """Test the zone monitoring query that our app will use."""
    
    print(f"\n=== Testing Zone Monitoring for {zone_id} ===")
    
    query = f'''
    query GetZoneStatus($zoneId: ID!) {{
        soundZone(id: $zoneId) {{
            id
            isPaired
        }}
    }}
    '''
    
    variables = {"zoneId": zone_id}
    
    try:
        response = await client.post(
            api_url,
            json={"query": query, "variables": variables},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "errors" in data:
                print("❌ GraphQL Errors:")
                for error in data["errors"]:
                    print(f"  - {error.get('message', error)}")
            
            if "data" in data and data["data"]:
                print("✅ Zone Monitoring Query Works!")
                print(json.dumps(data["data"], indent=2))
                
                zone_data = data["data"].get("soundZone")
                if zone_data:
                    is_paired = zone_data.get("isPaired")
                    print(f"\n🎵 Zone {zone_id} is {'ONLINE' if is_paired else 'OFFLINE'}")
        
    except Exception as e:
        print(f"❌ Zone monitoring test failed: {e}")


async def update_env_file(zone_ids):
    """Update the .env file with discovered zone IDs."""
    
    print(f"\n=== Updating .env file ===")
    
    try:
        # Read current .env
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        # Update ZONE_IDS line
        updated_lines = []
        for line in lines:
            if line.startswith('ZONE_IDS='):
                updated_lines.append(f'ZONE_IDS={",".join(zone_ids)}\n')
                print(f"✅ Updated ZONE_IDS to: {','.join(zone_ids)}")
            else:
                updated_lines.append(line)
        
        # Write back to .env
        with open('.env', 'w') as f:
            f.writelines(updated_lines)
        
        print("✅ .env file updated successfully!")
        
    except Exception as e:
        print(f"❌ Failed to update .env file: {e}")


if __name__ == "__main__":
    print("SYB Working Zone Discovery")
    print(f"Timestamp: {datetime.now()}")
    
    asyncio.run(discover_zones())