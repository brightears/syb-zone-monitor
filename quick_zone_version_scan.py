#!/usr/bin/env python3
"""
Quick scan of zone versions and subscription states using known zone IDs.
"""

import asyncio
import json
from datetime import datetime
import httpx
from typing import Dict, Any, List

# API Configuration
API_TOKEN = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
API_URL = "https://api.soundtrackyourbrand.com/v2"

# Extended list of zone IDs to test
ZONE_IDS = [
    # First batch
    "U291bmRab25lLCwxbjFteGk0NHJnZy9Mb2NhdGlvbiwsMWdoZXh3eDdhNGcvQWNjb3VudCwsMW1sbTJ0ZW52OWMv",
    "U291bmRab25lLCwxcDEzcWhzYTBhby9Mb2NhdGlvbiwsMThscnUwenZldjQvQWNjb3VudCwsMWVuaXV0emJhYmsv",
    "U291bmRab25lLCwxbnNrdnVtdXd3MC9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxbGRxZ2cwcG12NC9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxbzVqeXdvMjVmay9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    
    # Second batch
    "U291bmRab25lLCwxc2hkemw2azR4cy9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxYW9jcmF4d2lyay9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxZzdzNnkxaWs4dy9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxb2ZyNDhhbHc1Yy9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxZGQzcnFqNDVqNC9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    
    # Third batch
    "U291bmRab25lLCwxcGlmZGlzNjFhOC9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxdDBmeXJoNXQ2by9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxanU5NGtyMmViay9Mb2NhdGlvbiwsMWc5OGI1dm5jM2svQWNjb3VudCwsMWZ0eGhhYTl0a3cv",
    "U291bmRab25lLCwxc21hNTdwOXN6ay9Mb2NhdGlvbiwsMWo3aTdjYmczY3cvQWNjb3VudCwsMWU1OTBhenpremsv",
    "U291bmRab25lLCwxY2xnZG83b2dlOC9Mb2NhdGlvbiwsMXRva2s4cHRjemsvQWNjb3VudCwsMXRiOThzZDMwMXMv",
    
    # Fourth batch
    "U291bmRab25lLCwxbzhpZWJoaTNuay9Mb2NhdGlvbiwsMXRva2s4cHRjemsvQWNjb3VudCwsMXRiOThzZDMwMXMv",
    "U291bmRab25lLCwxbnl0a3R4djR6ay9Mb2NhdGlvbiwsMXQwa3lsM3JmdW8vQWNjb3VudCwsMXNjOHNycmUwYW8v",
    "U291bmRab25lLCwxcmh0b2xqdzNjdy9Mb2NhdGlvbiwsMW5oOHA2dXlxZGMvQWNjb3VudCwsMXJsbmd0eDZ3b3cv",
    "U291bmRab25lLCwxbWF1YzE2ZWlvMC9Mb2NhdGlvbiwsMXNyc2h6dGZ1OXMvQWNjb3VudCwsMThtYnZ5amV2NDAv",
    "U291bmRab25lLCwxYXFicXVuMWJscy9Mb2NhdGlvbiwsMWtpNXdrd2dsYzAvQWNjb3VudCwsMXF0cjB5YXh5cHMv",
    
    # Additional zones
    "U291bmRab25lLCwxYTZ5ZmgxNGdnby9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxOXAweXZ0dWw4Zy9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxZDRiazk4MW1sby9Mb2NhdGlvbiwsMXQwa3lsM3JmdW8vQWNjb3VudCwsMXNjOHNycmUwYW8v",
    "U291bmRab25lLCwxcm9nb2xzaTZwYy9Mb2NhdGlvbiwsMXQwa3lsM3JmdW8vQWNjb3VudCwsMXNjOHNycmUwYW8v",
    "U291bmRab25lLCwxdTQ2NDBpNXg4MC9Mb2NhdGlvbiwsMWo3aTdjYmczY3cvQWNjb3VudCwsMWU1OTBhenpremsv"
]


async def query_zone(client: httpx.AsyncClient, zone_id: str) -> Dict[str, Any]:
    """Query a single zone for its details."""
    query = """
    query GetZoneDetails($zoneId: ID!) {
        soundZone(id: $zoneId) {
            id
            name
            isPaired
            online
            
            device {
                id
                name
                softwareVersion
                osVersion
            }
            
            subscription {
                isActive
                state
            }
            
            account {
                id
                businessName
            }
            
            location {
                id
                name
            }
        }
    }
    """
    
    try:
        response = await client.post(
            API_URL,
            json={"query": query, "variables": {"zoneId": zone_id}}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


async def main():
    """Main function to scan zones."""
    print("=" * 80)
    print("ZONE VERSION AND SUBSCRIPTION SCAN")
    print(f"Timestamp: {datetime.now()}")
    print(f"Scanning {len(ZONE_IDS)} zones...")
    print("=" * 80)
    
    client = httpx.AsyncClient(
        timeout=30,
        headers={
            "Authorization": f"Basic {API_TOKEN}",
            "Content-Type": "application/json"
        }
    )
    
    results = []
    version_distribution = {}
    subscription_distribution = {}
    zones_with_old_versions = []
    zones_without_subscriptions = []
    
    try:
        for i, zone_id in enumerate(ZONE_IDS):
            print(f"\nZone {i + 1}/{len(ZONE_IDS)}: {zone_id[:30]}...")
            
            result = await query_zone(client, zone_id)
            
            if "errors" in result:
                print(f"  ❌ Error: {result['errors'][0].get('message', 'Unknown error')}")
                continue
            
            if "data" in result and result["data"] and result["data"]["soundZone"]:
                zone = result["data"]["soundZone"]
                
                # Extract info
                zone_name = zone.get("name", "Unknown")
                is_paired = zone.get("isPaired", False)
                online = zone.get("online", False)
                
                account = zone.get("account", {})
                account_name = account.get("businessName", "Unknown") if account else "Unknown"
                
                location = zone.get("location", {})
                location_name = location.get("name", "Unknown") if location else "Unknown"
                
                device = zone.get("device", {})
                software_version = device.get("softwareVersion") if device else None
                
                subscription = zone.get("subscription", {})
                subscription_state = subscription.get("state") if subscription else "NO_SUBSCRIPTION"
                subscription_active = subscription.get("isActive", False) if subscription else False
                
                # Print summary
                print(f"  ✅ {zone_name} ({account_name} - {location_name})")
                print(f"     Paired: {is_paired}, Online: {online}")
                
                if software_version:
                    print(f"     App Version: {software_version}")
                    version_distribution[software_version] = version_distribution.get(software_version, 0) + 1
                    
                    # Check for old versions
                    if float(software_version) < 240.0:
                        zones_with_old_versions.append({
                            "zone_name": zone_name,
                            "account_name": account_name,
                            "location_name": location_name,
                            "version": software_version,
                            "zone_id": zone_id
                        })
                
                print(f"     Subscription: {subscription_state} (Active: {subscription_active})")
                subscription_distribution[subscription_state] = subscription_distribution.get(subscription_state, 0) + 1
                
                # Check for no subscription
                if subscription_state == "NO_SUBSCRIPTION":
                    zones_without_subscriptions.append({
                        "zone_name": zone_name,
                        "account_name": account_name,
                        "location_name": location_name,
                        "version": software_version,
                        "zone_id": zone_id
                    })
                
                # Store result
                results.append({
                    "zone_id": zone_id,
                    "zone_name": zone_name,
                    "account_name": account_name,
                    "location_name": location_name,
                    "is_paired": is_paired,
                    "online": online,
                    "software_version": software_version,
                    "subscription_state": subscription_state,
                    "subscription_active": subscription_active
                })
            
            # Rate limiting
            if i < len(ZONE_IDS) - 1:
                await asyncio.sleep(1)
        
        # Print analysis
        print("\n" + "=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)
        
        print("\n📱 APP VERSION DISTRIBUTION:")
        if version_distribution:
            sorted_versions = sorted(version_distribution.items(), key=lambda x: float(x[0]))
            for version, count in sorted_versions:
                print(f"  Version {version}: {count} zones")
            
            versions_float = [float(v) for v in version_distribution.keys()]
            print(f"\n  Version Range: {min(versions_float)} - {max(versions_float)}")
        
        print(f"\n💳 SUBSCRIPTION STATE DISTRIBUTION:")
        for state, count in sorted(subscription_distribution.items()):
            print(f"  {state}: {count} zones")
        
        if zones_with_old_versions:
            print(f"\n🔴 ZONES WITH OLD VERSIONS (< 240.0): {len(zones_with_old_versions)}")
            for zone in zones_with_old_versions[:5]:
                print(f"  • {zone['zone_name']} ({zone['account_name']})")
                print(f"    Version: {zone['version']}")
                print(f"    Zone ID: {zone['zone_id']}")
        
        if zones_without_subscriptions:
            print(f"\n🔴 ZONES WITHOUT SUBSCRIPTIONS: {len(zones_without_subscriptions)}")
            for zone in zones_without_subscriptions[:5]:
                print(f"  • {zone['zone_name']} ({zone['account_name']})")
                if zone['version']:
                    print(f"    Version: {zone['version']}")
                print(f"    Zone ID: {zone['zone_id']}")
        
        # Save results
        output = {
            "timestamp": datetime.now().isoformat(),
            "total_zones_scanned": len(results),
            "version_distribution": version_distribution,
            "subscription_distribution": subscription_distribution,
            "zones_with_old_versions": zones_with_old_versions,
            "zones_without_subscriptions": zones_without_subscriptions,
            "detailed_results": results
        }
        
        filename = f"zone_version_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Results saved to {filename}")
        
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())