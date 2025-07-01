# Checkpoint v5.1-stable

**Date**: July 1, 2025

## New Features Since v5.0

### Account Management System
- ✅ **Dynamic Account Management**: Add/remove accounts without code changes
- ✅ **Dashboard UI**: New "Account Management" tab with table view
- ✅ **API Endpoints**: Full REST API for account CRUD operations
- ✅ **CLI Tool**: `add_single_account.py` for command-line additions
- ✅ **Auto-refresh**: Zone monitor automatically updates when accounts change

### Account Changes
- ✅ Added Mövenpick Hotel Amman (account ID: QWNjb3VudCwsMWs3bHVkeGY1czAv)
  - 4 zones
  - 5 users
  - Total now: 856 accounts, 2,540 zones

## Working Features (from v5.0)

### Zone Monitoring
- ✅ Monitors 2,540 zones across 856 accounts
- ✅ Detects online/offline/expired/unpaired status
- ✅ Tracks offline duration
- ✅ Shows "Now Playing" information for online zones
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

## New Files in v5.1
- `account_manager.py` - Account management module
- `add_single_account.py` - CLI tool for adding accounts

## Modified Files
- `enhanced_dashboard.py` - Added Account Management tab and API endpoints
- `accounts_discovery_results.json` - Updated with Mövenpick Hotel Amman

## How to Use Account Management

### Via Dashboard
1. Navigate to "Account Management" tab
2. Click "Add New Account"
3. Enter account ID
4. System queries SYB API and adds all zones

### Via Command Line
```bash
python add_single_account.py QWNjb3VudCwsMWs3bHVkeGY1czAv
```

### Via API
```bash
# Add account
curl -X POST http://your-app.onrender.com/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"account_id": "QWNjb3VudCwsMWs3bHVkeGY1czAv"}'

# List accounts
curl http://your-app.onrender.com/api/accounts

# Remove account
curl -X DELETE http://your-app.onrender.com/api/accounts/{account_id}

# Refresh account
curl -X POST http://your-app.onrender.com/api/accounts/{account_id}/refresh
```

## Architecture Decision
- Keeping single web service architecture (no background workers)
- Suitable for current scale (856 accounts, 2,540 zones)
- Will consider background workers if scaling beyond 5,000 zones

## How to Restore This Checkpoint

```bash
git fetch --tags
git checkout v5.1-stable
```

Or create a new branch from this checkpoint:
```bash
git checkout -b new-feature-branch v5.1-stable
```