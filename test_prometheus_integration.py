#!/usr/bin/env python3
"""
Prometheus Integration Test
Phase 6 Task 3: Performance Monitoring Enhancement
"""

import pytest
import time
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Import the app and components
from main import app
from monitor import get_monitor
from prometheus_client import REGISTRY, CollectorRegistry

# Create test client
client = TestClient(app)

class TestPrometheusIntegration:
    """Test Prometheus metrics integration"""
    
    def test_metrics_endpoint_exists(self):
        """Test that /metrics endpoint exists and returns Prometheus format"""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
        
        content = response.text
        
        # Check for expected metrics
        expected_metrics = [
            "predict_requests_total",
            "predict_duration_seconds",
            "cpu_usage_percent",
            "memory_usage_mb",
            "system_uptime_seconds",
            "active_connections"
        ]
        
        for metric in expected_metrics:
            assert metric in content, f"Metric {metric} not found in /metrics output"
    
    def test_prediction_metrics_recording(self):
        """Test that prediction requests record metrics"""
        # Mock the prediction engine to avoid external dependencies
        with patch("main.prediction_engine") as mock_engine:
            mock_result = MagicMock()
            mock_result.combination = "大单"
            mock_result.sum_range = "14-17"
            mock_result.confidence = 0.75
            mock_result.probabilities = {"大单": 0.3, "小双": 0.25, "小单": 0.2, "大双": 0.25}
            mock_result.timestamp = "2025-10-18T13:00:00"
            mock_engine.generate_prediction.return_value = mock_result
            
            # Make prediction request
            response = client.post("/predict")
            
            assert response.status_code == 200
            
            # Check that metrics were recorded
            metrics_response = client.get("/metrics")
            metrics_content = metrics_response.text
            
            # Should have at least one prediction request recorded
            assert "predict_requests_total" in metrics_content
            assert "predict_duration_seconds" in metrics_content
    
    def test_monitor_performance_metrics(self):
        """Test monitor performance metrics integration"""
        monitor = get_monitor()
        
        # Record some performance data
        monitor.monitor_performance(0.15)  # 150ms response time
        monitor.monitor_performance(0.25)  # 250ms response time
        monitor.monitor_performance(0.10)  # 100ms response time
        
        # Get performance metrics
        metrics = monitor.get_performance_metrics()
        
        assert "response_time" in metrics
        assert "system" in metrics
        
        # Check that response time metrics are calculated
        response_time = metrics["response_time"]
        assert "p50_ms" in response_time
        assert "p95_ms" in response_time
        assert "p99_ms" in response_time
        
        # Check that system metrics are included
        system = metrics["system"]
        assert "cpu_usage" in system
        assert "memory_usage_mb" in system
    
    def test_system_health_calculation(self):
        """Test system health score calculation"""
        monitor = get_monitor()
        
        # Test with good response time
        monitor.monitor_performance(0.1)  # 100ms - should be good
        
        # Test with poor response time
        monitor.monitor_performance(2.5)  # 2.5s - should reduce health score
        
        # Get metrics to verify health score is being calculated
        metrics_response = client.get("/metrics")
        metrics_content = metrics_response.text
        
        assert "system_health_score" in metrics_content
    
    def test_accuracy_metrics_integration(self):
        """Test accuracy metrics integration with Prometheus"""
        monitor = get_monitor()
        
        # Mock some accuracy data
        with patch.object(monitor, 'calculate_accuracy') as mock_calc:
            mock_calc.return_value = {
                "combination_accuracy": 0.58,
                "big_small_accuracy": 0.63,
                "sum_range_accuracy": 0.67
            }
            
            # Trigger performance monitoring which should update accuracy metrics
            monitor.monitor_performance(0.2)
            
            # Check that accuracy metrics are in Prometheus output
            metrics_response = client.get("/metrics")
            metrics_content = metrics_response.text
            
            assert "prediction_accuracy" in metrics_content
    
    def test_metrics_labels(self):
        """Test that metrics have proper labels"""
        # Make a prediction request to generate labeled metrics
        with patch("main.prediction_engine") as mock_engine:
            mock_result = MagicMock()
            mock_result.combination = "大单"
            mock_result.sum_range = "14-17"
            mock_result.confidence = 0.75
            mock_result.probabilities = {"大单": 0.3, "小双": 0.25, "小单": 0.2, "大双": 0.25}
            mock_result.timestamp = "2025-10-18T13:00:00"
            mock_engine.generate_prediction.return_value = mock_result
            
            response = client.post("/predict")
            assert response.status_code == 200
        
        # Check metrics with labels
        metrics_response = client.get("/metrics")
        metrics_content = metrics_response.text
        
        # Check for labeled metrics
        assert 'predict_requests_total{endpoint="predict",method="POST"}' in metrics_content
        assert 'predict_duration_seconds_bucket{endpoint="predict"' in metrics_content
    
    def test_performance_thresholds(self):
        """Test performance threshold monitoring"""
        monitor = get_monitor()
        
        # Test response times that should trigger different health scores
        test_cases = [
            (0.1, "Good response time"),      # Should maintain high health score
            (0.6, "Moderate response time"),  # Should slightly reduce health score  
            (1.2, "Slow response time"),      # Should reduce health score more
            (2.5, "Very slow response time")  # Should significantly reduce health score
        ]
        
        for response_time, description in test_cases:
            monitor.monitor_performance(response_time)
            
            # Verify that metrics are being recorded
            metrics_response = client.get("/metrics")
            assert metrics_response.status_code == 200
            
            print(f"✅ {description}: {response_time}s recorded")
    
    def test_metrics_persistence(self):
        """Test that metrics persist across multiple requests"""
        initial_metrics = client.get("/metrics").text
        
        # Make multiple requests
        with patch("main.prediction_engine") as mock_engine:
            mock_result = MagicMock()
            mock_result.combination = "大单"
            mock_result.sum_range = "14-17"
            mock_result.confidence = 0.75
            mock_result.probabilities = {"大单": 0.3, "小双": 0.25, "小单": 0.2, "大双": 0.25}
            mock_result.timestamp = "2025-10-18T13:00:00"
            mock_engine.generate_prediction.return_value = mock_result
            
            for i in range(3):
                response = client.post("/predict")
                assert response.status_code == 200
                time.sleep(0.1)  # Small delay between requests
        
        final_metrics = client.get("/metrics").text
        
        # Metrics should have increased
        assert final_metrics != initial_metrics
        assert "predict_requests_total" in final_metrics

def test_prometheus_metrics_format():
    """Test that Prometheus metrics are in correct format"""
    response = client.get("/metrics")
    
    assert response.status_code == 200
    content = response.text
    
    # Basic format checks
    lines = content.strip().split('\n')
    
    for line in lines:
        if line.startswith('#'):
            # Comment lines should start with # HELP or # TYPE
            assert line.startswith('# HELP') or line.startswith('# TYPE')
        elif line.strip():  # Non-empty, non-comment lines
            # Should contain metric name and value
            assert ' ' in line or '\t' in line

def test_system_resource_monitoring():
    """Test system resource monitoring integration"""
    response = client.get("/metrics")
    
    assert response.status_code == 200
    content = response.text
    
    # Should include system resource metrics
    assert "cpu_usage_percent" in content
    assert "memory_usage_mb" in content
    assert "system_uptime_seconds" in content

if __name__ == "__main__":
    print("🚀 Running Prometheus Integration Tests...")
    pytest.main([__file__, "-v"])