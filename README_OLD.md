# SYB Zone Uptime Monitor

A lightweight Python service that monitors **Soundtrack Your Brand** zones and sends alerts when any zone is offline for ≥ 10 minutes.

## Features

- **Real-time monitoring** of SYB zones via GraphQL API
- **Web dashboard** for internal team monitoring with search and filtering
- **Dual notification system**: Pushover (primary) + Email (fallback)
- **Configurable thresholds** and polling intervals
- **Exponential backoff** for API failures
- **REST API endpoints** for integration
- **Multiple deployment options**: Docker or systemd service

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Zone Monitor  │───▶│ Notification     │───▶│ Pushover API    │
│                 │    │ Chain            │    │                 │
│ • GraphQL API   │    │                  │    └─────────────────┘
│ • Timer Logic   │    │ • Fallback Logic │           │
│ • State Mgmt    │    │ • Rate Limiting  │           ▼
└─────────────────┘    └──────────────────┘    ┌─────────────────┐
         │                       │             │ Email SMTP      │
         ▼                       └────────────▶│                 │
┌─────────────────┐                            └─────────────────┘
│ Web Dashboard   │
│ • Zone Listing  │
│ • Search/Filter │
│ • Real-time UI  │
│ • REST API      │
└─────────────────┘
```

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd syb-uptime-monitor
cp config.example.env .env
```

### 2. Configure Environment

Edit `.env` with your credentials:

```bash
# Required
SYB_API_KEY=your_syb_api_key_here
ZONE_IDS=zone_id_1,zone_id_2,zone_id_3

# Pushover (recommended)
PUSHOVER_TOKEN=your_pushover_app_token
PUSHOVER_USER_KEY=your_pushover_user_key

# Email fallback
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=alert_recipient@example.com
```

### 3. Choose Deployment Method

## Web Dashboard

The monitor includes a web dashboard for your internal team to view all zones in real-time:

- **URL**: `http://your-server:8080`
- **Features**: 
  - View all accounts and zones with online/offline status
  - Search by account name or zone name
  - Filter to show only offline zones
  - Real-time updates every 30 seconds
  - Mobile-responsive design

**Dashboard Features:**
- 🔍 **Search**: Find specific accounts or zones instantly
- 📊 **Account grouping**: Zones organized by hotel accounts
- 🟢🔴 **Status indicators**: Clear online/offline visualization
- ⏱️ **Offline duration**: See how long zones have been offline
- 🔄 **Auto-refresh**: Updates every 30 seconds automatically

## Deployment Option A: Docker (Recommended)

### Prerequisites
- Docker and Docker Compose installed
- Port 8080 available for web dashboard

### Deploy
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f uptime-monitor

# Access dashboard
open http://localhost:8080

# Health check
curl http://localhost:8080/api/health

# Stop
docker-compose down
```

### Integration with Existing Nginx
If you have Nginx running, add this location block to your server config:

```nginx
location /uptime-monitor/ {
    proxy_pass http://localhost:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Deployment Option B: Systemd Service

### Prerequisites
- Ubuntu 22.04+ (or similar systemd-based OS)
- Python 3.12+
- User with sudo privileges

### Install
```bash
# 1. Create application directory
sudo mkdir -p /opt/uptime-monitor
sudo chown $USER:$USER /opt/uptime-monitor

# 2. Copy files
cp -r . /opt/uptime-monitor/
cd /opt/uptime-monitor

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Setup environment
cp config.example.env .env
# Edit .env with your configuration

# 5. Install systemd service
sudo cp monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable monitor.service

# 6. Start service
sudo systemctl start monitor.service

# 7. Check status
sudo systemctl status monitor.service
sudo journalctl -u monitor.service -f
```

### Management Commands
```bash
# Start/stop/restart
sudo systemctl start monitor.service
sudo systemctl stop monitor.service
sudo systemctl restart monitor.service

# View logs
sudo journalctl -u monitor.service -f
sudo journalctl -u monitor.service --since "1 hour ago"

# Access dashboard
open http://localhost:8080

# Health check
curl http://localhost:8080/api/health
```

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `SYB_API_KEY` | **Required** | Your SYB API authentication key |
| `ZONE_IDS` | **Required** | Comma-separated list of zone IDs to monitor |
| `POLLING_INTERVAL` | `60` | Check interval in seconds |
| `OFFLINE_THRESHOLD` | `600` | Offline threshold in seconds (10 min) |
| `PUSHOVER_TOKEN` | - | Pushover application token |
| `PUSHOVER_USER_KEY` | - | Pushover user key |
| `SMTP_HOST` | - | SMTP server hostname |
| `SMTP_USERNAME` | - | SMTP authentication username |
| `EMAIL_FROM` | - | Sender email address |
| `EMAIL_TO` | - | Alert recipient email |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `REQUEST_TIMEOUT` | `30` | HTTP request timeout in seconds |
| `MAX_RETRIES` | `5` | Maximum retry attempts for failed requests |

## API Rate Limiting

The SYB API has rate limits. The default polling interval of 60 seconds should be safe for most use cases. If you experience rate limiting:

1. **Increase polling interval**: Set `POLLING_INTERVAL=120` or higher
2. **Monitor logs** for rate limit warnings
3. **Contact SYB support** if you need higher limits

## Notification Behavior

### Alert Triggering
- Alerts fire when a zone is offline ≥ 10 minutes
- Maximum one alert per zone per 30 minutes (prevents spam)
- Notifications include zone name, offline duration, and dashboard link

### Fallback Logic
1. **Primary**: Pushover push notification (if configured)
2. **Fallback**: Email notification (if Pushover fails or not configured)
3. **Retry**: Exponential backoff for failed API calls

### Message Format
```
🌐 Zone "Studio A" offline since 14:30 (>15 min)
Dashboard: https://app.soundtrackyourbrand.com
```

## Health Monitoring

The service exposes a health endpoint on port 8000:

```bash
curl http://localhost:8000/healthz
```

Response example:
```json
{
  "uptime": "2:15:30.123456",
  "zones": {
    "zone_123": {
      "name": "Studio A",
      "online": false,
      "offline_since": "2024-01-15T14:30:00.000Z",
      "offline_duration_seconds": 900
    }
  },
  "last_check": "2024-01-15T14:45:00.000Z",
  "status": "healthy"
}
```

## Testing

Run unit tests:
```bash
python -m pytest tests/ -v
```

Test notification configuration:
```bash
# Test Pushover
python -c "
import asyncio
from config import Config
from notifier.pushover import PushoverNotifier
from datetime import timedelta

config = Config.from_env()
notifier = PushoverNotifier(config)
asyncio.run(notifier.send_notification('Test Zone', timedelta(minutes=15)))
"
```

## Troubleshooting

### Common Issues

**Service won't start**
```bash
# Check configuration
python -c "from config import Config; Config.from_env()"

# Check logs
sudo journalctl -u monitor.service --no-pager
```

**No notifications received**
```bash
# Verify configuration
env | grep -E "(PUSHOVER|SMTP|EMAIL)"

# Test notification manually (see Testing section)
```

**API authentication errors**
```bash
# Verify API key
curl -H "Authorization: Bearer $SYB_API_KEY" \
     https://api.soundtrackyourbrand.com/v2/graphql \
     -d '{"query": "{ me { id } }"}'
```

**Health check fails**
```bash
# Check if service is running
sudo systemctl status monitor.service

# Check port availability
netstat -tlnp | grep 8000
```

### Log Analysis

Important log patterns to watch:
- `Zone .* went offline` - Zone status changes
- `Alert sent successfully` - Notification success
- `Pushover API error` - Notification failures
- `GraphQL errors` - API issues

## Security Considerations

- **API Keys**: Store in `.env` file with restricted permissions (`chmod 600 .env`)
- **SMTP Passwords**: Use app-specific passwords for Gmail
- **Firewall**: Restrict health endpoint access if needed
- **User Permissions**: Run service as non-root user (systemd configuration included)

## Next Steps

1. **Configure your `.env` file** with actual credentials
2. **Test notification providers** using the testing commands
3. **Deploy using your preferred method** (Docker or systemd)
4. **Set up monitoring** of the health endpoint
5. **Configure log rotation** if using systemd deployment

## Support

For issues related to:
- **SYB API**: Contact Soundtrack Your Brand support
- **This monitor**: Check logs and configuration first

## Architecture Notes

- **Modular design**: Easy to add new notification providers
- **Graceful shutdown**: Handles SIGINT/SIGTERM properly
- **Error resilience**: Exponential backoff and retry logic
- **State management**: Tracks zone states and offline durations
- **Health monitoring**: Built-in health endpoint for external monitoring