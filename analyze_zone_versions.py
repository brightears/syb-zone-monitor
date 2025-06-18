#!/usr/bin/env python3
"""
Analyze zone app versions and subscription states across multiple zones.
This script queries 20+ zones to find:
- Different app versions (especially older versions below 240.0)
- Different subscription states
- Zones without subscriptions
"""

import asyncio
import json
from datetime import datetime
import httpx
from typing import Dict, Any, List, Optional
import random

# API Configuration
API_TOKEN = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
API_URL = "https://api.soundtrackyourbrand.com/v2"


class ZoneVersionAnalyzer:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30,
            headers={
                "Authorization": f"Basic {API_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        self.results = []
        self.version_distribution = {}
        self.subscription_distribution = {}
        self.zones_by_version = {}
        self.zones_by_subscription = {}

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

    async def get_all_zones(self) -> List[str]:
        """Get all available zones from all accounts."""
        print("🔍 Discovering all available zones...")
        
        # First get all accounts
        accounts_query = """
        {
            me {
                ... on PublicAPIClient {
                    accounts(first: 200) {
                        edges {
                            node {
                                id
                                businessName
                                locations(first: 100) {
                                    edges {
                                        node {
                                            id
                                            name
                                            soundZones(first: 100) {
                                                edges {
                                                    node {
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
            }
        }
        """
        
        all_zone_ids = []
        result = await self.execute_query(accounts_query)
        
        if "error" in result:
            print(f"❌ Error getting accounts: {result['error']}")
            return []
        
        if "data" in result and result["data"] and result["data"].get("me") and result["data"]["me"].get("accounts"):
            accounts = result["data"]["me"]["accounts"]["edges"]
            
            for account_edge in accounts:
                account = account_edge["node"]
                locations = account["locations"]["edges"]
                
                for location_edge in locations:
                    location = location_edge["node"]
                    zones = location["soundZones"]["edges"]
                    
                    for zone_edge in zones:
                        zone = zone_edge["node"]
                        all_zone_ids.append(zone["id"])
        
        print(f"✅ Found {len(all_zone_ids)} total zones")
        return all_zone_ids

    async def analyze_zone(self, zone_id: str) -> Dict[str, Any]:
        """Analyze a single zone for app version and subscription state."""
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
                    softwareVersion
                    osVersion
                }
                
                # Subscription information
                subscription {
                    isActive
                    state
                }
                
                # Account information
                account {
                    id
                    businessName
                }
                
                # Location information
                location {
                    id
                    name
                }
                
                # Player status
                playerStatus {
                    state
                    currentTrack {
                        title
                    }
                }
            }
        }
        """
        
        result = await self.execute_query(query, {"zoneId": zone_id})
        
        zone_info = {
            "zone_id": zone_id,
            "zone_name": None,
            "account_name": None,
            "location_name": None,
            "is_paired": None,
            "online": None,
            "device_name": None,
            "software_version": None,
            "os_version": None,
            "subscription_active": None,
            "subscription_state": None,
            "player_state": None,
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
                
                # Account info
                account = zone_data.get("account", {})
                if account:
                    zone_info["account_name"] = account.get("businessName")
                
                # Location info
                location = zone_data.get("location", {})
                if location:
                    zone_info["location_name"] = location.get("name")
                
                # Device info
                device = zone_data.get("device", {})
                if device:
                    zone_info["device_name"] = device.get("name")
                    zone_info["software_version"] = device.get("softwareVersion")
                    zone_info["os_version"] = device.get("osVersion")
                
                # Subscription info
                subscription = zone_data.get("subscription", {})
                if subscription:
                    zone_info["subscription_active"] = subscription.get("isActive")
                    zone_info["subscription_state"] = subscription.get("state")
                
                # Player status
                player_status = zone_data.get("playerStatus", {})
                if player_status:
                    zone_info["player_state"] = player_status.get("state")
        
        return zone_info

    async def run_analysis(self, sample_size: int = 50):
        """Analyze a sample of zones for version and subscription diversity."""
        print("=" * 80)
        print("ZONE VERSION AND SUBSCRIPTION ANALYSIS")
        print(f"Timestamp: {datetime.now()}")
        print("=" * 80)
        
        # Get all available zones
        all_zones = await self.get_all_zones()
        
        if not all_zones:
            print("❌ No zones found!")
            return
        
        # Sample zones randomly to get diversity
        sample_zones = random.sample(all_zones, min(sample_size, len(all_zones)))
        
        print(f"\n📊 Analyzing {len(sample_zones)} zones...")
        print("-" * 80)
        
        # Analyze each zone
        for i, zone_id in enumerate(sample_zones):
            print(f"\nAnalyzing zone {i + 1}/{len(sample_zones)}: {zone_id[:30]}...")
            
            zone_info = await self.analyze_zone(zone_id)
            self.results.append(zone_info)
            
            if zone_info["error"]:
                print(f"  ❌ Error: {zone_info['error']}")
            else:
                print(f"  ✅ Zone: {zone_info['zone_name']}")
                print(f"     Account: {zone_info['account_name']}")
                print(f"     Location: {zone_info['location_name']}")
                print(f"     Paired: {zone_info['is_paired']}, Online: {zone_info['online']}")
                
                # Track versions
                if zone_info["software_version"]:
                    version = zone_info["software_version"]
                    print(f"     App Version: {version}")
                    
                    self.version_distribution[version] = self.version_distribution.get(version, 0) + 1
                    
                    if version not in self.zones_by_version:
                        self.zones_by_version[version] = []
                    self.zones_by_version[version].append({
                        "zone_name": zone_info["zone_name"],
                        "account_name": zone_info["account_name"],
                        "location_name": zone_info["location_name"],
                        "zone_id": zone_id
                    })
                
                # Track subscription states
                sub_state = zone_info["subscription_state"] or "NO_SUBSCRIPTION"
                print(f"     Subscription: {sub_state} (Active: {zone_info['subscription_active']})")
                
                self.subscription_distribution[sub_state] = self.subscription_distribution.get(sub_state, 0) + 1
                
                if sub_state not in self.zones_by_subscription:
                    self.zones_by_subscription[sub_state] = []
                self.zones_by_subscription[sub_state].append({
                    "zone_name": zone_info["zone_name"],
                    "account_name": zone_info["account_name"],
                    "location_name": zone_info["location_name"],
                    "zone_id": zone_id,
                    "app_version": zone_info["software_version"]
                })
            
            # Rate limiting delay
            if i < len(sample_zones) - 1:
                await asyncio.sleep(1)
        
        # Print comprehensive analysis
        self.print_analysis()
        
        # Save detailed results
        self.save_results()

    def print_analysis(self):
        """Print comprehensive analysis of the results."""
        print("\n" + "=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)
        
        # Version distribution
        print("\n📱 APP VERSION DISTRIBUTION:")
        if self.version_distribution:
            sorted_versions = sorted(self.version_distribution.items(), 
                                   key=lambda x: float(x[0]) if x[0] else 0)
            
            for version, count in sorted_versions:
                print(f"  Version {version}: {count} zones")
            
            # Find oldest versions
            versions_float = [float(v) for v in self.version_distribution.keys() if v]
            if versions_float:
                oldest = min(versions_float)
                newest = max(versions_float)
                print(f"\n  Version Range: {oldest} - {newest}")
                
                # Zones with old versions (< 240.0)
                print(f"\n  🔴 Zones with OLD versions (< 240.0):")
                old_version_found = False
                for version, zones in sorted(self.zones_by_version.items()):
                    if version and float(version) < 240.0:
                        old_version_found = True
                        print(f"\n    Version {version}:")
                        for zone in zones[:3]:  # Show up to 3 examples
                            print(f"      • {zone['zone_name']} ({zone['account_name']})")
                            print(f"        Zone ID: {zone['zone_id']}")
                
                if not old_version_found:
                    print("    None found in this sample")
        
        # Subscription distribution
        print(f"\n\n💳 SUBSCRIPTION STATE DISTRIBUTION:")
        for state, count in sorted(self.subscription_distribution.items()):
            print(f"  {state}: {count} zones")
        
        # Zones without subscriptions
        if "NO_SUBSCRIPTION" in self.zones_by_subscription:
            print(f"\n  🔴 Zones WITHOUT subscriptions:")
            for zone in self.zones_by_subscription["NO_SUBSCRIPTION"][:5]:
                print(f"    • {zone['zone_name']} ({zone['account_name']})")
                print(f"      Zone ID: {zone['zone_id']}")
                if zone['app_version']:
                    print(f"      App Version: {zone['app_version']}")
        
        # Zones with cancelled subscriptions
        if "CANCELLED" in self.zones_by_subscription:
            print(f"\n  🟡 Zones with CANCELLED subscriptions:")
            for zone in self.zones_by_subscription["CANCELLED"][:5]:
                print(f"    • {zone['zone_name']} ({zone['account_name']})")
                print(f"      Zone ID: {zone['zone_id']}")
                if zone['app_version']:
                    print(f"      App Version: {zone['app_version']}")
        
        # Summary statistics
        print(f"\n\n📊 SUMMARY STATISTICS:")
        print(f"  Total zones analyzed: {len(self.results)}")
        print(f"  Zones with errors: {sum(1 for r in self.results if r['error'])}")
        print(f"  Zones online: {sum(1 for r in self.results if r['online'])}")
        print(f"  Zones paired: {sum(1 for r in self.results if r['is_paired'])}")
        
        # Interesting patterns
        print(f"\n\n🔍 INTERESTING PATTERNS:")
        
        # Old versions without subscription
        old_no_sub = []
        for zone in self.results:
            if (zone["software_version"] and 
                float(zone["software_version"]) < 240.0 and 
                (zone["subscription_state"] is None or zone["subscription_state"] == "CANCELLED")):
                old_no_sub.append(zone)
        
        if old_no_sub:
            print(f"\n  Zones with OLD versions AND no active subscription ({len(old_no_sub)} found):")
            for zone in old_no_sub[:3]:
                print(f"    • {zone['zone_name']} - Version: {zone['software_version']}, Subscription: {zone['subscription_state'] or 'None'}")

    def save_results(self):
        """Save detailed results to file."""
        output = {
            "timestamp": datetime.now().isoformat(),
            "total_zones_analyzed": len(self.results),
            "version_distribution": self.version_distribution,
            "subscription_distribution": self.subscription_distribution,
            "zones_by_version": self.zones_by_version,
            "zones_by_subscription": self.zones_by_subscription,
            "detailed_results": self.results
        }
        
        filename = f"zone_version_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"\n\n💾 Detailed results saved to {filename}")
        
        # Also save a CSV for easy analysis
        csv_filename = f"zone_version_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(csv_filename, "w") as f:
            # Header
            f.write("Zone ID,Zone Name,Account Name,Location Name,App Version,Subscription State,Is Online,Is Paired\n")
            
            # Data
            for zone in self.results:
                if not zone["error"]:
                    f.write(f'"{zone["zone_id"]}",')
                    f.write(f'"{zone["zone_name"] or ""}",')
                    f.write(f'"{zone["account_name"] or ""}",')
                    f.write(f'"{zone["location_name"] or ""}",')
                    f.write(f'"{zone["software_version"] or ""}",')
                    f.write(f'"{zone["subscription_state"] or "NO_SUBSCRIPTION"}",')
                    f.write(f'{zone["online"] or False},')
                    f.write(f'{zone["is_paired"] or False}\n')
        
        print(f"💾 CSV results saved to {csv_filename}")

    async def close(self):
        """Clean up resources."""
        await self.client.aclose()


async def main():
    analyzer = ZoneVersionAnalyzer()
    try:
        # Analyze 50 zones to get a good sample
        await analyzer.run_analysis(sample_size=50)
    finally:
        await analyzer.close()


if __name__ == "__main__":
    asyncio.run(main())