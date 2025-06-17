#!/usr/bin/env python3
"""Discover what data is available through the PublicAPIClient."""

import asyncio
import json
from datetime import datetime

import httpx


async def discover_client_data():
    """Explore what data we can access as a PublicAPIClient."""
    
    api_token = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
    api_url = "https://api.soundtrackyourbrand.com/v2"
    
    headers = {
        "Authorization": f"Basic {api_token}",
        "Content-Type": "application/json"
    }
    
    # Explore PublicAPIClient fields
    test_queries = [
        {
            "name": "PublicAPIClient Type Info",
            "query": "{ __type(name: \"PublicAPIClient\") { fields { name description type { name kind } } } }"
        },
        {
            "name": "Me with all possible fields",
            "query": """
            {
                me {
                    __typename
                    ... on PublicAPIClient {
                        id
                        name
                        email
                        accounts {
                            id
                            name
                        }
                    }
                }
            }
            """
        },
        {
            "name": "Try different me fields",
            "query": """
            {
                me {
                    ... on PublicAPIClient {
                        __typename
                        id
                        description
                        createdAt
                        updatedAt
                    }
                }
            }
            """
        }
    ]
    
    async with httpx.AsyncClient(timeout=30) as client:
        for query_info in test_queries:
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
                        
                        # Special handling for type info
                        if "PublicAPIClient Type Info" in query_info["name"] and data["data"]:
                            type_data = data["data"].get("__type", {})
                            fields = type_data.get("fields", [])
                            
                            print("\n🔍 Available PublicAPIClient Fields:")
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
        
        # Since we can't get accounts through me, let's try the individual queries
        print("\n=== Testing Individual Queries ===")
        
        # Test if we can get specific data by trying some IDs
        individual_queries = [
            {
                "name": "Test Account Query", 
                "query": 'query { account(id: "1") { id name } }'
            },
            {
                "name": "Test Location Query",
                "query": 'query { location(id: "1") { id name } }'
            },
            {
                "name": "Test Device Query",
                "query": 'query { device(id: "1") { id name } }'
            }
        ]
        
        for query_info in individual_queries:
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
                        for error in data["errors"]:
                            print(f"❌ {error.get('message', error)}")
                    
                    if "data" in data and data["data"]:
                        print(f"✅ {json.dumps(data['data'])}")
                        
            except Exception as e:
                print(f"❌ {e}")


if __name__ == "__main__":
    print("SYB PublicAPIClient Data Discovery")
    print(f"Timestamp: {datetime.now()}")
    
    asyncio.run(discover_client_data())