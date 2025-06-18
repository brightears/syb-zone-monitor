#!/usr/bin/env python3
"""Test script to verify all 6 zone statuses are detected correctly."""

import asyncio
import json
import httpx
from datetime import datetime

async def test_zone_statuses():
    """Test zone status detection with the new fields."""
    
    api_token = "YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg=="
    api_url = "https://api.soundtrackyourbrand.com/v2"
    
    headers = {
        "Authorization": f"Basic {api_token}",
        "Content-Type": "application/json"
    }
    
    # Test query with all the new fields
    test_query = """
    {
        me {
            ... on PublicAPIClient {
                accounts(first: 2) {
                    edges {
                        node {
                            businessName
                            soundZones(first: 3) {
                                edges {
                                    node {
                                        id
                                        name
                                        isPaired
                                        online
                                        device {
                                            id
                                            name
                                            softwareVersion
                                        }
                                        subscription {
                                            isActive
                                            state
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
    
    async with httpx.AsyncClient(timeout=30) as client:
        print("🔍 Testing zone status detection with new fields...")
        print("=" * 60)
        
        try:
            response = await client.post(
                api_url,
                json={"query": test_query},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print("❌ GraphQL Errors:")
                    for error in data["errors"]:
                        print(f"  - {error.get('message', error)}")
                
                if "data" in data and data["data"]:
                    me_data = data["data"].get("me", {})
                    accounts = me_data.get("accounts", {}).get("edges", [])
                    
                    status_examples = {
                        "online": [],
                        "offline": [],
                        "expired": [],
                        "unpaired": [],
                        "no_subscription": [],
                        "outdated": []
                    }
                    
                    for account_edge in accounts:
                        account = account_edge.get("node", {})
                        business_name = account.get("businessName", "Unknown")
                        zones = account.get("soundZones", {}).get("edges", [])
                        
                        for zone_edge in zones:
                            zone = zone_edge.get("node", {})
                            
                            # Extract zone data
                            zone_name = zone.get("name", "Unknown")
                            is_paired = zone.get("isPaired", False)
                            online = zone.get("online", False)
                            device = zone.get("device")
                            subscription = zone.get("subscription", {})
                            subscription_state = subscription.get("state") if subscription else None
                            subscription_active = subscription.get("isActive", True) if subscription else True
                            software_version = device.get("softwareVersion") if device else None
                            
                            # Determine status using the same logic as zone_monitor.py
                            status = determine_status(is_paired, online, device, subscription_active, subscription_state, software_version)
                            
                            zone_info = {
                                "account": business_name,
                                "zone": zone_name,
                                "isPaired": is_paired,
                                "online": online,
                                "hasDevice": device is not None,
                                "deviceName": device.get("name") if device else None,
                                "softwareVersion": software_version,
                                "subscriptionState": subscription_state,
                                "subscriptionActive": subscription_active
                            }
                            
                            status_examples[status].append(zone_info)
                    
                    # Print results
                    print("\n📊 Zone Status Distribution:")
                    print("-" * 40)
                    
                    for status, zones in status_examples.items():
                        print(f"\n{get_status_emoji(status)} {get_status_label(status)}: {len(zones)} zones")
                        
                        if zones and len(zones) > 0:
                            # Show first example
                            example = zones[0]
                            print(f"   Example: {example['zone']} ({example['account']})")
                            print(f"   - isPaired: {example['isPaired']}")
                            print(f"   - online: {example['online']}")
                            print(f"   - device: {example['deviceName'] or 'None'}")
                            if example['softwareVersion']:
                                print(f"   - appVersion: {example['softwareVersion']}")
                            if example['subscriptionState']:
                                print(f"   - subscriptionState: {example['subscriptionState']}")
                    
                    # Save detailed results
                    results = {
                        "timestamp": datetime.now().isoformat(),
                        "status_distribution": {status: len(zones) for status, zones in status_examples.items()},
                        "examples": {status: zones[:2] for status, zones in status_examples.items() if zones}
                    }
                    
                    with open("six_status_test_results.json", "w") as f:
                        json.dump(results, f, indent=2)
                    
                    print(f"\n✅ Test completed! Results saved to six_status_test_results.json")
                    
            else:
                print(f"❌ HTTP {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

def determine_status(is_paired, online, device, subscription_active, subscription_state, software_version):
    """Determine zone status based on the 6 levels (same logic as zone_monitor.py)."""
    # Level 6: No paired device
    if not is_paired or device is None:
        return "unpaired"
    
    # Level 5: No subscription
    if subscription_state is None:
        return "no_subscription"
    
    # Level 4: Subscription expired
    if subscription_state == "EXPIRED" or (subscription_state != "ACTIVE" and not subscription_active):
        return "expired"
    
    # Level 3: App outdated (minimum version is 240.0)
    minimum_version = 240.0
    if software_version:
        try:
            version_float = float(software_version)
            if version_float < minimum_version:
                return "outdated"
        except (ValueError, TypeError):
            pass
    
    # Level 1 & 2: Device is paired, subscription active, app up to date
    if online:
        return "online"    # Level 1: Paired and online
    else:
        return "offline"   # Level 2: Paired but offline

def get_status_emoji(status):
    """Get emoji for status."""
    emojis = {
        "online": "✅",
        "offline": "🔴",
        "expired": "🟠",
        "unpaired": "🔗",
        "no_subscription": "💳",
        "outdated": "📱"
    }
    return emojis.get(status, "❓")

def get_status_label(status):
    """Get human-readable label for status."""
    labels = {
        "online": "Connected",
        "offline": "Offline",
        "expired": "Subscription Expired",
        "unpaired": "No Device Paired",
        "no_subscription": "No Subscription",
        "outdated": "App Update Required"
    }
    return labels.get(status, status.title())

if __name__ == "__main__":
    print("SYB Zone Status Test - All 6 Status Types")
    print(f"Timestamp: {datetime.now()}")
    
    asyncio.run(test_zone_statuses())