#!/usr/bin/env python3
"""
Test discovered fields on multiple zones to understand different subscription states
and device software versions.
"""

import asyncio
import json
from datetime import datetime
import httpx
from typing import Dict, Any, List, Optional

# API Configuration
API_TOKEN = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
API_URL = "https://api.soundtrackyourbrand.com/v2"

# Test more zone IDs to find different states
TEST_ZONE_IDS = [
    # First 20 zones from the list
    "U291bmRab25lLCwxbjFteGk0NHJnZy9Mb2NhdGlvbiwsMWdoZXh3eDdhNGcvQWNjb3VudCwsMW1sbTJ0ZW52OWMv",
    "U291bmRab25lLCwxcDEzcWhzYTBhby9Mb2NhdGlvbiwsMThscnUwenZldjQvQWNjb3VudCwsMWVuaXV0emJhYmsv",
    "U291bmRab25lLCwxbnNrdnVtdXd3MC9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxbGRxZ2cwcG12NC9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxbzVqeXdvMjVmay9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxc2hkemw2azR4cy9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxYW9jcmF4d2lyay9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxZzdzNnkxaWs4dy9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxb2ZyNDhhbHc1Yy9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxZGQzcnFqNDVqNC9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxcGlmZGlzNjFhOC9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxdDBmeXJoNXQ2by9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxanU5NGtyMmViay9Mb2NhdGlvbiwsMWc5OGI1dm5jM2svQWNjb3VudCwsMWZ0eGhhYTl0a3cv",
    "U291bmRab25lLCwxc21hNTdwOXN6ay9Mb2NhdGlvbiwsMWo3aTdjYmczY3cvQWNjb3VudCwsMWU1OTBhenpremsv",
    "U291bmRab25lLCwxY2xnZG83b2dlOC9Mb2NhdGlvbiwsMXRva2s4cHRjemsvQWNjb3VudCwsMXRiOThzZDMwMXMv",
    "U291bmRab25lLCwxbzhpZWJoaTNuay9Mb2NhdGlvbiwsMXRva2s4cHRjemsvQWNjb3VudCwsMXRiOThzZDMwMXMv",
    "U291bmRab25lLCwxbnl0a3R4djR6ay9Mb2NhdGlvbiwsMXQwa3lsM3JmdW8vQWNjb3VudCwsMXNjOHNycmUwYW8v",
    "U291bmRab25lLCwxcmh0b2xqdzNjdy9Mb2NhdGlvbiwsMW5oOHA2dXlxZGMvQWNjb3VudCwsMXJsbmd0eDZ3b3cv",
    "U291bmRab25lLCwxbWF1YzE2ZWlvMC9Mb2NhdGlvbiwsMXNyc2h6dGZ1OXMvQWNjb3VudCwsMThtYnZ5amV2NDAv",
    "U291bmRab25lLCwxYXFicXVuMWJscy9Mb2NhdGlvbiwsMWtpNXdrd2dsYzAvQWNjb3VudCwsMXF0cjB5YXh5cHMv"
]


class ZoneStatusTester:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30,
            headers={
                "Authorization": f"Basic {API_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        self.results = []
        self.unique_states = set()
        self.software_versions = set()

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

    async def test_zone_status(self, zone_id: str) -> Dict[str, Any]:
        """Test a zone to get its subscription state and device information."""
        query = """
        query GetZoneStatus($zoneId: ID!) {
            soundZone(id: $zoneId) {
                id
                name
                isPaired
                online
                
                # Device information
                device {
                    id
                    name
                    softwareVersion
                    osVersion
                }
                
                # Subscription information - using discovered fields
                subscription {
                    isActive
                    state
                }
                
                # Account information
                account {
                    id
                }
                
                # Zone status (discovered field)
                status {
                    __typename
                }
            }
        }
        """
        
        result = await self.execute_query(query, {"zoneId": zone_id})
        
        zone_info = {
            "zone_id": zone_id,
            "zone_name": None,
            "is_paired": None,
            "online": None,
            "device_name": None,
            "software_version": None,
            "os_version": None,
            "subscription_active": None,
            "subscription_state": None,
            "status": None,
            "error": None
        }
        
        if "errors" in result:
            zone_info["error"] = result["errors"][0].get("message", "Unknown error")
            return zone_info
        
        if "data" in result and result["data"]:
            zone_data = result["data"].get("soundZone", {})
            if zone_data:
                zone_info["zone_name"] = zone_data.get("name")
                zone_info["is_paired"] = zone_data.get("isPaired")
                zone_info["online"] = zone_data.get("online")
                
                # Device info
                device = zone_data.get("device", {})
                if device:
                    zone_info["device_name"] = device.get("name")
                    zone_info["software_version"] = device.get("softwareVersion")
                    zone_info["os_version"] = device.get("osVersion")
                    
                    if zone_info["software_version"]:
                        self.software_versions.add(zone_info["software_version"])
                
                # Subscription info
                subscription = zone_data.get("subscription", {})
                if subscription:
                    zone_info["subscription_active"] = subscription.get("isActive")
                    zone_info["subscription_state"] = subscription.get("state")
                    
                    if zone_info["subscription_state"]:
                        self.unique_states.add(zone_info["subscription_state"])
                
                # Status info
                status = zone_data.get("status")
                if status:
                    zone_info["status"] = status
        
        return zone_info

    async def run_tests(self):
        """Test all zones and collect results."""
        print("=" * 80)
        print("TESTING SUBSCRIPTION STATES AND DEVICE VERSIONS")
        print(f"Timestamp: {datetime.now()}")
        print(f"Testing {len(TEST_ZONE_IDS)} zones...")
        print("=" * 80)
        
        # Test zones with delays to avoid rate limiting
        for i, zone_id in enumerate(TEST_ZONE_IDS):
            print(f"\nTesting zone {i + 1}/{len(TEST_ZONE_IDS)}: {zone_id[:30]}...")
            
            zone_info = await self.test_zone_status(zone_id)
            self.results.append(zone_info)
            
            # Print summary
            if zone_info["error"]:
                print(f"  ❌ Error: {zone_info['error']}")
            else:
                print(f"  ✅ Zone: {zone_info['zone_name']}")
                print(f"     Paired: {zone_info['is_paired']}, Online: {zone_info['online']}")
                
                if zone_info["device_name"]:
                    print(f"     Device: {zone_info['device_name']}")
                    if zone_info["software_version"]:
                        print(f"     Software Version: {zone_info['software_version']}")
                    if zone_info["os_version"]:
                        print(f"     OS Version: {zone_info['os_version']}")
                
                if zone_info["subscription_state"]:
                    print(f"     Subscription State: {zone_info['subscription_state']}")
                    print(f"     Subscription Active: {zone_info['subscription_active']}")
            
            # Delay to avoid rate limiting
            if i < len(TEST_ZONE_IDS) - 1:
                await asyncio.sleep(2)  # 2 second delay between requests
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        print(f"\n📊 UNIQUE SUBSCRIPTION STATES FOUND:")
        for state in sorted(self.unique_states):
            count = sum(1 for r in self.results if r["subscription_state"] == state)
            print(f"  • {state}: {count} zones")
        
        print(f"\n📱 SOFTWARE VERSIONS FOUND:")
        for version in sorted(self.software_versions):
            count = sum(1 for r in self.results if r["software_version"] == version)
            print(f"  • {version}: {count} devices")
        
        # Analyze patterns
        print(f"\n🔍 ANALYSIS:")
        
        # Check for zones with no subscription
        no_subscription = [r for r in self.results if r["subscription_state"] is None and not r["error"]]
        if no_subscription:
            print(f"\nZones with NO subscription info ({len(no_subscription)} found):")
            for zone in no_subscription[:5]:  # Show first 5
                print(f"  • {zone['zone_name']} - Paired: {zone['is_paired']}, Online: {zone['online']}")
        
        # Check for cancelled subscriptions
        cancelled = [r for r in self.results if r["subscription_state"] == "CANCELLED"]
        if cancelled:
            print(f"\nZones with CANCELLED subscription ({len(cancelled)} found):")
            for zone in cancelled[:5]:  # Show first 5
                print(f"  • {zone['zone_name']} - Paired: {zone['is_paired']}, Online: {zone['online']}")
        
        # Check for old software versions
        if self.software_versions:
            versions = sorted([float(v) for v in self.software_versions if v])
            if versions:
                oldest = min(versions)
                newest = max(versions)
                print(f"\nSoftware version range: {oldest} - {newest}")
                
                # Zones with old versions (< 245.0 as an example)
                old_version_zones = [r for r in self.results if r["software_version"] and float(r["software_version"]) < 245.0]
                if old_version_zones:
                    print(f"\nZones with old software versions (<245.0): {len(old_version_zones)}")
                    for zone in old_version_zones[:5]:
                        print(f"  • {zone['zone_name']} - Version: {zone['software_version']}")
        
        # Save results
        with open("subscription_state_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "unique_states": list(self.unique_states),
                "software_versions": list(self.software_versions),
                "results": self.results
            }, f, indent=2)
        
        print(f"\n📁 Detailed results saved to subscription_state_results.json")

    async def close(self):
        """Clean up resources."""
        await self.client.aclose()


async def main():
    tester = ZoneStatusTester()
    try:
        await tester.run_tests()
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())