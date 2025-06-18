#!/usr/bin/env python3
"""Test the status detection priority fix."""

from zone_monitor import ZoneMonitor

# Create a dummy zone monitor to test the logic
class DummyConfig:
    zone_ids = []
    syb_api_key = "dummy"
    syb_api_url = "dummy"
    request_timeout = 30
    max_retries = 3

monitor = ZoneMonitor(DummyConfig())

# Test cases
test_cases = [
    {
        "name": "Offline with old app version",
        "params": {
            "is_paired": True,
            "online": False,
            "device": {"id": "123"},
            "subscription_active": True,
            "subscription_state": "ACTIVE",
            "software_version": 235.0
        },
        "expected": "offline"  # Should be offline, not outdated
    },
    {
        "name": "Online with old app version",
        "params": {
            "is_paired": True,
            "online": True,
            "device": {"id": "123"},
            "subscription_active": True,
            "subscription_state": "ACTIVE",
            "software_version": 235.0
        },
        "expected": "outdated"  # Should be outdated when online
    },
    {
        "name": "Online with current app version",
        "params": {
            "is_paired": True,
            "online": True,
            "device": {"id": "123"},
            "subscription_active": True,
            "subscription_state": "ACTIVE",
            "software_version": 248.0
        },
        "expected": "online"
    },
    {
        "name": "Offline with current app version",
        "params": {
            "is_paired": True,
            "online": False,
            "device": {"id": "123"},
            "subscription_active": True,
            "subscription_state": "ACTIVE",
            "software_version": 248.0
        },
        "expected": "offline"
    }
]

print("Testing status detection priority...")
print("=" * 50)

for test in test_cases:
    result = monitor._determine_zone_status(**test["params"])
    passed = result == test["expected"]
    
    print(f"\nTest: {test['name']}")
    print(f"Expected: {test['expected']}")
    print(f"Got: {result}")
    print(f"Result: {'✅ PASS' if passed else '❌ FAIL'}")

print("\n" + "=" * 50)
print("Test complete!")