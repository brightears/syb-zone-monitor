# Checkpoint v5.0-stable

**Date**: June 26, 2025

## Working Features

### Zone Monitoring
- ✅ Monitors 2536 zones across 855 accounts
- ✅ Detects online/offline/expired/unpaired status
- ✅ Tracks offline duration
- ✅ Shows "Now Playing" information for online zones
  - Track title, artists, album
  - Current playlist or schedule name
- ✅ Persists all data in PostgreSQL database
- ✅ Auto-refreshes every 30 seconds

### Notifications
- ✅ WhatsApp notifications (custom messages)
- ✅ Email notifications (SMTP + manual contacts)
- ✅ Automatic notifications for zones offline > X hours
- ✅ Cooldown period to prevent spam
- ✅ Per-account notification settings

### WhatsApp Integration
- ✅ Send custom WhatsApp messages
- ✅ Receive and display WhatsApp conversations
- ✅ Reply to messages from dashboard
- ✅ Webhook integration with Meta
- ✅ System User token (non-expiring)

### Contact Management
- ✅ Manual email contacts per account
- ✅ WhatsApp contacts per account
- ✅ Add/edit/delete functionality
- ✅ Integration with discovered user data

## Environment Variables (Render)

Required:
- `SYB_API_KEY`
- `ZONE_IDS`
- `DATABASE_URL`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN`

Optional:
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `EMAIL_FROM`

## Known Limitations

1. Initial load takes ~7 minutes for all zones due to API rate limits
2. NowPlaying only shows when music is actively playing
3. Zone checking is randomized for fairness

## How to Restore

If you need to restore to this checkpoint:

```bash
git fetch --tags
git checkout v5.0-stable
```

Or to create a new branch from this checkpoint:

```bash
git checkout -b new-feature-branch v5.0-stable
```

## Recent Changes in v5.0

1. Added nowPlaying information to zone monitoring
2. Enhanced UI to display currently playing tracks
3. Fixed datetime serialization issues
4. Improved token cost calculation for GraphQL queries