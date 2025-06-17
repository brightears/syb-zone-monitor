#!/usr/bin/env python3
"""
Soundtrack Your Brand Zone Uptime Monitor with Web Dashboard
Monitors SYB zones and sends alerts when zones are offline ≥ 10 minutes.
Includes a web dashboard for internal team monitoring.
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional

import httpx
from config import Config
from notifier import NotificationChain
from zone_monitor import ZoneMonitor
from web_server import DashboardServer
import uvicorn


class UptimeMonitorWithDashboard:
    """Main application class for monitoring SYB zones with web dashboard."""
    
    def __init__(self, config: Config):
        self.config = config
        self.zone_monitor = ZoneMonitor(config)
        self.notification_chain = NotificationChain(config)
        self.running = False
        self.start_time = datetime.now()
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger(__name__)
        
        # Setup web dashboard
        self.dashboard_server = DashboardServer(self.zone_monitor)
        
    async def start(self):
        """Start the monitoring service with web dashboard."""
        self.running = True
        self.logger.info("Starting SYB Zone Uptime Monitor with Web Dashboard")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Start dashboard server and monitoring concurrently
            await asyncio.gather(
                self._run_dashboard_server(),
                self._monitor_loop()
            )
        except Exception as e:
            self.logger.error(f"Application failed: {e}")
            raise
        finally:
            await self.zone_monitor.close()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def _run_dashboard_server(self):
        """Run the dashboard web server."""
        config = uvicorn.Config(
            self.dashboard_server.app, 
            host="0.0.0.0", 
            port=8080, 
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        self.logger.info("Starting web dashboard on http://0.0.0.0:8080")
        await server.serve()
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        # Give dashboard server time to start
        await asyncio.sleep(2)
        
        while self.running:
            try:
                await self.zone_monitor.check_zones()
                offline_zones = self.zone_monitor.get_offline_zones()
                
                for zone_id, offline_duration in offline_zones.items():
                    if offline_duration >= timedelta(minutes=10):
                        zone_name = self.zone_monitor.get_zone_name(zone_id)
                        await self.notification_chain.send_alert(zone_name, offline_duration)
                
                # Log current status
                zone_status = self.zone_monitor.get_zone_status_summary()
                self.logger.info(f"Zone status check complete. {zone_status}")
                
            except Exception as e:
                self.logger.error(f"Error during monitoring cycle: {e}")
            
            # Wait for next polling interval
            await asyncio.sleep(self.config.polling_interval)
    
    def get_health_status(self) -> Dict:
        """Return health status for health endpoint."""
        uptime = datetime.now() - self.start_time
        zones_status = self.zone_monitor.get_detailed_status()
        
        return {
            "uptime": str(uptime),
            "zones": zones_status,
            "last_check": self.zone_monitor.last_check_time.isoformat() if self.zone_monitor.last_check_time else None,
            "status": "healthy" if self.running else "stopping"
        }


async def main():
    """Main entry point."""
    try:
        config = Config.from_env()
        monitor = UptimeMonitorWithDashboard(config)
        await monitor.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())