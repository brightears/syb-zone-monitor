#!/usr/bin/env python3
"""
Comprehensive exploration of SYB GraphQL API to find fields related to:
1. App outdated status (device needs app update)
2. No subscription status (different from expired subscription)
"""

import asyncio
import json
from datetime import datetime
import httpx
from typing import Dict, Any, List, Optional

# API Configuration
API_TOKEN = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
API_URL = "https://api.soundtrackyourbrand.com/v2"

# Test zone IDs - using a variety from the .env file
TEST_ZONE_IDS = [
    "U291bmRab25lLCwxbjFteGk0NHJnZy9Mb2NhdGlvbiwsMWdoZXh3eDdhNGcvQWNjb3VudCwsMW1sbTJ0ZW52OWMv",
    "U291bmRab25lLCwxcDEzcWhzYTBhby9Mb2NhdGlvbiwsMThscnUwenZldjQvQWNjb3VudCwsMWVuaXV0emJhYmsv",
    "U291bmRab25lLCwxbnNrdnVtdXd3MC9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxbGRxZ2cwcG12NC9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxbzVqeXdvMjVmay9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv"
]


class GraphQLExplorer:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30,
            headers={
                "Authorization": f"Basic {API_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        self.results = []

    async def execute_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a GraphQL query and return the result."""
        try:
            response = await self.client.post(
                API_URL,
                json={"query": query, "variables": variables or {}}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def explore_sound_zone_fields(self):
        """Explore all available fields on the SoundZone type."""
        print("\n=== EXPLORING SOUNDZONE TYPE FIELDS ===")
        
        # First, use introspection to find all fields
        introspection_query = """
        query {
            __type(name: "SoundZone") {
                name
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
        
        result = await self.execute_query(introspection_query)
        
        if "data" in result and result["data"]:
            type_info = result["data"].get("__type")
            if type_info:
                fields = type_info.get("fields", [])
            else:
                fields = []
            
            print(f"\nFound {len(fields)} fields on SoundZone type:")
            
            # Look for interesting fields related to app version, updates, or subscriptions
            interesting_keywords = [
                "version", "update", "app", "subscription", "plan", "billing",
                "status", "expired", "active", "outdated", "needs", "require"
            ]
            
            interesting_fields = []
            for field in fields:
                field_name = field.get("name", "")
                field_desc = field.get("description", "")
                
                # Check if field name or description contains interesting keywords
                if any(keyword in field_name.lower() or keyword in (field_desc or "").lower() 
                       for keyword in interesting_keywords):
                    interesting_fields.append(field)
                    print(f"  🔍 {field_name}: {field.get('type', {}).get('name', 'Unknown')} - {field_desc}")
            
            self.results.append({
                "test": "SoundZone Type Fields",
                "total_fields": len(fields),
                "interesting_fields": interesting_fields
            })
        else:
            print("❌ Failed to get SoundZone type information")
            print(json.dumps(result, indent=2))

    async def explore_device_fields(self):
        """Explore fields on the Device type that might indicate app version or update needs."""
        print("\n=== EXPLORING DEVICE TYPE FIELDS ===")
        
        introspection_query = """
        query {
            __type(name: "Device") {
                name
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
        
        result = await self.execute_query(introspection_query)
        
        if "data" in result and result["data"]:
            type_info = result["data"].get("__type")
            if type_info:
                fields = type_info.get("fields", [])
            else:
                fields = []
            
            print(f"\nFound {len(fields)} fields on Device type:")
            
            # Look for version-related fields
            for field in fields:
                field_name = field.get("name", "")
                field_desc = field.get("description", "")
                field_type = field.get("type", {}).get("name", "Unknown")
                
                keywords = ["version", "app", "update", "needs", "outdated", "require", "firmware", "software"]
                if any(keyword in field_name.lower() or keyword in (field_desc or "").lower() for keyword in keywords):
                    print(f"  🔍 {field_name}: {field_type} - {field_desc}")
            
            self.results.append({
                "test": "Device Type Fields",
                "fields": fields
            })

    async def explore_subscription_fields(self):
        """Explore fields on the Subscription type."""
        print("\n=== EXPLORING SUBSCRIPTION TYPE FIELDS ===")
        
        introspection_query = """
        query {
            __type(name: "Subscription") {
                name
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
        
        result = await self.execute_query(introspection_query)
        
        if "data" in result and result["data"]:
            type_info = result["data"].get("__type")
            if type_info:
                fields = type_info.get("fields", [])
            else:
                fields = []
            
            print(f"\nFound {len(fields)} fields on Subscription type:")
            
            for field in fields:
                field_name = field.get("name", "")
                field_desc = field.get("description", "")
                field_type = field.get("type", {}).get("name", "Unknown")
                print(f"  • {field_name}: {field_type} - {field_desc}")
            
            self.results.append({
                "test": "Subscription Type Fields",
                "fields": fields
            })

    async def test_comprehensive_zone_query(self, zone_id: str):
        """Test a comprehensive query with all potential fields."""
        print(f"\n=== TESTING COMPREHENSIVE QUERY FOR ZONE {zone_id[:20]}... ===")
        
        # Build a comprehensive query with all potential fields
        query = """
        query GetZoneDetails($zoneId: ID!) {
            soundZone(id: $zoneId) {
                id
                name
                isPaired
                online
                
                # Device information
                device {
                    id
                    name
                    # Try potential version/update fields
                    ... on Device {
                        __typename
                    }
                }
                
                # Subscription information
                subscription {
                    isActive
                    # Try additional subscription fields
                    ... on Subscription {
                        __typename
                    }
                }
                
                # Account information
                account {
                    id
                    name
                    # Try subscription fields on account
                    ... on Account {
                        __typename
                    }
                }
                
                # Try direct fields that might exist
                __typename
            }
        }
        """
        
        result = await self.execute_query(query, {"zoneId": zone_id})
        
        if "data" in result and result["data"]:
            zone_data = result["data"].get("soundZone", {})
            if zone_data:
                print(f"\n✅ Zone: {zone_data.get('name', 'Unknown')}")
                print(f"   ID: {zone_data.get('id', 'N/A')}")
                print(f"   Is Paired: {zone_data.get('isPaired', 'N/A')}")
                print(f"   Online: {zone_data.get('online', 'N/A')}")
                
                device = zone_data.get('device', {})
                if device:
                    print(f"   Device: {device.get('name', 'N/A')} (Type: {device.get('__typename', 'N/A')})")
                
                subscription = zone_data.get('subscription', {})
                if subscription:
                    print(f"   Subscription Active: {subscription.get('isActive', 'N/A')} (Type: {subscription.get('__typename', 'N/A')})")
                
                return zone_data
        else:
            print(f"❌ Failed to get zone data")
            if "errors" in result:
                for error in result["errors"]:
                    print(f"   Error: {error.get('message', error)}")
        
        return None

    async def explore_with_fragments(self, zone_id: str):
        """Try to explore additional fields using fragments and inline fragments."""
        print(f"\n=== EXPLORING WITH FRAGMENTS FOR ZONE {zone_id[:20]}... ===")
        
        # Try various field combinations that might reveal app status
        test_queries = [
            {
                "name": "Device Version Fields",
                "query": """
                query GetDeviceVersion($zoneId: ID!) {
                    soundZone(id: $zoneId) {
                        id
                        name
                        device {
                            id
                            name
                            # Try various version field names
                            ... on Device {
                                __typename
                            }
                        }
                    }
                }
                """
            },
            {
                "name": "Account Subscription Details",
                "query": """
                query GetAccountSubscription($zoneId: ID!) {
                    soundZone(id: $zoneId) {
                        id
                        name
                        account {
                            id
                            name
                            # Try subscription-related fields
                            ... on Account {
                                __typename
                            }
                        }
                    }
                }
                """
            },
            {
                "name": "Zone Status Fields",
                "query": """
                query GetZoneStatus($zoneId: ID!) {
                    soundZone(id: $zoneId) {
                        id
                        name
                        isPaired
                        online
                        # Try additional status fields
                        ... on SoundZone {
                            __typename
                        }
                    }
                }
                """
            }
        ]
        
        for test in test_queries:
            print(f"\n--- Testing: {test['name']} ---")
            result = await self.execute_query(test["query"], {"zoneId": zone_id})
            
            if "data" in result:
                print(f"Result: {json.dumps(result['data'], indent=2)}")
            if "errors" in result:
                print(f"Errors: {json.dumps(result['errors'], indent=2)}")

    async def test_field_availability(self, zone_id: str):
        """Test specific fields that might exist based on the status types we're looking for."""
        print(f"\n=== TESTING SPECIFIC FIELD AVAILABILITY ===")
        
        # Fields to test based on common patterns
        potential_fields = {
            "device": [
                "appVersion", "app_version", "version", 
                "needsUpdate", "needs_update", "requiresUpdate", "requires_update",
                "isOutdated", "is_outdated", "outdated",
                "firmwareVersion", "firmware_version",
                "softwareVersion", "software_version"
            ],
            "subscription": [
                "status", "state", "plan", "type", "tier",
                "expirationDate", "expiration_date", "expiresAt", "expires_at",
                "isExpired", "is_expired", "expired"
            ],
            "soundZone": [
                "status", "state", "appUpdateRequired", "app_update_required",
                "subscriptionStatus", "subscription_status"
            ],
            "account": [
                "subscriptionStatus", "subscription_status",
                "subscriptionPlan", "subscription_plan",
                "subscriptionType", "subscription_type",
                "hasSu bscription", "has_subscription"
            ]
        }
        
        results = {}
        
        for entity, fields in potential_fields.items():
            print(f"\n--- Testing {entity} fields ---")
            
            for field in fields:
                # Build dynamic query
                if entity == "device":
                    query = f"""
                    query TestField($zoneId: ID!) {{
                        soundZone(id: $zoneId) {{
                            device {{
                                {field}
                            }}
                        }}
                    }}
                    """
                elif entity == "subscription":
                    query = f"""
                    query TestField($zoneId: ID!) {{
                        soundZone(id: $zoneId) {{
                            subscription {{
                                {field}
                            }}
                        }}
                    }}
                    """
                elif entity == "soundZone":
                    query = f"""
                    query TestField($zoneId: ID!) {{
                        soundZone(id: $zoneId) {{
                            {field}
                        }}
                    }}
                    """
                elif entity == "account":
                    query = f"""
                    query TestField($zoneId: ID!) {{
                        soundZone(id: $zoneId) {{
                            account {{
                                {field}
                            }}
                        }}
                    }}
                    """
                
                result = await self.execute_query(query, {"zoneId": zone_id})
                
                if "errors" not in result and "data" in result:
                    # Field exists!
                    print(f"  ✅ {field} EXISTS!")
                    if entity not in results:
                        results[entity] = []
                    results[entity].append(field)
                    
                    # Get the actual value
                    data = result["data"]
                    if entity == "device" and data.get("soundZone", {}).get("device"):
                        value = data["soundZone"]["device"].get(field)
                        print(f"     Value: {value}")
                    elif entity == "subscription" and data.get("soundZone", {}).get("subscription"):
                        value = data["soundZone"]["subscription"].get(field)
                        print(f"     Value: {value}")
                    elif entity == "soundZone" and data.get("soundZone"):
                        value = data["soundZone"].get(field)
                        print(f"     Value: {value}")
                    elif entity == "account" and data.get("soundZone", {}).get("account"):
                        value = data["soundZone"]["account"].get(field)
                        print(f"     Value: {value}")
        
        return results

    async def run_all_tests(self):
        """Run all exploration tests."""
        print("=" * 80)
        print("SYB GraphQL API EXPLORATION - APP STATUS FIELDS")
        print(f"Timestamp: {datetime.now()}")
        print("=" * 80)
        
        # First explore type definitions
        await self.explore_sound_zone_fields()
        await self.explore_device_fields()
        await self.explore_subscription_fields()
        
        # Then test with actual zones
        discovered_fields = {}
        
        for i, zone_id in enumerate(TEST_ZONE_IDS[:3]):  # Test first 3 zones
            print(f"\n\n{'=' * 80}")
            print(f"TESTING ZONE {i + 1} OF {len(TEST_ZONE_IDS[:3])}")
            print(f"{'=' * 80}")
            
            # Run comprehensive query
            zone_data = await self.test_comprehensive_zone_query(zone_id)
            
            # Test specific fields
            fields = await self.test_field_availability(zone_id)
            if fields:
                for entity, field_list in fields.items():
                    if entity not in discovered_fields:
                        discovered_fields[entity] = set()
                    discovered_fields[entity].update(field_list)
            
            # Explore with fragments
            await self.explore_with_fragments(zone_id)
            
            # Small delay between zones
            if i < len(TEST_ZONE_IDS) - 1:
                await asyncio.sleep(1)
        
        # Summary
        print("\n\n" + "=" * 80)
        print("DISCOVERY SUMMARY")
        print("=" * 80)
        
        if discovered_fields:
            print("\n🎉 DISCOVERED FIELDS:")
            for entity, fields in discovered_fields.items():
                print(f"\n{entity.upper()}:")
                for field in sorted(fields):
                    print(f"  • {field}")
        else:
            print("\n❌ No additional fields discovered beyond the known ones.")
        
        # Save results
        with open("api_exploration_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "discovered_fields": {k: list(v) for k, v in discovered_fields.items()},
                "all_results": self.results
            }, f, indent=2)
        
        print(f"\n📁 Results saved to api_exploration_results.json")

    async def close(self):
        """Clean up resources."""
        await self.client.aclose()


async def main():
    explorer = GraphQLExplorer()
    try:
        await explorer.run_all_tests()
    finally:
        await explorer.close()


if __name__ == "__main__":
    asyncio.run(main())