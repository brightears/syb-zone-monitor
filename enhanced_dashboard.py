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
    from whatsapp_service import get_whatsapp_service
except ImportError:
    # WhatsApp service not available yet
    def get_whatsapp_service():
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
whatsapp_contacts: Dict = {}  # Store WhatsApp contacts by account_id


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


def load_whatsapp_contacts():
    """Load WhatsApp contacts from whatsapp_contacts.json."""
    global whatsapp_contacts
    
    whatsapp_file = Path("whatsapp_contacts.json")
    if whatsapp_file.exists():
        with open(whatsapp_file, 'r') as f:
            whatsapp_contacts = json.load(f)
            logger.info(f"Loaded WhatsApp contacts for {len(whatsapp_contacts)} accounts")
    else:
        logger.info("No WhatsApp contacts file found - starting with empty data")
        whatsapp_contacts = {}


def save_whatsapp_contacts():
    """Save WhatsApp contacts to whatsapp_contacts.json."""
    whatsapp_file = Path("whatsapp_contacts.json")
    with open(whatsapp_file, 'w') as f:
        json.dump(whatsapp_contacts, f, indent=2)
    logger.info(f"Saved WhatsApp contacts for {len(whatsapp_contacts)} accounts")


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
    load_whatsapp_contacts()
    
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
            polling_interval=int(os.getenv("POLLING_INTERVAL", "60").split('#')[0].strip()),
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
            color: #1a1a1a !important;
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
    
    <!-- WhatsApp Management Modal -->
    <div class="modal" id="whatsappModal">
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">
                <h2 class="modal-title">Manage WhatsApp Contacts</h2>
                <button class="close-btn" onclick="closeWhatsAppModal()">&times;</button>
            </div>
            <div id="whatsappModalBody">
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
        
        async function loadWhatsAppContacts(accountId) {
            try {
                const response = await fetch(`/api/whatsapp/${accountId}`);
                const data = await response.json();
                return data.contacts || [];
            } catch (error) {
                console.error('Error loading WhatsApp contacts:', error);
                return [];
            }
        }
        
        function renderWhatsAppContact(contact, checked = false) {
            return `
                <div class="contact-item">
                    <input type="checkbox" id="whatsapp_${contact.id}" 
                           value="${contact.phone}" ${checked ? 'checked' : ''}>
                    <div class="contact-info">
                        <div class="contact-email">${escapeHtml(contact.phone)}</div>
                        <div class="contact-name">${escapeHtml(contact.name)}</div>
                    </div>
                </div>
            `;
        }
        
        async function showNotificationModal(accountId, accountName) {
            const account = allData.accounts[accountId];
            if (!account || !account.contacts || account.contacts.length === 0) {
                alert('No contacts available for this account');
                return;
            }
            window.currentAccountId = accountId;
            window.currentAccount = account;
            
            // Load WhatsApp contacts
            const whatsappContacts = await loadWhatsAppContacts(accountId);
            
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
                
                <div class="whatsapp-section" style="margin-top: 1.5rem; padding: 1rem; background: #f5f5f5; border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                        <h4 style="color: #1a1a1a; margin: 0;">
                            <svg style="width: 1.5rem; height: 1.5rem; vertical-align: middle; margin-right: 0.25rem;" viewBox="0 0 24 24" fill="#25D366">
                                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                            </svg>WhatsApp Contacts
                        </h4>
                        <button class="btn-secondary" onclick="showWhatsAppManagementModal('${accountId}')" style="padding: 0.25rem 0.75rem; font-size: 0.75rem;">
                            Manage Contacts
                        </button>
                    </div>
                    <div id="whatsappContactsList">
                        <!-- WhatsApp contacts will be loaded here -->
                    </div>
                    <div style="margin-top: 1rem;">
                        <input type="tel" id="whatsappNumber" placeholder="+60123456789 (Quick send)" style="width: 100%; padding: 0.75rem; border: 1px solid #e5e5e5; border-radius: 6px; font-size: 0.875rem; background: white;">
                        <div style="font-size: 0.75rem; color: #666666; margin-top: 0.5rem;">
                            Enter number for one-time send, or manage contacts above for regular use
                        </div>
                    </div>
                    
                    <div style="margin-top: 1.5rem;">
                        <h4 style="margin-bottom: 0.75rem; color: #1a1a1a;">WhatsApp Message</h4>
                        <select id="whatsappMessageTemplate" onchange="updateWhatsAppMessagePreview()" style="
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
                        <textarea id="whatsappMessageContent" rows="4" style="
                            width: 100%;
                            padding: 0.75rem;
                            border: 1px solid #e5e5e5;
                            border-radius: 6px;
                            resize: vertical;
                            font-family: inherit;
                            color: #1a1a1a;
                            background: white;
                        " placeholder="Your WhatsApp message will appear here..."></textarea>
                    </div>
                </div>
                
                <div class="modal-actions">
                    <button class="btn-secondary" onclick="closeModal()">Cancel</button>
                    <button class="btn-primary" onclick="sendNotification('${accountId}')">
                        Send Notification
                    </button>
                </div>
            `;
            
            modal.style.display = 'flex';
            
            // Populate WhatsApp contacts
            const whatsappList = document.getElementById('whatsappContactsList');
            if (whatsappContacts.length > 0) {
                whatsappList.innerHTML = `
                    <div class="contact-list">
                        ${whatsappContacts.map(contact => renderWhatsAppContact(contact, true)).join('')}
                    </div>
                `;
            } else {
                whatsappList.innerHTML = '<div style="color: #666666; font-size: 0.875rem; text-align: center; padding: 1rem;">No WhatsApp contacts saved. Use "Manage Contacts" to add some.</div>';
            }
            
            // Initialize with offline template
            setTimeout(() => {
                updateMessagePreview();
                updateWhatsAppMessagePreview();
            }, 100);
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
                    message = `Dear ${account.name} team,\n\n`;
                    if (offlineZones.length > 0) {
                        message += `We've detected that ${offlineZones.length} of your music zones are currently offline:\n\n`;
                        offlineZones.forEach(z => {
                            message += `• ${z.name}`;
                            if (z.offline_duration) {
                                const duration = formatDuration(z.offline_duration);
                                message += ` (offline for ${duration})`;
                            }
                            message += `\n`;
                        });
                    } else {
                        message += `We've detected that some of your music zones are currently offline:\n\n`;
                        message += `• [Zone names will be listed here]\n`;
                    }
                    message += `\nThis interruption may affect your customers' experience. Here's what you can do:\n\n`;
                    message += `1. Check that the device is powered on\n`;
                    message += `2. Verify your internet connection is working\n`;
                    message += `3. Restart the Soundtrack player device\n`;
                    message += `4. Ensure no firewall is blocking the connection\n\n`;
                    message += `If the issue persists after trying these steps, please contact our support team at support@bmasiamusic.com or call us directly.\n\n`;
                    message += `We're here to help ensure your music plays smoothly.\n\n`;
                    message += `Best regards,\nBMAsia Support Team`;
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
                    message += `Best regards,\nBMAsia Support Team`;
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
                    message += `Best regards,\nBMAsia Support Team`;
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
                    message += `Best regards,\nBMAsia Support Team`;
                    break;
                    
                case 'custom':
                    message = ''; // Let user write their own
                    break;
            }
            
            messageContent.value = message;
        }
        
        function updateWhatsAppMessagePreview() {
            const template = document.getElementById('whatsappMessageTemplate').value;
            const messageContent = document.getElementById('whatsappMessageContent');
            const account = window.currentAccount;
            
            if (!account) return;
            
            const offlineZones = account.zones.filter(z => z.status === 'offline');
            const expiredZones = account.zones.filter(z => z.status === 'expired');
            const unpairedZones = account.zones.filter(z => z.status === 'unpaired');
            const noSubZones = account.zones.filter(z => z.status === 'no_subscription');
            
            let message = '';
            
            switch(template) {
                case 'offline':
                    message = `🚨 Zone Alert - ${account.name}\n\n`;
                    if (offlineZones.length > 0) {
                        message += `${offlineZones.length} zone${offlineZones.length > 1 ? 's' : ''} offline:\n`;
                        offlineZones.forEach(z => {
                            message += `• ${z.name}`;
                            if (z.offline_duration) {
                                const duration = formatDuration(z.offline_duration);
                                message += ` (${duration})`;
                            }
                            message += `\n`;
                        });
                    } else {
                        message += `Zones are offline. Please check:\n`;
                    }
                    message += `\nPlease check device power & internet connection.\n`;
                    message += `Need help? Contact support@bmasiamusic.com`;
                    break;
                    
                case 'expired':
                    message = `⚠️ Subscription Alert - ${account.name}\n\n`;
                    if (expiredZones.length > 0) {
                        message += `${expiredZones.length} zone${expiredZones.length > 1 ? 's' : ''} expired:\n`;
                        expiredZones.forEach(z => {
                            message += `• ${z.name}\n`;
                        });
                    } else {
                        message += `Your zones have expired subscriptions.\n`;
                    }
                    message += `\nMusic service suspended. Contact us to renew.\n`;
                    message += `📞 Call or reply to this message`;
                    break;
                    
                case 'unpaired':
                    message = `📱 Setup Required - ${account.name}\n\n`;
                    if (unpairedZones.length > 0) {
                        message += `${unpairedZones.length} zone${unpairedZones.length > 1 ? 's need' : ' needs'} device pairing:\n`;
                        unpairedZones.forEach(z => {
                            message += `• ${z.name}\n`;
                        });
                    } else {
                        message += `Zones need device pairing.\n`;
                    }
                    message += `\nDownload Soundtrack Player app & log in to pair.\n`;
                    message += `Need help? We'll guide you through setup.`;
                    break;
                    
                case 'no_subscription':
                    message = `🎵 Activation Required - ${account.name}\n\n`;
                    if (noSubZones.length > 0) {
                        message += `${noSubZones.length} zone${noSubZones.length > 1 ? 's need' : ' needs'} subscription:\n`;
                        noSubZones.forEach(z => {
                            message += `• ${z.name}\n`;
                        });
                    } else {
                        message += `Zones need subscription activation.\n`;
                    }
                    message += `\nReady to start playing music!\n`;
                    message += `Contact us for subscription options.`;
                    break;
                    
                case 'custom':
                    message = ''; // Let user write their own
                    break;
            }
            
            messageContent.value = message;
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
        
        function closeWhatsAppModal() {
            document.getElementById('whatsappModal').style.display = 'none';
        }
        
        async function showWhatsAppManagementModal(accountId) {
            window.currentAccountId = accountId;
            const account = allData.accounts[accountId];
            
            const modal = document.getElementById('whatsappModal');
            const modalBody = document.getElementById('whatsappModalBody');
            
            // Load current WhatsApp contacts
            const whatsappContacts = await loadWhatsAppContacts(accountId);
            
            modalBody.innerHTML = `
                <div style="margin-bottom: 1.5rem;">
                    <h3 style="color: #666666; margin-bottom: 1rem;">Account: ${escapeHtml(account.name)}</h3>
                    
                    <div style="background: #f5f5f5; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                        <h4 style="margin-bottom: 0.75rem; color: #1a1a1a;">Add New Contact</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 0.75rem;">
                            <input type="text" id="newContactName" placeholder="Contact Name" style="padding: 0.5rem; border: 1px solid #e5e5e5; border-radius: 6px; background: white;">
                            <input type="tel" id="newContactPhone" placeholder="+60123456789" style="padding: 0.5rem; border: 1px solid #e5e5e5; border-radius: 6px; background: white;">
                        </div>
                        <button class="btn-primary" onclick="addWhatsAppContact()" style="width: 100%;">
                            Add Contact
                        </button>
                    </div>
                    
                    <h4 style="margin-bottom: 0.75rem; color: #1a1a1a;">Existing Contacts</h4>
                    <div id="whatsappContactsManagement">
                        ${whatsappContacts.length > 0 ? 
                            whatsappContacts.map(contact => renderWhatsAppContactForManagement(contact)).join('') :
                            '<div style="text-align: center; color: #666666; padding: 2rem;">No WhatsApp contacts saved yet</div>'
                        }
                    </div>
                </div>
                
                <div class="modal-actions">
                    <button class="btn-secondary" onclick="closeWhatsAppModal()">Close</button>
                </div>
            `;
            
            modal.style.display = 'flex';
        }
        
        function renderWhatsAppContactForManagement(contact) {
            return `
                <div class="contact-item" style="justify-content: space-between;">
                    <div class="contact-info">
                        <div class="contact-email">${escapeHtml(contact.phone)}</div>
                        <div class="contact-name">${escapeHtml(contact.name)}</div>
                    </div>
                    <button class="btn-secondary" onclick="deleteWhatsAppContact('${contact.id}')" style="padding: 0.25rem 0.75rem; font-size: 0.75rem; color: #dc2626; border-color: #dc2626;">
                        Delete
                    </button>
                </div>
            `;
        }
        
        async function addWhatsAppContact() {
            const name = document.getElementById('newContactName').value.trim();
            const phone = document.getElementById('newContactPhone').value.trim();
            
            if (!name || !phone) {
                alert('Please enter both name and phone number');
                return;
            }
            
            // Basic phone validation
            if (!phone.startsWith('+')) {
                alert('Phone number must include country code (e.g., +60123456789)');
                return;
            }
            
            try {
                const response = await fetch('/api/whatsapp', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        account_id: window.currentAccountId,
                        contact: {
                            name: name,
                            phone: phone
                        }
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    // Refresh the modal
                    showWhatsAppManagementModal(window.currentAccountId);
                } else {
                    alert('Failed to add contact: ' + result.message);
                }
            } catch (error) {
                alert('Error adding contact: ' + error.message);
            }
        }
        
        async function deleteWhatsAppContact(contactId) {
            if (!confirm('Are you sure you want to delete this contact?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/whatsapp/${contactId}?account_id=${window.currentAccountId}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                if (result.success) {
                    // Refresh the modal
                    showWhatsAppManagementModal(window.currentAccountId);
                } else {
                    alert('Failed to delete contact: ' + result.message);
                }
            } catch (error) {
                alert('Error deleting contact: ' + error.message);
            }
        }
        
        async function sendNotification(accountId) {
            const selectedEmails = [];
            const selectedWhatsAppNumbers = [];
            
            // Get selected email contacts
            document.querySelectorAll('#modalBody input[type="checkbox"]:checked').forEach(checkbox => {
                if (checkbox.id.startsWith('contact_')) {
                    selectedEmails.push(checkbox.value);
                } else if (checkbox.id.startsWith('whatsapp_')) {
                    selectedWhatsAppNumbers.push(checkbox.value);
                }
            });
            
            // Add manual WhatsApp number if provided
            const whatsappNumber = document.getElementById('whatsappNumber').value.trim();
            if (whatsappNumber) {
                selectedWhatsAppNumbers.push(whatsappNumber);
            }
            
            const emailMessage = document.getElementById('messageContent').value;
            const whatsappMessage = document.getElementById('whatsappMessageContent').value;
            
            if (selectedEmails.length === 0 && selectedWhatsAppNumbers.length === 0) {
                alert('Please select at least one contact or enter a WhatsApp number');
                return;
            }
            
            if (selectedEmails.length > 0 && !emailMessage.trim()) {
                alert('Please enter an email notification message');
                return;
            }
            
            if (selectedWhatsAppNumbers.length > 0 && !whatsappMessage.trim()) {
                alert('Please enter a WhatsApp notification message');
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
                        emails: selectedEmails,
                        whatsapp_numbers: selectedWhatsAppNumbers,
                        email_message: emailMessage,
                        whatsapp_message: whatsappMessage
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    let successMsg = 'Notification sent successfully!\\n\\n';
                    if (result.email_sent) {
                        successMsg += '✅ Email sent to ' + result.email_sent + ' recipient(s)\\n';
                    }
                    if (result.whatsapp_sent) {
                        successMsg += '✅ WhatsApp sent to ' + result.whatsapp_sent + ' recipient(s)\\n';
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
            const notificationModal = document.getElementById('notificationModal');
            const whatsappModal = document.getElementById('whatsappModal');
            
            if (event.target === notificationModal) {
                closeModal();
            } else if (event.target === whatsappModal) {
                closeWhatsAppModal();
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


@app.get("/api/whatsapp/{account_id}")
async def get_whatsapp_contacts(account_id: str):
    """Get WhatsApp contacts for an account."""
    contacts = whatsapp_contacts.get(account_id, [])
    return JSONResponse(content={'contacts': contacts})


@app.post("/api/whatsapp")
async def add_whatsapp_contact(data: dict):
    """Add or update a WhatsApp contact."""
    account_id = data.get('account_id')
    contact_data = data.get('contact')
    
    if not account_id or not contact_data:
        return JSONResponse(
            content={'success': False, 'message': 'Missing account_id or contact data'},
            status_code=400
        )
    
    # Validate contact data
    if not contact_data.get('phone') or not contact_data.get('name'):
        return JSONResponse(
            content={'success': False, 'message': 'Phone number and name are required'},
            status_code=400
        )
    
    # Initialize account contacts list if it doesn't exist
    if account_id not in whatsapp_contacts:
        whatsapp_contacts[account_id] = []
    
    # Generate contact ID if not provided (for new contacts)
    if 'id' not in contact_data:
        import uuid
        contact_data['id'] = str(uuid.uuid4())
    
    # Check if updating existing contact
    existing_index = None
    for i, contact in enumerate(whatsapp_contacts[account_id]):
        if contact['id'] == contact_data['id']:
            existing_index = i
            break
    
    if existing_index is not None:
        # Update existing contact
        whatsapp_contacts[account_id][existing_index] = contact_data
    else:
        # Add new contact
        whatsapp_contacts[account_id].append(contact_data)
    
    # Save to file
    save_whatsapp_contacts()
    
    return JSONResponse(content={'success': True, 'contact': contact_data})


@app.delete("/api/whatsapp/{contact_id}")
async def delete_whatsapp_contact(contact_id: str, account_id: str = None):
    """Delete a WhatsApp contact."""
    if not account_id:
        return JSONResponse(
            content={'success': False, 'message': 'account_id parameter is required'},
            status_code=400
        )
    
    if account_id not in whatsapp_contacts:
        return JSONResponse(
            content={'success': False, 'message': 'Account not found'},
            status_code=404
        )
    
    # Find and remove the contact
    contact_found = False
    for i, contact in enumerate(whatsapp_contacts[account_id]):
        if contact['id'] == contact_id:
            whatsapp_contacts[account_id].pop(i)
            contact_found = True
            break
    
    if not contact_found:
        return JSONResponse(
            content={'success': False, 'message': 'Contact not found'},
            status_code=404
        )
    
    # Save to file
    save_whatsapp_contacts()
    
    return JSONResponse(content={'success': True})


@app.post("/api/notify")
async def send_notification(data: dict):
    """Send notification for an account."""
    account_id = data.get('account_id')
    emails = data.get('emails', [])
    whatsapp_numbers = data.get('whatsapp_numbers', [])
    email_message = data.get('email_message', data.get('message', ''))  # Fallback for compatibility
    whatsapp_message = data.get('whatsapp_message', data.get('message', ''))
    
    if not account_id:
        return JSONResponse(
            content={'success': False, 'message': 'Missing account_id'},
            status_code=400
        )
    
    if not emails and not whatsapp_numbers:
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
    full_message = email_message
    if zone_details:
        full_message += f"\n\n--- Current Zone Status ---\n" + "\n".join(zone_details)
    
    # Track results
    email_sent = 0
    whatsapp_sent = False
    
    try:
        # Send email if requested
        if emails:
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
                
                email_sent = len(emails)
                logger.info(f"Email sent to {len(emails)} recipients")
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
                
                email_sent = len(emails)
                logger.info(f"Email saved to {filename} (SMTP not configured)")
        
        # Send WhatsApp messages if requested
        whatsapp_sent_count = 0
        if whatsapp_numbers:
            whatsapp_service = get_whatsapp_service()
            if whatsapp_service and whatsapp_service.enabled:
                # Use the WhatsApp-specific message
                # Send WhatsApp message to each number
                for phone_number in whatsapp_numbers:
                    result = await whatsapp_service.send_message(phone_number, whatsapp_message)
                    if result['success']:
                        whatsapp_sent_count += 1
                        logger.info(f"WhatsApp sent to {phone_number}")
                    else:
                        logger.error(f"WhatsApp failed for {phone_number}: {result.get('error')}")
                
                whatsapp_sent = whatsapp_sent_count > 0
            else:
                logger.info("WhatsApp service not enabled")
        
        return JSONResponse(content={
            'success': True,
            'email_sent': email_sent,
            'whatsapp_sent': whatsapp_sent_count
        })
            
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return JSONResponse(content={
            'success': False,
            'message': f'Failed to send notification: {str(e)}'
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