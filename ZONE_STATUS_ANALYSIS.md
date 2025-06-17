# SYB GraphQL API Zone Status Analysis

## Summary

Investigation completed to determine what additional fields are available in the SYB GraphQL API to distinguish between the 4 zone status levels requested by the user.

## Current Implementation

The existing `zone_monitor.py` only checks the `isPaired` field:
- `isPaired=true` → Zone considered "online"
- `isPaired=false` → Zone considered "offline"

## Available Fields for Enhanced Status Detection

After comprehensive testing, the following fields are confirmed to be available:

### Basic Fields (Currently Used)
- `isPaired` (Boolean) - Shows if zone has a device connected
- `online` (Boolean) - Shows if zone is actually online

### Device Fields
- `device` (Object or null) - Device information if connected
  - `device.id` - Device identifier
  - `device.name` - Device name
  - `device.type` - Device type (mobile, desktop, etc.)
  - `device.platform` - Platform identifier
  - `device.isPairing` - Whether device is currently pairing

### Subscription Fields
- `subscription.isActive` (Boolean) - Whether subscription is active

### Fields That Don't Exist
These fields were tested but don't exist in the API:
- `subscription.isPaid`
- `subscription.isSuspended` 
- `subscription.expiresAt`
- `subscription.trialEndsAt`
- `status.canPlay`
- `status.canListen`

## Recommended Enhanced GraphQL Query

```graphql
query GetZoneStatus($zoneId: ID!) {
    soundZone(id: $zoneId) {
        id
        name
        isPaired
        online
        device {
            id
            name
        }
        subscription {
            isActive
        }
    }
}
```

## Enhanced Status Detection Logic

Based on the available fields, the 4 status levels can be detected as follows:

### 4. No Paired Device
**Detection Logic:**
- `isPaired = false` OR
- `device = null`

**Fields Used:** `isPaired`, `device`

### 3. Subscription Expired  
**Detection Logic:**
- `isPaired = true` AND `device != null` AND
- `subscription.isActive = false`

**Fields Used:** `isPaired`, `device`, `subscription.isActive`

### 2. Paired but Offline
**Detection Logic:**
- `isPaired = true` AND `device != null` AND
- `subscription.isActive = true` AND
- `online = false`

**Fields Used:** `isPaired`, `device`, `subscription.isActive`, `online`

### 1. Paired and Online
**Detection Logic:**
- `isPaired = true` AND `device != null` AND  
- `subscription.isActive = true` AND
- `online = true`

**Fields Used:** `isPaired`, `device`, `subscription.isActive`, `online`

## Test Results Examples

From testing actual zones, here are real examples:

### Example 1: Subscription Expired (Current logic would miss)
```json
{
  "name": "Trial Zone",
  "isPaired": true,
  "online": true,
  "device": { "name": "ADES's iPad 2" },
  "subscription": { "isActive": false }
}
```
- **Current logic:** Online (isPaired=true)
- **Enhanced logic:** 3. Subscription expired (isActive=false)
- **Issue:** Current system would not detect subscription problems

### Example 2: Paired but Offline (Current logic would miss)
```json
{
  "name": "Kids´ Club Room 1", 
  "isPaired": true,
  "online": false,
  "device": { "name": "Some Device" },
  "subscription": { "isActive": true }
}
```
- **Current logic:** Online (isPaired=true)
- **Enhanced logic:** 2. Paired but offline (online=false)
- **Issue:** Current system would not detect offline devices

### Example 3: Properly Online
```json
{
  "name": "Basalt",
  "isPaired": true, 
  "online": true,
  "device": { "name": "Some Device" },
  "subscription": { "isActive": true }
}
```
- **Current logic:** Online (isPaired=true)
- **Enhanced logic:** 1. Paired and online
- **Result:** Both logics agree

## Implementation Recommendations

1. **Update GraphQL Query** in `zone_monitor.py` to include:
   - `online` field
   - `device` object (to check for null)
   - `subscription.isActive` field

2. **Update Status Detection Logic** to implement 4-level categorization

3. **Update Notifications** to distinguish between different offline reasons:
   - Device disconnected
   - Subscription expired  
   - Device offline
   - Actually online

4. **Backward Compatibility** - The enhanced logic can be implemented while maintaining existing behavior as a fallback

## Benefits of Enhanced Detection

1. **More Accurate Monitoring** - Distinguish between different types of "offline" states
2. **Better Notifications** - Alert users to specific issues (subscription vs connectivity)
3. **Reduced False Positives** - Don't alert for subscription issues when the real problem is device connectivity
4. **Better Troubleshooting** - Users get actionable information about what's wrong

## Files Created During Investigation

- `/Users/benorbe/Documents/SYB Offline Alarm/explore_soundzone_schema.py` - Schema exploration
- `/Users/benorbe/Documents/SYB Offline Alarm/test_enhanced_fields.py` - Enhanced field testing
- `/Users/benorbe/Documents/SYB Offline Alarm/test_fields_individually.py` - Individual field validation
- `/Users/benorbe/Documents/SYB Offline Alarm/test_working_fields.py` - Working field combinations
- `/Users/benorbe/Documents/SYB Offline Alarm/final_field_analysis.py` - Comprehensive analysis
- `/Users/benorbe/Documents/SYB Offline Alarm/ZONE_STATUS_ANALYSIS.md` - This summary document