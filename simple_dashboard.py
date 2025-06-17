#!/usr/bin/env python3
"""Simple dashboard server without complex contact loading."""

import asyncio
import logging
from config import Config
from zone_monitor import ZoneMonitor
from web_server import DashboardServer

async def main():
    """Start simple dashboard."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Load config
        config = Config.from_env()
        logger.info(f"Loaded {len(config.zone_ids)} zones")
        
        # Create zone monitor
        zone_monitor = ZoneMonitor(config)
        logger.info("Created zone monitor")
        
        # Create dashboard server
        dashboard = DashboardServer(zone_monitor)
        logger.info("Created dashboard server")
        
        # Start monitoring task
        async def monitor_task():
            while True:
                try:
                    await zone_monitor.check_zones()
                    logger.info("Zone check completed")
                except Exception as e:
                    logger.error(f"Monitor error: {e}")
                await asyncio.sleep(60)  # Check every minute
        
        # Start dashboard server task  
        async def server_task():
            import uvicorn
            config_obj = uvicorn.Config(
                dashboard.app, 
                host="127.0.0.1", 
                port=8080, 
                log_level="info"
            )
            server = uvicorn.Server(config_obj)
            await server.serve()
        
        logger.info("🚀 Starting dashboard on http://127.0.0.1:8080")
        
        # Run both tasks concurrently
        await asyncio.gather(
            monitor_task(),
            server_task()
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())