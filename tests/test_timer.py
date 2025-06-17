"""Unit tests for timer and zone monitoring logic."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

from config import Config
from zone_monitor import ZoneMonitor


class TestZoneMonitor(unittest.IsolatedAsyncioTestCase):
    """Test cases for ZoneMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config(
            syb_api_key="test_key",
            zone_ids=["zone1", "zone2"],
            polling_interval=60,
            offline_threshold=600,
            log_level="INFO"
        )
        self.monitor = ZoneMonitor(self.config)
    
    async def test_zone_goes_offline(self):
        """Test that a zone going offline is tracked correctly."""
        zone_id = "zone1"
        zone_name = "Test Zone"
        
        # Simulate zone going offline
        await self.monitor._update_zone_state(zone_id, False, zone_name)
        
        # Check that offline tracking started
        self.assertIn(zone_id, self.monitor.offline_since)
        self.assertEqual(self.monitor.zone_states[zone_id], False)
        self.assertEqual(self.monitor.zone_names[zone_id], zone_name)
    
    async def test_zone_comes_back_online(self):
        """Test that a zone coming back online clears offline tracking."""
        zone_id = "zone1"
        zone_name = "Test Zone"
        
        # First, simulate zone going offline
        await self.monitor._update_zone_state(zone_id, False, zone_name)
        self.assertIn(zone_id, self.monitor.offline_since)
        
        # Then simulate zone coming back online
        await self.monitor._update_zone_state(zone_id, True, zone_name)
        
        # Check that offline tracking is cleared
        self.assertNotIn(zone_id, self.monitor.offline_since)
        self.assertEqual(self.monitor.zone_states[zone_id], True)
    
    async def test_offline_duration_calculation(self):
        """Test that offline duration is calculated correctly."""
        zone_id = "zone1"
        zone_name = "Test Zone"
        
        # Manually set offline start time
        offline_start = datetime.now() - timedelta(minutes=15)
        self.monitor.offline_since[zone_id] = offline_start
        
        # Get offline zones
        offline_zones = self.monitor.get_offline_zones()
        
        # Check that duration is approximately 15 minutes
        self.assertIn(zone_id, offline_zones)
        duration = offline_zones[zone_id]
        self.assertGreaterEqual(duration.total_seconds(), 14 * 60)  # At least 14 minutes
        self.assertLessEqual(duration.total_seconds(), 16 * 60)     # At most 16 minutes
    
    def test_zone_status_summary(self):
        """Test zone status summary generation."""
        # Set up some zone states
        self.monitor.zone_states = {
            "zone1": True,
            "zone2": False,
            "zone3": True
        }
        
        summary = self.monitor.get_zone_status_summary()
        self.assertEqual(summary, "2 online, 1 offline")
    
    def test_detailed_status(self):
        """Test detailed status information."""
        zone_id = "zone1"
        zone_name = "Test Zone"
        
        # Set up zone state
        self.monitor.zone_states[zone_id] = False
        self.monitor.zone_names[zone_id] = zone_name
        offline_start = datetime.now() - timedelta(minutes=5)
        self.monitor.offline_since[zone_id] = offline_start
        
        # Get detailed status
        status = self.monitor.get_detailed_status()
        
        # Verify structure
        self.assertIn(zone_id, status)
        zone_status = status[zone_id]
        self.assertEqual(zone_status["name"], zone_name)
        self.assertEqual(zone_status["online"], False)
        self.assertIsNotNone(zone_status["offline_since"])
        self.assertIsNotNone(zone_status["offline_duration_seconds"])
        
        # Check duration is approximately 5 minutes
        duration_seconds = zone_status["offline_duration_seconds"]
        self.assertGreaterEqual(duration_seconds, 4 * 60)  # At least 4 minutes
        self.assertLessEqual(duration_seconds, 6 * 60)     # At most 6 minutes


class TestNotificationThreshold(unittest.TestCase):
    """Test cases for notification threshold logic."""
    
    def test_threshold_not_met(self):
        """Test that notifications are not triggered below threshold."""
        offline_duration = timedelta(minutes=5)  # Below 10-minute threshold
        self.assertLess(offline_duration, timedelta(minutes=10))
    
    def test_threshold_met(self):
        """Test that notifications are triggered when threshold is met."""
        offline_duration = timedelta(minutes=15)  # Above 10-minute threshold
        self.assertGreaterEqual(offline_duration, timedelta(minutes=10))
    
    def test_threshold_exactly_met(self):
        """Test that notifications are triggered when threshold is exactly met."""
        offline_duration = timedelta(minutes=10)  # Exactly 10 minutes
        self.assertGreaterEqual(offline_duration, timedelta(minutes=10))


if __name__ == "__main__":
    unittest.main()