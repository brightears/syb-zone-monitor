# SYB Offline Alarm - Project Summary

**Last Updated:** June 10, 2025  
**Version:** 1.1  
**Status:** Active Development

## 1. Project Overview

### Purpose
The SYB Offline Alarm is a comprehensive monitoring and notification system for Soundtrack Your Brand (SYB) zones. It provides real-time monitoring of audio zone status across multiple business accounts and sends notifications when zones go offline for extended periods.

### What It Does
- **Monitors 329+ SYB zones** across 100+ business accounts in real-time
- **Detects zone status**: Online, Offline, Subscription Expired, No Paired Device
- **Web Dashboard**: Clean, responsive interface showing zone status by account
- **Notification System**: Account-specific email notifications with individual contact selection
- **Health Monitoring**: Built-in health endpoints and uptime tracking
- **Auto-refresh**: Real-time updates every 30 seconds
- **Direct Account Access**: Can query accounts by ID for complete contact discovery

### Target Users
- **SYB Account Managers**: Monitor client zones and send status reports
- **Business Owners**: Receive notifications when their zones go offline
- **Technical Teams**: System health monitoring and maintenance
- **BMAsia Staff**: Manage music service across all client locations

## 2. Tech Stack

### Languages & Frameworks
- **Python 3.x**: Main backend language
- **FastAPI**: Web framework for dashboard and API endpoints
- **HTML/CSS/JavaScript**: Frontend (embedded in Python)
- **GraphQL**: SYB API communication

### Key Dependencies
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.2
pydantic==2.5.0
python-multipart==0.0.6
python-dotenv==1.0.0
```

### External APIs
- **SYB GraphQL API**: `https://api.soundtrackyourbrand.com/v2`
- **Authentication**: Basic Auth with API key

## 3. Architecture

### High-Level Structure
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Dashboard │    │   Zone Monitor   │    │   SYB GraphQL   │
│   (FastAPI)     │◄──►│   (Core Logic)   │◄──►│      API        │
│   Port 8080     │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       
         ▼                       ▼                       
┌─────────────────┐    ┌──────────────────┐             
│  Notification   │    │  Health Server   │             
│    System       │    │   (Port 8000)    │             
└─────────────────┘    └──────────────────┘             
```

### Main Components

1. **ZoneMonitor** (`zone_monitor.py`)
   - Polls SYB API for zone status
   - Maintains zone state and offline duration tracking
   - Provides detailed status information
   - Handles GraphQL queries and error management

2. **DashboardServer** (`web_server.py`)
   - FastAPI web server
   - Serves dashboard UI and API endpoints
   - Handles contact data and notifications
   - Real-time zone status updates

3. **NotificationChain** (`notifier/`)
   - Email notification system
   - Account-specific contact management
   - Support for multiple notification methods

4. **HealthServer** (`health_server.py`)
   - System health monitoring on port 8000
   - Uptime tracking

### Data Flow
1. **Zone Monitoring**: Continuous polling of SYB API → Status updates → Dashboard display
2. **Notifications**: User selects accounts → Contact lookup → Email preparation → Status feedback
3. **Dashboard**: Zone data → Account grouping → Real-time display → User interactions
4. **Account Discovery**: Account IDs → Direct API queries → Contact extraction → Database update

## 4. Recent Changes

### Last Session (June 10, 2025)
- ✅ **Discovered account ID approach** - Can query accounts directly by ID for complete access
- ✅ **Successfully queried Hilton Pattaya** - Retrieved 11 users with email addresses
- ✅ **Created account ID processor** - Script to batch process account IDs for zones and contacts
- ✅ **Identified access limitation** - Current API key sees 100 accounts, but more exist (like Hilton Pattaya)
- ✅ **Updated contact database** - Added Hilton Pattaya with all 11 user contacts
- ✅ **Built comprehensive discovery tools** - Scripts for finding all zones and contacts by account ID

### Previous Session (June 9, 2025)
- ✅ **Fixed notification modal styling** - Complete CSS overhaul for professional appearance
- ✅ **Implemented account-specific notifications** - Each account card has individual "📧 Notify" button
- ✅ **Added individual contact selection** - Checkboxes for each email address
- ✅ **Updated contact data structure** - FINAL_CONTACT_ANALYSIS.json includes multiple accounts
- ✅ **Improved name matching** - Flexible matching between dashboard and contact names

### Key Decisions Made
- **Account ID approach**: Direct querying by account ID provides complete access
- **Modal-based UI**: Chose modal popups over inline forms for better UX
- **Individual contact selection**: Checkboxes per email rather than bulk selection
- **Flexible matching**: Handle account name discrepancies gracefully
- **BMAsia email filtering**: Identified need to separate internal vs client emails

## 5. Current Status

### ✅ Working Features
- **Dashboard loads successfully** on http://127.0.0.1:8080
- **Zone monitoring** - 329 zones across 100+ accounts
- **Real-time status updates** - Online/Offline/Expired/Unpaired detection
- **Account grouping** - Zones organized by business account
- **Search and filtering** - By account name, zone name, status type
- **Health monitoring** - /healthz endpoint on port 8000
- **Notification UI** - Modal opens, shows contact selection interface
- **Account ID queries** - Can retrieve complete account data by ID
- **Contact discovery** - Successfully extracts all user emails from accounts

### 🔄 In Progress
- **Complete account list** - Waiting for full list of account IDs from user
- **Contact data completeness** - Currently only 5 accounts have contact info
- **Email filtering** - Need to separate BMAsia emails from client contacts
- **Dashboard zone coverage** - Some accounts (like Hilton Pattaya) not in default discovery

### ❌ Known Issues
1. **Limited API discovery**: Default account query returns 100 accounts, missing some
2. **Email sending**: Currently simulated (saves to files), needs real SMTP integration
3. **Account access discrepancy**: Some accounts only accessible via direct ID query
4. **Contact coverage**: Only 5/100+ accounts have contact information in database

## 6. Next Steps

### Immediate Priorities
1. **Process complete account ID list** - When user provides all IDs, run comprehensive discovery
2. **Update zone monitoring** - Include all discovered zones from account IDs
3. **Filter BMAsia emails** - Separate internal emails from client contacts
4. **Complete contact database** - Ensure all accounts have contact information
5. **Test notification flow** - Verify end-to-end with real account data

### Planned Features
- **Email templates** - HTML email templates for different notification types
- **Notification history** - Track sent notifications and responses
- **SMTP integration** - Replace file-based simulation with real email sending
- **Contact management UI** - Interface to add/edit/remove contacts
- **Alert thresholds** - Configurable offline time thresholds per account
- **Bulk operations** - Select multiple accounts for batch notifications

### Technical Improvements
- **Caching layer** - Cache account/zone data to reduce API calls
- **Background workers** - Separate monitoring from web serving
- **Database integration** - Store zones, accounts, contacts in proper database
- **Authentication** - Add user authentication to dashboard
- **API rate limiting** - Implement proper rate limit handling
- **Webhook support** - Real-time zone status updates via webhooks

## 7. Development Notes

### Important Patterns
- **Async/await everywhere** - All HTTP calls and main loops use async patterns
- **GraphQL queries** - Complex nested queries for zone and account data
- **Error resilience** - Continue monitoring even if individual zones fail
- **Real-time updates** - 30-second refresh cycle with countdown display
- **Direct ID access** - Account IDs provide more complete access than general queries

### Key Discoveries
- **Account IDs are Base64 encoded** - Format: `Account,,{actual_id}/`
- **Zone IDs contain hierarchy** - Include zone, location, and account information
- **API access levels vary** - Some accounts only accessible via direct ID query
- **User fields limited** - Only basic fields available (id, name, email, companyRole)
- **BMAsia emails present** - @bmasiamusic.com emails are internal, not client contacts

### Conventions
- **File naming**: snake_case for Python files
- **Class naming**: PascalCase for classes
- **Variable naming**: snake_case for variables and functions
- **API endpoints**: RESTful patterns (/api/zones, /api/contacts, /api/notify)
- **Error handling**: Log warnings but continue operation

### Gotchas to Remember
- **Zone IDs are Base64 encoded** - Decode to see account/location structure
- **Account names inconsistent** - Dashboard vs API names don't always match
- **GraphQL field availability** - Not all fields exist (e.g., no billing.email)
- **API rate limiting** - Be careful with API call frequency
- **Port conflicts** - Always kill port 8080 processes before restart
- **Virtual environment required** - Must activate venv before running
- **Contact data format** - Different formats in different discovery files

## 8. Key Files

### Core Application Files
- **`zone_monitor.py`** - Core zone monitoring logic and SYB API interface
- **`web_server.py`** - FastAPI dashboard server with notification system
- **`simple_dashboard.py`** - Simplified dashboard server for testing
- **`config.py`** - Configuration management and environment variables
- **`notifier/`** - Notification system modules (base, email, pushover)

### Discovery & Processing Scripts
- **`process_account_ids.py`** - Process account IDs to discover zones and contacts
- **`discover_all_zones.py`** - Discover all zones from accessible accounts
- **`test_account_by_id.py`** - Test querying specific accounts by ID
- **`final_contact_analysis.py`** - Comprehensive contact discovery script

### Data Files
- **`FINAL_CONTACT_ANALYSIS.json`** - Account contact information (currently 5 accounts)
- **`all_zones_discovered.json`** - Complete zone discovery results
- **`account_id_zones_discovered.json`** - Zones discovered via account IDs
- **`account_id_contacts_discovered.json`** - Contacts discovered via account IDs
- **`.env`** - Environment variables (API keys, configuration)

### Documentation
- **`PROJECT_SUMMARY.md`** - This file
- **`README.md`** - Basic project documentation
- **`FINAL_CONTACT_DISCOVERY_REPORT.md`** - Contact analysis results

## 9. Setup Instructions

### Prerequisites
- Python 3.x installed
- SYB API access credentials

### Initial Setup
```bash
# 1. Clone/access the project directory
cd "/Users/benorbe/Documents/SYB Offline Alarm"

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install fastapi uvicorn httpx pydantic python-multipart python-dotenv

# 4. Configure environment
# Create .env file with:
# SYB_API_KEY=your_api_key_here
# SYB_API_URL=https://api.soundtrackyourbrand.com/v2
# POLLING_INTERVAL=60
# LOG_LEVEL=INFO
```

### Running the Application
```bash
# Activate virtual environment
source venv/bin/activate

# Option 1: Dashboard + Monitoring (recommended)
python run_with_dashboard.py

# Option 2: Simple dashboard only (for testing)
python simple_dashboard.py

# Option 3: Process account IDs (when list is available)
python process_account_ids.py account_ids.txt
```

### Accessing the Dashboard
- **Main Dashboard**: http://127.0.0.1:8080
- **Health Check**: http://127.0.0.1:8000/healthz

### Troubleshooting
```bash
# Kill existing processes on port 8080
lsof -ti:8080 | xargs kill -9

# Check if virtual environment is activated
which python  # Should show venv path

# Test API connection
python test_api_connection.py

# Test specific account access
python test_account_by_id.py
```

## 10. Context for Future Sessions

### Current Development State
We've discovered that direct account ID queries provide more complete access than the general API discovery. The system can successfully monitor zones and extract contact information, but we're waiting for a complete list of account IDs to build the full database.

### Immediate Context
- **Dashboard server runs successfully** on http://127.0.0.1:8080
- **Account ID approach proven** - Hilton Pattaya successfully queried with 11 contacts
- **Processing script ready** - `process_account_ids.py` awaits the full ID list
- **Contact database limited** - Only 5 accounts in FINAL_CONTACT_ANALYSIS.json
- **Notification UI complete** - Modal interface ready, just needs more contact data

### What to Pick Up Next
1. **Process account ID list** - When provided, run `process_account_ids.py`
2. **Update zone monitoring** - Include all zones from account ID discovery
3. **Filter BMAsia emails** - Implement logic to separate internal vs client emails
4. **Update dashboard** - Ensure all discovered zones appear in monitoring
5. **Test notifications** - Verify the complete flow with all account contacts
6. **Implement SMTP** - Replace file-based email simulation with real sending

### Key Information for Account ID Processing
- **Script ready**: `process_account_ids.py` can process a list from a text file
- **Expected format**: One account ID per line in the text file
- **Output files**: Creates zone and contact JSON files plus zone ID list
- **Hilton Pattaya example**: ID `QWNjb3VudCwsMXN4N242NTZyeTgv` returns 11 users, 4 zones

### Testing After Account Processing
```bash
# 1. Process the account IDs
python process_account_ids.py account_ids.txt

# 2. Update the dashboard to use new zones
# May need to modify config.py or zone loading logic

# 3. Restart dashboard with new data
python simple_dashboard.py

# 4. Test notification for accounts with contacts
# Visit http://127.0.0.1:8080 and click notify buttons
```

### Success Metrics
The system will be considered feature-complete when:
1. ✅ All provided account IDs are processed
2. ✅ Complete contact database is built
3. ✅ All zones appear in dashboard monitoring
4. ✅ Notifications can be sent to all accounts
5. ✅ BMAsia emails are filtered appropriately
6. ❌ Real emails are sent via SMTP
7. ❌ Notification history is tracked

**Current Progress: 5/7 technically ready, awaiting account ID list**