# Performance Recommendations for SYB Zone Monitor

## Current Issues & Solutions

### 1. **"Checking" Status Not Showing**
✅ **Fixed** - Zones now show "Checking..." with pulsing animation on initial load instead of incorrectly showing "Offline"

### 2. **Auto-Refresh Functionality**
**Current behavior:**
- Dashboard refreshes every 30 seconds (frontend)
- Zone status checks every 60 seconds (backend)
- Zone list is static - loaded once at startup

**Issues:**
- Removed zones stay in dashboard until restart
- New zones don't appear until restart

### 3. **Recommended Improvements**

#### A. **Dynamic Zone Discovery** (Highest Priority)
- Implement periodic zone discovery (every 5-10 minutes)
- Automatically add new zones and remove deleted ones
- Use the `dynamic_zone_discovery.py` module provided

#### B. **Database Integration** (PostgreSQL)
**Benefits:**
- Store historical data for trending
- Cache zone status to reduce API calls
- Faster initial load (show last known status immediately)
- Enable multiple worker processes

**Implementation:**
```python
# Store zone status with timestamps
CREATE TABLE zone_status (
    zone_id VARCHAR(255) PRIMARY KEY,
    zone_name VARCHAR(255),
    account_id VARCHAR(255),
    status VARCHAR(50),
    last_checked TIMESTAMP,
    offline_since TIMESTAMP,
    details JSONB
);

# Historical tracking
CREATE TABLE zone_history (
    id SERIAL PRIMARY KEY,
    zone_id VARCHAR(255),
    status VARCHAR(50),
    timestamp TIMESTAMP,
    INDEX idx_zone_timestamp (zone_id, timestamp)
);
```

#### C. **Render Performance Upgrades**
1. **Upgrade to Professional Plan ($25/month)**
   - 4GB RAM (vs 512MB on free)
   - More CPU resources
   - Faster response times

2. **Enable Auto-scaling**
   - Handle multiple concurrent users
   - Automatic resource adjustment

#### D. **Code Optimizations**

1. **Batch API Calls More Efficiently**
```python
# Current: 50 zones per batch
batch_size = 50  

# Recommended: Increase to 100-200 for faster processing
batch_size = 100
```

2. **Implement Caching**
```python
# Cache zone details that don't change often
zone_cache = {
    "zone_id": {
        "name": "Zone Name",
        "account": "Account Name",
        "cached_at": datetime.now()
    }
}

# Only refresh cache every hour
CACHE_TTL = 3600  # 1 hour
```

3. **Use Redis for State Management**
- Store zone states in Redis
- Enable horizontal scaling
- Share state between workers

```python
import redis

r = redis.Redis(host='localhost', port=6379)

# Store zone status
r.hset(f"zone:{zone_id}", mapping={
    "status": "online",
    "last_check": datetime.now().isoformat()
})

# Get all zones at once
all_zones = r.keys("zone:*")
```

#### E. **Frontend Optimizations**

1. **Progressive Loading**
```javascript
// Show cached data immediately
showCachedData();

// Then fetch fresh data
fetchFreshData().then(updateDisplay);
```

2. **WebSocket for Real-time Updates**
```python
# Add WebSocket support
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        # Send zone updates as they happen
        updates = get_zone_updates()
        await websocket.send_json(updates)
        await asyncio.sleep(1)
```

## Recommended Implementation Order

1. **Immediate (No cost)**
   - Implement dynamic zone discovery
   - Increase batch size to 100
   - Add basic caching

2. **Short-term (Low cost)**
   - Upgrade Render to Professional ($25/month)
   - Add PostgreSQL database (Render PostgreSQL starter: $7/month)
   - Implement database caching

3. **Long-term (For scale)**
   - Add Redis for distributed caching
   - Implement WebSocket for real-time updates
   - Enable auto-scaling on Render

## Performance Metrics to Expect

| Metric | Current | With Optimizations |
|--------|---------|-------------------|
| Initial Load | 30-60s | 2-5s (with cache) |
| Zone Check Time | 60-120s | 20-30s |
| Memory Usage | ~200MB | ~500MB |
| Concurrent Users | 1-5 | 50-100 |
| Zone Limit | ~1000 | 10,000+ |

## Cost Analysis

| Service | Monthly Cost | Benefit |
|---------|-------------|---------|
| Render Pro | $25 | 8x more RAM, faster CPU |
| PostgreSQL | $7 | Data persistence, caching |
| Redis | $15 | Distributed cache, scaling |
| **Total** | **$47** | **10x performance improvement** |

## Quick Start

To implement dynamic zone discovery immediately:

```python
# In zone_monitor.py, add:
from dynamic_zone_discovery import DynamicZoneDiscovery, update_zone_list

# In check_zones method:
async def check_zones(self) -> None:
    # Every 10 checks, refresh zone list
    if self.check_count % 10 == 0:
        discovery = DynamicZoneDiscovery(self.config.syb_api_key, self.config.syb_api_url)
        await update_zone_list(self, discovery)
        await discovery.close()
    
    # Continue normal zone checking...
```