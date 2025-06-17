#!/usr/bin/env python3
"""Quick test of zone status fields."""

import asyncio
import json
import httpx


async def quick_test():
    """Quick test of zone status fields."""
    
    api_token = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
    api_url = "https://api.soundtrackyourbrand.com/v2"
    
    headers = {
        "Authorization": f"Basic {api_token}",
        "Content-Type": "application/json"
    }
    
    # Test if the key status fields work
    test_query = """
    {
        me {
            ... on PublicAPIClient {
                accounts(first: 1) {
                    edges {
                        node {
                            soundZones(first: 2) {
                                edges {
                                    node {
                                        id
                                        name
                                        isPaired
                                        online
                                        status {
                                            canPlay
                                            isPaid
                                        }
                                        subscription {
                                            status
                                            isActive
                                            isPaid
                                        }
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
            }
        }
    }
    """
    
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            response = await client.post(
                api_url,
                json={"query": test_query},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print("❌ GraphQL Errors:")
                    for error in data["errors"]:
                        print(f"  - {error.get('message', error)}")
                
                if "data" in data and data["data"]:
                    print("✅ Success! Sample zone data:")
                    print(json.dumps(data["data"], indent=2))
                else:
                    print("❌ No data returned")
            else:
                print(f"❌ HTTP {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Request failed: {e}")


if __name__ == "__main__":
    asyncio.run(quick_test())