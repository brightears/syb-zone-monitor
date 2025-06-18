#!/usr/bin/env python3
"""
Test for additional status fields and edge cases, including:
- Testing unpaired zones
- Testing zones with different subscription states
- Looking for app update requirements based on software version
"""

import asyncio
import json
from datetime import datetime
import httpx
from typing import Dict, Any, List, Optional

# API Configuration
API_TOKEN = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
API_URL = "https://api.soundtrackyourbrand.com/v2"

# Test specific zones from our previous results
TEST_ZONES = {
    "cancelled_unpaired": "U291bmRab25lLCwxc21hNTdwOXN6ay9Mb2NhdGlvbiwsMWo3aTdjYmczY3cvQWNjb3VudCwsMWU1OTBhenpremsv",  # Hotel Made In Louise
    "cancelled_paired": "U291bmRab25lLCwxYXFicXVuMWJscy9Mb2NhdGlvbiwsMWtpNXdrd2dsYzAvQWNjb3VudCwsMXF0cjB5YXh5cHMv",  # 3rd floor Swimming Pool Bar
    "active_unpaired": "U291bmRab25lLCwxanU5NGtyMmViay9Mb2NhdGlvbiwsMWc5OGI1dm5jM2svQWNjb3VudCwsMWZ0eGhhYTl0a3cv",  # Kids' Club Room 1 (unpaired)
    "active_old_version": "U291bmRab25lLCwxcmh0b2xqdzNjdy9Mb2NhdGlvbiwsMW5oOHA2dXlxZGMvQWNjb3VudCwsMXJsbmd0eDZ3b3cv",  # P&B with version 235.0
    "active_new_version": "U291bmRab25lLCwxbnNrdnVtdXd3MC9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",  # Basalt with version 248.0
}


class StatusFieldTester:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30,
            headers={
                "Authorization": f"Basic {API_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        self.results = {}

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

    async def test_status_field(self, zone_id: str, test_name: str):
        """Test the status field in detail for a zone."""
        print(f"\n=== Testing {test_name} ===")
        
        # Query for status field details
        query = """
        query GetZoneStatusDetails($zoneId: ID!) {
            soundZone(id: $zoneId) {
                id
                name
                isPaired
                online
                
                # Status field discovered earlier
                status {
                    __typename
                    ... on ZoneStatus {
                        __typename
                    }
                }
                
                # Device with version info
                device {
                    id
                    name
                    softwareVersion
                    osVersion
                }
                
                # Subscription with state
                subscription {
                    isActive
                    state
                }
            }
        }
        """
        
        result = await self.execute_query(query, {"zoneId": zone_id})
        
        if "errors" in result:
            print(f"❌ Error: {result['errors'][0].get('message', 'Unknown error')}")
            self.results[test_name] = {"error": result["errors"]}
            return
        
        if "data" in result and result["data"]:
            zone_data = result["data"].get("soundZone", {})
            if zone_data:
                print(f"✅ Zone: {zone_data.get('name')}")
                print(f"   ID: {zone_data.get('id', 'N/A')[:30]}...")
                print(f"   Is Paired: {zone_data.get('isPaired')}")
                print(f"   Online: {zone_data.get('online')}")
                
                # Status info
                status = zone_data.get('status')
                if status:
                    print(f"   Status: {json.dumps(status, indent=6)}")
                else:
                    print(f"   Status: None")
                
                # Device info
                device = zone_data.get('device', {})
                if device:
                    print(f"   Device: {device.get('name')}")
                    print(f"   Software Version: {device.get('softwareVersion')}")
                    print(f"   OS Version: {device.get('osVersion')}")
                
                # Subscription info
                subscription = zone_data.get('subscription', {})
                if subscription:
                    print(f"   Subscription Active: {subscription.get('isActive')}")
                    print(f"   Subscription State: {subscription.get('state')}")
                
                self.results[test_name] = zone_data

    async def test_minimum_version_requirement(self):
        """Test if there's a way to determine minimum required app version."""
        print("\n=== Testing for Minimum Version Requirements ===")
        
        # Try to query account or system level information
        query = """
        query GetSystemInfo {
            me {
                __typename
                ... on Viewer {
                    accounts {
                        id
                    }
                }
            }
        }
        """
        
        result = await self.execute_query(query)
        
        if "data" in result:
            print(f"System query result: {json.dumps(result['data'], indent=2)}")
        if "errors" in result:
            print(f"Errors: {json.dumps(result['errors'], indent=2)}")

    async def test_subscription_enum_values(self):
        """Test to get all possible subscription state values."""
        print("\n=== Testing Subscription State Enum Values ===")
        
        # Introspection query for enum values
        query = """
        query GetSubscriptionStateEnum {
            __type(name: "SubscriptionState") {
                name
                kind
                enumValues {
                    name
                    description
                }
            }
        }
        """
        
        result = await self.execute_query(query)
        
        if "data" in result and result["data"]:
            type_info = result["data"].get("__type")
            if type_info and type_info.get("enumValues"):
                print("Possible Subscription States:")
                for value in type_info["enumValues"]:
                    print(f"  • {value['name']}: {value.get('description', 'No description')}")
                    
                self.results["subscription_states"] = type_info["enumValues"]
            else:
                print("❌ Could not find SubscriptionState enum")

    async def analyze_version_patterns(self):
        """Analyze software version patterns to infer update requirements."""
        print("\n=== ANALYSIS: Version Patterns ===")
        
        # Based on collected data, analyze patterns
        if all(key in self.results for key in ["active_old_version", "active_new_version"]):
            old_zone = self.results["active_old_version"]
            new_zone = self.results["active_new_version"]
            
            old_version = float(old_zone.get("device", {}).get("softwareVersion", 0))
            new_version = float(new_zone.get("device", {}).get("softwareVersion", 0))
            
            print(f"\n📊 Version Analysis:")
            print(f"   Oldest active version found: {old_version}")
            print(f"   Newest active version found: {new_version}")
            print(f"   Version difference: {new_version - old_version}")
            
            # Hypothesis: versions significantly behind might need updates
            if new_version - old_version > 10:
                print(f"\n   ⚠️  Large version gap detected!")
                print(f"   Zones with version < {new_version - 10} might need app updates")

    async def run_all_tests(self):
        """Run all tests."""
        print("=" * 80)
        print("TESTING ADDITIONAL STATUS FIELDS AND PATTERNS")
        print(f"Timestamp: {datetime.now()}")
        print("=" * 80)
        
        # Test enum values first
        await self.test_subscription_enum_values()
        await asyncio.sleep(2)
        
        # Test each zone type
        for test_name, zone_id in TEST_ZONES.items():
            await self.test_status_field(zone_id, test_name)
            await asyncio.sleep(2)  # Avoid rate limiting
        
        # Test for system-level version requirements
        await self.test_minimum_version_requirement()
        
        # Analyze patterns
        await self.analyze_version_patterns()
        
        # Summary
        print("\n" + "=" * 80)
        print("FINDINGS SUMMARY")
        print("=" * 80)
        
        print("\n🔍 KEY FINDINGS:")
        
        # Check if status field provides useful info
        has_status_info = False
        for test_name, result in self.results.items():
            if isinstance(result, dict) and "status" in result and result["status"]:
                has_status_info = True
                print(f"\n  Status field found in {test_name}: {result['status']}")
        
        if not has_status_info:
            print("\n  • The 'status' field appears to be null/empty in all tested zones")
        
        # Subscription states
        if "subscription_states" in self.results:
            states = self.results["subscription_states"]
            print(f"\n  • Found {len(states)} possible subscription states:")
            for state in states:
                print(f"    - {state['name']}")
        
        # Pattern-based findings
        print("\n  • PATTERN-BASED STATUS DETECTION:")
        print("    1. 'App Update Required': Could be inferred from very old softwareVersion (e.g., < 240.0)")
        print("    2. 'No Subscription': subscription.state = null (not CANCELLED, just missing)")
        print("    3. 'Subscription Expired': subscription.state = 'CANCELLED'")
        print("    4. 'Device Not Paired': isPaired = false")
        
        # Save results
        with open("additional_status_findings.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.results,
                "recommendations": {
                    "app_update_detection": "Check if device.softwareVersion < (currentVersion - threshold)",
                    "no_subscription_detection": "Check if subscription is null or subscription.state is null",
                    "expired_subscription_detection": "Check if subscription.state == 'CANCELLED'",
                    "unpaired_detection": "Check if isPaired == false"
                }
            }, f, indent=2)
        
        print(f"\n📁 Findings saved to additional_status_findings.json")

    async def close(self):
        """Clean up resources."""
        await self.client.aclose()


async def main():
    tester = StatusFieldTester()
    try:
        await tester.run_all_tests()
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())