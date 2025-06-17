#!/usr/bin/env python3
"""Explore the SYB GraphQL schema to find available fields."""

import asyncio
import json
from datetime import datetime

import httpx


async def explore_schema():
    """Explore the GraphQL schema to find available queries."""
    
    api_token = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
    api_url = "https://api.soundtrackyourbrand.com/v2"
    
    headers = {
        "Authorization": f"Basic {api_token}",
        "Content-Type": "application/json"
    }
    
    # GraphQL introspection query to discover schema
    introspection_query = """
    query IntrospectionQuery {
        __schema {
            queryType {
                name
                fields {
                    name
                    description
                    type {
                        name
                        kind
                    }
                }
            }
        }
    }
    """
    
    # Also try some common queries based on the docs
    test_queries = [
        {
            "name": "Introspection",
            "query": introspection_query
        },
        {
            "name": "Me/Viewer",
            "query": "{ me { __typename } }"
        },
        {
            "name": "Viewer Fields",
            "query": """
            {
                me {
                    __typename
                    ... on Viewer {
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
            "name": "Root Query Fields",
            "query": "{ __type(name: \"Query\") { fields { name description } } }"
        },
        {
            "name": "Test Sound Zone by ID",
            "query": 'query { soundZone(id: "test") { id name } }'
        },
        {
            "name": "Test Now Playing",
            "query": 'query { nowPlaying(soundZone: "test") { track { name } } }'
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
                        
                        # Special handling for introspection
                        if query_info["name"] == "Introspection" and data["data"]:
                            schema_data = data["data"].get("__schema", {})
                            query_type = schema_data.get("queryType", {})
                            fields = query_type.get("fields", [])
                            
                            print("\n🔍 Available Query Fields:")
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


if __name__ == "__main__":
    print("SYB GraphQL Schema Explorer")
    print(f"Timestamp: {datetime.now()}")
    
    asyncio.run(explore_schema())