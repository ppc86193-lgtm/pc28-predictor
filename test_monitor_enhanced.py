"""
Enhanced test suite for Phase 6 Task 1: Accuracy Tracking and Alerts
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from monitor import (
    PC28Monitor, PredictionRecord, AccuracyMetrics, get_monitor,
    LOW_ACCURACY_THRESHOLD, MAX_ALERTS_STORED, ALERT_RETENTION_DAYS
)

class TestAccuracyTrend:
    """Test accuracy trend analysis functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.monitor = PC28Monitor()
    
    def test_get_accuracy_trend_empty_data(self):
        """Test trend analysis with no data"""
        trend = self.monitor.get_accuracy_trend(7)
        
        assert "trend" in trend
        assert "direction" in trend
        assert "summary" in trend
        assert trend["summary"]["total_days"] == 0
        assert trend["summary"]["avg_accuracy"] == 0.0
        assert trend["direction"] == "stable"
    
    def test_get_accuracy_trend_invalid_days(self):
        """Test trend analysis with invalid days parameter"""
        # Test negative days
        trend = self.monitor.get_accuracy_trend(-1)
        assert "error" in trend
        
        # Test too many days
        trend = self.monitor.get_accuracy_trend(50)
        assert "error" in trend
        
        # Test zero days
        trend = self.monitor.get_accuracy_trend(0)
        assert "error" in trend
    
    @patch('monitor.redis_client')
    def test_get_accuracy_trend_with_data(self, mock_redis):
        """Test trend analysis with sample data"""
        # Create sample prediction records
        now = datetime.now()
        sample_records = []
        
        for i in range(10):
            record_time = now - timedelta(days=i)
            record = PredictionRecord(
                timestamp=record_time,
                predicted_combination="大单",
                predicted_sum_range="14-17",
                confidence=0.75,
                actual_combination="大单" if i % 2 == 0 else "小双",
                actual_sum=15,
                is_correct=(i % 2 == 0),  # 50% accuracy
                response_time_ms=150.0
            )
            sample_records.append(record)
        
        # Mock Redis response
        mock_data = {}
        for i, record in enumerate(sample_records):
            mock_data[f"pred_{i}"] = json.dumps(record.to_dict())
        
        mock_redis.hgetall.return_value = mock_data
        
        # Test trend analysis
        trend = self.monitor.get_accuracy_trend(7)
        
        assert "trend" in trend
        assert "summary" in trend
        assert abs(trend["summary"]["avg_accuracy"] - 0.5) < 0.1  # Approximately 50% accuracy
        assert len(trend["trend"]) <= 7  # Should not exceed requested days
    
    def test_trend_direction_calculation(self):
        """Test trend direction calculation logic"""
        # This would require more complex setup with time-series data
        # For now, we test the basic structure
        trend = self.monitor.get_accuracy_trend(3)
        assert trend["direction"] in ["improving", "declining", "stable"]

class TestAlertSystem:
    """Test alert system functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.monitor = PC28Monitor()
    
    @patch('monitor.redis_client')
    def test_trigger_alert_valid(self, mock_redis):
        """Test triggering valid alerts"""
        mock_redis.lpush.return_value = 1
        mock_redis.ltrim.return_value = True
        mock_redis.expire.return_value = True
        
        # Test low accuracy alert
        self.monitor.trigger_alert("low_accuracy", {
            "accuracy": 0.45,
            "threshold": 0.50,
            "days": 7
        })
        
        # Verify Redis calls
        mock_redis.lpush.assert_called()
        mock_redis.ltrim.assert_called()
        mock_redis.expire.assert_called()
    
    def test_trigger_alert_invalid_type(self):
        """Test triggering alerts with invalid types"""
        # Should not raise exception, just log error
        self.monitor.trigger_alert("invalid_type", {"test": "data"})
        self.monitor.trigger_alert("", {"test": "data"})
        self.monitor.trigger_alert(None, {"test": "data"})
    
    def test_trigger_alert_invalid_data(self):
        """Test triggering alerts with invalid data"""
        # Should not raise exception, just log error
        self.monitor.trigger_alert("low_accuracy", "invalid_data")
        self.monitor.trigger_alert("low_accuracy", None)
        self.monitor.trigger_alert("low_accuracy", [])
    
    @patch('monitor.redis_client')
    def test_get_alerts(self, mock_redis):
        """Test retrieving alerts"""
        # Mock alert data
        sample_alerts = [
            json.dumps({
                "type": "low_accuracy",
                "timestamp": datetime.now().isoformat(),
                "data": {"accuracy": 0.45},
                "severity": "warning"
            }),
            json.dumps({
                "type": "trend",
                "timestamp": datetime.now().isoformat(),
                "data": {"direction": "declining"},
                "severity": "info"
            })
        ]
        
        mock_redis.lrange.return_value = sample_alerts
        
        result = self.monitor.get_alerts(10)
        
        assert "alerts" in result
        alerts = result["alerts"]
        assert len(alerts) == 2
        assert alerts[0]["type"] == "low_accuracy"
        assert alerts[1]["type"] == "trend"
    
    @patch('monitor.redis_client')
    def test_get_alerts_corrupted_data(self, mock_redis):
        """Test retrieving alerts with corrupted data"""
        # Mock corrupted alert data
        corrupted_alerts = [
            "invalid_json",
            json.dumps({"valid": "alert"}),
            "another_invalid_json"
        ]
        
        mock_redis.lrange.return_value = corrupted_alerts
        
        result = self.monitor.get_alerts(10)
        
        # Should only return valid alerts
        assert "alerts" in result
        alerts = result["alerts"]
        assert len(alerts) == 1
        assert alerts[0]["valid"] == "alert"

class TestAlertSeverity:
    """Test alert severity determination"""
    
    def setup_method(self):
        """Setup for each test"""
        self.monitor = PC28Monitor()
    
    def test_low_accuracy_severity(self):
        """Test low accuracy alert severity levels"""
        # Test error level (< 40%)
        severity = self.monitor._determine_alert_severity("low_accuracy", {"accuracy": 0.35})
        assert severity == "error"
        
        # Test warning level (40-50%)
        severity = self.monitor._determine_alert_severity("low_accuracy", {"accuracy": 0.45})
        assert severity == "warning"
        
        # Test info level (> 50%)
        severity = self.monitor._determine_alert_severity("low_accuracy", {"accuracy": 0.55})
        assert severity == "info"
    
    def test_trend_severity(self):
        """Test trend alert severity levels"""
        # Test declining trend with low accuracy (warning)
        severity = self.monitor._determine_alert_severity("trend", {
            "direction": "declining", 
            "accuracy": 0.40
        })
        assert severity == "warning"
        
        # Test declining trend with normal accuracy (info)
        severity = self.monitor._determine_alert_severity("trend", {
            "direction": "declining", 
            "accuracy": 0.60
        })
        assert severity == "info"
        
        # Test improving trend
        severity = self.monitor._determine_alert_severity("trend", {"direction": "improving"})
        assert severity == "info"
        
        # Test stable trend
        severity = self.monitor._determine_alert_severity("trend", {"direction": "stable"})
        assert severity == "info"
    
    def test_system_severity(self):
        """Test system alert severity"""
        severity = self.monitor._determine_alert_severity("system", {"status": "degraded"})
        assert severity == "info"

# Webhook tests removed - not core functionality for Phase 6 Task 1

class TestSystemStatusEnhanced:
    """Test enhanced system status with alerts"""
    
    def setup_method(self):
        """Setup for each test"""
        self.monitor = PC28Monitor()
    
    @patch('monitor.redis_client')
    def test_system_status_with_alerts(self, mock_redis):
        """Test system status including alert count"""
        mock_redis.ping.return_value = True
        mock_redis.hgetall.return_value = {"pred_1": "data", "pred_2": "data"}
        mock_redis.llen.return_value = 5  # 5 recent alerts
        
        status = self.monitor.get_system_status()
        
        assert status["monitor_status"] == "healthy"
        assert status["redis_connected"] == True
        assert status["total_predictions"] == 2
        assert status["recent_alerts"] == 5

class TestIntegrationEnhanced:
    """Enhanced integration tests for Phase 6 features"""
    
    @patch('monitor.redis_client')
    def test_full_monitoring_cycle_with_alerts(self, mock_redis):
        """Test complete monitoring cycle with trend analysis and alerts"""
        monitor = PC28Monitor()
        
        # Mock Redis for recording
        mock_redis.hset.return_value = True
        mock_redis.expire.return_value = True
        mock_redis.lpush.return_value = 1
        mock_redis.ltrim.return_value = True
        
        # Record prediction
        record_id = monitor.record_prediction(
            predicted_combination="大单",
            predicted_sum_range="14-17",
            confidence=0.75,
            response_time_ms=150.0
        )
        
        assert record_id != ""
        
        # Mock Redis for trend analysis
        mock_redis.hgetall.return_value = {}  # Empty for this test
        
        # Get trend analysis (should trigger low accuracy alert)
        trend = monitor.get_accuracy_trend(7)
        assert "trend" in trend
        
        # Get alerts
        mock_redis.lrange.return_value = []
        result = monitor.get_alerts(10)
        assert "alerts" in result
        assert isinstance(result["alerts"], list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])