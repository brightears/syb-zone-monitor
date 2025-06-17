"""Web dashboard server for SYB Zone monitoring."""

from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import json
import os

from config import Config
from zone_monitor import ZoneMonitor


class DashboardServer:
    """Web dashboard server for zone monitoring."""
    
    def __init__(self, zone_monitor: ZoneMonitor):
        self.zone_monitor = zone_monitor
        self.app = FastAPI(title="SYB Zone Monitor Dashboard", version="1.0.0")
        self.logger = logging.getLogger(__name__)
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Serve the main dashboard page."""
            return self._get_dashboard_html()
        
        @self.app.get("/api/zones")
        async def get_zones():
            """API endpoint to get all zones with account grouping."""
            try:
                zones_data = await self._get_zones_with_accounts()
                return JSONResponse(zones_data)
            except Exception as e:
                self.logger.error(f"Error getting zones data: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint."""
            try:
                # Get basic health data
                uptime = datetime.now() - self.zone_monitor.last_check_time if self.zone_monitor.last_check_time else None
                detailed_status = self.zone_monitor.get_detailed_status()
                
                total_zones = len(detailed_status)
                online_zones = sum(1 for zone in detailed_status.values() if zone['online'])
                offline_zones = total_zones - online_zones
                
                return {
                    "status": "healthy",
                    "last_check": self.zone_monitor.last_check_time.isoformat() if self.zone_monitor.last_check_time else None,
                    "total_zones": total_zones,
                    "online_zones": online_zones,
                    "offline_zones": offline_zones,
                    "uptime_seconds": int(uptime.total_seconds()) if uptime else 0
                }
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/contacts")
        async def get_account_contacts():
            """API endpoint to get all account contacts for notifications."""
            try:
                contacts_data = await self._get_account_contacts()
                return JSONResponse(contacts_data)
            except Exception as e:
                self.logger.error(f"Error getting contacts data: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/notify")
        async def send_notifications(request: Request):
            """Send notifications to selected accounts."""
            try:
                form_data = await request.form()
                selected_accounts = form_data.getlist("selected_accounts")
                
                if not selected_accounts:
                    return JSONResponse({"error": "No accounts selected"})
                    
                result = await self._send_notifications(selected_accounts)
                return JSONResponse(result)
            except Exception as e:
                self.logger.error(f"Error sending notifications: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _get_zones_with_accounts(self) -> Dict:
        """Get zones data grouped by accounts with additional metadata."""
        detailed_status = self.zone_monitor.get_detailed_status()
        
        # Group zones by account (extracted from zone ID)
        accounts = {}
        
        for zone_id, zone_info in detailed_status.items():
            # Extract account info from zone ID (Base64 encoded)
            try:
                # Zone IDs contain account information - we'll group by business name pattern
                zone_name = zone_info['name']
                
                # Determine account grouping based on zone names and patterns
                account_name = self._determine_account_name(zone_name, zone_id)
                
                if account_name not in accounts:
                    accounts[account_name] = {
                        "account_name": account_name,
                        "zones": [],
                        "total_zones": 0,
                        "online_zones": 0,
                        "offline_zones": 0
                    }
                
                # Add zone to account with detailed status
                zone_data = {
                    "id": zone_id,
                    "name": zone_name,
                    "online": zone_info['online'],  # Backward compatibility
                    "status": zone_info.get('status', 'offline'),
                    "status_label": zone_info.get('status_label', 'Unknown'),
                    "offline_since": zone_info['offline_since'],
                    "offline_duration_seconds": zone_info['offline_duration_seconds'],
                    "offline_duration_minutes": zone_info['offline_duration_seconds'] // 60 if zone_info['offline_duration_seconds'] else 0,
                    "details": zone_info.get('details', {})
                }
                
                accounts[account_name]["zones"].append(zone_data)
                accounts[account_name]["total_zones"] += 1
                
                # Count zones by detailed status
                status = zone_info.get('status', 'offline')
                if status == 'online':
                    accounts[account_name]["online_zones"] += 1
                elif status in ['offline', 'expired', 'unpaired']:
                    accounts[account_name]["offline_zones"] += 1
                
                # Add detailed status counts
                status_key = f"{status}_zones"
                if status_key not in accounts[account_name]:
                    accounts[account_name][status_key] = 0
                accounts[account_name][status_key] += 1
                    
            except Exception as e:
                self.logger.warning(f"Error processing zone {zone_id}: {e}")
        
        # Convert to list and sort
        accounts_list = list(accounts.values())
        accounts_list.sort(key=lambda x: x['account_name'])
        
        # Calculate totals including new status types
        total_zones = sum(acc['total_zones'] for acc in accounts_list)
        total_online = sum(acc.get('online_zones', 0) for acc in accounts_list)
        total_offline = sum(acc.get('offline_zones', 0) for acc in accounts_list)
        total_expired = sum(acc.get('expired_zones', 0) for acc in accounts_list)
        total_unpaired = sum(acc.get('unpaired_zones', 0) for acc in accounts_list)
        
        return {
            "accounts": accounts_list,
            "summary": {
                "total_accounts": len(accounts_list),
                "total_zones": total_zones,
                "total_online": total_online,
                "total_offline": total_offline,
                "total_expired": total_expired,
                "total_unpaired": total_unpaired,
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def _determine_account_name(self, zone_name: str, zone_id: str) -> str:
        """Extract the real account name from the zone ID."""
        try:
            # Zone IDs are Base64 encoded and contain account information
            # Format: U291bmRab25lLCwxbjFteGk0NHJnZy9Mb2NhdGlvbiwsMWdoZXh3eDdhNGcvQWNjb3VudCwsMW1sbTJ0ZW52OWMv
            # When decoded, this contains references to the account ID
            
            # Load the account mapping we discovered
            import json
            import os
            
            mapping_file = os.path.join(os.path.dirname(__file__), "account_mapping.json")
            
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r') as f:
                    account_mapping = json.load(f)
                
                # Extract account ID from zone ID by looking for account patterns
                for account_id, account_name in account_mapping["accounts"].items():
                    # The account ID is Base64 encoded and might be part of the zone ID
                    # Try to match the account ID pattern in the zone ID
                    if account_id.replace("=", "").replace("/", "") in zone_id.replace("=", "").replace("/", ""):
                        return account_name
                
                # Alternative approach: decode and parse the zone ID
                try:
                    import base64
                    decoded = base64.b64decode(zone_id + "==").decode('utf-8', errors='ignore')
                    
                    # Look for account ID patterns in decoded string
                    for account_id, account_name in account_mapping["accounts"].items():
                        account_short = account_id.split(',')[1] if ',' in account_id else account_id
                        if account_short in decoded:
                            return account_name
                            
                except Exception:
                    pass
            
        except Exception as e:
            self.logger.warning(f"Error determining account name for zone {zone_id}: {e}")
        
        # Fallback to zone name grouping if mapping fails
        return f"Unknown Account ({zone_name})"
    
    async def _get_account_contacts(self) -> Dict:
        """Get account contacts from the FINAL_CONTACT_ANALYSIS.json file."""
        try:
            # Load the contact analysis data
            contacts_file = os.path.join(os.path.dirname(__file__), "FINAL_CONTACT_ANALYSIS.json")
            
            if not os.path.exists(contacts_file):
                return {
                    "error": "Contact data not found. Please run the contact discovery script first.",
                    "accounts": [],
                    "total_contacts": 0
                }
            
            with open(contacts_file, 'r') as f:
                contact_data = json.load(f)
            
            # Process the contact data for the notification UI
            accounts_with_contacts = []
            
            for account_info in contact_data.get("accounts_with_contacts", []):
                business_name = account_info["business_name"].strip()
                active_users = account_info.get("active_users", 0)
                pending_users = account_info.get("pending_users", 0)
                total_contacts = active_users + pending_users
                
                # Get contact details
                contacts = account_info.get("contacts", [])
                active_contacts = [c for c in contacts if c.get("type") == "active"]
                pending_contacts = [c for c in contacts if c.get("type") == "pending"]
                
                accounts_with_contacts.append({
                    "business_name": business_name,
                    "total_contacts": total_contacts,
                    "active_users": active_users,
                    "pending_users": pending_users,
                    "active_contacts": active_contacts,
                    "pending_contacts": pending_contacts,
                    "all_emails": [c.get("email") for c in contacts if c.get("email")]
                })
            
            # Sort by business name
            accounts_with_contacts.sort(key=lambda x: x["business_name"])
            
            return {
                "accounts": accounts_with_contacts,
                "total_accounts": len(accounts_with_contacts),
                "total_contacts": sum(acc["total_contacts"] for acc in accounts_with_contacts),
                "analysis": contact_data.get("analysis", {}),
                "timestamp": contact_data.get("timestamp")
            }
            
        except Exception as e:
            self.logger.error(f"Error loading contact data: {e}")
            return {
                "error": str(e),
                "accounts": [],
                "total_contacts": 0
            }
    
    async def _send_notifications(self, selected_accounts: list) -> Dict:
        """Send notifications to selected accounts."""
        try:
            # Load contact data
            contacts_data = await self._get_account_contacts()
            
            if "error" in contacts_data:
                return {"error": contacts_data["error"]}
            
            # Get current zone status for the accounts
            zones_data = await self._get_zones_with_accounts()
            
            notifications_sent = []
            errors = []
            
            for account_name in selected_accounts:
                try:
                    # Find account contact info
                    account_contacts = None
                    for acc in contacts_data["accounts"]:
                        if acc["business_name"] == account_name:
                            account_contacts = acc
                            break
                    
                    if not account_contacts:
                        errors.append(f"No contacts found for {account_name}")
                        continue
                    
                    # Find account zone status
                    account_zones = None
                    for acc in zones_data["accounts"]:
                        if acc["account_name"] == account_name:
                            account_zones = acc
                            break
                    
                    if not account_zones:
                        errors.append(f"No zone data found for {account_name}")
                        continue
                    
                    # Prepare notification content
                    notification_result = await self._send_account_notification(
                        account_contacts, account_zones
                    )
                    
                    notifications_sent.append({
                        "account": account_name,
                        "emails_sent": notification_result["emails_sent"],
                        "message": notification_result["message"]
                    })
                    
                except Exception as e:
                    errors.append(f"Error notifying {account_name}: {str(e)}")
            
            return {
                "success": True,
                "notifications_sent": len(notifications_sent),
                "total_emails": sum(n["emails_sent"] for n in notifications_sent),
                "results": notifications_sent,
                "errors": errors
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_account_notification(self, account_contacts: Dict, account_zones: Dict) -> Dict:
        """Send notification to a specific account."""
        try:
            # For now, we'll simulate sending emails and log the content
            # In a real implementation, you would integrate with an email service
            
            account_name = account_contacts["business_name"]
            emails = account_contacts["all_emails"]
            
            # Generate status report
            total_zones = account_zones["total_zones"]
            online_zones = account_zones.get("online_zones", 0)
            offline_zones = account_zones.get("offline_zones", 0)
            expired_zones = account_zones.get("expired_zones", 0)
            unpaired_zones = account_zones.get("unpaired_zones", 0)
            
            # Create email content
            subject = f"SYB Zone Status Report - {account_name}"
            
            if offline_zones > 0 or expired_zones > 0 or unpaired_zones > 0:
                status_type = "⚠️ Issues Detected"
            else:
                status_type = "✅ All Systems Operational"
            
            email_content = f"""
            Subject: {subject}
            
            {status_type}
            
            Dear {account_name} Team,
            
            Here's your current SYB zone status report:
            
            📊 ZONE SUMMARY:
            • Total Zones: {total_zones}
            • Online: {online_zones}
            • Offline: {offline_zones}
            • Subscription Expired: {expired_zones}
            • No Paired Device: {unpaired_zones}
            
            🎵 ZONE DETAILS:
            """
            
            # Add individual zone status
            for zone in account_zones["zones"]:
                status_emoji = {
                    "online": "✅",
                    "offline": "❌", 
                    "expired": "⚠️",
                    "unpaired": "⭕"
                }.get(zone.get("status", "offline"), "❓")
                
                email_content += f"\n            {status_emoji} {zone['name']} - {zone.get('status_label', 'Unknown')}"
                
                if zone.get("offline_duration_minutes", 0) > 0:
                    email_content += f" (offline for {zone['offline_duration_minutes']} minutes)"
            
            email_content += f"""
            
            📅 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            If you have any questions or need assistance, please contact your SYB support team.
            
            Best regards,
            SYB Monitoring System
            """
            
            # Log the notification (in a real implementation, send actual emails here)
            self.logger.info(f"Notification prepared for {account_name}:")
            self.logger.info(f"Recipients: {', '.join(emails)}")
            self.logger.info(f"Content:\n{email_content}")
            
            # For demonstration, we'll write to a file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            notification_file = f"notification_{account_name.replace(' ', '_')}_{timestamp}.txt"
            
            with open(notification_file, 'w') as f:
                f.write(f"Recipients: {', '.join(emails)}\n\n")
                f.write(email_content)
            
            return {
                "emails_sent": len(emails),
                "message": f"Notification prepared for {len(emails)} recipients (saved to {notification_file})"
            }
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
            return {
                "emails_sent": 0,
                "message": f"Error: {str(e)}"
            }
    
    def _get_dashboard_html(self) -> str:
        """Generate the dashboard HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SYB Zone Monitor Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f7;
            color: #1d1d1f;
            line-height: 1.4;
        }
        
        .header {
            background: white;
            border-bottom: 1px solid #d1d1d6;
            padding: 1rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .summary {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        
        .summary-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }
        
        .status-online { background: #34c759; }
        .status-offline { background: #ff3b30; }
        .status-expired { background: #ff9500; }
        .status-unpaired { background: #8e8e93; }
        .status-total { background: #007aff; }
        
        .controls {
            background: white;
            padding: 1rem 2rem;
            border-bottom: 1px solid #d1d1d6;
        }
        
        .controls-row {
            display: flex;
            gap: 1rem;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .search-box {
            flex: 1;
            min-width: 250px;
            padding: 0.5rem 1rem;
            border: 1px solid #d1d1d6;
            border-radius: 8px;
            font-size: 0.9rem;
        }
        
        .filter-buttons {
            display: flex;
            gap: 0.5rem;
        }
        
        .filter-btn {
            padding: 0.5rem 1rem;
            border: 1px solid #d1d1d6;
            background: white;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s;
        }
        
        .filter-btn:hover {
            background: #f5f5f7;
        }
        
        .filter-btn.active {
            background: #007aff;
            color: white;
            border-color: #007aff;
        }
        
        .auto-refresh {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            color: #666;
        }
        
        .main-content {
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
        }
        
        .account-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid #d1d1d6;
        }
        
        .account-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .account-name {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1d1d1f;
        }
        
        .account-summary {
            display: flex;
            gap: 1rem;
            font-size: 0.85rem;
            color: #666;
        }
        
        .zones-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 0.75rem;
        }
        
        .zone-card {
            padding: 0.75rem;
            border: 1px solid #f0f0f0;
            border-radius: 8px;
            transition: all 0.2s;
        }
        
        .zone-card:hover {
            border-color: #d1d1d6;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        .zone-card.online {
            border-left: 3px solid #34c759;
        }
        
        .zone-card.offline {
            border-left: 3px solid #ff3b30;
            background: #fff5f5;
        }
        
        .zone-card.expired {
            border-left: 3px solid #ff9500;
            background: #fff8f0;
        }
        
        .zone-card.unpaired {
            border-left: 3px solid #8e8e93;
            background: #f8f8f8;
        }
        
        .zone-name {
            font-weight: 500;
            margin-bottom: 0.25rem;
        }
        
        .zone-status {
            font-size: 0.8rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .zone-offline-time {
            font-size: 0.75rem;
            color: #ff3b30;
            margin-top: 0.25rem;
        }
        
        .no-results {
            text-align: center;
            padding: 3rem;
            color: #666;
        }
        
        /* Notification Modal Styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        
        .modal-content {
            background: white;
            margin: 5% auto;
            padding: 2rem;
            border-radius: 12px;
            width: 90%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
            position: relative;
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #d1d1d6;
        }
        
        .modal-header h2 {
            margin: 0;
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        .close-btn {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #666;
            padding: 0.5rem;
            border-radius: 6px;
        }
        
        .close-btn:hover {
            background: #f5f5f7;
        }
        
        .notification-section {
            margin-bottom: 2rem;
        }
        
        .notification-section h3 {
            margin-bottom: 1rem;
            font-size: 1.1rem;
            color: #1d1d1f;
        }
        
        .account-selector {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #d1d1d6;
            border-radius: 8px;
            padding: 1rem;
        }
        
        .account-checkbox {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .account-checkbox:hover {
            background: #f5f5f7;
        }
        
        .account-checkbox input[type="checkbox"] {
            width: 16px;
            height: 16px;
        }
        
        .account-info {
            flex: 1;
        }
        
        .account-info .name {
            font-weight: 500;
            margin-bottom: 0.25rem;
        }
        
        .account-info .contacts {
            font-size: 0.85rem;
            color: #666;
        }
        
        .notification-controls {
            display: flex;
            gap: 1rem;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .select-all-btn, .send-btn {
            padding: 0.5rem 1rem;
            border: 1px solid #d1d1d6;
            background: white;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
        }
        
        .select-all-btn:hover {
            background: #f5f5f7;
        }
        
        .send-btn {
            background: #34c759;
            color: white;
            border-color: #34c759;
            font-weight: 500;
        }
        
        .send-btn:hover {
            background: #28a745;
        }
        
        .send-btn:disabled {
            background: #ccc;
            border-color: #ccc;
            cursor: not-allowed;
        }
        
        .notification-result {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 8px;
            display: none;
        }
        
        .notification-result.success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        
        .notification-result.error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        
        .loading-spinner {
            display: none;
            margin-left: 0.5rem;
        }
        
        @media (max-width: 768px) {
            .header, .controls, .main-content {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            
            .summary {
                flex-wrap: wrap;
                gap: 1rem;
            }
            
            .controls-row {
                flex-direction: column;
                align-items: stretch;
            }
            
            .search-box {
                min-width: auto;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎵 SYB Zone Monitor Dashboard</h1>
        <div class="summary" id="summary">
            <div class="summary-item">
                <span class="status-dot status-total"></span>
                <span id="total-zones">0</span> Total Zones
            </div>
            <div class="summary-item">
                <span class="status-dot status-online"></span>
                <span id="online-zones">0</span> Online
            </div>
            <div class="summary-item">
                <span class="status-dot status-offline"></span>
                <span id="offline-zones">0</span> Offline
            </div>
            <div class="summary-item">
                <span class="status-dot status-expired"></span>
                <span id="expired-zones">0</span> Expired
            </div>
            <div class="summary-item">
                <span class="status-dot status-unpaired"></span>
                <span id="unpaired-zones">0</span> Unpaired
            </div>
            <div class="summary-item">
                <span id="accounts-count">0</span> Accounts
            </div>
        </div>
    </div>
    
    <div class="controls">
        <div class="controls-row">
            <input type="text" class="search-box" id="search" placeholder="Search accounts or zones...">
            <div class="filter-buttons">
                <button class="filter-btn active" data-filter="all">All</button>
                <button class="filter-btn" data-filter="online">Online</button>
                <button class="filter-btn" data-filter="offline">Offline</button>
                <button class="filter-btn" data-filter="expired">Expired</button>
                <button class="filter-btn" data-filter="unpaired">Unpaired</button>
            </div>
            <button class="filter-btn" id="notifications-btn" style="background: #007aff; color: white; border-color: #007aff;">📧 Send Notifications</button>
            <div class="auto-refresh">
                <span>Auto-refresh: <span id="refresh-countdown">30</span>s</span>
            </div>
        </div>
    </div>
    
    <div class="main-content">
        <div id="loading" class="loading">Loading zones...</div>
        <div id="accounts-container" style="display: none;"></div>
        <div id="no-results" class="no-results" style="display: none;">
            <h3>No zones found</h3>
            <p>Try adjusting your search or filter settings.</p>
        </div>
    </div>
    
    <!-- Notification Modal -->
    <div id="notification-modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>📧 Send Account Notifications</h2>
                <button class="close-btn" id="close-modal">&times;</button>
            </div>
            
            <div class="notification-section">
                <h3 id="notification-title">Select Contacts to Notify</h3>
                <div id="account-name-display" style="font-size: 0.9rem; color: #666; margin-bottom: 1rem;"></div>
                <div class="notification-controls">
                    <button class="select-all-btn" id="select-all-contacts">Select All</button>
                    <button class="select-all-btn" id="select-none-contacts">Select None</button>
                    <span id="selected-count">0 contacts selected</span>
                </div>
                
                <div class="account-selector" id="contact-selector">
                    <div class="loading">Loading account contacts...</div>
                </div>
            </div>
            
            <div class="notification-section">
                <button class="send-btn" id="send-notifications" disabled>
                    Send Notifications
                    <span class="loading-spinner" id="send-spinner">⏳</span>
                </button>
                
                <div id="notification-result" class="notification-result">
                    <!-- Results will appear here -->
                </div>
            </div>
        </div>
    </div>

    <script>
        let zonesData = [];
        let currentFilter = 'all';
        let currentSearch = '';
        let refreshTimer;
        let countdownTimer;
        let countdownValue = 30;

        async function loadZones() {
            try {
                const response = await fetch('/api/zones');
                const data = await response.json();
                zonesData = data;
                updateSummary(data.summary);
                renderAccounts(data.accounts);
                document.getElementById('loading').style.display = 'none';
                document.getElementById('accounts-container').style.display = 'block';
                resetCountdown();
            } catch (error) {
                console.error('Error loading zones:', error);
                document.getElementById('loading').innerHTML = 'Error loading data. Please refresh the page.';
            }
        }

        function updateSummary(summary) {
            document.getElementById('total-zones').textContent = summary.total_zones;
            document.getElementById('online-zones').textContent = summary.total_online;
            document.getElementById('offline-zones').textContent = summary.total_offline;
            document.getElementById('expired-zones').textContent = summary.total_expired || 0;
            document.getElementById('unpaired-zones').textContent = summary.total_unpaired || 0;
            document.getElementById('accounts-count').textContent = summary.total_accounts;
        }

        function renderAccounts(accounts) {
            const container = document.getElementById('accounts-container');
            const noResults = document.getElementById('no-results');
            
            const filteredAccounts = filterAccounts(accounts);
            
            if (filteredAccounts.length === 0) {
                container.style.display = 'none';
                noResults.style.display = 'block';
                return;
            }
            
            container.style.display = 'block';
            noResults.style.display = 'none';
            
            container.innerHTML = filteredAccounts.map(account => `
                <div class="account-card">
                    <div class="account-header">
                        <div class="account-name">${account.account_name}</div>
                        <div class="account-summary">
                            <span>${account.total_zones} zones</span>
                            <span style="color: #34c759;">${account.online_zones || 0} online</span>
                            ${(account.offline_zones || 0) > 0 ? `<span style="color: #ff3b30;">${account.offline_zones} offline</span>` : ''}
                            ${(account.expired_zones || 0) > 0 ? `<span style="color: #ff9500;">${account.expired_zones} expired</span>` : ''}
                            ${(account.unpaired_zones || 0) > 0 ? `<span style="color: #8e8e93;">${account.unpaired_zones} unpaired</span>` : ''}
                            <button class="notify-account-btn" onclick="openAccountNotification('${account.account_name}')" style="margin-left: 1rem; padding: 0.3rem 0.8rem; background: #007aff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">📧 Notify</button>
                        </div>
                    </div>
                    <div class="zones-grid">
                        ${account.zones.map(zone => {
                            const matchesFilter = 
                                currentFilter === 'all' || 
                                (currentFilter === 'online' && zone.status === 'online') ||
                                (currentFilter === 'offline' && zone.status === 'offline') ||
                                (currentFilter === 'expired' && zone.status === 'expired') ||
                                (currentFilter === 'unpaired' && zone.status === 'unpaired');
                            
                            const matchesSearch = 
                                zone.name.toLowerCase().includes(currentSearch.toLowerCase()) ||
                                account.account_name.toLowerCase().includes(currentSearch.toLowerCase());
                            
                            if (!matchesFilter || !matchesSearch) return '';
                            
                            const status = zone.status || (zone.online ? 'online' : 'offline');
                            const statusLabel = zone.status_label || (zone.online ? 'Online' : 'Offline');
                            
                            return `
                                <div class="zone-card ${status}">
                                    <div class="zone-name">${zone.name}</div>
                                    <div class="zone-status">
                                        <span class="status-dot status-${status}"></span>
                                        ${statusLabel}
                                    </div>
                                    ${status === 'offline' && zone.offline_duration_minutes > 0 ? 
                                        `<div class="zone-offline-time">Offline for ${zone.offline_duration_minutes} minutes</div>` : ''}
                                    ${zone.details && zone.details.deviceName ? 
                                        `<div class="zone-offline-time" style="color: #666;">Device: ${zone.details.deviceName}</div>` : ''}
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `).join('');
        }

        function filterAccounts(accounts) {
            return accounts.map(account => ({
                ...account,
                zones: account.zones.filter(zone => {
                    const matchesFilter = 
                        currentFilter === 'all' || 
                        (currentFilter === 'online' && zone.status === 'online') ||
                        (currentFilter === 'offline' && zone.status === 'offline') ||
                        (currentFilter === 'expired' && zone.status === 'expired') ||
                        (currentFilter === 'unpaired' && zone.status === 'unpaired');
                    
                    const matchesSearch = 
                        zone.name.toLowerCase().includes(currentSearch.toLowerCase()) ||
                        account.account_name.toLowerCase().includes(currentSearch.toLowerCase());
                    
                    return matchesFilter && matchesSearch;
                })
            })).filter(account => account.zones.length > 0);
        }

        function resetCountdown() {
            countdownValue = 30;
            document.getElementById('refresh-countdown').textContent = countdownValue;
        }

        function startAutoRefresh() {
            refreshTimer = setInterval(loadZones, 30000);
            countdownTimer = setInterval(() => {
                countdownValue--;
                document.getElementById('refresh-countdown').textContent = countdownValue;
                if (countdownValue <= 0) {
                    countdownValue = 30;
                }
            }, 1000);
        }

        // Event listeners
        document.getElementById('search').addEventListener('input', (e) => {
            currentSearch = e.target.value;
            if (zonesData.accounts) {
                renderAccounts(zonesData.accounts);
            }
        });

        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                if (zonesData.accounts) {
                    renderAccounts(zonesData.accounts);
                }
            });
        });

        // Notification system
        let allAccountContacts = [];
        let currentAccount = null;
        let selectedContacts = new Set();
        
        async function loadAllAccountContacts() {
            try {
                const response = await fetch('/api/contacts');
                const data = await response.json();
                allAccountContacts = data;
                return data;
            } catch (error) {
                console.error('Error loading contacts:', error);
                return { error: 'Failed to load contacts', accounts: [] };
            }
        }
        
        function openAccountNotification(accountName) {
            currentAccount = accountName;
            document.getElementById('notification-modal').style.display = 'block';
            loadAccountContactsForAccount(accountName);
        }
        
        async function loadAccountContactsForAccount(accountName) {
            const selector = document.getElementById('contact-selector');
            const titleEl = document.getElementById('notification-title');
            const accountDisplayEl = document.getElementById('account-name-display');
            
            // Update title and account display
            titleEl.textContent = 'Select Contacts to Notify';
            accountDisplayEl.textContent = `Account: ${accountName}`;
            
            selector.innerHTML = '<div class="loading">Loading contacts for this account...</div>';
            
            if (!allAccountContacts.accounts) {
                await loadAllAccountContacts();
            }
            
            // Find the specific account with flexible matching
            let account = allAccountContacts.accounts.find(acc => acc.business_name === accountName);
            
            // If exact match fails, try partial matching
            if (!account) {
                account = allAccountContacts.accounts.find(acc => {
                    const businessName = acc.business_name.toLowerCase();
                    const searchName = accountName.toLowerCase();
                    
                    // Try various matching strategies
                    return businessName.includes(searchName) || 
                           searchName.includes(businessName) ||
                           businessName.replace(/[^a-z0-9]/g, '').includes(searchName.replace(/[^a-z0-9]/g, '')) ||
                           searchName.replace(/[^a-z0-9]/g, '').includes(businessName.replace(/[^a-z0-9]/g, ''));
                });
            }
            
            if (!account) {
                // Show available account names for debugging
                const availableAccounts = allAccountContacts.accounts.map(acc => acc.business_name).join(', ');
                selector.innerHTML = `
                    <div class="error">
                        No contact information found for "${accountName}". This account may not have configured admin users.
                        <br><br>
                        <details>
                            <summary>Available accounts with contacts (${allAccountContacts.accounts.length})</summary>
                            <div style="margin-top: 10px; font-size: 0.8rem; max-height: 200px; overflow-y: auto;">
                                ${availableAccounts}
                            </div>
                        </details>
                    </div>
                `;
                return;
            }
            
            renderContactSelector(account);
        }
        
        function renderContactSelector(account) {
            const selector = document.getElementById('contact-selector');
            
            const allContacts = [
                ...account.active_contacts.map(c => ({ ...c, type: 'active' })),
                ...account.pending_contacts.map(c => ({ ...c, type: 'pending' }))
            ];
            
            if (allContacts.length === 0) {
                selector.innerHTML = '<div class="no-results">This account has no configured contacts.</div>';
                return;
            }
            
            selector.innerHTML = allContacts.map((contact, index) => `
                <label class="account-checkbox">
                    <input type="checkbox" value="${contact.email}" onchange="updateSelectedContacts()">
                    <div class="account-info">
                        <div class="name">${contact.email}</div>
                        <div class="contacts">${contact.name || 'No name'} - ${contact.type} user ${contact.role ? `(${contact.role})` : ''}</div>
                    </div>
                </label>
            `).join('');
            
            updateSelectedContactCount();
        }
        
        function updateSelectedContacts() {
            selectedContacts.clear();
            document.querySelectorAll('#contact-selector input[type="checkbox"]:checked').forEach(cb => {
                selectedContacts.add(cb.value);
            });
            updateSelectedContactCount();
        }
        
        function updateSelectedContactCount() {
            const count = selectedContacts.size;
            document.getElementById('selected-count').textContent = `${count} contact${count !== 1 ? 's' : ''} selected`;
            document.getElementById('send-notifications').disabled = count === 0;
        }
        
        function selectAllContacts() {
            document.querySelectorAll('#contact-selector input[type="checkbox"]').forEach(cb => {
                cb.checked = true;
            });
            updateSelectedContacts();
        }
        
        function selectNoneContacts() {
            document.querySelectorAll('#contact-selector input[type="checkbox"]').forEach(cb => {
                cb.checked = false;
            });
            updateSelectedContacts();
        }
        
        async function sendNotifications() {
            const selectedContactsList = Array.from(selectedContacts);
            
            if (selectedContactsList.length === 0) {
                alert('Please select at least one contact to notify.');
                return;
            }
            
            if (!currentAccount) {
                alert('No account selected.');
                return;
            }
            
            const sendBtn = document.getElementById('send-notifications');
            const spinner = document.getElementById('send-spinner');
            const resultDiv = document.getElementById('notification-result');
            
            // Show loading state
            sendBtn.disabled = true;
            spinner.style.display = 'inline';
            resultDiv.style.display = 'none';
            
            try {
                // Prepare form data
                const formData = new FormData();
                formData.append('selected_accounts', currentAccount);
                selectedContactsList.forEach(contact => {
                    formData.append('selected_contacts', contact);
                });
                
                const response = await fetch('/api/notify', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                // Show results
                resultDiv.style.display = 'block';
                
                if (result.success) {
                    resultDiv.className = 'notification-result success';
                    resultDiv.innerHTML = `
                        <h4>✅ Notifications Sent Successfully!</h4>
                        <p>Sent emails to ${selectedContactsList.length} contacts for ${currentAccount}.</p>
                        <p><strong>Recipients:</strong> ${selectedContactsList.join(', ')}</p>
                        ${result.errors && result.errors.length > 0 ? `<p><strong>Errors:</strong> ${result.errors.join(', ')}</p>` : ''}
                    `;
                } else {
                    resultDiv.className = 'notification-result error';
                    resultDiv.innerHTML = `
                        <h4>❌ Error Sending Notifications</h4>
                        <p>${result.error}</p>
                    `;
                }
                
            } catch (error) {
                console.error('Error sending notifications:', error);
                resultDiv.style.display = 'block';
                resultDiv.className = 'notification-result error';
                resultDiv.innerHTML = `
                    <h4>❌ Network Error</h4>
                    <p>Failed to send notifications. Please try again.</p>
                `;
            } finally {
                // Hide loading state
                sendBtn.disabled = false;
                spinner.style.display = 'none';
            }
        }
        
        // Modal event listeners - wait for DOM to be ready
        document.addEventListener('DOMContentLoaded', function() {
            const notificationsBtn = document.getElementById('notifications-btn');
            const closeModal = document.getElementById('close-modal');
            const selectAllBtn = document.getElementById('select-all-accounts');
            const selectNoneBtn = document.getElementById('select-none-accounts');
            const sendBtn = document.getElementById('send-notifications');
            
            if (notificationsBtn) {
                notificationsBtn.addEventListener('click', () => {
                    document.getElementById('notification-modal').style.display = 'block';
                    loadAccountContacts();
                });
            }
            
            if (closeModal) {
                closeModal.addEventListener('click', () => {
                    document.getElementById('notification-modal').style.display = 'none';
                });
            }
            
            if (selectAllBtn) selectAllBtn.addEventListener('click', selectAllAccounts);
            if (selectNoneBtn) selectNoneBtn.addEventListener('click', selectNoneAccounts);
            if (sendBtn) sendBtn.addEventListener('click', sendNotifications);
            
            // Close modal when clicking outside
            window.addEventListener('click', (event) => {
                const modal = document.getElementById('notification-modal');
                if (modal && event.target === modal) {
                    modal.style.display = 'none';
                }
            });
        });
        
        // Initialize
        loadZones();
        startAutoRefresh();
    </script>
</body>
</html>
        """
    
    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Run the web server."""
        self.logger.info(f"Starting dashboard server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, log_level="info")


async def run_dashboard_server(zone_monitor: ZoneMonitor, host: str = "0.0.0.0", port: int = 8080):
    """Run the dashboard server in the background."""
    dashboard = DashboardServer(zone_monitor)
    config = uvicorn.Config(dashboard.app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()