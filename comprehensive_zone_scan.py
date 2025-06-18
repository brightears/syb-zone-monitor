#!/usr/bin/env python3
"""
Comprehensive zone scan with better rate limiting and more diverse zones.
"""

import asyncio
import json
from datetime import datetime
import httpx
from typing import Dict, Any, List
import random

# API Configuration
API_TOKEN = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
API_URL = "https://api.soundtrackyourbrand.com/v2"

# Extended diverse list of zone IDs from different accounts
ZONE_IDS = [
    # From GF ISABEL (Free Trial expected to have different states)
    "U291bmRab25lLCwxanU5NGtyMmViay9Mb2NhdGlvbiwsMWc5OGI1dm5jM2svQWNjb3VudCwsMWZ0eGhhYTl0a3cv",
    
    # From HOTEL MADE IN LOUISE (Cancelled subscription)
    "U291bmRab25lLCwxc21hNTdwOXN6ay9Mb2NhdGlvbiwsMWo3aTdjYmczY3cvQWNjb3VudCwsMWU1OTBhenpremsv",
    
    # From Hotel Riu Oliva Beach Resort (Various zones)
    "U291bmRab25lLCwxY2xnZG83b2dlOC9Mb2NhdGlvbiwsMXRva2s4cHRjemsvQWNjb3VudCwsMXRiOThzZDMwMXMv",
    "U291bmRab25lLCwxbzhpZWJoaTNuay9Mb2NhdGlvbiwsMXRva2s4cHRjemsvQWNjb3VudCwsMXRiOThzZDMwMXMv",
    
    # From Grand Palladium Palace Resort Spa & Casino
    "U291bmRab25lLCwxbnl0a3R4djR6ay9Mb2NhdGlvbiwsMXQwa3lsM3JmdW8vQWNjb3VudCwsMXNjOHNycmUwYW8v",
    "U291bmRab25lLCwxZDRiazk4MW1sby9Mb2NhdGlvbiwsMXQwa3lsM3JmdW8vQWNjb3VudCwsMXNjOHNycmUwYW8v",
    "U291bmRab25lLCwxcm9nb2xzaTZwYy9Mb2NhdGlvbiwsMXQwa3lsM3JmdW8vQWNjb3VudCwsMXNjOHNycmUwYW8v",
    
    # From IBEROSTAR Hotels
    "U291bmRab25lLCwxcmh0b2xqdzNjdy9Mb2NhdGlvbiwsMW5oOHA2dXlxZGMvQWNjb3VudCwsMXJsbmd0eDZ3b3cv",
    
    # From Park Club Europe
    "U291bmRab25lLCwxbWF1YzE2ZWlvMC9Mb2NhdGlvbiwsMXNyc2h6dGZ1OXMvQWNjb3VudCwsMThtYnZ5amV2NDAv",
    
    # From Ramada Plaza by Wyndham Waikiki (might have different versions)
    "U291bmRab25lLCwxYXFicXVuMWJscy9Mb2NhdGlvbiwsMWtpNXdrd2dsYzAvQWNjb3VudCwsMXF0cjB5YXh5cHMv",
    
    # Desert Rock Resort zones (248.0 versions)
    "U291bmRab25lLCwxbnNrdnVtdXd3MC9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxbGRxZ2cwcG12NC9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxbzVqeXdvMjVmay9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxc2hkemw2azR4cy9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxYW9jcmF4d2lyay9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxZzdzNnkxaWs4dy9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxb2ZyNDhhbHc1Yy9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    
    # More random zones from different accounts
    "U291bmRab25lLCwxdTQ2NDBpNXg4MC9Mb2NhdGlvbiwsMWo3aTdjYmczY3cvQWNjb3VudCwsMWU1OTBhenpremsv",
    "U291bmRab25lLCwxbjFteGk0NHJnZy9Mb2NhdGlvbiwsMWdoZXh3eDdhNGcvQWNjb3VudCwsMW1sbTJ0ZW52OWMv",
    "U291bmRab25lLCwxcDEzcWhzYTBhby9Mb2NhdGlvbiwsMThscnUwenZldjQvQWNjb3VudCwsMWVuaXV0emJhYmsv",
    
    # Additional zones that might have older versions
    "U291bmRab25lLCwxZGQzcnFqNDVqNC9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxcGlmZGlzNjFhOC9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxdDBmeXJoNXQ2by9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxYTZ5ZmgxNGdnby9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    "U291bmRab25lLCwxOXAweXZ0dWw4Zy9Mb2NhdGlvbiwsMWo3d2pxM3ZhNGcvQWNjb3VudCwsMWNqMTM3Ymp3MXMv",
    
    # Test more zones from the test_subscription_states.py list
    "U291bmRab25lLCwxcDFzMGRwM3AwOC9Mb2NhdGlvbiwsMWc5OGI1dm5jM2svQWNjb3VudCwsMWZ0eGhhYTl0a3cv",
    "U291bmRab25lLCwxcGdhMHdwem9vdy9Mb2NhdGlvbiwsMWc5OGI1dm5jM2svQWNjb3VudCwsMWZ0eGhhYTl0a3cv",
    "U291bmRab25lLCwxZ3B5OWl3d2Zlby9Mb2NhdGlvbiwsMWc5OGI1dm5jM2svQWNjb3VudCwsMWZ0eGhhYTl0a3cv",
    "U291bmRab25lLCwxdDl2ZDdvYnIxcy9Mb2NhdGlvbiwsMWc5OGI1dm5jM2svQWNjb3VudCwsMWZ0eGhhYTl0a3cv",
    "U291bmRab25lLCwxcXNhcXJsMnRjZy9Mb2NhdGlvbiwsMWc5OGI1dm5jM2svQWNjb3VudCwsMWZ0eGhhYTl0a3cv"
]


async def query_zone_minimal(client: httpx.AsyncClient, zone_id: str) -> Dict[str, Any]:
    """Query a single zone with minimal fields to reduce token cost."""
    query = """
    query GetZoneMinimal($zoneId: ID!) {
        soundZone(id: $zoneId) {
            id
            name
            isPaired
            online
            device {
                softwareVersion
            }
            subscription {
                state
            }
            account {
                businessName
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
    """Main function to scan zones comprehensively."""
    print("=" * 80)
    print("COMPREHENSIVE ZONE VERSION AND SUBSCRIPTION SCAN")
    print(f"Timestamp: {datetime.now()}")
    print(f"Scanning {len(ZONE_IDS)} zones with rate limiting...")
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
    zones_by_version_range = {
        "below_240": [],
        "240_to_245": [],
        "above_245": []
    }
    zones_by_subscription = {
        "NO_SUBSCRIPTION": [],
        "CANCELLED": [],
        "EXPIRED": [],
        "ACTIVE": [],
        "OTHER": []
    }
    
    try:
        # Shuffle zones to get variety
        shuffled_zones = ZONE_IDS.copy()
        random.shuffle(shuffled_zones)
        
        successful_queries = 0
        
        for i, zone_id in enumerate(shuffled_zones):
            print(f"\nZone {i + 1}/{len(shuffled_zones)}: {zone_id[:30]}...")
            
            # Longer delay to avoid rate limiting
            if i > 0:
                await asyncio.sleep(5)  # 5 second delay between requests
            
            result = await query_zone_minimal(client, zone_id)
            
            if "errors" in result:
                error_msg = result['errors'][0].get('message', 'Unknown error')
                print(f"  ❌ Error: {error_msg}")
                
                # If rate limited, wait longer
                if "rate limited" in error_msg:
                    print("  ⏳ Waiting 30 seconds due to rate limit...")
                    await asyncio.sleep(30)
                continue
            
            if "data" in result and result["data"] and result["data"]["soundZone"]:
                zone = result["data"]["soundZone"]
                successful_queries += 1
                
                # Extract info
                zone_name = zone.get("name", "Unknown")
                is_paired = zone.get("isPaired", False)
                online = zone.get("online", False)
                
                account = zone.get("account", {})
                account_name = account.get("businessName", "Unknown") if account else "Unknown"
                
                device = zone.get("device", {})
                software_version = device.get("softwareVersion") if device else None
                
                subscription = zone.get("subscription", {})
                subscription_state = subscription.get("state") if subscription else "NO_SUBSCRIPTION"
                
                # Print summary
                print(f"  ✅ {zone_name} ({account_name})")
                print(f"     Paired: {is_paired}, Online: {online}")
                
                if software_version:
                    print(f"     App Version: {software_version}")
                    version_distribution[software_version] = version_distribution.get(software_version, 0) + 1
                    
                    # Categorize by version range
                    version_float = float(software_version)
                    zone_info = {
                        "zone_name": zone_name,
                        "account_name": account_name,
                        "version": software_version,
                        "zone_id": zone_id,
                        "subscription_state": subscription_state
                    }
                    
                    if version_float < 240.0:
                        zones_by_version_range["below_240"].append(zone_info)
                    elif version_float <= 245.0:
                        zones_by_version_range["240_to_245"].append(zone_info)
                    else:
                        zones_by_version_range["above_245"].append(zone_info)
                
                print(f"     Subscription: {subscription_state}")
                subscription_distribution[subscription_state] = subscription_distribution.get(subscription_state, 0) + 1
                
                # Categorize by subscription
                zone_sub_info = {
                    "zone_name": zone_name,
                    "account_name": account_name,
                    "version": software_version,
                    "zone_id": zone_id
                }
                
                if subscription_state in zones_by_subscription:
                    zones_by_subscription[subscription_state].append(zone_sub_info)
                else:
                    zones_by_subscription["OTHER"].append(zone_sub_info)
                
                # Store result
                results.append({
                    "zone_id": zone_id,
                    "zone_name": zone_name,
                    "account_name": account_name,
                    "is_paired": is_paired,
                    "online": online,
                    "software_version": software_version,
                    "subscription_state": subscription_state
                })
        
        # Print comprehensive analysis
        print("\n" + "=" * 80)
        print("COMPREHENSIVE ANALYSIS RESULTS")
        print("=" * 80)
        print(f"\nSuccessfully queried {successful_queries} zones")
        
        print("\n📱 APP VERSION DISTRIBUTION:")
        if version_distribution:
            sorted_versions = sorted(version_distribution.items(), key=lambda x: float(x[0]))
            for version, count in sorted_versions:
                print(f"  Version {version}: {count} zones")
            
            versions_float = [float(v) for v in version_distribution.keys()]
            print(f"\n  Version Range: {min(versions_float)} - {max(versions_float)}")
            
            print("\n  VERSION RANGES:")
            print(f"  • Below 240.0: {len(zones_by_version_range['below_240'])} zones")
            print(f"  • 240.0-245.0: {len(zones_by_version_range['240_to_245'])} zones")
            print(f"  • Above 245.0: {len(zones_by_version_range['above_245'])} zones")
        
        print(f"\n💳 SUBSCRIPTION STATE DISTRIBUTION:")
        for state, count in sorted(subscription_distribution.items()):
            print(f"  {state}: {count} zones")
        
        # Show examples of interesting cases
        if zones_by_version_range["below_240"]:
            print(f"\n🔴 ZONES WITH OLD VERSIONS (< 240.0):")
            for zone in zones_by_version_range["below_240"][:5]:
                print(f"  • {zone['zone_name']} ({zone['account_name']})")
                print(f"    Version: {zone['version']}, Subscription: {zone['subscription_state']}")
                print(f"    Zone ID: {zone['zone_id']}")
        
        if zones_by_subscription["NO_SUBSCRIPTION"]:
            print(f"\n🔴 ZONES WITHOUT SUBSCRIPTIONS:")
            for zone in zones_by_subscription["NO_SUBSCRIPTION"][:5]:
                print(f"  • {zone['zone_name']} ({zone['account_name']})")
                if zone['version']:
                    print(f"    Version: {zone['version']}")
                print(f"    Zone ID: {zone['zone_id']}")
        
        if zones_by_subscription["CANCELLED"]:
            print(f"\n🟡 ZONES WITH CANCELLED SUBSCRIPTIONS:")
            for zone in zones_by_subscription["CANCELLED"][:5]:
                print(f"  • {zone['zone_name']} ({zone['account_name']})")
                if zone['version']:
                    print(f"    Version: {zone['version']}")
                print(f"    Zone ID: {zone['zone_id']}")
        
        # Save comprehensive results
        output = {
            "timestamp": datetime.now().isoformat(),
            "total_zones_scanned": len(shuffled_zones),
            "successful_queries": successful_queries,
            "version_distribution": version_distribution,
            "subscription_distribution": subscription_distribution,
            "zones_by_version_range": zones_by_version_range,
            "zones_by_subscription": zones_by_subscription,
            "detailed_results": results
        }
        
        filename = f"comprehensive_zone_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Comprehensive results saved to {filename}")
        
        # Also create a CSV for easy analysis
        csv_filename = f"comprehensive_zone_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(csv_filename, "w") as f:
            f.write("Zone ID,Zone Name,Account Name,App Version,Subscription State,Is Paired,Is Online\n")
            for zone in results:
                f.write(f'"{zone["zone_id"]}",')
                f.write(f'"{zone["zone_name"]}",')
                f.write(f'"{zone["account_name"]}",')
                f.write(f'"{zone.get("software_version", "")}",')
                f.write(f'"{zone["subscription_state"]}",')
                f.write(f'{zone["is_paired"]},')
                f.write(f'{zone["online"]}\n')
        
        print(f"💾 CSV results saved to {csv_filename}")
        
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())