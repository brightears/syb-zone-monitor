#!/usr/bin/env python3
"""Enhanced dashboard that uses discovered account data.

This dashboard reads from the accounts_discovery_results.json file
to display all zones across all 863 accounts with their current status.
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from zone_monitor import ZoneMonitor
import os
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Global variables
zone_monitor: Optional[ZoneMonitor] = None
discovered_data: Dict = {}
contact_data: Dict = {}


def load_discovered_data():
    """Load the discovered account data."""
    global discovered_data
    
    results_file = Path("accounts_discovery_results.json")
    if results_file.exists():
        with open(results_file, 'r') as f:
            data = json.load(f)
            discovered_data = data.get('accounts', {})
            logger.info(f"Loaded data for {len(discovered_data)} accounts")
    else:
        logger.warning("No discovery results found. Run process_all_accounts.py first.")
        discovered_data = {}


def load_contact_data():
    """Load contact data from FINAL_CONTACT_ANALYSIS.json."""
    global contact_data
    
    contact_file = Path("FINAL_CONTACT_ANALYSIS.json")
    if contact_file.exists():
        with open(contact_file, 'r') as f:
            data = json.load(f)
            # Convert to dict by business name for easy lookup
            contact_data = {}
            for account in data.get('accounts_with_contacts', []):
                contact_data[account['business_name']] = account['contacts']
            logger.info(f"Loaded contacts for {len(contact_data)} accounts")
    else:
        logger.warning("No contact data found")
        contact_data = {}


def get_all_zone_ids() -> List[str]:
    """Extract all zone IDs from discovered data."""
    zone_ids = []
    for account_data in discovered_data.values():
        for location in account_data.get('locations', []):
            for zone in location.get('zones', []):
                if zone.get('id'):
                    zone_ids.append(zone['id'])
    return zone_ids


async def monitor_zones_background():
    """Background task to periodically check zone status."""
    global zone_monitor
    
    while True:
        try:
            if zone_monitor:
                await zone_monitor.check_zones()
                logger.debug("Zone check completed")
        except Exception as e:
            logger.error(f"Error in background monitoring: {e}")
        
        # Wait for the polling interval
        await asyncio.sleep(60)  # Check every 60 seconds


@app.on_event("startup")
async def startup_event():
    """Initialize the application."""
    global zone_monitor
    import os
    
    # Load discovered data
    load_discovered_data()
    load_contact_data()
    
    # Get all zone IDs
    zone_ids = get_all_zone_ids()
    
    if not zone_ids:
        logger.error("No zones found in discovery data!")
        return
    
    # Initialize zone monitor with discovered zones
    api_key = os.getenv("SYB_API_KEY")
    if not api_key:
        logger.error("SYB_API_KEY not found in environment")
        return
        
    # Initialize zone monitor with discovered zones
    from zone_monitor import ZoneMonitor
    from types import SimpleNamespace
    
    # Create a mock config for the zone monitor
    mock_config = SimpleNamespace(
        syb_api_key=api_key,
        syb_api_url="https://api.soundtrackyourbrand.com/v2",
        zone_ids=zone_ids,
        polling_interval=int(os.getenv("POLLING_INTERVAL", "60")),
        offline_threshold=600,
        request_timeout=30,
        max_retries=5,
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )
    
    zone_monitor = ZoneMonitor(mock_config)
    logger.info(f"Initialized zone monitor with {len(zone_ids)} zones")
    
    # Zone monitor will be used by the background task
    logger.info("Zone monitor initialized and ready")
    
    # Start background task to check zones periodically
    asyncio.create_task(monitor_zones_background())


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the enhanced dashboard."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SYB Zone Monitor - Enhanced Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #0a0e27;
            color: #e4e4e7;
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            padding: 1.5rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.5);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header h1 {
            font-size: 1.75rem;
            font-weight: 600;
            background: linear-gradient(to right, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .stats-bar {
            background: #1e293b;
            padding: 1rem 2rem;
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
            align-items: center;
            border-bottom: 1px solid #334155;
        }
        
        .stat-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 0.5rem 1rem;
            background: #0f172a;
            border-radius: 8px;
            min-width: 120px;
        }
        
        .stat-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #60a5fa;
        }
        
        .stat-label {
            font-size: 0.875rem;
            color: #94a3b8;
        }
        
        .controls {
            padding: 1rem 2rem;
            background: #0f172a;
            border-bottom: 1px solid #1e293b;
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        .search-box {
            flex: 1;
            position: relative;
        }
        
        .search-box input {
            width: 100%;
            padding: 0.75rem 1rem 0.75rem 2.5rem;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            color: #e4e4e7;
            font-size: 0.875rem;
        }
        
        .search-icon {
            position: absolute;
            left: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            color: #64748b;
        }
        
        .filter-buttons {
            display: flex;
            gap: 0.5rem;
        }
        
        .filter-btn {
            padding: 0.5rem 1rem;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 6px;
            color: #e4e4e7;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.875rem;
        }
        
        .filter-btn:hover {
            background: #334155;
        }
        
        .filter-btn.active {
            background: #3b82f6;
            border-color: #3b82f6;
        }
        
        .accounts-container {
            padding: 2rem;
            display: grid;
            gap: 1.5rem;
        }
        
        .account-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 1.5rem;
            transition: all 0.3s;
        }
        
        .account-card:hover {
            border-color: #475569;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        
        .account-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .account-name {
            font-size: 1.125rem;
            font-weight: 600;
            color: #f1f5f9;
        }
        
        .account-stats {
            display: flex;
            gap: 1rem;
            font-size: 0.875rem;
            color: #94a3b8;
        }
        
        .zones-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 0.75rem;
        }
        
        .zone-item {
            background: #0f172a;
            padding: 0.75rem;
            border-radius: 8px;
            border: 1px solid #334155;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .zone-name {
            font-size: 0.875rem;
            color: #e4e4e7;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin-right: 0.5rem;
        }
        
        .zone-status {
            display: flex;
            align-items: center;
            gap: 0.25rem;
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            white-space: nowrap;
        }
        
        .status-online {
            background: #065f46;
            color: #6ee7b7;
        }
        
        .status-offline {
            background: #991b1b;
            color: #fca5a5;
        }
        
        .status-no-device {
            background: #92400e;
            color: #fcd34d;
        }
        
        .status-expired {
            background: #6b21a8;
            color: #e9d5ff;
        }
        
        .notify-btn {
            padding: 0.5rem 1rem;
            background: #3b82f6;
            border: none;
            border-radius: 6px;
            color: white;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.2s;
        }
        
        .notify-btn:hover {
            background: #2563eb;
        }
        
        .notify-btn:disabled {
            background: #475569;
            cursor: not-allowed;
        }
        
        .countdown {
            margin-left: auto;
            font-size: 0.875rem;
            color: #64748b;
        }
        
        .loading {
            text-align: center;
            padding: 4rem;
            color: #64748b;
        }
        
        /* Modal styles */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        
        .modal-content {
            background: #1e293b;
            padding: 2rem;
            border-radius: 12px;
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            border: 1px solid #334155;
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }
        
        .modal-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: #f1f5f9;
        }
        
        .close-btn {
            background: none;
            border: none;
            color: #94a3b8;
            font-size: 1.5rem;
            cursor: pointer;
        }
        
        .close-btn:hover {
            color: #e4e4e7;
        }
        
        .contact-list {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }
        
        .contact-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem;
            background: #0f172a;
            border-radius: 8px;
            border: 1px solid #334155;
        }
        
        .contact-item input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
        }
        
        .contact-info {
            flex: 1;
        }
        
        .contact-email {
            color: #60a5fa;
            font-size: 0.875rem;
        }
        
        .contact-name {
            color: #94a3b8;
            font-size: 0.75rem;
        }
        
        .modal-actions {
            margin-top: 1.5rem;
            display: flex;
            gap: 1rem;
            justify-content: flex-end;
        }
        
        .btn-primary {
            padding: 0.75rem 1.5rem;
            background: #3b82f6;
            border: none;
            border-radius: 6px;
            color: white;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.2s;
        }
        
        .btn-primary:hover {
            background: #2563eb;
        }
        
        .btn-secondary {
            padding: 0.75rem 1.5rem;
            background: #475569;
            border: none;
            border-radius: 6px;
            color: white;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.2s;
        }
        
        .btn-secondary:hover {
            background: #64748b;
        }
        
        .no-contacts {
            text-align: center;
            padding: 2rem;
            color: #64748b;
        }
        
        /* BMAsia email indicator */
        .bmasia-tag {
            background: #581c87;
            color: #e9d5ff;
            padding: 0.125rem 0.5rem;
            border-radius: 4px;
            font-size: 0.625rem;
            margin-left: 0.5rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎵 SYB Zone Monitor - Enhanced Dashboard</h1>
    </div>
    
    <div class="stats-bar">
        <div class="stat-item">
            <div class="stat-value" id="totalAccounts">0</div>
            <div class="stat-label">Accounts</div>
        </div>
        <div class="stat-item">
            <div class="stat-value" id="totalZones">0</div>
            <div class="stat-label">Total Zones</div>
        </div>
        <div class="stat-item">
            <div class="stat-value" id="onlineZones">0</div>
            <div class="stat-label">Online</div>
        </div>
        <div class="stat-item">
            <div class="stat-value" id="offlineZones">0</div>
            <div class="stat-label">Offline</div>
        </div>
        <div class="stat-item">
            <div class="stat-value" id="issueAccounts">0</div>
            <div class="stat-label">Accounts with Issues</div>
        </div>
        <div class="countdown" id="countdown">30</div>
    </div>
    
    <div class="controls">
        <div class="search-box">
            <span class="search-icon">🔍</span>
            <input type="text" id="searchInput" placeholder="Search accounts or zones...">
        </div>
        <div class="filter-buttons">
            <button class="filter-btn active" data-filter="all">All</button>
            <button class="filter-btn" data-filter="issues">With Issues</button>
            <button class="filter-btn" data-filter="offline">Offline Zones</button>
            <button class="filter-btn" data-filter="no-device">No Device</button>
        </div>
    </div>
    
    <div class="accounts-container" id="accountsContainer">
        <div class="loading">Loading zone data...</div>
    </div>
    
    <!-- Notification Modal -->
    <div class="modal" id="notificationModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">Send Notification</h2>
                <button class="close-btn" onclick="closeModal()">&times;</button>
            </div>
            <div id="modalBody">
                <!-- Content will be populated dynamically -->
            </div>
        </div>
    </div>
    
    <script>
        let allData = {};
        let currentFilter = 'all';
        let searchTerm = '';
        let countdownValue = 30;
        let countdownInterval;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            fetchZoneData();
            startCountdown();
            
            // Setup event listeners
            document.getElementById('searchInput').addEventListener('input', handleSearch);
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.addEventListener('click', handleFilter);
            });
        });
        
        function startCountdown() {
            countdownInterval = setInterval(() => {
                countdownValue--;
                document.getElementById('countdown').textContent = countdownValue;
                
                if (countdownValue <= 0) {
                    countdownValue = 30;
                    fetchZoneData();
                }
            }, 1000);
        }
        
        async function fetchZoneData() {
            try {
                const response = await fetch('/api/zones');
                const data = await response.json();
                allData = data;
                updateDisplay();
            } catch (error) {
                console.error('Error fetching zone data:', error);
            }
        }
        
        function handleSearch(event) {
            searchTerm = event.target.value.toLowerCase();
            updateDisplay();
        }
        
        function handleFilter(event) {
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            currentFilter = event.target.dataset.filter;
            updateDisplay();
        }
        
        function updateDisplay() {
            const container = document.getElementById('accountsContainer');
            const stats = calculateStats();
            
            // Update stats
            document.getElementById('totalAccounts').textContent = stats.totalAccounts;
            document.getElementById('totalZones').textContent = stats.totalZones;
            document.getElementById('onlineZones').textContent = stats.onlineZones;
            document.getElementById('offlineZones').textContent = stats.offlineZones;
            document.getElementById('issueAccounts').textContent = stats.issueAccounts;
            
            // Filter and search
            let filteredAccounts = Object.entries(allData.accounts || {}).filter(([id, account]) => {
                // Apply search filter
                if (searchTerm) {
                    const matchesSearch = account.name.toLowerCase().includes(searchTerm) ||
                        account.zones.some(z => z.name.toLowerCase().includes(searchTerm));
                    if (!matchesSearch) return false;
                }
                
                // Apply status filter
                if (currentFilter === 'issues') {
                    return account.hasIssues;
                } else if (currentFilter === 'offline') {
                    return account.zones.some(z => z.status === 'offline');
                } else if (currentFilter === 'no-device') {
                    return account.zones.some(z => z.status === 'no_device');
                }
                
                return true;
            });
            
            // Render accounts
            if (filteredAccounts.length === 0) {
                container.innerHTML = '<div class="loading">No accounts found</div>';
                return;
            }
            
            container.innerHTML = filteredAccounts.map(([id, account]) => renderAccount(id, account)).join('');
        }
        
        function calculateStats() {
            const accounts = Object.values(allData.accounts || {});
            return {
                totalAccounts: accounts.length,
                totalZones: accounts.reduce((sum, acc) => sum + acc.zones.length, 0),
                onlineZones: accounts.reduce((sum, acc) => 
                    sum + acc.zones.filter(z => z.status === 'online').length, 0),
                offlineZones: accounts.reduce((sum, acc) => 
                    sum + acc.zones.filter(z => z.status === 'offline').length, 0),
                issueAccounts: accounts.filter(acc => acc.hasIssues).length
            };
        }
        
        function renderAccount(id, account) {
            const offlineCount = account.zones.filter(z => z.status === 'offline').length;
            const noDeviceCount = account.zones.filter(z => z.status === 'no_device').length;
            
            return `
                <div class="account-card">
                    <div class="account-header">
                        <div>
                            <div class="account-name">${escapeHtml(account.name)}</div>
                            <div class="account-stats">
                                <span>${account.zones.length} zones</span>
                                ${offlineCount > 0 ? `<span style="color: #fca5a5">${offlineCount} offline</span>` : ''}
                                ${noDeviceCount > 0 ? `<span style="color: #fcd34d">${noDeviceCount} no device</span>` : ''}
                            </div>
                        </div>
                        <button class="notify-btn" onclick="showNotificationModal('${id}', '${escapeHtml(account.name)}')"
                                ${account.hasContacts ? '' : 'disabled'}>
                            📧 Notify
                        </button>
                    </div>
                    <div class="zones-grid">
                        ${account.zones.map(zone => renderZone(zone)).join('')}
                    </div>
                </div>
            `;
        }
        
        function renderZone(zone) {
            const statusClass = `status-${zone.status}`;
            const statusText = zone.status.replace('_', ' ');
            
            return `
                <div class="zone-item">
                    <div class="zone-name" title="${escapeHtml(zone.name)}">${escapeHtml(zone.name)}</div>
                    <div class="zone-status ${statusClass}">
                        ${zone.status === 'online' ? '✓' : '✗'} ${statusText}
                    </div>
                </div>
            `;
        }
        
        function showNotificationModal(accountId, accountName) {
            const account = allData.accounts[accountId];
            if (!account || !account.contacts || account.contacts.length === 0) {
                alert('No contacts available for this account');
                return;
            }
            
            const modal = document.getElementById('notificationModal');
            const modalBody = document.getElementById('modalBody');
            
            // Filter out BMAsia emails by default
            const clientContacts = account.contacts.filter(c => 
                !c.email.endsWith('@bmasiamusic.com')
            );
            const bmasiaContacts = account.contacts.filter(c => 
                c.email.endsWith('@bmasiamusic.com')
            );
            
            modalBody.innerHTML = `
                <h3 style="margin-bottom: 1rem; color: #94a3b8;">Account: ${escapeHtml(accountName)}</h3>
                
                ${clientContacts.length > 0 ? `
                    <h4 style="margin-bottom: 0.75rem; color: #f1f5f9;">Client Contacts</h4>
                    <div class="contact-list">
                        ${clientContacts.map(contact => renderContact(contact, true)).join('')}
                    </div>
                ` : ''}
                
                ${bmasiaContacts.length > 0 ? `
                    <h4 style="margin-top: 1.5rem; margin-bottom: 0.75rem; color: #f1f5f9;">
                        Internal Contacts
                        <span class="bmasia-tag">BMAsia</span>
                    </h4>
                    <div class="contact-list">
                        ${bmasiaContacts.map(contact => renderContact(contact, false)).join('')}
                    </div>
                ` : ''}
                
                ${clientContacts.length === 0 && bmasiaContacts.length === 0 ? 
                    '<div class="no-contacts">No contacts available</div>' : ''}
                
                <div class="modal-actions">
                    <button class="btn-secondary" onclick="closeModal()">Cancel</button>
                    <button class="btn-primary" onclick="sendNotification('${accountId}')">
                        Send Notification
                    </button>
                </div>
            `;
            
            modal.style.display = 'flex';
        }
        
        function renderContact(contact, checked) {
            return `
                <div class="contact-item">
                    <input type="checkbox" id="contact_${contact.email}" 
                           value="${contact.email}" ${checked ? 'checked' : ''}>
                    <div class="contact-info">
                        <div class="contact-email">${escapeHtml(contact.email)}</div>
                        ${contact.name ? `<div class="contact-name">${escapeHtml(contact.name)}</div>` : ''}
                    </div>
                </div>
            `;
        }
        
        function closeModal() {
            document.getElementById('notificationModal').style.display = 'none';
        }
        
        async function sendNotification(accountId) {
            const selectedEmails = [];
            document.querySelectorAll('#modalBody input[type="checkbox"]:checked').forEach(checkbox => {
                selectedEmails.push(checkbox.value);
            });
            
            if (selectedEmails.length === 0) {
                alert('Please select at least one contact');
                return;
            }
            
            try {
                const response = await fetch('/api/notify', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        account_id: accountId,
                        emails: selectedEmails
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    alert('Notification sent successfully!');
                    closeModal();
                } else {
                    alert('Failed to send notification: ' + result.message);
                }
            } catch (error) {
                alert('Error sending notification: ' + error.message);
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Handle modal close on outside click
        window.onclick = function(event) {
            const modal = document.getElementById('notificationModal');
            if (event.target === modal) {
                closeModal();
            }
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/zones")
async def get_zones():
    """API endpoint to get all zone data."""
    if not zone_monitor:
        raise HTTPException(status_code=503, detail="Zone monitor not initialized")
    
    # Combine discovered data with current status
    accounts_data = {}
    
    for account_id, account_info in discovered_data.items():
        account_zones = []
        has_issues = False
        
        for location in account_info.get('locations', []):
            for zone in location.get('zones', []):
                zone_id = zone.get('id')
                if not zone_id:
                    continue
                    
                # Get current status from zone monitor
                zone_status = zone_monitor.zone_status.get(zone_id)
                
                status = 'unknown'
                if zone_status:
                    if zone_status.status == 'OFFLINE':
                        status = 'offline'
                        has_issues = True
                    elif zone_status.status == 'ONLINE':
                        status = 'online'
                    elif zone_status.status == 'NO_DEVICE':
                        status = 'no_device'
                        has_issues = True
                    elif zone_status.status == 'EXPIRED':
                        status = 'expired'
                        has_issues = True
                
                account_zones.append({
                    'id': zone_id,
                    'name': zone.get('name', 'Unknown'),
                    'status': status,
                    'location': location.get('name', 'Unknown')
                })
        
        # Get contacts from both discovered data and FINAL_CONTACT_ANALYSIS
        contacts = []
        
        # Add users from discovered data
        for user in account_info.get('users', []):
            if user.get('email'):
                contacts.append({
                    'name': user.get('name', ''),
                    'email': user['email'],
                    'role': user.get('role', '')
                })
        
        # Add contacts from FINAL_CONTACT_ANALYSIS if available
        account_name = account_info.get('name', '')
        if account_name in contact_data:
            for contact in contact_data[account_name]:
                # Avoid duplicates
                if not any(c['email'] == contact.get('email') for c in contacts):
                    contacts.append({
                        'name': contact.get('name', ''),
                        'email': contact.get('email', ''),
                        'role': contact.get('role', '')
                    })
        
        accounts_data[account_id] = {
            'id': account_id,
            'name': account_info.get('name', 'Unknown'),
            'zones': account_zones,
            'hasIssues': has_issues,
            'contacts': contacts,
            'hasContacts': len(contacts) > 0
        }
    
    return JSONResponse(content={'accounts': accounts_data})


@app.post("/api/notify")
async def send_notification(data: dict):
    """Send notification for an account."""
    account_id = data.get('account_id')
    emails = data.get('emails', [])
    
    if not account_id or not emails:
        return JSONResponse(
            content={'success': False, 'message': 'Missing account_id or emails'},
            status_code=400
        )
    
    # Get account info
    account_info = discovered_data.get(account_id)
    if not account_info:
        return JSONResponse(
            content={'success': False, 'message': 'Account not found'},
            status_code=404
        )
    
    # Simulate sending notification (replace with actual email logic)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"notification_{account_info['name'].replace(' ', '_')}_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write(f"Notification for: {account_info['name']}\n")
        f.write(f"Account ID: {account_id}\n")
        f.write(f"Recipients: {', '.join(emails)}\n")
        f.write(f"Timestamp: {datetime.now()}\n\n")
        f.write("Zone Status:\n")
        
        for location in account_info.get('locations', []):
            for zone in location.get('zones', []):
                zone_id = zone.get('id')
                if zone_id and zone_id in zone_monitor.zone_status:
                    status = zone_monitor.zone_status[zone_id]
                    f.write(f"- {zone['name']}: {status.status}\n")
    
    return JSONResponse(content={
        'success': True,
        'message': f'Notification saved to {filename}'
    })


if __name__ == "__main__":
    import uvicorn
    
    # Make sure we have discovery data before starting
    if not Path("accounts_discovery_results.json").exists():
        print("No discovery data found!")
        print("Please run: python process_all_accounts.py")
        exit(1)
    
    print("🚀 Starting Enhanced Dashboard on http://127.0.0.1:8080")
    uvicorn.run(app, host="127.0.0.1", port=8080)