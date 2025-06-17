#!/usr/bin/env python3
"""Explore the SoundZone schema to find all available fields."""

import asyncio
import json
from datetime import datetime

import httpx


async def explore_soundzone_schema():
    """Explore what fields are available on the SoundZone type."""
    
    api_token = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
    api_url = "https://api.soundtrackyourbrand.com/v2"
    
    headers = {
        "Authorization": f"Basic {api_token}",
        "Content-Type": "application/json"
    }
    
    # First, let's get the SoundZone type schema
    introspection_query = """
    query {
        __type(name: "SoundZone") {
            name
            kind
            description
            fields {
                name
                description
                type {
                    name
                    kind
                    ofType {
                        name
                        kind
                    }
                }
            }
        }
    }
    """
    
    # Also check what's available on the Device type
    device_introspection_query = """
    query {
        __type(name: "Device") {
            name
            kind
            description
            fields {
                name
                description
                type {
                    name
                    kind
                    ofType {
                        name
                        kind
                    }
                }
            }
        }
    }
    """
    
    async with httpx.AsyncClient(timeout=30) as client:
        print("🔍 Exploring SoundZone schema...")
        
        # Explore SoundZone type
        try:
            response = await client.post(
                api_url,
                json={"query": introspection_query},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print("❌ GraphQL Errors:")
                    for error in data["errors"]:
                        print(f"  - {error.get('message', error)}")
                
                if "data" in data and data["data"]:
                    type_info = data["data"].get("__type")
                    if type_info:
                        print(f"\n✅ SoundZone Type Found!")
                        print(f"Description: {type_info.get('description', 'No description')}")
                        
                        fields = type_info.get("fields", [])
                        print(f"\n🔍 Available SoundZone Fields ({len(fields)} total):")
                        
                        for field in fields:
                            field_name = field.get("name", "")
                            field_desc = field.get("description", "")
                            field_type = field.get("type", {})
                            
                            type_info_str = format_type_info(field_type)
                            
                            print(f"  - {field_name}: {type_info_str}")
                            if field_desc:
                                print(f"    Description: {field_desc}")
                        
                        # Let's also find fields that might be relevant to device status
                        relevant_fields = []
                        for field in fields:
                            field_name = field.get("name", "").lower()
                            if any(keyword in field_name for keyword in [
                                'pair', 'connect', 'online', 'offline', 'status', 
                                'device', 'subscription', 'account', 'active'
                            ]):
                                relevant_fields.append(field)
                        
                        if relevant_fields:
                            print(f"\n🎯 Potentially Relevant Fields for Status:")
                            for field in relevant_fields:
                                field_name = field.get("name", "")
                                field_desc = field.get("description", "")
                                field_type = field.get("type", {})
                                type_info_str = format_type_info(field_type)
                                print(f"  - {field_name}: {type_info_str}")
                                if field_desc:
                                    print(f"    Description: {field_desc}")
            
            print("\n" + "="*60)
            
        except Exception as e:
            print(f"❌ SoundZone schema request failed: {e}")
        
        # Explore Device type
        try:
            response = await client.post(
                api_url,
                json={"query": device_introspection_query},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and data["data"]:
                    type_info = data["data"].get("__type")
                    if type_info:
                        print(f"\n✅ Device Type Found!")
                        print(f"Description: {type_info.get('description', 'No description')}")
                        
                        fields = type_info.get("fields", [])
                        print(f"\n🔍 Available Device Fields ({len(fields)} total):")
                        
                        for field in fields:
                            field_name = field.get("name", "")
                            field_desc = field.get("description", "")
                            field_type = field.get("type", {})
                            
                            type_info_str = format_type_info(field_type)
                            
                            print(f"  - {field_name}: {type_info_str}")
                            if field_desc:
                                print(f"    Description: {field_desc}")
            
        except Exception as e:
            print(f"❌ Device schema request failed: {e}")


def format_type_info(type_obj):
    """Format GraphQL type information for display."""
    if not type_obj:
        return "Unknown"
    
    kind = type_obj.get("kind", "")
    name = type_obj.get("name")
    
    if kind == "NON_NULL":
        of_type = type_obj.get("ofType", {})
        return f"{format_type_info(of_type)}!"
    elif kind == "LIST":
        of_type = type_obj.get("ofType", {})
        return f"[{format_type_info(of_type)}]"
    elif name:
        return name
    else:
        return kind


async def test_real_zone():
    """Test with a real zone ID to see what data we can get."""
    
    api_token = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNHeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
    api_url = "https://api.soundtrackyourbrand.com/v2"
    
    headers = {
        "Authorization": f"Basic {api_token}",
        "Content-Type": "application/json"
    }
    
    # First get a zone ID from working discovery
    get_zone_query = """
    {
        me {
            ... on PublicAPIClient {
                accounts(first: 1) {
                    edges {
                        node {
                            soundZones(first: 1) {
                                edges {
                                    node {
                                        id
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
        print("\n🔍 Getting a real zone ID for testing...")
        
        try:
            response = await client.post(
                api_url,
                json={"query": get_zone_query},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract a zone ID
                me_data = data.get("data", {}).get("me", {})
                accounts = me_data.get("accounts", {}).get("edges", [])
                if accounts:
                    zones = accounts[0].get("node", {}).get("soundZones", {}).get("edges", [])
                    if zones:
                        zone_id = zones[0].get("node", {}).get("id")
                        
                        if zone_id:
                            print(f"✅ Found zone ID: {zone_id}")
                            await test_zone_fields(client, api_url, headers, zone_id)
                        else:
                            print("❌ No zone ID found")
                    else:
                        print("❌ No zones found")
                else:
                    print("❌ No accounts found")
            
        except Exception as e:
            print(f"❌ Zone discovery failed: {e}")


async def test_zone_fields(client, api_url, headers, zone_id):
    """Test a comprehensive query on a real zone to see what data is available."""
    
    print(f"\n🔍 Testing comprehensive zone query on {zone_id}...")
    
    # Comprehensive test query with many potential fields
    test_query = """
    query GetZoneDetails($zoneId: ID!) {
        soundZone(id: $zoneId) {
            id
            name
            isPaired
            isActive
            device {
                id
                name
                status
                isOnline
                isConnected
                lastSeen
                connectionStatus
            }
            account {
                id
                businessName
                subscription {
                    status
                    isActive
                    expiresAt
                }
            }
            location {
                id
                name
            }
            lastActivity
            createdAt
            updatedAt
        }
    }
    """
    
    variables = {"zoneId": zone_id}
    
    try:
        response = await client.post(
            api_url,
            json={"query": test_query, "variables": variables},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "errors" in data:
                print("❌ Some fields not available:")
                for error in data["errors"]:
                    print(f"  - {error.get('message', error)}")
            
            if "data" in data and data["data"]:
                zone_data = data["data"].get("soundZone")
                if zone_data:
                    print("✅ Available zone data:")
                    print(json.dumps(zone_data, indent=2))
                else:
                    print("❌ No zone data returned")
        
    except Exception as e:
        print(f"❌ Comprehensive zone test failed: {e}")


if __name__ == "__main__":
    print("SYB SoundZone Schema Explorer")
    print(f"Timestamp: {datetime.now()}")
    
    asyncio.run(explore_soundzone_schema())
    asyncio.run(test_real_zone())