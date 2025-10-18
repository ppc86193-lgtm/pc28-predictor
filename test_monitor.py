"""
Test suite for PC28 monitoring system
Phase 6: Monitoring and Performance Tracking Tests
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from monitor import (
    PC28Monitor, PredictionRecord, AccuracyMetrics, get_monitor,
    DEFAULT_CACHE_TTL, PREDICTION_RETENTION_DAYS
)

class TestPredictionRecord:
    """Test PredictionRecord dataclass"""
    
    def test_prediction_record_creation(self):
        """Test creating a prediction record"""
        record = PredictionRecord(
            timestamp=datetime.now(),
            predicted_combination="大单",
            predicted_sum_range="14-17",
            confidence=0.75,
            response_time_ms=150.5
        )
        
        assert record.predicted_combination == "大单"
        assert record.confidence == 0.75
        assert record.actual_combination is None
        assert record.is_correct is None
    
    def test_prediction_record_serialization(self):
        """Test record serialization and deserialization"""
        original = PredictionRecord(
            timestamp=datetime.now(),
            predicted_combination="小双",
            predicted_sum_range="10-13",
            confidence=0.65,
            actual_combination="小双",
            actual_sum=12,
            is_correct=True,
            response_time_ms=200.0
        )
        
        # Test to_dict
        record_dict = original.to_dict()
        assert isinstance(record_dict['timestamp'], str)
        assert record_dict['predicted_combination'] == "小双"
        assert record_dict['is_correct'] == True
        
        # Test from_dict
        restored = PredictionRecord.from_dict(record_dict)
        assert isinstance(restored.timestamp, datetime)
        assert restored.predicted_combination == original.predicted_combination
        assert restored.is_correct == original.is_correct

class TestAccuracyMetrics:
    """Test AccuracyMetrics dataclass"""
    
    def test_accuracy_metrics_creation(self):
        """Test creating accuracy metrics"""
        metrics = AccuracyMetrics(
            combination_accuracy=0.65,
            sum_range_accuracy=0.70,
            overall_accuracy=0.60,
            total_predictions=100,
            correct_predictions=60,
            time_period="24h"
        )
        
        assert metrics.combination_accuracy == 0.65
        assert metrics.total_predictions == 100
        assert metrics.time_period == "24h"

class TestPC28Monitor:
    """Test PC28Monitor class"""
    
    def setup_method(self):
        """Setup for each test"""
        self.monitor = PC28Monitor()
    
    @patch('monitor.redis_client')
    def test_record_prediction_success(self, mock_redis):
        """Test successful prediction recording"""
        mock_redis.hset.return_value = True
        mock_redis.expire.return_value = True
        
        record_id = self.monitor.record_prediction(
            predicted_combination="大单",
            predicted_sum_range="14-17",
            confidence=0.75,
            response_time_ms=150.0
        )
        
        assert record_id.startswith("pred_")
        assert len(self.monitor.response_times) == 1
        assert self.monitor.response_times[0] == 150.0
        
        # Verify Redis calls
        mock_redis.hset.assert_called_once()
        mock_redis.expire.assert_called_once()
    
    def test_record_prediction_invalid_input(self):
        """Test prediction recording with invalid input"""
        # Test invalid combination
        result = self.monitor.record_prediction("", "14-17", 0.75, 150.0)
        assert result == ""
        
        # Test invalid confidence
        result = self.monitor.record_prediction("大单", "14-17", 1.5, 150.0)
        assert result == ""
        
        # Test negative response time
        result = self.monitor.record_prediction("大单", "14-17", 0.75, -10.0)
        assert result == ""
    
    @patch('monitor.redis_client')
    def test_update_prediction_result_success(self, mock_redis):
        """Test successful prediction result update"""
        # Mock Redis responses
        record_data = {
            'timestamp': datetime.now().isoformat(),
            'predicted_combination': '大单',
            'predicted_sum_range': '14-17',
            'confidence': 0.75,
            'response_time_ms': 150.0
        }
        
        mock_redis.hget.return_value = json.dumps(record_data)
        mock_redis.hset.return_value = True
        
        success = self.monitor.update_prediction_result(
            record_id="pred_123456789",
            actual_combination="大单",
            actual_sum=15
        )
        
        assert success == True
        assert len(self.monitor.accuracy_window) == 1
        assert self.monitor.accuracy_window[0] == 1  # Correct prediction
        
        # Verify Redis calls
        mock_redis.hget.assert_called_once()
        mock_redis.hset.assert_called()
    
    def test_update_prediction_result_invalid_input(self):
        """Test prediction result update with invalid input"""
        # Test invalid record_id
        result = self.monitor.update_prediction_result("", "大单", 15)
        assert result == False
        
        # Test invalid actual_sum
        result = self.monitor.update_prediction_result("pred_123", "大单", 30)
        assert result == False
        
        # Test invalid actual_combination
        result = self.monitor.update_prediction_result("pred_123", "", 15)
        assert result == False
    
    def test_is_sum_in_range(self):
        """Test sum range validation"""
        # Test valid ranges
        assert self.monitor._is_sum_in_range(5, "0-9") == True
        assert self.monitor._is_sum_in_range(12, "10-13") == True
        assert self.monitor._is_sum_in_range(15, "14-17") == True
        assert self.monitor._is_sum_in_range(25, "18-27") == True
        
        # Test invalid ranges
        assert self.monitor._is_sum_in_range(10, "0-9") == False
        assert self.monitor._is_sum_in_range(5, "10-13") == False
        assert self.monitor._is_sum_in_range(30, "18-27") == False
        
        # Test unknown range
        assert self.monitor._is_sum_in_range(15, "unknown-range") == False
    
    @patch('monitor.redis_client')
    def test_get_recent_predictions(self, mock_redis):
        """Test getting recent predictions"""
        # Create test data
        now = datetime.now()
        old_time = now - timedelta(hours=25)  # Older than 24h
        recent_time = now - timedelta(hours=1)  # Within 24h
        
        test_records = {
            "pred_old": json.dumps({
                'timestamp': old_time.isoformat(),
                'predicted_combination': '大单',
                'predicted_sum_range': '14-17',
                'confidence': 0.75,
                'response_time_ms': 150.0
            }),
            "pred_recent": json.dumps({
                'timestamp': recent_time.isoformat(),
                'predicted_combination': '小双',
                'predicted_sum_range': '10-13',
                'confidence': 0.65,
                'response_time_ms': 200.0
            })
        }
        
        mock_redis.hgetall.return_value = test_records
        
        recent_predictions = self.monitor._get_recent_predictions(hours=24)
        
        # Should only return the recent prediction
        assert len(recent_predictions) == 1
        assert recent_predictions[0].predicted_combination == "小双"
    
    @patch('monitor.redis_client')
    def test_get_accuracy_metrics(self, mock_redis):
        """Test getting accuracy metrics"""
        # Test with cached metrics
        cached_metrics = {
            "combination_accuracy": 0.65,
            "sum_range_accuracy": 0.70,
            "overall_accuracy": 0.60,
            "total_predictions": 100,
            "correct_predictions": 60,
            "time_period": "24h"
        }
        
        mock_redis.get.return_value = json.dumps(cached_metrics)
        
        metrics = self.monitor.get_accuracy_metrics("24h")
        
        assert metrics["combination_accuracy"] == 0.65
        assert metrics["total_predictions"] == 100
        assert metrics["time_period"] == "24h"
    
    def test_get_performance_metrics(self):
        """Test getting performance metrics"""
        # Add some test data
        self.monitor.response_times.extend([100, 150, 200, 250, 300])
        self.monitor.accuracy_window.extend([1, 1, 0, 1, 0, 1, 1, 0, 1, 1])
        
        metrics = self.monitor.get_performance_metrics()
        
        assert "response_time" in metrics
        assert "accuracy" in metrics
        assert "system" in metrics
        
        # Check response time calculations
        assert metrics["response_time"]["avg_ms"] == 200.0
        assert metrics["response_time"]["min_ms"] == 100
        assert metrics["response_time"]["max_ms"] == 300
        
        # Check accuracy calculations
        assert metrics["accuracy"]["current_window"] == 0.7  # 7/10
    
    @patch('monitor.redis_client')
    def test_get_prediction_history(self, mock_redis):
        """Test getting prediction history"""
        # Mock Redis response
        test_records = {
            "pred_1": json.dumps({
                'timestamp': datetime.now().isoformat(),
                'predicted_combination': '大单',
                'predicted_sum_range': '14-17',
                'confidence': 0.75,
                'response_time_ms': 150.0
            })
        }
        
        mock_redis.hgetall.return_value = test_records
        
        history = self.monitor.get_prediction_history(limit=10)
        
        assert len(history) == 1
        assert history[0]['predicted_combination'] == '大单'
    
    @patch('monitor.redis_client')
    def test_cleanup_old_data(self, mock_redis):
        """Test cleaning up old data"""
        # Create test data with old and new records
        old_time = datetime.now() - timedelta(days=35)
        new_time = datetime.now() - timedelta(days=5)
        
        test_records = {
            "pred_old": json.dumps({
                'timestamp': old_time.isoformat(),
                'predicted_combination': '大单',
                'predicted_sum_range': '14-17',
                'confidence': 0.75,
                'response_time_ms': 150.0
            }),
            "pred_new": json.dumps({
                'timestamp': new_time.isoformat(),
                'predicted_combination': '小双',
                'predicted_sum_range': '10-13',
                'confidence': 0.65,
                'response_time_ms': 200.0
            })
        }
        
        mock_redis.hgetall.return_value = test_records
        mock_redis.hdel.return_value = 1
        
        self.monitor.cleanup_old_data(days=30)
        
        # Should delete the old record
        mock_redis.hdel.assert_called_with(self.monitor.prediction_history_key, "pred_old")
    
    @patch('monitor.redis_client')
    def test_get_system_status(self, mock_redis):
        """Test getting system status"""
        mock_redis.ping.return_value = True
        mock_redis.hgetall.return_value = {"pred_1": "data", "pred_2": "data"}
        
        status = self.monitor.get_system_status()
        
        assert status["monitor_status"] == "healthy"
        assert status["redis_connected"] == True
        assert status["total_predictions"] == 2
        assert "memory_usage" in status

class TestSingleton:
    """Test singleton pattern"""
    
    def test_get_monitor_singleton(self):
        """Test that get_monitor returns the same instance"""
        monitor1 = get_monitor()
        monitor2 = get_monitor()
        
        assert monitor1 is monitor2

class TestIntegration:
    """Integration tests for monitoring system"""
    
    @patch('monitor.redis_client')
    def test_full_prediction_lifecycle(self, mock_redis):
        """Test complete prediction lifecycle"""
        monitor = PC28Monitor()
        
        # Mock Redis for recording
        mock_redis.hset.return_value = True
        mock_redis.expire.return_value = True
        
        # Record prediction
        record_id = monitor.record_prediction(
            predicted_combination="大单",
            predicted_sum_range="14-17",
            confidence=0.75,
            response_time_ms=150.0
        )
        
        assert record_id != ""
        
        # Mock Redis for updating
        record_data = {
            'timestamp': datetime.now().isoformat(),
            'predicted_combination': '大单',
            'predicted_sum_range': '14-17',
            'confidence': 0.75,
            'response_time_ms': 150.0
        }
        mock_redis.hget.return_value = json.dumps(record_data)
        
        # Update with actual result
        success = monitor.update_prediction_result(record_id, "大单", 15)
        assert success == True
        
        # Check that accuracy was updated
        assert len(monitor.accuracy_window) == 1
        assert monitor.accuracy_window[0] == 1  # Correct prediction

if __name__ == "__main__":
    pytest.main([__file__, "-v"])