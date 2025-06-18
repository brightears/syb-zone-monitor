#!/usr/bin/env python3
"""Check if there's a specific field for app update required status."""

import asyncio
import json
import httpx

async def check_zone_details():
    """Check detailed zone information for app update status."""
    
    api_token = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNHeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
    api_url = "https://api.soundtrackyourbrand.com/v2"
    
    headers = {
        "Authorization": f"Basic {api_token}",
        "Content-Type": "application/json"
    }
    
    # Test the specific zone mentioned by the user
    zone_id = "U291bmRab25lLCwxbjhvcmV5NWthby9Mb2NhdGlvbiwsMWloNjg1MHVtODAvQWNjb3VudCwsMTh1ZHBmbnRubmsv"
    account_id = "QWNjb3VudCwsMTh1ZHBmbnRubmsv"
    
    # Try a comprehensive query to see all available fields
    query = """
    query GetZoneDetails($zoneId: ID!) {
        soundZone(id: $zoneId) {
            id
            name
            isPaired
            online
            status {
                __typename
            }
            device {
                id
                name
                softwareVersion
                platform
                osVersion
                type
                model
                appVersion
                needsUpdate
                updateRequired
                appUpdateRequired
                requiresUpdate
            }
            subscription {
                isActive
                state
                status
            }
            location {
                id
                name
            }
            account {
                id
                businessName
            }
        }
    }
    """
    
    async with httpx.AsyncClient(timeout=30) as client:
        print(f"Checking zone: {zone_id}")
        print("=" * 60)
        
        try:
            response = await client.post(
                api_url,
                json={"query": query, "variables": {"zoneId": zone_id}},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print("GraphQL Errors:")
                    for error in data["errors"]:
                        print(f"  - {error.get('message', error)}")
                
                if "data" in data and data["data"]:
                    zone_data = data["data"].get("soundZone")
                    if zone_data:
                        print("Zone Data:")
                        print(json.dumps(zone_data, indent=2))
                        
                        # Check if there's any field that indicates app update required
                        device = zone_data.get("device", {})
                        if device:
                            print("\nDevice fields available:")
                            for key, value in device.items():
                                if value is not None:
                                    print(f"  - {key}: {value}")
                    else:
                        print("No zone data returned")
            else:
                print(f"HTTP {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_zone_details())