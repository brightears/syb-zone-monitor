#!/usr/bin/env python3
"""Main application entry point for Render deployment."""

import os
import asyncio
import logging
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# Import our dashboard app
from enhanced_dashboard import app as dashboard_app
from enhanced_dashboard import startup_event, zone_monitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting SYB Zone Monitor...")
    
    # Check for required environment variables
    if not os.getenv("SYB_API_KEY"):
        logger.error("SYB_API_KEY environment variable is required!")
    else:
        # Initialize the dashboard
        await startup_event()
        logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SYB Zone Monitor...")
    if zone_monitor:
        # Any cleanup needed
        pass


# Create the main app with lifespan management
app = FastAPI(
    title="SYB Zone Monitor",
    description="Real-time monitoring system for Soundtrack Your Brand zones",
    version="1.0.0",
    lifespan=lifespan
)

# Mount the dashboard app
app.mount("/", dashboard_app)


@app.get("/health")
async def health_check():
    """Health check endpoint for Render."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "syb-zone-monitor",
            "zone_monitor_active": zone_monitor is not None
        }
    )


@app.get("/api/status")
async def get_status():
    """Get current system status."""
    if zone_monitor:
        total_zones = len(zone_monitor.zone_ids)
        monitored_zones = len(zone_monitor.zone_status)
        online_zones = sum(
            1 for status in zone_monitor.zone_status.values() 
            if status.status == "ONLINE"
        )
        offline_zones = sum(
            1 for status in zone_monitor.zone_status.values() 
            if status.status == "OFFLINE"
        )
        
        return JSONResponse(
            content={
                "status": "active",
                "total_zones": total_zones,
                "monitored_zones": monitored_zones,
                "online_zones": online_zones,
                "offline_zones": offline_zones
            }
        )
    else:
        return JSONResponse(
            content={
                "status": "initializing",
                "message": "Zone monitor not yet initialized"
            },
            status_code=503
        )


if __name__ == "__main__":
    # For local development
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )