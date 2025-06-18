#!/usr/bin/env python3
"""
Final simplified test to verify subscription states and determine app update requirements.
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

# Define minimum supported app version (hypothesis based on observed data)
MINIMUM_APP_VERSION = 240.0  # Versions below this might need updates


class FinalStatusTester:
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

    async def test_zone_comprehensive_status(self, zone_id: str, test_name: str):
        """Test comprehensive status for a zone."""
        print(f"\n=== Testing {test_name} ===")
        
        # Simplified query without problematic fragments
        query = """
        query GetZoneComprehensiveStatus($zoneId: ID!) {
            soundZone(id: $zoneId) {
                id
                name
                isPaired
                online
                
                # Status field (we know it exists but might be null)
                status {
                    __typename
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
                
                # Account info
                account {
                    id
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
                # Determine comprehensive status
                status_info = self.determine_comprehensive_status(zone_data)
                
                print(f"✅ Zone: {zone_data.get('name')}")
                print(f"   Is Paired: {zone_data.get('isPaired')}")
                print(f"   Online: {zone_data.get('online')}")
                
                # Device info
                device = zone_data.get('device', {})
                if device:
                    print(f"   Device: {device.get('name')}")
                    print(f"   Software Version: {device.get('softwareVersion')}")
                
                # Subscription info
                subscription = zone_data.get('subscription', {})
                if subscription:
                    print(f"   Subscription State: {subscription.get('state')}")
                    print(f"   Subscription Active: {subscription.get('isActive')}")
                else:
                    print(f"   Subscription: None")
                
                # Comprehensive status
                print(f"\n   📊 COMPREHENSIVE STATUS:")
                print(f"   Status Code: {status_info['status_code']}")
                print(f"   Status Label: {status_info['status_label']}")
                print(f"   Needs App Update: {status_info['needs_app_update']}")
                print(f"   Reason: {status_info['reason']}")
                
                self.results[test_name] = {
                    "zone_data": zone_data,
                    "status_info": status_info
                }

    def determine_comprehensive_status(self, zone_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine comprehensive status based on all available fields."""
        
        is_paired = zone_data.get("isPaired", False)
        online = zone_data.get("online", False)
        device = zone_data.get("device", {})
        subscription = zone_data.get("subscription", {})
        
        # Extract key values
        software_version = None
        if device and device.get("softwareVersion"):
            try:
                software_version = float(device["softwareVersion"])
            except:
                pass
        
        subscription_state = subscription.get("state") if subscription else None
        subscription_active = subscription.get("isActive", False) if subscription else False
        
        # Determine status based on priority order
        status_info = {
            "status_code": "unknown",
            "status_label": "Unknown",
            "needs_app_update": False,
            "reason": "Unable to determine status"
        }
        
        # Priority 1: Check if unpaired
        if not is_paired:
            status_info = {
                "status_code": "unpaired",
                "status_label": "No Device Paired",
                "needs_app_update": False,
                "reason": "No device is paired with this zone"
            }
        
        # Priority 2: Check subscription status
        elif not subscription:
            status_info = {
                "status_code": "no_subscription",
                "status_label": "No Subscription",
                "needs_app_update": False,
                "reason": "No subscription information available"
            }
        elif subscription_state == "CANCELLED":
            status_info = {
                "status_code": "subscription_cancelled",
                "status_label": "Subscription Cancelled",
                "needs_app_update": False,
                "reason": "Subscription has been cancelled"
            }
        elif subscription_state == "EXPIRED":
            status_info = {
                "status_code": "subscription_expired",
                "status_label": "Subscription Expired",
                "needs_app_update": False,
                "reason": "Subscription has expired"
            }
        elif subscription_state in ["INACTIVE", "PAUSED"]:
            status_info = {
                "status_code": "subscription_inactive",
                "status_label": f"Subscription {subscription_state.title()}",
                "needs_app_update": False,
                "reason": f"Subscription is {subscription_state.lower()}"
            }
        
        # Priority 3: Check if app update is needed (only if subscription is active)
        elif subscription_state == "ACTIVE" and software_version and software_version < MINIMUM_APP_VERSION:
            status_info = {
                "status_code": "app_update_required",
                "status_label": "App Update Required",
                "needs_app_update": True,
                "reason": f"App version {software_version} is below minimum required version {MINIMUM_APP_VERSION}"
            }
        
        # Priority 4: Check online status (everything else is OK)
        elif subscription_state == "ACTIVE":
            if online:
                status_info = {
                    "status_code": "online",
                    "status_label": "Online",
                    "needs_app_update": False,
                    "reason": "Zone is online and working normally"
                }
            else:
                status_info = {
                    "status_code": "offline",
                    "status_label": "Offline",
                    "needs_app_update": False,
                    "reason": "Device is offline but subscription is active"
                }
        
        return status_info

    async def run_all_tests(self):
        """Run all tests."""
        print("=" * 80)
        print("FINAL COMPREHENSIVE STATUS TESTING")
        print(f"Timestamp: {datetime.now()}")
        print(f"Minimum App Version Threshold: {MINIMUM_APP_VERSION}")
        print("=" * 80)
        
        # Test each zone type
        for test_name, zone_id in TEST_ZONES.items():
            await self.test_zone_comprehensive_status(zone_id, test_name)
            await asyncio.sleep(2)  # Avoid rate limiting
        
        # Summary
        print("\n" + "=" * 80)
        print("COMPREHENSIVE STATUS MAPPING")
        print("=" * 80)
        
        print("\n📋 STATUS DETECTION LOGIC (in priority order):")
        print("\n1. UNPAIRED - isPaired = false")
        print("   → Status: 'No Device Paired'")
        
        print("\n2. NO SUBSCRIPTION - subscription = null or subscription.state = null")
        print("   → Status: 'No Subscription'")
        
        print("\n3. SUBSCRIPTION ISSUES - Based on subscription.state:")
        print("   • CANCELLED → Status: 'Subscription Cancelled'")
        print("   • EXPIRED → Status: 'Subscription Expired'")
        print("   • INACTIVE/PAUSED → Status: 'Subscription Inactive/Paused'")
        
        print(f"\n4. APP UPDATE REQUIRED - subscription.state = ACTIVE AND softwareVersion < {MINIMUM_APP_VERSION}")
        print("   → Status: 'App Update Required'")
        
        print("\n5. ONLINE/OFFLINE - subscription.state = ACTIVE AND softwareVersion >= minimum")
        print("   • online = true → Status: 'Online'")
        print("   • online = false → Status: 'Offline'")
        
        # Show test results summary
        print("\n\n📊 TEST RESULTS SUMMARY:")
        for test_name, result in self.results.items():
            if "status_info" in result:
                status = result["status_info"]
                print(f"\n{test_name}:")
                print(f"  Status: {status['status_label']} ({status['status_code']})")
                print(f"  Reason: {status['reason']}")
        
        # Save comprehensive results
        detection_logic = {
            "minimum_app_version": MINIMUM_APP_VERSION,
            "status_priority": [
                {
                    "priority": 1,
                    "condition": "isPaired = false",
                    "status_code": "unpaired",
                    "status_label": "No Device Paired"
                },
                {
                    "priority": 2,
                    "condition": "subscription = null or subscription.state = null",
                    "status_code": "no_subscription",
                    "status_label": "No Subscription"
                },
                {
                    "priority": 3,
                    "condition": "subscription.state = 'CANCELLED'",
                    "status_code": "subscription_cancelled",
                    "status_label": "Subscription Cancelled"
                },
                {
                    "priority": 4,
                    "condition": "subscription.state = 'EXPIRED'",
                    "status_code": "subscription_expired",
                    "status_label": "Subscription Expired"
                },
                {
                    "priority": 5,
                    "condition": f"subscription.state = 'ACTIVE' AND softwareVersion < {MINIMUM_APP_VERSION}",
                    "status_code": "app_update_required",
                    "status_label": "App Update Required"
                },
                {
                    "priority": 6,
                    "condition": "subscription.state = 'ACTIVE' AND online = true",
                    "status_code": "online",
                    "status_label": "Online"
                },
                {
                    "priority": 7,
                    "condition": "subscription.state = 'ACTIVE' AND online = false",
                    "status_code": "offline",
                    "status_label": "Offline"
                }
            ]
        }
        
        with open("comprehensive_status_detection.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "detection_logic": detection_logic,
                "test_results": self.results,
                "discovered_fields": {
                    "subscription.state": ["ACTIVE", "CANCELLED", "EXPIRED", "INACTIVE", "PAUSED"],
                    "device.softwareVersion": "Float value representing app version",
                    "device.osVersion": "String value representing OS version"
                }
            }, f, indent=2)
        
        print(f"\n\n📁 Comprehensive detection logic saved to comprehensive_status_detection.json")

    async def close(self):
        """Clean up resources."""
        await self.client.aclose()


async def main():
    tester = FinalStatusTester()
    try:
        await tester.run_all_tests()
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())