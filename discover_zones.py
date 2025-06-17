#!/usr/bin/env python3
"""Script to discover available zones in the SYB account."""

import asyncio
import json
import sys
from datetime import datetime

import httpx


async def discover_zones():
    """Discover and list all available zones in the account."""
    api_key = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
    api_url = "https://api.soundtrackyourbrand.com/v2"
    
    # First, let's check what we can access with this API key
    queries = [
        # Get current user info
        {
            "name": "Current User",
            "query": """
            query {
                me {
                    id
                    name
                    email
                }
            }
            """
        },
        # Get accounts
        {
            "name": "Accounts",
            "query": """
            query {
                accounts {
                    id
                    name
                    locations {
                        id
                        name
                        soundZones {
                            id
                            name
                            isPaired
                        }
                    }
                }
            }
            """
        },
        # Alternative: try to get sound zones directly
        {
            "name": "Sound Zones Direct",
            "query": """
            query {
                soundZones {
                    id
                    name
                    isPaired
                }
            }
            """
        }
    ]
    
    headers = {"Authorization": f"Basic {api_key}"}
    
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
                    print(f"Response: {json.dumps(data, indent=2)}")
                    
                    if "errors" in data:
                        print(f"GraphQL Errors: {data['errors']}")
                    
                else:
                    print(f"HTTP Error: {response.text}")
                    
            except Exception as e:
                print(f"Request failed: {e}")
            
            print("-" * 50)


if __name__ == "__main__":
    print("SYB Zone Discovery Tool")
    print(f"Timestamp: {datetime.now()}")
    
    try:
        asyncio.run(discover_zones())
    except KeyboardInterrupt:
        print("\nDiscovery cancelled by user")
    except Exception as e:
        print(f"Discovery failed: {e}")
        sys.exit(1)