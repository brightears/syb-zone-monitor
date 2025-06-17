# SYB Zone Monitor

Real-time monitoring and notification system for Soundtrack Your Brand (SYB) zones.

## Features

- **Real-time Monitoring**: Tracks online/offline status of 800+ music zones across 100+ business accounts
- **Web Dashboard**: Clean, responsive interface showing zone status by account
- **Smart Notifications**: Account-specific email notifications with contact filtering
- **Automatic Discovery**: Discovers zones and contacts from configured accounts
- **Status Tracking**: Monitors online, offline, unpaired devices, and expired subscriptions

## Technology Stack

- **Backend**: Python 3.x, FastAPI
- **API Integration**: SYB GraphQL API
- **Frontend**: HTML/CSS/JavaScript (embedded)
- **Deployment**: Render Web Service

## Quick Start

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/brightears/syb-zone-monitor.git
cd syb-zone-monitor
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your SYB_API_KEY
```

5. Run the application:
```bash
python main.py
```

Visit http://localhost:8080 to view the dashboard.

## Environment Variables

- `SYB_API_KEY` (required): Your Soundtrack Your Brand API key
- `POLLING_INTERVAL`: Zone status check interval in seconds (default: 60)
- `LOG_LEVEL`: Logging level (default: INFO)

## Deployment on Render

1. Fork this repository
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Add environment variables in Render dashboard
5. Deploy!

The `render.yaml` file contains all necessary configuration.

## Account Management

Accounts are loaded from the `account_ids.json` file. To update accounts:

1. Update the CSV files with new account data
2. Run the extraction script:
```bash
python extract_account_ids.py
```
3. Commit and push changes

## API Endpoints

- `/` - Main dashboard
- `/health` - Health check endpoint
- `/api/status` - System status
- `/api/zones` - Get all zone data
- `/api/notify` - Send notifications

## Development

### Project Structure

```
syb-zone-monitor/
├── main.py                 # Main application entry point
├── enhanced_dashboard.py   # Dashboard UI and API
├── zone_monitor.py        # Core monitoring logic
├── account_config.py      # Account configuration management
├── process_all_accounts.py # Account discovery script
└── requirements.txt       # Python dependencies
```

### Adding Features

1. Create a feature branch
2. Make your changes
3. Test locally
4. Submit a pull request

## License

Private repository - All rights reserved

## Support

For issues or questions, please open an issue on GitHub.