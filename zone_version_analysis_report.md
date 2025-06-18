# Zone Version and Subscription Analysis Report

## Summary

Analysis of SYB API zones to identify different app versions and subscription states.

**Date:** 2025-06-18

## Key Findings

### App Version Distribution

From the analyzed zones, we found the following app version distribution:

1. **Version 248.0** - Latest version (5 zones)
2. **Version 245.0** - Recent version (2 zones)
3. **Version 235.0** - Older version (1 zone)
4. **Version 57.15** - Very old version (1 zone)

**Version Range:** 57.15 - 248.0

### Examples of Different App Versions

#### Zones with Old App Versions (< 240.0)

1. **Version 235.0**
   - Zone: P&B | Teens | Active Vibes
   - Account: IBEROSTAR Hotels
   - Device: TMM-iPad-F9FWX8XNJF88
   - OS Version: 17.7.0
   - Subscription: ACTIVE
   - Zone ID: `U291bmRab25lLCwxcmh0b2xqdzNjdy9Mb2NhdGlvbiwsMW5oOHA2dXlxZGMvQWNjb3VudCwsMXJsbmd0eDZ3b3cv`

2. **Version 57.15** (Very old)
   - Zone: 3rd floor Swimming Pool Bar
   - Account: Ramada Plaza by Wyndham Waikiki
   - Device: HUAWEI CRO-L22
   - OS Version: 6.0
   - Subscription: CANCELLED
   - Zone ID: `U291bmRab25lLCwxYXFicXVuMWJscy9Mb2NhdGlvbiwsMWtpNXdrd2dsYzAvQWNjb3VudCwsMXF0cjB5YXh5cHMv`

### Subscription State Distribution

- **ACTIVE**: 7 zones
- **CANCELLED**: 2 zones
- **NO_SUBSCRIPTION**: 0 zones (in this sample)

### Examples of Different Subscription States

#### Zones with CANCELLED Subscriptions

1. **Hotel Made In Louise**
   - Account: HOTEL MADE IN LOUISE (Free Trial)
   - Is Paired: False
   - Subscription: CANCELLED
   - Zone ID: `U291bmRab25lLCwxc21hNTdwOXN6ay9Mb2NhdGlvbiwsMWo3aTdjYmczY3cvQWNjb3VudCwsMWU1OTBhenpremsv`

2. **Trial Zone**
   - Account: Anantara Desaru Coast Resort & Villas
   - App Version: 245.0
   - Is Paired: True
   - Subscription: CANCELLED
   - Zone ID: `U291bmRab25lLCwxbjFteGk0NHJnZy9Mb2NhdGlvbiwsMWdoZXh3eDdhNGcvQWNjb3VudCwsMW1sbTJ0ZW52OWMv`

#### Zones with ACTIVE Subscriptions but Not Paired

1. **Kids' Club Room 1**
   - Account: GF ISABEL (Unlimited)
   - Is Paired: False
   - Subscription: ACTIVE
   - Zone ID: `U291bmRab25lLCwxanU5NGtyMmViay9Mb2NhdGlvbiwsMWc5OGI1dm5jM2svQWNjb3VudCwsMWZ0eGhhYTl0a3cv`

## Interesting Patterns

1. **Old App Versions with Active Subscriptions**: The zone with version 235.0 (IBEROSTAR Hotels) has an active subscription, suggesting it might need an app update.

2. **Very Old Version with Cancelled Subscription**: The zone with version 57.15 has a cancelled subscription, which might indicate it's been abandoned.

3. **Unpaired Zones with Active Subscriptions**: Some zones have active subscriptions but no paired devices, indicating they're paying but not using the service.

## API Credentials Used

```
API Token: YVhId2UyTWJVWEhMRWlycUFPaUl3Y2NtOXNGeUoxR0Q6SVRHazZSWDVYV2FTenhiS1ZwNE1sSmhHUUJEVVRDdDZGU0FwVjZqMXNEQU1EMjRBT2pub2hmZ3NQODRRNndQWg==
API URL: https://api.soundtrackyourbrand.com/v2
```

## Rate Limiting

The API has strict rate limiting (token-based). To avoid rate limits:
- Use minimal queries with only necessary fields
- Add delays between requests (5-30 seconds)
- Simplify queries to reduce token cost

## Files Generated

1. `zone_version_scan_20250618_143708.json` - Initial scan results
2. `subscription_state_results.json` - Comprehensive subscription state analysis
3. `zone_version_analysis_*.json` - Failed attempts due to schema issues
4. `comprehensive_zone_scan.py` - Script for extended analysis