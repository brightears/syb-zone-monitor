#!/usr/bin/env python3
"""Find actual zones available in the test account."""

import asyncio
import json
from datetime import datetime

import httpx


async def find_zones():
    """Find all available zones in the account."""
    
    api_token = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
    api_url = "https://api.soundtrackyourbrand.com/v2"
    
    headers = {
        "Authorization": f"Basic {api_token}",
        "Content-Type": "application/json"
    }
    
    # First, explore the accounts connection
    queries = [
        {
            "name": "Get Client ID",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        id
                    }
                }
            }
            """
        },
        {
            "name": "Get Accounts Connection",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        accounts {
                            edges {
                                node {
                                    id
                                }
                            }
                        }
                    }
                }
            }
            """
        },
        {
            "name": "Explore Account Type",
            "query": "{ __type(name: \"Account\") { fields { name description type { name kind } } } }"
        }
    ]
    
    async with httpx.AsyncClient(timeout=30) as client:
        for query_info in queries:
            print(f"\n=== {query_info['name']} ===")
            
            try:
                response = await client.post(
                    api_url,
                    json={"query": query_info["query"]},
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
                        print("✅ Success! Data:")
                        print(json.dumps(data["data"], indent=2))
                        
                        # Extract account IDs for next query
                        if "accounts" in query_info["name"].lower() and data["data"]:
                            me_data = data["data"].get("me", {})
                            accounts_data = me_data.get("accounts", {})
                            edges = accounts_data.get("edges", [])
                            
                            if edges:
                                print("\n🎯 Found Account IDs:")
                                account_ids = []
                                for edge in edges:
                                    account_id = edge.get("node", {}).get("id")
                                    if account_id:
                                        print(f"  - {account_id}")
                                        account_ids.append(account_id)
                                
                                # Now query each account for details
                                await query_account_details(client, api_url, headers, account_ids)
                        
                        # Show Account type fields
                        if "Account Type" in query_info["name"] and data["data"]:
                            type_data = data["data"].get("__type", {})
                            fields = type_data.get("fields", [])
                            
                            print("\n🔍 Available Account Fields:")
                            for field in fields:
                                field_name = field.get("name", "")
                                field_desc = field.get("description", "")
                                field_type = field.get("type", {}).get("name", "")
                                print(f"  - {field_name}: {field_type} - {field_desc}")
                    
                else:
                    print(f"❌ HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    
            except Exception as e:
                print(f"❌ Request failed: {e}")
            
            print("-" * 60)


async def query_account_details(client, api_url, headers, account_ids):
    """Query details for each account to find zones."""
    
    for account_id in account_ids:
        print(f"\n=== Account {account_id} Details ===")
        
        # Try different account queries
        account_queries = [
            {
                "name": f"Account {account_id} Basic",
                "query": f'query {{ account(id: "{account_id}") {{ id }} }}'
            },
            {
                "name": f"Account {account_id} with Locations",
                "query": f'''
                query {{
                    account(id: "{account_id}") {{
                        id
                        locations {{
                            edges {{
                                node {{
                                    id
                                    soundZones {{
                                        edges {{
                                            node {{
                                                id
                                                isPaired
                                            }}
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
                '''
            }
        ]
        
        for query_info in account_queries:
            print(f"\n--- {query_info['name']} ---")
            
            try:
                response = await client.post(
                    api_url,
                    json={"query": query_info["query"]},
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "errors" in data:
                        print("❌ GraphQL Errors:")
                        for error in data["errors"]:
                            print(f"  - {error.get('message', error)}")
                    
                    if "data" in data and data["data"]:
                        print("✅ Success! Data:")
                        print(json.dumps(data["data"], indent=2))
                        
                        # Extract zone information
                        account_data = data["data"].get("account")
                        if account_data and "locations" in account_data:
                            locations = account_data.get("locations", {}).get("edges", [])
                            
                            print(f"\n🎯 Found Zones in Account {account_id}:")
                            zone_ids = []
                            
                            for location_edge in locations:
                                location = location_edge.get("node", {})
                                location_id = location.get("id")
                                
                                zones = location.get("soundZones", {}).get("edges", [])
                                for zone_edge in zones:
                                    zone = zone_edge.get("node", {})
                                    zone_id = zone.get("id")
                                    is_paired = zone.get("isPaired")
                                    
                                    if zone_id:
                                        print(f"  - Zone ID: {zone_id}, Paired: {is_paired}")
                                        zone_ids.append(zone_id)
                            
                            if zone_ids:
                                print(f"\n🎉 ZONE IDS FOR CONFIG: {','.join(zone_ids)}")
                                
                                # Test querying one of the zones directly
                                await test_zone_query(client, api_url, headers, zone_ids[0])
                
                else:
                    print(f"❌ HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    
            except Exception as e:
                print(f"❌ Request failed: {e}")


async def test_zone_query(client, api_url, headers, zone_id):
    """Test querying a specific zone."""
    
    print(f"\n=== Testing Zone Query for {zone_id} ===")
    
    query = f'''
    query {{
        soundZone(id: "{zone_id}") {{
            id
            isPaired
        }}
    }}
    '''
    
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
                print("✅ Zone Query Success!")
                print(json.dumps(data["data"], indent=2))
        
    except Exception as e:
        print(f"❌ Zone query failed: {e}")


if __name__ == "__main__":
    print("SYB Zone Discovery")
    print(f"Timestamp: {datetime.now()}")
    
    asyncio.run(find_zones())