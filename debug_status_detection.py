#!/usr/bin/env python3
"""Debug script to test status detection locally."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zone_monitor import ZoneMonitor
from config import Config
import logging

logging.basicConfig(level=logging.DEBUG)

async def test_status_detection():
    """Test the status detection with real zones."""
    config = Config()
    monitor = ZoneMonitor(config)
    
    print("Testing zone status detection...")
    print("=" * 60)
    
    # Check a few specific zones
    test_zone_ids = [
        "U291bmRab25lLCwxcmh0b2xqdzNjdy9Mb2NhdGlvbiwsMW5oOHA2dXlxZGMvQWNjb3VudCwsMXJsbmd0eDZ3b3cv",  # Version 235
        "U291bmRab25lLCwxYXFicXVuMWJscy9Mb2NhdGlvbiwsMWtpNXdrd2dsYzAvQWNjb3VudCwsMXF0cjB5YXh5cHMv",  # Version 57.15
    ]
    
    for zone_id in test_zone_ids[:1]:  # Test just one to avoid rate limits
        try:
            status, name, details = await monitor._check_zone_status(zone_id)
            print(f"\nZone: {name}")
            print(f"Status: {status}")
            print(f"Details: {details}")
            print(f"Status Label: {monitor._get_status_label(status)}")
        except Exception as e:
            print(f"Error checking zone {zone_id}: {e}")
    
    # Also check the status determination logic directly
    print("\n" + "=" * 60)
    print("Testing status determination logic:")
    
    # Test case 1: Outdated app
    status1 = monitor._determine_zone_status(
        is_paired=True,
        online=True,
        device={"id": "123"},
        subscription_active=True,
        subscription_state="ACTIVE",
        software_version=235.0
    )
    print(f"Test 1 - App version 235.0: {status1} (expected: outdated)")
    
    # Test case 2: No subscription
    status2 = monitor._determine_zone_status(
        is_paired=True,
        online=True,
        device={"id": "123"},
        subscription_active=True,
        subscription_state=None,
        software_version=248.0
    )
    print(f"Test 2 - No subscription state: {status2} (expected: no_subscription)")
    
    # Test case 3: Expired subscription
    status3 = monitor._determine_zone_status(
        is_paired=True,
        online=True,
        device={"id": "123"},
        subscription_active=False,
        subscription_state="CANCELLED",
        software_version=248.0
    )
    print(f"Test 3 - Cancelled subscription: {status3} (expected: expired)")
    
    await monitor.close()

if __name__ == "__main__":
    asyncio.run(test_status_detection())