#!/usr/bin/env python3
"""
Test script for new trend analysis functionality
"""

import sys
sys.path.append('pc28_predictor')

def test_trend_analysis():
    """Test the new trend analysis features"""
    try:
        from monitor import PC28Monitor
        from datetime import datetime, timedelta
        import json
        
        print("Testing trend analysis functionality...")
        
        # Create monitor instance
        monitor = PC28Monitor()
        
        # Test get_accuracy_trend with no data
        trend = monitor.get_accuracy_trend(7)
        print(f"✅ Empty trend analysis: {trend}")
        
        # Test trigger_alert
        monitor.trigger_alert("test_alert", {"message": "Test alert"})
        print("✅ Alert triggered successfully")
        
        # Test get_alerts
        alerts = monitor.get_alerts(10)
        print(f"✅ Retrieved {len(alerts)} alerts")
        
        # Test system status with alerts
        status = monitor.get_system_status()
        print(f"✅ System status: {status.get('monitor_status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Trend analysis test failed: {e}")
        return False

def test_api_endpoints():
    """Test new API endpoints"""
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        print("Testing new API endpoints...")
        
        # Test trend endpoint
        response = client.get("/monitor/trend?days=7")
        print(f"✅ /monitor/trend status: {response.status_code}")
        
        # Test alerts endpoint
        response = client.get("/monitor/alerts?limit=10")
        print(f"✅ /monitor/alerts status: {response.status_code}")
        
        # Test with Chinese language
        response = client.get("/monitor/trend?days=3", headers={"Accept-Language": "zh-CN"})
        print(f"✅ Chinese trend endpoint status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Phase 6 Task 1 Implementation...")
    print("=" * 50)
    
    tests = [
        test_trend_analysis,
        test_api_endpoints
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Phase 6 Task 1 implementation successful!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)