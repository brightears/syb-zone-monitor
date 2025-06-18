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
from zone_monitor_optimized import ZoneMonitor
try:
    from sms_service import get_sms_service
except ImportError:
    # SMS service not available yet
    def get_sms_service():
        return None
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
    minimal_file = Path("accounts_discovery_minimal.json")
    
    if results_file.exists():
        with open(results_file, 'r') as f:
            data = json.load(f)
            discovered_data = data.get('accounts', {})
            logger.info(f"Loaded data for {len(discovered_data)} accounts")
    elif minimal_file.exists():
        with open(minimal_file, 'r') as f:
            data = json.load(f)
            discovered_data = data.get('accounts', {})
            logger.info(f"Loaded minimal data for {len(discovered_data)} accounts")
    else:
        logger.warning("No discovery results found. Using empty data.")
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
        logger.warning("No zones found in discovery data - app will run with empty data")
        # Don't return early - let the app run even with no zones
    
    # Initialize zone monitor with discovered zones
    api_key = os.getenv("SYB_API_KEY")
    if not api_key:
        logger.error("SYB_API_KEY not found in environment")
        return
    
    if zone_ids:
        # Initialize zone monitor with discovered zones
        from zone_monitor_optimized import ZoneMonitor
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
        
        # Initialize database and load saved states
        await zone_monitor.initialize()
        
        logger.info(f"Initialized zone monitor with {len(zone_ids)} zones")
        
        # Start background task to check zones periodically
        asyncio.create_task(monitor_zones_background())
    else:
        logger.warning("No zones to monitor - running in display-only mode")
        zone_monitor = None


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
            background: #fafafa;
            color: #1a1a1a;
            line-height: 1.6;
        }
        
        .header {
            background: #ffffff;
            border-bottom: 1px solid #e5e5e5;
            padding: 1.25rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header h1 {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1a1a1a;
            letter-spacing: -0.5px;
        }
        
        .stats-bar {
            background: #ffffff;
            padding: 1.5rem 2rem;
            display: flex;
            gap: 3rem;
            flex-wrap: wrap;
            align-items: center;
            border-bottom: 1px solid #e5e5e5;
        }
        
        .stat-item {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #1a1a1a;
            line-height: 1;
        }
        
        .stat-label {
            font-size: 0.875rem;
            color: #666666;
            font-weight: 400;
            margin-top: 0.25rem;
        }
        
        .controls {
            padding: 1.25rem 2rem;
            background: #ffffff;
            border-bottom: 1px solid #e5e5e5;
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
            background: #f9f9f9;
            border: 1px solid #d1d1d6;
            border-radius: 8px;
            color: #1d1d1f;
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
            background: transparent;
            border: 1px solid #e5e5e5;
            border-radius: 20px;
            color: #666666;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .filter-btn:hover {
            border-color: #cccccc;
            color: #1a1a1a;
        }
        
        .filter-btn.active {
            background: #1a1a1a;
            color: white;
            border-color: #1a1a1a;
        }
        
        .accounts-container {
            padding: 2rem;
            display: grid;
            gap: 1.5rem;
        }
        
        .account-card {
            background: #ffffff;
            border: 1px solid #e5e5e5;
            border-radius: 8px;
            padding: 1.5rem;
            transition: all 0.2s;
        }
        
        .account-card:hover {
            border-color: #cccccc;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        
        .account-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .account-name {
            font-size: 1.125rem;
            font-weight: 700;
            color: #1a1a1a;
            letter-spacing: -0.3px;
        }
        
        .account-stats {
            display: flex;
            gap: 1rem;
            font-size: 0.875rem;
            color: #666666;
            margin-top: 0.25rem;
        }
        
        .zones-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1rem;
        }
        
        .zone-item {
            background: #f5f5f5;
            padding: 1rem;
            border-radius: 6px;
            border: 1px solid transparent;
            display: grid;
            grid-template-rows: 1fr auto auto;
            gap: 0.5rem;
            min-height: 120px;
            position: relative;
            transition: all 0.15s ease;
        }
        
        .zone-item:hover {
            background: #eeeeee;
            border-color: #e5e5e5;
        }
        
        .zone-name {
            font-size: 0.9375rem;
            font-weight: 600;
            color: #1a1a1a;
            line-height: 1.4;
            word-break: break-word;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            letter-spacing: -0.2px;
            align-self: start;
        }
        
        .zone-status {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.375rem;
            font-size: 0.8125rem;
            padding: 0.375rem 0.75rem;
            border-radius: 16px;
            white-space: nowrap;
            font-weight: 500;
            align-self: center;
        }
        
        .status-online {
            background: #10b981;
            color: white;
        }
        
        .status-offline {
            background: #ef4444;
            color: white;
        }
        
        .status-unpaired {
            background: #f59e0b;
            color: white;
        }
        
        .status-expired {
            background: #6b7280;
            color: white;
        }
        
        .status-no_subscription {
            background: #5856d6;
            color: white;
        }
        
        .status-checking {
            background: #007aff;
            color: white;
            animation: pulse 1.5s infinite;
        }
        
        .status-unknown {
            background: #e5e5e5;
            color: #666666;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .zone-duration {
            font-size: 0.8125rem;
            color: #dc2626;
            font-weight: 500;
            text-align: center;
            align-self: end;
        }
        
        .notify-btn {
            padding: 0.5rem 1.25rem;
            background: #1a1a1a;
            border: none;
            border-radius: 20px;
            color: white;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.15s;
        }
        
        .notify-btn:hover {
            background: #000000;
            transform: translateY(-1px);
        }
        
        .notify-btn:disabled {
            background: #e5e5e5;
            color: #999999;
            cursor: not-allowed;
            transform: none;
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
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        
        .modal-content {
            background: #ffffff;
            padding: 2rem;
            border-radius: 8px;
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
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
            background: #f5f5f5;
            border-radius: 6px;
            border: 1px solid #e5e5e5;
        }
        
        .contact-item input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
            accent-color: #1a1a1a;
        }
        
        .contact-info {
            flex: 1;
        }
        
        .contact-email {
            color: #1a1a1a;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .contact-name {
            color: #666666;
            font-size: 0.75rem;
        }
        
        .modal-actions {
            margin-top: 1.5rem;
            display: flex;
            gap: 1rem;
            justify-content: flex-end;
        }
        
        .btn-primary {
            padding: 0.625rem 1.25rem;
            background: #1a1a1a;
            border: none;
            border-radius: 20px;
            color: white;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.15s;
        }
        
        .btn-primary:hover {
            background: #000000;
            transform: translateY(-1px);
        }
        
        .btn-secondary {
            padding: 0.625rem 1.25rem;
            background: transparent;
            border: 1px solid #e5e5e5;
            border-radius: 20px;
            color: #666666;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.15s;
        }
        
        .btn-secondary:hover {
            border-color: #cccccc;
            color: #1a1a1a;
        }
        
        .no-contacts {
            text-align: center;
            padding: 2rem;
            color: #64748b;
        }
        
        /* BMAsia email indicator */
        .bmasia-tag {
            background: #8b5cf6;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.625rem;
            margin-left: 0.5rem;
            font-weight: 600;
            text-transform: uppercase;
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
            <button class="filter-btn" data-filter="offline">Offline</button>
            <button class="filter-btn" data-filter="no-device">No Device</button>
            <button class="filter-btn" data-filter="no-subscription">No Sub</button>
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
                    return account.zones.some(z => z.status === 'unpaired');
                } else if (currentFilter === 'no-subscription') {
                    return account.zones.some(z => z.status === 'no_subscription');
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
            const unpairedCount = account.zones.filter(z => z.status === 'unpaired').length;
            const expiredCount = account.zones.filter(z => z.status === 'expired').length;
            const noSubCount = account.zones.filter(z => z.status === 'no_subscription').length;
            
            return `
                <div class="account-card">
                    <div class="account-header">
                        <div>
                            <div class="account-name">${escapeHtml(account.name)}</div>
                            <div class="account-stats">
                                <span>${account.zones.length} zones</span>
                                ${offlineCount > 0 ? `<span style="color: #ef4444">${offlineCount} offline</span>` : ''}
                                ${expiredCount > 0 ? `<span style="color: #6b7280">${expiredCount} expired</span>` : ''}
                                ${noSubCount > 0 ? `<span style="color: #5856d6">${noSubCount} no sub</span>` : ''}
                                ${unpairedCount > 0 ? `<span style="color: #f59e0b">${unpairedCount} unpaired</span>` : ''}
                            </div>
                        </div>
                        <button class="notify-btn" onclick="showNotificationModal('${id}', '${escapeHtml(account.name)}')"
                                ${account.hasContacts ? '' : 'disabled'}>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display: inline-block; vertical-align: middle;">
                                <path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                            </svg>
                            <span>Notify</span>
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
            let statusText = zone.status.replace('_', ' ');
            let statusIcon = '';
            
            // Map status to proper display text
            switch(zone.status) {
                case 'online':
                    statusText = 'Connected';
                    statusIcon = '✓';
                    break;
                case 'offline':
                    statusText = 'Offline';
                    statusIcon = '✗';
                    break;
                case 'unpaired':
                    statusText = 'No Paired Device';
                    statusIcon = '⚠';
                    break;
                case 'expired':
                    statusText = 'Subscription Expired';
                    statusIcon = '⚠';
                    break;
                case 'no_subscription':
                    statusText = 'No Subscription';
                    statusIcon = '💳';
                    break;
                case 'checking':
                    statusText = 'Checking...';
                    statusIcon = '⋯';
                    break;
                case 'unknown':
                    statusText = 'Checking...';
                    statusIcon = '⋯';
                    break;
                default:
                    statusIcon = '?';
            }
            
            // Add offline duration if available
            let durationText = '';
            if (zone.status === 'offline' && zone.offline_duration) {
                const duration = formatDuration(zone.offline_duration);
                durationText = `<div class="zone-duration">${duration}</div>`;
            }
            
            return `
                <div class="zone-item">
                    <div class="zone-name" title="${escapeHtml(zone.name)}">${escapeHtml(zone.name)}</div>
                    <div class="zone-status ${statusClass}">
                        ${statusIcon} ${statusText}
                    </div>
                    ${durationText}
                </div>
            `;
        }
        
        function formatDuration(seconds) {
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);
            const days = Math.floor(hours / 24);
            
            if (days > 0) {
                return `${days} day${days !== 1 ? 's' : ''}`;
            } else if (hours > 0) {
                return `${hours} hour${hours !== 1 ? 's' : ''}`;
            } else if (minutes > 0) {
                return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
            } else {
                return `${seconds} second${seconds !== 1 ? 's' : ''}`;
            }
        }
        
        function showNotificationModal(accountId, accountName) {
            const account = allData.accounts[accountId];
            if (!account || !account.contacts || account.contacts.length === 0) {
                alert('No contacts available for this account');
                return;
            }
            window.currentAccountId = accountId;
            window.currentAccount = account;
            
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
                <h3 style="margin-bottom: 1rem; color: #666666;">Account: ${escapeHtml(accountName)}</h3>
                
                <!-- Notification Method Selection -->
                <div class="notification-methods" style="margin-bottom: 1.5rem; padding: 1rem; background: #f5f5f5; border-radius: 8px;">
                    <h4 style="margin-bottom: 0.75rem; color: #1a1a1a;">Notification Method</h4>
                    <div style="display: flex; gap: 1.5rem;">
                        <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                            <input type="checkbox" id="emailNotification" checked style="width: 18px; height: 18px;">
                            <span style="font-size: 0.875rem;">📧 Email</span>
                        </label>
                        <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                            <input type="checkbox" id="smsNotification" style="width: 18px; height: 18px;">
                            <span style="font-size: 0.875rem;">📱 SMS</span>
                        </label>
                    </div>
                    <div id="smsWarning" style="display: none; margin-top: 0.5rem; padding: 0.5rem; background: #fef3c7; border-radius: 4px; font-size: 0.75rem; color: #92400e;">
                        ⚠️ SMS notifications will be sent to contacts with verified phone numbers only
                    </div>
                </div>
                
                ${clientContacts.length > 0 ? `
                    <h4 style="margin-bottom: 0.75rem; color: #1a1a1a;">Client Contacts</h4>
                    <div class="contact-list">
                        ${clientContacts.map(contact => renderContact(contact, true)).join('')}
                    </div>
                ` : ''}
                
                ${bmasiaContacts.length > 0 ? `
                    <h4 style="margin-top: 1.5rem; margin-bottom: 0.75rem; color: #1a1a1a;">
                        Internal Contacts
                        <span class="bmasia-tag">BMAsia</span>
                    </h4>
                    <div class="contact-list">
                        ${bmasiaContacts.map(contact => renderContact(contact, false)).join('')}
                    </div>
                ` : ''}
                
                ${clientContacts.length === 0 && bmasiaContacts.length === 0 ? 
                    '<div class="no-contacts">No contacts available</div>' : ''}
                
                <div class="message-section" style="margin-top: 1.5rem;">
                    <h4 style="margin-bottom: 0.75rem; color: #1a1a1a;">Notification Message</h4>
                    <select id="messageTemplate" onchange="updateMessagePreview()" style="
                        width: 100%;
                        padding: 0.5rem;
                        margin-bottom: 0.75rem;
                        border: 1px solid #e5e5e5;
                        border-radius: 6px;
                        background: white;
                        color: #1a1a1a;
                    ">
                        <option value="offline">Zones Offline Alert</option>
                        <option value="expired">Subscription Expired</option>
                        <option value="unpaired">No Paired Device</option>
                        <option value="no_subscription">No Subscription</option>
                        <option value="custom">Custom Message</option>
                    </select>
                    <textarea id="messageContent" rows="6" style="
                        width: 100%;
                        padding: 0.75rem;
                        border: 1px solid #e5e5e5;
                        border-radius: 6px;
                        resize: vertical;
                        font-family: inherit;
                        color: #1a1a1a;
                        background: white;
                    " placeholder="Your notification message will appear here..."></textarea>
                </div>
                
                <div class="modal-actions">
                    <button class="btn-secondary" onclick="closeModal()">Cancel</button>
                    <button class="btn-primary" onclick="sendNotification('${accountId}')">
                        Send Notification
                    </button>
                </div>
            `;
            
            modal.style.display = 'flex';
            
            // Initialize with offline template
            setTimeout(() => updateMessagePreview(), 100);
            
            // Add event listener for SMS checkbox
            document.getElementById('smsNotification').addEventListener('change', function(e) {
                const smsWarning = document.getElementById('smsWarning');
                if (e.target.checked) {
                    smsWarning.style.display = 'block';
                } else {
                    smsWarning.style.display = 'none';
                }
            });
        }
        
        function updateMessagePreview() {
            const template = document.getElementById('messageTemplate').value;
            const messageContent = document.getElementById('messageContent');
            const account = window.currentAccount;
            
            if (!account) return;
            
            const offlineZones = account.zones.filter(z => z.status === 'offline');
            const expiredZones = account.zones.filter(z => z.status === 'expired');
            const unpairedZones = account.zones.filter(z => z.status === 'unpaired');
            const noSubZones = account.zones.filter(z => z.status === 'no_subscription');
            
            let message = '';
            
            switch(template) {
                case 'offline':
                    if (offlineZones.length > 0) {
                        message = `Dear ${account.name} team,\n\n`;
                        message += `We've detected that ${offlineZones.length} of your music zones are currently offline:\n\n`;
                        offlineZones.forEach(z => {
                            message += `• ${z.name}`;
                            if (z.offline_duration) {
                                const duration = formatDuration(z.offline_duration);
                                message += ` (offline for ${duration})`;
                            }
                            message += `\n`;
                        });
                        message += `\nThis interruption may affect your customers' experience. Here's what you can do:\n\n`;
                        message += `1. Check that the device is powered on\n`;
                        message += `2. Verify your internet connection is working\n`;
                        message += `3. Restart the Soundtrack player device\n`;
                        message += `4. Ensure no firewall is blocking the connection\n\n`;
                        message += `If the issue persists after trying these steps, please contact our support team at support@bmasiamusic.com or call us directly.\n\n`;
                        message += `We're here to help ensure your music plays smoothly.\n\n`;
                        message += `Best regards,\nSoundtrack Your Brand Support Team`;
                    }
                    break;
                    
                case 'expired':
                    message = `Dear ${account.name} team,\n\n`;
                    if (expiredZones.length > 0) {
                        message += `We noticed that your Soundtrack Your Brand subscription has expired for the following ${expiredZones.length} zone${expiredZones.length > 1 ? 's' : ''}:\n\n`;
                        expiredZones.forEach(z => {
                            message += `• ${z.name}\n`;
                        });
                    } else {
                        message += `We noticed that your Soundtrack Your Brand subscription has expired for the following zones:\n\n`;
                        message += `• [Zone names will be listed here]\n`;
                    }
                    message += `\nYour music service has been temporarily suspended for these zones. To avoid any disruption to your business atmosphere:\n\n`;
                    message += `📅 Renew Now: Contact our team to quickly reactivate your subscription\n`;
                    message += `💳 Flexible Plans: We offer various subscription options to fit your needs\n`;
                    message += `🎵 Instant Reactivation: Your music will resume immediately upon renewal\n\n`;
                    message += `Don't let silence impact your customer experience. Our account team is ready to help you get back to playing the perfect soundtrack for your business.\n\n`;
                    message += `To renew your subscription or discuss your options, please:\n`;
                    message += `• Reply to this email\n`;
                    message += `• Call our support team\n`;
                    message += `• Visit your account dashboard\n\n`;
                    message += `Thank you for choosing Soundtrack Your Brand. We look forward to continuing to serve your music needs.\n\n`;
                    message += `Best regards,\nSoundtrack Your Brand Support Team`;
                    break;
                    
                case 'unpaired':
                    message = `Dear ${account.name} team,\n\n`;
                    if (unpairedZones.length > 0) {
                        message += `We've identified ${unpairedZones.length} zone${unpairedZones.length > 1 ? 's' : ''} in your account that ${unpairedZones.length > 1 ? 'are' : 'is'} not connected to any playback device:\n\n`;
                        unpairedZones.forEach(z => {
                            message += `• ${z.name}\n`;
                        });
                    } else {
                        message += `We've identified zones in your account that are not connected to any playback device:\n\n`;
                        message += `• [Zone names will be listed here]\n`;
                    }
                    message += `\nThese zones are ready to play music but need a device to stream from. Here's how to get started:\n\n`;
                    message += `📱 Quick Setup Guide:\n`;
                    message += `1. Download the Soundtrack Player app on your chosen device (tablet, phone, or computer)\n`;
                    message += `2. Log in with your Soundtrack Your Brand credentials\n`;
                    message += `3. Select the zone you want to pair\n`;
                    message += `4. Start playing your curated playlists!\n\n`;
                    message += `🔧 Recommended Devices:\n`;
                    message += `• iPad or Android tablet (dedicated music device)\n`;
                    message += `• Spare smartphone\n`;
                    message += `• Computer or laptop\n`;
                    message += `• Soundtrack hardware player (contact us for options)\n\n`;
                    message += `Need help with setup? Our support team can walk you through the process step-by-step. We're just an email or phone call away.\n\n`;
                    message += `Let's get your music playing and enhance your customer experience today!\n\n`;
                    message += `Best regards,\nSoundtrack Your Brand Support Team`;
                    break;
                    
                case 'no_subscription':
                    message = `Dear ${account.name} team,\n\n`;
                    if (noSubZones.length > 0) {
                        message += `We've noticed that ${noSubZones.length} zone${noSubZones.length > 1 ? 's' : ''} in your account ${noSubZones.length > 1 ? 'do' : 'does'} not have an active subscription:\n\n`;
                        noSubZones.forEach(z => {
                            message += `• ${z.name}\n`;
                        });
                    } else {
                        message += `We've noticed that zones in your account do not have an active subscription:\n\n`;
                        message += `• [Zone names will be listed here]\n`;
                    }
                    message += `\nThese zones are set up but require a subscription to start playing music. Here's how we can help:\n\n`;
                    message += `🎵 Start Your Musical Journey:\n`;
                    message += `• Choose from our flexible subscription plans\n`;
                    message += `• Access thousands of licensed tracks perfect for your business\n`;
                    message += `• Create the perfect atmosphere for your customers\n`;
                    message += `• Enjoy legal, commercial-use music without worry\n\n`;
                    message += `💼 Special Offer for New Subscriptions:\n`;
                    message += `Contact us today to learn about our current promotions and find the perfect plan for your business needs.\n\n`;
                    message += `Ready to transform your space with the power of music? Our team is standing by to help you get started. Simply reply to this email or give us a call.\n\n`;
                    message += `We're excited to help you create the perfect soundtrack for your business!\n\n`;
                    message += `Best regards,\nSoundtrack Your Brand Support Team`;
                    break;
                    
                case 'custom':
                    message = ''; // Let user write their own
                    break;
            }
            
            messageContent.value = message;
        }
        
        function renderContact(contact, checked) {
            const hasPhone = contact.phone && contact.phone !== '';
            const safeId = contact.email.replace(/[@.]/g, '_');
            return `
                <div class="contact-item">
                    <input type="checkbox" id="contact_${safeId}" 
                           value="${contact.email}" 
                           data-phone="${contact.phone || ''}"
                           data-has-phone="${hasPhone}"
                           ${checked ? 'checked' : ''}>
                    <div class="contact-info">
                        <div class="contact-email">${escapeHtml(contact.email)}</div>
                        ${contact.name ? `<div class="contact-name">${escapeHtml(contact.name)}</div>` : ''}
                        ${hasPhone ? `
                            <div class="contact-phone" style="font-size: 0.75rem; color: #10b981; margin-top: 0.25rem;">
                                📱 ${escapeHtml(contact.phone)}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }
        
        function closeModal() {
            document.getElementById('notificationModal').style.display = 'none';
        }
        
        async function sendNotification(accountId) {
            const selectedContacts = [];
            const selectedEmails = [];
            const selectedPhones = [];
            
            const sendEmail = document.getElementById('emailNotification').checked;
            const sendSMS = document.getElementById('smsNotification').checked;
            
            // Collect selected contacts and their info
            document.querySelectorAll('#modalBody input[type="checkbox"]:checked').forEach(checkbox => {
                if (checkbox.id && checkbox.id.startsWith('contact_')) {
                    const email = checkbox.value;
                    const phone = checkbox.dataset.phone;
                    const hasPhone = checkbox.dataset.hasPhone === 'true';
                    
                    selectedEmails.push(email);
                    if (hasPhone && phone) {
                        selectedPhones.push({email: email, phone: phone});
                    }
                }
            });
            
            const message = document.getElementById('messageContent').value;
            
            if (selectedEmails.length === 0) {
                alert('Please select at least one contact');
                return;
            }
            
            if (!sendEmail && !sendSMS) {
                alert('Please select at least one notification method (Email or SMS)');
                return;
            }
            
            if (sendSMS && selectedPhones.length === 0) {
                alert('No selected contacts have phone numbers. Please add phone numbers or use email only.');
                return;
            }
            
            if (!message.trim()) {
                alert('Please enter a notification message');
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
                        emails: sendEmail ? selectedEmails : [],
                        phones: sendSMS ? selectedPhones : [],
                        message: message,
                        send_email: sendEmail,
                        send_sms: sendSMS
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    let successMsg = 'Notification sent successfully!\n\n';
                    
                    if (result.results) {
                        if (result.results.email_sent) {
                            successMsg += `✅ Email sent to ${result.results.email_sent} recipient(s)\n`;
                        }
                        if (result.results.sms_sent) {
                            successMsg += `✅ SMS sent to ${result.results.sms_sent} recipient(s)\n`;
                        }
                        if (result.results.sms_failed && result.results.sms_failed > 0) {
                            successMsg += `⚠️ SMS failed for ${result.results.sms_failed} recipient(s)\n`;
                        }
                    }
                    
                    alert(successMsg);
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
        # Return empty data when no zones are configured
        return {"accounts": {}}
    
    # Get detailed status from zone monitor
    detailed_status = zone_monitor.get_detailed_status()
    
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
                    
                # Get current status from detailed status
                zone_info = detailed_status.get(zone_id, {})
                zone_status = zone_info.get('status', 'checking')
                
                # Get offline duration if available
                offline_duration = zone_info.get('offline_duration_seconds')
                
                status = 'checking'  # Default to 'checking' instead of 'unknown'
                if zone_status:
                    status = zone_status
                    if zone_status in ['offline', 'unpaired', 'expired', 'no_subscription']:
                        has_issues = True
                    elif zone_status == 'checking':
                        # Don't mark as having issues while checking
                        pass
                
                zone_data = {
                    'id': zone_id,
                    'name': zone.get('name', 'Unknown'),
                    'status': status,
                    'location': location.get('name', 'Unknown')
                }
                
                # Add offline duration if applicable
                if offline_duration is not None:
                    zone_data['offline_duration'] = offline_duration
                
                
                account_zones.append(zone_data)
        
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
    phones = data.get('phones', [])
    message = data.get('message', '')
    send_email = data.get('send_email', True)
    send_sms = data.get('send_sms', False)
    
    if not account_id:
        return JSONResponse(
            content={'success': False, 'message': 'Missing account_id'},
            status_code=400
        )
    
    if not emails and not phones:
        return JSONResponse(
            content={'success': False, 'message': 'No recipients specified'},
            status_code=400
        )
    
    # Get account info
    account_info = discovered_data.get(account_id)
    if not account_info:
        return JSONResponse(
            content={'success': False, 'message': 'Account not found'},
            status_code=404
        )
    
    # Initialize results
    results = {
        'email_sent': 0,
        'sms_sent': 0,
        'sms_failed': 0
    }
    
    # Send actual email
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Get SMTP settings from environment
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    email_from = os.getenv('EMAIL_FROM', 'support@bmasiamusic.com')
    
    # Build zone status details
    zone_details = []
    for location in account_info.get('locations', []):
        for zone in location.get('zones', []):
            zone_id = zone.get('id')
            if zone_id and zone_id in zone_monitor.zone_states:
                status = zone_monitor.zone_states[zone_id]
                zone_details.append(f"• {zone['name']}: {status}")
    
    # Create email
    subject = f"Zone Status Alert - {account_info['name']}"
    
    # Add zone details to message if any
    full_message = message
    if zone_details:
        full_message += f"\n\n--- Current Zone Status ---\n" + "\n".join(zone_details)
    
    try:
        # Send emails if requested
        if send_email and emails:
            # If SMTP credentials are configured, send real email
            if smtp_username and smtp_password:
                msg = MIMEMultipart()
                msg['From'] = email_from
                msg['To'] = ', '.join(emails)
                msg['Subject'] = subject
                
                msg.attach(MIMEText(full_message, 'plain'))
                
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)
                
                results['email_sent'] = len(emails)
                logger.info(f"Email sent to {len(emails)} recipients for {account_info['name']}")
            else:
                # Fallback: save to file if SMTP not configured
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"notification_{account_info['name'].replace(' ', '_')}_{timestamp}.txt"
                
                with open(filename, 'w') as f:
                    f.write(f"=== NOTIFICATION EMAIL ===\n\n")
                    f.write(f"TO: {', '.join(emails)}\n")
                    f.write(f"FROM: {email_from}\n")
                    f.write(f"SUBJECT: {subject}\n")
                    f.write(f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"\n--- MESSAGE ---\n\n")
                    f.write(full_message)
                
                results['email_sent'] = len(emails)
                logger.info(f"Email saved to {filename} (SMTP not configured)")
        
        # Send SMS if requested
        if send_sms and phones:
            sms_service = get_sms_service()
            
            if sms_service and hasattr(sms_service, 'enabled') and sms_service.enabled:
                # Prepare zone data for SMS formatting
                zones_data = []
                for location in account_info.get('locations', []):
                    for zone in location.get('zones', []):
                        zone_id = zone.get('id')
                        if zone_id and zone_id in zone_monitor.zone_states:
                            zone_status = zone_monitor.zone_states[zone_id]
                            offline_duration = None
                            if zone_id in zone_monitor.offline_since:
                                offline_duration = int((datetime.now() - zone_monitor.offline_since[zone_id]).total_seconds())
                            
                            zones_data.append({
                                'name': zone['name'],
                                'status': zone_status,
                                'offline_duration': offline_duration
                            })
                
                # Format SMS message based on zone status
                sms_message = sms_service.format_sms_alert(account_info['name'], zones_data)
                
                # If no pre-formatted message, use a shortened version of the email
                if not sms_message:
                    sms_message = sms_service.format_custom_sms(message)
                
                # Send SMS to each phone number
                for phone_data in phones:
                    phone = phone_data.get('phone') if isinstance(phone_data, dict) else phone_data
                    if phone:
                        result = await sms_service.send_sms(phone, sms_message)
                        if result['success']:
                            results['sms_sent'] += 1
                        else:
                            results['sms_failed'] += 1
                            logger.error(f"SMS failed for {phone}: {result.get('error')}")
            else:
                logger.warning("SMS requested but service not enabled")
        
        return JSONResponse(content={
            'success': True,
            'results': results
        })
            
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return JSONResponse(content={
            'success': False,
            'message': f'Failed to send email: {str(e)}'
        }, status_code=500)


if __name__ == "__main__":
    import uvicorn
    
    # Make sure we have discovery data before starting
    if not Path("accounts_discovery_results.json").exists():
        print("No discovery data found!")
        print("Please run: python process_all_accounts.py")
        exit(1)
    
    print("🚀 Starting Enhanced Dashboard on http://127.0.0.1:8080")
    uvicorn.run(app, host="127.0.0.1", port=8080)