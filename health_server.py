"""Health check HTTP server for monitoring the uptime monitor."""

import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Dict, Callable

logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoints."""
    
    def __init__(self, get_health_status: Callable[[], Dict], *args, **kwargs):
        self.get_health_status = get_health_status
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/healthz":
            self._handle_health_check()
        else:
            self._handle_not_found()
    
    def _handle_health_check(self):
        """Handle health check requests."""
        try:
            status = self.get_health_status()
            response = json.dumps(status, indent=2)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response.encode())
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.send_error(500, "Internal Server Error")
    
    def _handle_not_found(self):
        """Handle 404 responses."""
        self.send_error(404, "Not Found")
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.debug(format % args)


class HealthServer:
    """Simple HTTP server for health checks."""
    
    def __init__(self, get_health_status: Callable[[], Dict], port: int = 8000):
        self.get_health_status = get_health_status
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the health server in a separate thread."""
        def handler(*args, **kwargs):
            return HealthHandler(self.get_health_status, *args, **kwargs)
        
        self.server = HTTPServer(("", self.port), handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        logger.info(f"Health server started on port {self.port}")
    
    def stop(self):
        """Stop the health server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Health server stopped")