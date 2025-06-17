#!/usr/bin/env python3
"""
Run SYB Zone Monitor with Web Dashboard
Combines the main monitoring service with the web dashboard server.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime

from config import Config
from zone_monitor import ZoneMonitor
from health_server import HealthServer
from web_server import run_dashboard_server
from notifier import NotificationChain


class MonitorWithDashboard:
    """Combined monitor and dashboard service."""
    
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
        
        # Setup health server
        self.health_server = HealthServer(self.get_health_status)
        
    async def start(self):
        """Start both monitoring and dashboard services."""
        self.running = True
        self.logger.info("🚀 Starting SYB Zone Monitor with Web Dashboard")
        self.logger.info(f"📊 Monitoring {len(self.config.zone_ids)} zones")
        self.logger.info("🌐 Dashboard will be available at http://localhost:8080")
        
        # Start health server
        self.health_server.start()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Run both monitoring and dashboard concurrently
            await asyncio.gather(
                self._monitor_loop(),
                run_dashboard_server(self.zone_monitor, host="0.0.0.0", port=8080)
            )
        except Exception as e:
            self.logger.error(f"Service failed: {e}")
            raise
        finally:
            self.health_server.stop()
            await self.zone_monitor.close()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                await self.zone_monitor.check_zones()
                offline_zones = self.zone_monitor.get_offline_zones()
                
                for zone_id, offline_duration in offline_zones.items():
                    if offline_duration.total_seconds() >= 600:  # 10 minutes
                        zone_name = self.zone_monitor.get_zone_name(zone_id)
                        await self.notification_chain.send_alert(zone_name, offline_duration)
                
                # Log current status
                zone_status = self.zone_monitor.get_zone_status_summary()
                self.logger.info(f"Zone status check complete. {zone_status}")
                
            except Exception as e:
                self.logger.error(f"Error during monitoring cycle: {e}")
            
            # Wait for next polling interval
            await asyncio.sleep(self.config.polling_interval)
    
    def get_health_status(self):
        """Return health status for /healthz endpoint."""
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
        
        # Validate we have zones configured
        if not config.zone_ids:
            print("❌ No zones configured! Please check your .env file.")
            sys.exit(1)
            
        monitor = MonitorWithDashboard(config)
        await monitor.start()
        
    except KeyboardInterrupt:
        print("\n👋 Shutdown requested by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())