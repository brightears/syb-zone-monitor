#!/usr/bin/env python3
"""Final analysis of available fields for enhanced zone status detection."""

import asyncio
import json
import httpx
from config import Config


async def test_confirmed_fields():
    """Test only the fields we're confident exist."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    # Test subscription fields one by one to see what exists
    subscription_tests = [
        {
            "name": "Subscription - isActive only",
            "query": """
            query GetZoneStatus($zoneId: ID!) {
                soundZone(id: $zoneId) {
                    id
                    name
                    isPaired
                    online
                    subscription {
                        isActive
                    }
                }
            }
            """
        },
        {
            "name": "Subscription - isSuspended only", 
            "query": """
            query GetZoneStatus($zoneId: ID!) {
                soundZone(id: $zoneId) {
                    id
                    name
                    isPaired
                    online
                    subscription {
                        isSuspended
                    }
                }
            }
            """
        },
        {
            "name": "Subscription - expiresAt only",
            "query": """
            query GetZoneStatus($zoneId: ID!) {
                soundZone(id: $zoneId) {
                    id
                    name
                    isPaired
                    online
                    subscription {
                        expiresAt
                    }
                }
            }
            """
        },
        {
            "name": "Subscription - trialEndsAt only",
            "query": """
            query GetZoneStatus($zoneId: ID!) {
                soundZone(id: $zoneId) {
                    id
                    name
                    isPaired
                    online
                    subscription {
                        trialEndsAt
                    }
                }
            }
            """
        }
    ]
    
    zone_id = config.zone_ids[0]
    variables = {"zoneId": zone_id}
    
    print(f"Testing subscription fields individually for zone: {zone_id}")
    
    working_subscription_fields = []
    
    async with httpx.AsyncClient(timeout=config.request_timeout) as client:
        
        for test in subscription_tests:
            print(f"\n--- {test['name']} ---")
            
            try:
                response = await client.post(
                    config.syb_api_url,
                    json={"query": test["query"], "variables": variables},
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "errors" in data:
                        print("❌ Errors:", [e.get('message') for e in data['errors']])
                    else:
                        zone_data = data["data"].get("soundZone", {})
                        subscription = zone_data.get("subscription", {})
                        
                        field_name = list(subscription.keys())[0] if subscription else None
                        if field_name:
                            field_value = subscription[field_name]
                            print(f"✅ {field_name}: {field_value}")
                            working_subscription_fields.append(field_name)
                        else:
                            print("❌ No subscription data")
                else:
                    print(f"❌ HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Request failed: {e}")
        
        # Now test the final comprehensive query with only working fields
        print(f"\n{'='*60}")
        print(f"FINAL COMPREHENSIVE QUERY WITH WORKING FIELDS")
        print(f"{'='*60}")
        
        working_fields = ["isActive"] if "isActive" in working_subscription_fields else []
        if "isSuspended" in working_subscription_fields:
            working_fields.append("isSuspended")
        if "expiresAt" in working_subscription_fields:
            working_fields.append("expiresAt")
        if "trialEndsAt" in working_subscription_fields:
            working_fields.append("trialEndsAt")
        
        subscription_fields_str = "\n                        ".join(working_fields) if working_fields else ""
        
        final_query = f"""
        query GetZoneStatus($zoneId: ID!) {{
            soundZone(id: $zoneId) {{
                id
                name
                isPaired
                online
                device {{
                    id
                    name
                    type
                    platform
                    isPairing
                }}
                subscription {{
                    {subscription_fields_str}
                }}
            }}
        }}
        """
        
        print(f"Query with working fields:")
        print(final_query)
        
        try:
            response = await client.post(
                config.syb_api_url,
                json={"query": final_query, "variables": variables},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print("❌ Final query errors:", [e.get('message') for e in data['errors']])
                else:
                    zone_data = data["data"].get("soundZone", {})
                    print("✅ Final comprehensive data:")
                    print(json.dumps(zone_data, indent=2))
                    
                    # Analyze for status detection
                    analyze_final_status(zone_data, working_fields)
            else:
                print(f"❌ Final query HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Final query failed: {e}")


def analyze_final_status(zone_data, available_subscription_fields):
    """Analyze the final comprehensive zone data."""
    
    print(f"\n🔍 FINAL STATUS ANALYSIS")
    print(f"Available subscription fields: {available_subscription_fields}")
    
    # Extract data
    is_paired = zone_data.get("isPaired", False)
    is_online = zone_data.get("online", False)
    device = zone_data.get("device")
    subscription = zone_data.get("subscription", {})
    zone_name = zone_data.get("name", "Unknown")
    
    print(f"\nZone: {zone_name}")
    print(f"Basic status: isPaired={is_paired}, online={is_online}")
    
    # Device analysis
    if device:
        print(f"Device: {device.get('name')} ({device.get('type')})")
        print(f"Device pairing: {device.get('isPairing')}")
    else:
        print(f"Device: None (device=null)")
    
    # Subscription analysis
    if subscription:
        print(f"Subscription data:")
        for field in available_subscription_fields:
            value = subscription.get(field)
            print(f"  {field}: {value}")
    else:
        print(f"Subscription: No data available")
    
    # Enhanced status determination
    print(f"\n🎯 ENHANCED STATUS DETERMINATION:")
    
    # Level 4: No paired device
    if not is_paired or device is None:
        status = "4. No paired device"
        reasoning = "isPaired=False" if not is_paired else "device=null"
        fields_used = ["isPaired"] if not is_paired else ["device"]
    
    # Level 3: Subscription issues (if we have subscription data)
    elif subscription:
        subscription_issue = None
        if "isActive" in available_subscription_fields and not subscription.get("isActive", True):
            subscription_issue = f"isActive={subscription.get('isActive')}"
        elif "isSuspended" in available_subscription_fields and subscription.get("isSuspended", False):
            subscription_issue = f"isSuspended={subscription.get('isSuspended')}"
        
        if subscription_issue:
            status = "3. Subscription expired"
            reasoning = subscription_issue
            fields_used = ["subscription." + subscription_issue.split("=")[0]]
        else:
            # Level 1 or 2: Based on online status
            if is_online:
                status = "1. Paired and online"
                reasoning = "isPaired=True AND online=True"
                fields_used = ["isPaired", "online"]
            else:
                status = "2. Paired but offline"
                reasoning = "isPaired=True BUT online=False"
                fields_used = ["isPaired", "online"]
    
    # Level 1 or 2: No subscription data available, use basic fields
    else:
        if is_online:
            status = "1. Paired and online"
            reasoning = "isPaired=True AND online=True (no subscription data to check)"
            fields_used = ["isPaired", "online"]
        else:
            status = "2. Paired but offline"
            reasoning = "isPaired=True BUT online=False (no subscription data to check)"
            fields_used = ["isPaired", "online"]
    
    print(f"Status: {status}")
    print(f"Reasoning: {reasoning}")
    print(f"Fields used: {fields_used}")
    
    # Implementation recommendations
    print(f"\n💡 IMPLEMENTATION RECOMMENDATIONS:")
    print(f"Current zone_monitor.py logic:")
    print(f"  - Only checks 'isPaired' field")
    print(f"  - isPaired=True → Zone online")
    print(f"  - isPaired=False → Zone offline")
    
    print(f"\nEnhanced logic could be:")
    print(f"  1. Check if device exists (device != null)")
    print(f"  2. Check isPaired status")
    if "isActive" in available_subscription_fields:
        print(f"  3. Check subscription.isActive")
    if "isSuspended" in available_subscription_fields:
        print(f"  4. Check subscription.isSuspended")
    print(f"  5. Check online status")
    
    print(f"\nRecommended GraphQL query for zone_monitor.py:")
    subscription_fields = []
    if "isActive" in available_subscription_fields:
        subscription_fields.append("isActive")
    if "isSuspended" in available_subscription_fields:
        subscription_fields.append("isSuspended")
    
    sub_query = ""
    if subscription_fields:
        sub_fields = "\n                    ".join(subscription_fields)
        sub_query = f"""
                subscription {{
                    {sub_fields}
                }}"""
    
    recommended_query = f"""
    query GetZoneStatus($zoneId: ID!) {{
        soundZone(id: $zoneId) {{
            id
            name
            isPaired
            online
            device {{
                id
                name
            }}{sub_query}
        }}
    }}
    """
    
    print(recommended_query)


async def test_multiple_zones_final():
    """Test the final enhanced query on multiple zones to see different patterns."""
    
    config = Config.from_env()
    
    headers = {
        "Authorization": f"Basic {config.syb_api_key}",
        "Content-Type": "application/json"
    }
    
    # Use the proven working query
    query = """
    query GetZoneStatus($zoneId: ID!) {
        soundZone(id: $zoneId) {
            id
            name
            isPaired
            online
            device {
                id
                name
                type
            }
            subscription {
                isActive
            }
        }
    }
    """
    
    print(f"\n{'='*60}")
    print(f"TESTING ENHANCED STATUS DETECTION ON MULTIPLE ZONES")
    print(f"{'='*60}")
    
    async with httpx.AsyncClient(timeout=config.request_timeout) as client:
        
        for i, zone_id in enumerate(config.zone_ids[:5]):  # Test first 5 zones
            print(f"\nZone {i+1}:")
            
            try:
                variables = {"zoneId": zone_id}
                response = await client.post(
                    config.syb_api_url,
                    json={"query": query, "variables": variables},
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "data" in data and data["data"]:
                        zone_data = data["data"].get("soundZone")
                        if zone_data:
                            name = zone_data.get("name", "Unknown")
                            is_paired = zone_data.get("isPaired", False)
                            is_online = zone_data.get("online", False)
                            device = zone_data.get("device")
                            subscription = zone_data.get("subscription", {})
                            
                            print(f"  {name}")
                            print(f"    Basic: isPaired={is_paired}, online={is_online}")
                            print(f"    Device: {'Yes' if device else 'None'}")
                            print(f"    Subscription active: {subscription.get('isActive', 'Unknown')}")
                            
                            # Determine enhanced status
                            if not is_paired or device is None:
                                enhanced_status = "4. No paired device"
                            elif not subscription.get("isActive", True):
                                enhanced_status = "3. Subscription expired"
                            elif is_paired and is_online:
                                enhanced_status = "1. Paired and online"
                            else:
                                enhanced_status = "2. Paired but offline"
                            
                            current_status = "Online" if is_paired else "Offline"
                            
                            print(f"    Current logic: {current_status}")
                            print(f"    Enhanced logic: {enhanced_status}")
                            
                            if current_status == "Online" and "offline" in enhanced_status.lower():
                                print(f"    ⚠️  Current logic would miss this offline state!")
                            elif current_status == "Online" and "expired" in enhanced_status.lower():
                                print(f"    ⚠️  Current logic would miss subscription issue!")
                        else:
                            print(f"  ❌ No zone data")
                else:
                    print(f"  ❌ HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Request failed: {e}")


if __name__ == "__main__":
    print("SYB Final Field Analysis")
    print("Determining exactly what fields are available for enhanced status detection")
    print("="*80)
    
    asyncio.run(test_confirmed_fields())
    asyncio.run(test_multiple_zones_final())