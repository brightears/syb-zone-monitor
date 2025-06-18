#!/usr/bin/env python3
"""Analyze zone IDs to see if there's a pattern for app update required."""

import base64

# Sample zone IDs from the .env file
zone_ids = [
    "U291bmRab25lLCwxbjFteGk0NHJnZy9Mb2NhdGlvbiwsMWdoZXh3eDdhNGcvQWNjb3VudCwsMW1sbTJ0ZW52OWMv",
    "U291bmRab25lLCwxcDEzcWhzYTBhby9Mb2NhdGlvbiwsMThscnUwenZldjQvQWNjb3VudCwsMWVuaXV0emJhYmsv",
    "U291bmRab25lLCwxbjhvcmV5NWthby9Mb2NhdGlvbiwsMWloNjg1MHVtODAvQWNjb3VudCwsMTh1ZHBmbnRubmsv",
    "U291bmRab25lLCwxcmh0b2xqdzNjdy9Mb2NhdGlvbiwsMW5oOHA2dXlxZGMvQWNjb3VudCwsMXJsbmd0eDZ3b3cv",
]

# Account ID mentioned by user
account_id = "QWNjb3VudCwsMTh1ZHBmbnRubmsv"

print("Analyzing Zone IDs and Account IDs...")
print("=" * 60)

# Decode account ID
try:
    decoded_account = base64.b64decode(account_id + "=").decode('utf-8', errors='ignore')
    print(f"\nAccount ID: {account_id}")
    print(f"Decoded: {decoded_account}")
except:
    pass

print("\nZone ID Analysis:")
for zone_id in zone_ids:
    try:
        # Try different padding
        for padding in ["", "=", "=="]:
            try:
                decoded = base64.b64decode(zone_id + padding).decode('utf-8', errors='ignore')
                if decoded:
                    print(f"\nZone ID: {zone_id[:50]}...")
                    print(f"Decoded: {decoded}")
                    
                    # Check if it contains the account ID pattern
                    if "18udpfntnk" in decoded:
                        print("  ✓ Contains account ID from user's example")
                    
                    break
            except:
                continue
    except Exception as e:
        print(f"Error decoding {zone_id[:30]}...: {e}")

# Look for patterns
print("\n" + "=" * 60)
print("Pattern Analysis:")
print("- Zone IDs appear to contain: SoundZone, Location ID, Account ID")
print("- Format seems to be: SoundZone,,{zone_id}/Location,,{location_id}/Account,,{account_id}/")
print("- No obvious indicator for 'App update required' in the ID structure"