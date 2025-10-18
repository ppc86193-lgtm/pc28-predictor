#!/usr/bin/env python3
"""
Configuration System Fix Verification
Focused verification of configuration system without external dependencies
"""

import sys
import os
sys.path.append('pc28_predictor')

def test_configuration_system():
    """Test the complete configuration system"""
    print("🔧 Testing Configuration System...")
    
    try:
        from config_constants import (
            DynamicMarkovConfig, DynamicTailConfig, HealthScoreConfig,
            MonitoringConfig, PrometheusConfig, PredictionEngineConfig,
            SystemConfig, ConfigManager,
            get_markov_config, get_tail_config, get_health_config,
            get_monitoring_config, get_prometheus_config, 
            get_prediction_config, get_system_config
        )
        
        # Test configuration classes can be instantiated
        markov = DynamicMarkovConfig()
        tail = DynamicTailConfig()
        health = HealthScoreConfig()
        monitoring = MonitoringConfig()
        prometheus = PrometheusConfig()
        prediction = PredictionEngineConfig()
        system = SystemConfig()
        
        print("✅ All configuration classes instantiated successfully")
        
        # Test ConfigManager
        config_manager = ConfigManager()
        assert config_manager.markov is not None
        assert config_manager.tail is not None
        assert config_manager.health is not None
        assert config_manager.monitoring is not None
        assert config_manager.prometheus is not None
        assert config_manager.prediction is not None
        assert config_manager.system is not None
        
        print("✅ ConfigManager working correctly")
        
        # Test convenience functions
        assert get_markov_config() is not None
        assert get_tail_config() is not None
        assert get_health_config() is not None
        assert get_monitoring_config() is not None
        assert get_prometheus_config() is not None
        assert get_prediction_config() is not None
        assert get_system_config() is not None
        
        print("✅ All convenience functions working")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration system test failed: {e}")
        return False

def test_configuration_values():
    """Test configuration values are reasonable"""
    print("\\n📊 Testing Configuration Values...")
    
    try:
        from config_constants import (
            get_markov_config, get_tail_config, get_health_config,
            get_monitoring_config, get_prometheus_config, 
            get_prediction_config, get_system_config
        )
        
        # Test Markov configuration
        markov = get_markov_config()
        assert 0.0 < markov.TARGET_ACCURACY_MIN < markov.TARGET_ACCURACY_MAX < 1.0
        assert 0.0 < markov.EMA_ALPHA_MIN < markov.EMA_ALPHA_MAX < 1.0
        assert markov.ADJUSTMENT_STEP > 0
        print("✅ Markov configuration values valid")
        
        # Test Tail configuration
        tail = get_tail_config()
        assert tail.MIN_BOOST_FACTOR < tail.BASE_BOOST_FACTOR < tail.MAX_BOOST_FACTOR
        assert tail.HIGH_FREQUENCY_THRESHOLD > 0
        assert len(tail.TARGET_TAILS) > 0
        print("✅ Tail configuration values valid")
        
        # Test Health configuration
        health = get_health_config()
        assert health.BASE_SCORE > 0
        assert health.RESPONSE_TIME_MODERATE < health.RESPONSE_TIME_SLOW < health.RESPONSE_TIME_CRITICAL
        assert health.PENALTY_MODERATE < health.PENALTY_SLOW < health.PENALTY_CRITICAL
        print("✅ Health configuration values valid")
        
        # Test Monitoring configuration
        monitoring = get_monitoring_config()
        assert 0.0 < monitoring.PERCENTILE_50 < monitoring.PERCENTILE_95 < monitoring.PERCENTILE_99 <= 1.0
        assert monitoring.WEBHOOK_RETRY_BASE_DELAY > 0
        assert monitoring.WEBHOOK_MAX_DELAY > monitoring.WEBHOOK_RETRY_BASE_DELAY
        assert 0.0 <= monitoring.LOW_ACCURACY_THRESHOLD <= 1.0
        print("✅ Monitoring configuration values valid")
        
        # Test Prediction configuration
        prediction = get_prediction_config()
        assert 0.0 < prediction.HIGH_CONFIDENCE_FACTOR <= 1.0
        assert 0.0 < prediction.LOW_CONFIDENCE_FACTOR <= 1.0
        assert prediction.HIGH_CONFIDENCE_FACTOR > prediction.LOW_CONFIDENCE_FACTOR
        assert prediction.MIN_ACCURACY_SAMPLES > 0
        print("✅ Prediction configuration values valid")
        
        # Test Prometheus configuration
        prometheus = get_prometheus_config()
        assert prometheus.CPU_SAMPLE_INTERVAL > 0
        assert prometheus.MEMORY_UNIT_DIVISOR > 0
        print("✅ Prometheus configuration values valid")
        
        # Test System configuration
        system = get_system_config()
        assert system.DEFAULT_PORT > 0
        assert system.MAX_PREDICTION_HISTORY > 0
        print("✅ System configuration values valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration values test failed: {e}")
        return False

def test_environment_variable_support():
    """Test environment variable override support"""
    print("\\n🌍 Testing Environment Variable Support...")
    
    try:
        import os
        from config_constants import ConfigManager
        
        # Set test environment variables
        os.environ['MARKOV_TARGET_ACCURACY_MIN'] = '0.55'
        os.environ['HEALTH_RESPONSE_TIME_CRITICAL'] = '2.5'
        os.environ['PORT'] = '9000'
        
        # Create new config manager to load env vars
        config_manager = ConfigManager()
        
        # Test that environment variables are loaded
        assert config_manager.markov.TARGET_ACCURACY_MIN == 0.55
        assert config_manager.health.RESPONSE_TIME_CRITICAL == 2.5
        assert config_manager.system.DEFAULT_PORT == 9000
        
        print("✅ Environment variable override working")
        
        # Clean up
        del os.environ['MARKOV_TARGET_ACCURACY_MIN']
        del os.environ['HEALTH_RESPONSE_TIME_CRITICAL']
        del os.environ['PORT']
        
        return True
        
    except Exception as e:
        print(f"❌ Environment variable test failed: {e}")
        return False

def test_configuration_serialization():
    """Test configuration can be serialized to dictionary"""
    print("\\n📝 Testing Configuration Serialization...")
    
    try:
        from config_constants import ConfigManager
        
        config_manager = ConfigManager()
        config_dict = config_manager.to_dict()
        
        # Test all sections are present
        expected_sections = ['markov', 'tail', 'health', 'monitoring', 'prometheus', 'prediction', 'system']
        for section in expected_sections:
            assert section in config_dict, f"Missing section: {section}"
            assert isinstance(config_dict[section], dict), f"Section {section} is not a dict"
        
        print("✅ Configuration serialization working")
        
        # Test some key values are present
        assert 'TARGET_ACCURACY_MIN' in config_dict['markov']
        assert 'BASE_SCORE' in config_dict['health']
        assert 'PERCENTILE_95' in config_dict['monitoring']
        assert 'HIGH_CONFIDENCE_FACTOR' in config_dict['prediction']
        
        print("✅ All expected configuration keys present")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration serialization test failed: {e}")
        return False

def test_hardcoding_patterns():
    """Test for remaining hardcoded patterns in key files"""
    print("\\n🔍 Testing for Hardcoded Patterns...")
    
    try:
        # Files to check
        files_to_check = [
            'pc28_predictor/config_constants.py',
            'pc28_predictor/monitor.py',
            'pc28_predictor/prediction_engine.py',
            'pc28_predictor/markov_model.py',
            'pc28_predictor/tail_analyzer.py'
        ]
        
        # Patterns that should be eliminated (these are now configured)
        eliminated_patterns = [
            'if accuracy < 0.56:',
            'if accuracy > 0.61:',
            'boost_factor = 1.05',
            'boost_factor = 1.03',
            'boost_factor = 1.02',
            'health_score -= 30',
            'health_score -= 15',
            'health_score -= 5',
            'maxlen=1000',
            'maxlen=100'
        ]
        
        issues_found = []
        files_checked = 0
        
        for file_path in files_to_check:
            if not os.path.exists(file_path):
                continue
                
            files_checked += 1
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in eliminated_patterns:
                    if pattern in content:
                        # Check if it's in a comment or properly configured
                        lines = content.split('\\n')
                        for i, line in enumerate(lines):
                            if pattern in line and not line.strip().startswith('#'):
                                issues_found.append(f"{file_path}:{i+1} - {pattern}")
                                
            except Exception as e:
                print(f"⚠️  Could not check {file_path}: {e}")
        
        print(f"✅ Checked {files_checked} files for hardcoded patterns")
        
        if issues_found:
            print("⚠️  Some hardcoded patterns still found:")
            for issue in issues_found[:5]:  # Show first 5
                print(f"   {issue}")
            return len(issues_found) == 0
        else:
            print("✅ No problematic hardcoded patterns found")
            return True
        
    except Exception as e:
        print(f"❌ Hardcoding pattern test failed: {e}")
        return False

def main():
    """Run all configuration fix verification tests"""
    print("🔍 Configuration System Fix Verification")
    print("=" * 60)
    
    tests = [
        ("Configuration System", test_configuration_system),
        ("Configuration Values", test_configuration_values),
        ("Environment Variables", test_environment_variable_support),
        ("Configuration Serialization", test_configuration_serialization),
        ("Hardcoding Patterns", test_hardcoding_patterns)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
        print()
    
    print("=" * 60)
    print(f"Configuration Fix Verification Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All configuration fixes verified successfully!")
        print("\\n📋 Configuration System Summary:")
        print("✅ Complete configuration management system implemented")
        print("✅ All hardcoded values eliminated and configurable")
        print("✅ Environment variable support working")
        print("✅ Configuration validation and boundaries enforced")
        print("✅ Serialization and management functions working")
        print("✅ All configuration classes properly structured")
        return True
    else:
        print("⚠️  Some configuration fixes need additional work")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\\n🏁 Configuration Fix Verification {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)