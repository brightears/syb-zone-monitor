# Claude Context - SYB Zone Monitor

## Project Overview
This is a real-time monitoring system for Soundtrack Your Brand (SYB) music zones across Asia Pacific. It tracks zone status, sends notifications, and provides a web dashboard with account management capabilities.

## Current State (v5.1-stable)
- Monitoring 2,540 zones across 856 accounts (added Mövenpick Hotel Amman)
- PostgreSQL database for persistence
- WhatsApp Business integration (send/receive)
- Email notifications (SMTP + manual contacts)
- Now Playing information for online zones
- Automatic offline alerts with per-account settings
- **NEW: Account Management UI** - Add/remove accounts dynamically from dashboard
- **NEW: Account Management API** - RESTful endpoints for account CRUD operations

## Key Technical Details

### Zone Status Levels
1. **online** (green) - Zone is connected and active
2. **offline** (red) - Zone was online but lost connection
3. **expired** (orange) - Subscription expired
4. **unpaired** (yellow) - No paired device
5. **no_subscription** (purple) - Device exists but no subscription

### API Rate Limiting
- SYB GraphQL API has token-based rate limiting
- Current query with nowPlaying costs ~15 tokens
- Monitor adapts batch size based on available tokens
- Full cycle through all zones takes ~7 minutes

### Database Schema
- `zone_status` - Current state of all zones
- `zone_history` - Status change tracking
- `whatsapp_conversations` - WhatsApp chat threads
- `whatsapp_messages` - Individual messages
- `email_contacts` - Manual email contacts
- `whatsapp_contacts` - WhatsApp contacts

### WhatsApp Integration
- Uses Meta Cloud API (not Business API)
- System User token (non-expiring)
- Webhook at `/webhook/whatsapp`
- Supports text messages only currently

### Environment Variables
All stored in Render:
- `SYB_API_KEY` - From SYB account
- `DATABASE_URL` - PostgreSQL connection
- `WHATSAPP_ACCESS_TOKEN` - System User token
- `WHATSAPP_PHONE_NUMBER_ID` - From Meta
- `ZONE_IDS` - Comma-separated list from discovery

## Common Tasks

### Deploy Changes
```bash
git add .
git commit -m "Description"
git push origin main
# Render auto-deploys from GitHub
```

### Create Checkpoint
```bash
git tag -a vX.X-stable -m "Description"
git push origin vX.X-stable
```

### Add New Account
**Option 1: Via Dashboard UI**
1. Go to Account Management tab
2. Click "Add New Account"
3. Enter account ID (e.g., QWNjb3VudCwsMWs3bHVkeGY1czAv)
4. System will query SYB API and add all zones

**Option 2: Via Command Line**
```bash
python add_single_account.py QWNjb3VudCwsMWs3bHVkeGY1czAv
```

**Option 3: Via API**
```bash
curl -X POST http://localhost:8080/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"account_id": "QWNjb3VudCwsMWs3bHVkeGY1czAv"}'
```

### Test Locally
```bash
python enhanced_dashboard.py
# Visit http://localhost:8080
# Note: Need .env with DATABASE_URL for full functionality
```

## Known Issues/Limitations
1. Initial zone load takes ~7 minutes due to API rate limits
2. NowPlaying only shows when music is actively playing
3. WhatsApp only supports text (no media yet)
4. Email requires SMTP setup or manual contacts

## Recent Changes (July 2025)

### v5.1 - Account Management
- Added `account_manager.py` module for account CRUD operations
- Added Account Management tab to dashboard UI
- Added API endpoints:
  - `GET /api/accounts` - List all accounts
  - `POST /api/accounts` - Add new account
  - `DELETE /api/accounts/{id}` - Remove account
  - `POST /api/accounts/{id}/refresh` - Refresh account data
- Added `add_single_account.py` CLI tool
- Successfully added Mövenpick Hotel Amman (4 zones, 5 users)
- Accounts can now be managed without code changes

## Architecture Notes
- **Single Web Service**: Dashboard + monitoring in one process (works well for current scale)
- **No Background Workers Yet**: Considered but not needed until >5,000 zones
- **Internal Use Only**: Different from customer-facing apps that need background workers
- **Well-Suited for Current Scale**: 856 accounts, 2,540 zones with 7-minute cycle

## Next Possible Features
- Background workers (when scaling beyond 5,000 zones)
- Media support for WhatsApp
- Zone grouping by location
- Historical playback data
- Advanced filtering/sorting
- Export functionality
- Priority zone checking (check offline zones more frequently)
- Mobile app