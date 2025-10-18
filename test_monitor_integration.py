#!/usr/bin/env python3
"""
Integration test for monitor.py with the existing PC28 system
"""

import sys
sys.path.append('pc28_predictor')

def test_monitor_imports():
    """Test that monitor imports work with existing system"""
    try:
        from monitor import PC28Monitor, get_monitor, PredictionRecord, AccuracyMetrics
        print("✅ Monitor imports successful")
        return True
    except ImportError as e:
        print(f"❌ Monitor import error: {e}")
        return False

def test_monitor_initialization():
    """Test monitor initialization"""
    try:
        from monitor import PC28Monitor
        
        monitor = PC28Monitor()
        assert hasattr(monitor, 'cache_prefix')
        assert hasattr(monitor, 'response_times')
        assert hasattr(monitor, 'accuracy_window')
        
        print("✅ Monitor initialization successful")
        return True
    except Exception as e:
        print(f"❌ Monitor initialization error: {e}")
        return False

def test_monitor_singleton():
    """Test singleton pattern"""
    try:
        from monitor import get_monitor
        
        monitor1 = get_monitor()
        monitor2 = get_monitor()
        
        assert monitor1 is monitor2
        print("✅ Monitor singleton pattern working")
        return True
    except Exception as e:
        print(f"❌ Monitor singleton error: {e}")
        return False

def test_prediction_record():
    """Test PredictionRecord functionality"""
    try:
        from monitor import PredictionRecord
        from datetime import datetime
        
        record = PredictionRecord(
            timestamp=datetime.now(),
            predicted_combination="大单",
            predicted_sum_range="14-17",
            confidence=0.75,
            response_time_ms=150.0
        )
        
        # Test serialization
        record_dict = record.to_dict()
        assert isinstance(record_dict['timestamp'], str)
        
        # Test deserialization
        restored = PredictionRecord.from_dict(record_dict)
        assert restored.predicted_combination == "大单"
        
        print("✅ PredictionRecord functionality working")
        return True
    except Exception as e:
        print(f"❌ PredictionRecord error: {e}")
        return False

def test_monitor_validation():
    """Test input validation"""
    try:
        from monitor import PC28Monitor
        
        monitor = PC28Monitor()
        
        # Test invalid inputs
        result = monitor.record_prediction("", "14-17", 0.75, 150.0)
        assert result == ""
        
        result = monitor.record_prediction("大单", "14-17", 1.5, 150.0)
        assert result == ""
        
        result = monitor.update_prediction_result("", "大单", 15)
        assert result == False
        
        result = monitor.update_prediction_result("pred_123", "大单", 30)
        assert result == False
        
        print("✅ Monitor input validation working")
        return True
    except Exception as e:
        print(f"❌ Monitor validation error: {e}")
        return False

def test_constants():
    """Test that constants are properly defined"""
    try:
        from monitor import (
            DEFAULT_CACHE_TTL, PREDICTION_RETENTION_DAYS, 
            MAX_RESPONSE_TIMES, MAX_ACCURACY_WINDOW, 
            BATCH_SIZE, TREND_THRESHOLD
        )
        
        assert DEFAULT_CACHE_TTL == 3600
        assert PREDICTION_RETENTION_DAYS == 30
        assert MAX_RESPONSE_TIMES == 1000
        assert MAX_ACCURACY_WINDOW == 100
        assert BATCH_SIZE == 100
        assert TREND_THRESHOLD == 0.05
        
        print("✅ Constants properly defined")
        return True
    except Exception as e:
        print(f"❌ Constants error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("Testing monitor.py integration...")
    print("=" * 50)
    
    tests = [
        test_monitor_imports,
        test_monitor_initialization,
        test_monitor_singleton,
        test_prediction_record,
        test_monitor_validation,
        test_constants
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
        print("🎉 Monitor integration successful!")
        return True
    else:
        print("⚠️  Some integration tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)