#!/usr/bin/env python3
"""Quick test of the dashboard with new account mapping."""

import asyncio
from datetime import datetime

from config import Config
from zone_monitor import ZoneMonitor
from web_server import DashboardServer


async def quick_test():
    """Quick test of dashboard functionality."""
    print("🔍 Testing Updated Dashboard")
    print(f"Timestamp: {datetime.now()}")
    
    # Load config
    config = Config.from_env()
    print(f"✅ Loaded config with {len(config.zone_ids)} zones")
    
    # Create monitor  
    monitor = ZoneMonitor(config)
    
    # Check a few zones quickly
    print("🔍 Checking first 10 zones...")
    test_zones = config.zone_ids[:10]
    
    zone_results = {}
    for zone_id in test_zones:
        try:
            is_online, zone_name = await monitor._check_zone_status(zone_id)
            zone_results[zone_id] = {"name": zone_name, "online": is_online}
            print(f"  {'🟢' if is_online else '🔴'} {zone_name}")
        except Exception as e:
            print(f"  ❌ Error checking {zone_id}: {e}")
    
    # Create dashboard and test account mapping  
    dashboard = DashboardServer(monitor)
    
    print(f"\n🔍 Testing Account Name Mapping...")
    for zone_id, result in zone_results.items():
        account_name = dashboard._determine_account_name(result["name"], zone_id)
        print(f"  {result['name']} → {account_name}")
    
    await monitor.close()
    print(f"\n✅ Quick test completed!")


if __name__ == "__main__":
    asyncio.run(quick_test())