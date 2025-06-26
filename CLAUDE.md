# Claude Context - SYB Zone Monitor

## Project Overview
This is a real-time monitoring system for Soundtrack Your Brand (SYB) music zones across 855 business accounts in Asia Pacific. It tracks zone status, sends notifications, and provides a web dashboard.

## Current State (v5.0-stable)
- Monitoring 2,536 zones across 855 accounts
- PostgreSQL database for persistence
- WhatsApp Business integration (send/receive)
- Email notifications (SMTP + manual contacts)
- Now Playing information for online zones
- Automatic offline alerts with per-account settings

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

## Next Possible Features
- Media support for WhatsApp
- Zone grouping by location
- Historical playback data
- Advanced filtering/sorting
- Export functionality
- Mobile app