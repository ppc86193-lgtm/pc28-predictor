"""
Test suite for prediction system integration
Phase 5: Prediction System Integration Tests
"""

import pytest
import json
import time
from unittest.mock import patch, MagicMock
from datetime import datetime

from prediction_engine import (
    PC28PredictionEngine, PredictionConfig, get_prediction_engine
)
from api_client import PC28Data, PredictionResult

class TestPredictionConfig:
    """Test prediction configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = PredictionConfig()
        
        assert config.tail_window == 16
        assert config.markov_min_count == 5
        assert config.ema_periods == 5
        assert config.confidence_threshold == 0.05
        assert config.accuracy_window == 100
        assert config.cache_ttl == 10
        assert len(config.states) == 5
        assert "大单" in config.states
        assert "极值" in config.states
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = PredictionConfig(
            tail_window=32,
            markov_min_count=10,
            states=["大单", "小双", "小单", "大双"]
        )
        
        assert config.tail_window == 32
        assert config.markov_min_count == 10
        assert len(config.states) == 4
        assert "极值" not in config.states

class TestPC28PredictionEngine:
    """Test main prediction engine"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.config = PredictionConfig(cache_ttl=1)  # Short TTL for testing
        self.engine = PC28PredictionEngine(self.config)
    
    @patch('prediction_engine.fetch_realtime_data')
    @patch('prediction_engine.fetch_history_data')
    @patch('prediction_engine.process_features')
    def test_fetch_and_process_data(self, mock_process, mock_history, mock_realtime):
        """Test data fetching and processing"""
        # Mock API responses
        mock_realtime.return_value = {"retdata": [{"number": [5, 5, 5], "period": "test1"}]}
        mock_history.return_value = {"retdata": [{"number": [7, 3, 4], "period": "test2"}]}
        
        # Mock processed features
        mock_process.side_effect = [
            [PC28Data(sum=15, tail=5, combination="大单", period="test1")],
            [PC28Data(sum=14, tail=4, combination="大双", period="test2")]
        ]
        
        features = self.engine._fetch_and_process_data()
        
        assert len(features) == 2
        assert features[0].sum == 14  # History first
        assert features[1].sum == 15  # Then realtime
        
        # Verify API calls
        mock_realtime.assert_called_once()
        mock_history.assert_called_once()
        assert mock_process.call_count == 2
    
    def test_analyze_tail_frequency(self):
        """Test tail frequency analysis"""
        features = [
            PC28Data(sum=15, tail=5, combination="大单"),
            PC28Data(sum=12, tail=2, combination="小双"),
            PC28Data(sum=17, tail=7, combination="大单"),
            PC28Data(sum=10, tail=0, combination="小双")
        ]
        
        analysis = self.engine._analyze_tail_frequency(features)
        
        assert "frequencies" in analysis
        assert "p_value" in analysis
        assert "statistics" in analysis
        assert "prediction_weights" in analysis
        assert "is_significant" in analysis
        
        # Check frequency structure
        assert len(analysis["frequencies"]) == 10
        assert all(0 <= freq <= 1 for freq in analysis["frequencies"].values())
    
    def test_generate_markov_prediction(self):
        """Test Markov chain prediction generation"""
        features = [
            PC28Data(sum=15, tail=5, combination="大单"),
            PC28Data(sum=12, tail=2, combination="小双"),
            PC28Data(sum=17, tail=7, combination="大单"),
            PC28Data(sum=14, tail=4, combination="大双")
        ]
        
        prediction = self.engine._generate_markov_prediction(features)
        
        assert len(prediction) == len(self.config.states)
        assert abs(sum(prediction.values()) - 1.0) < 1e-10
        assert all(0 <= prob <= 1 for prob in prediction.values())
    
    def test_combine_predictions(self):
        """Test prediction combination logic"""
        markov_probs = {"大单": 0.4, "小双": 0.3, "小单": 0.2, "大双": 0.1, "极值": 0.0}
        tail_analysis = {
            "frequencies": {7: 0.2, 8: 0.1, 9: 0.15},
            "prediction_weights": {"大单": 0.3, "小双": 0.25, "小单": 0.25, "大双": 0.2, "极值": 0.0},
            "is_significant": True
        }
        
        combined = self.engine._combine_predictions(markov_probs, tail_analysis)
        
        assert len(combined) == len(self.config.states)
        assert abs(sum(combined.values()) - 1.0) < 1e-10
        assert all(0 <= prob <= 1 for prob in combined.values())
    
    def test_finalize_prediction(self):
        """Test prediction finalization"""
        probabilities = {"大单": 0.4, "小双": 0.3, "小单": 0.2, "大双": 0.1, "极值": 0.0}
        tail_analysis = {"is_significant": True}
        
        # Set some accuracy history
        self.engine.accuracy_history = [1] * 15 + [0] * 5  # 75% accuracy
        
        result = self.engine._finalize_prediction(probabilities, tail_analysis)
        
        assert isinstance(result, PredictionResult)
        assert result.combination == "大单"  # Highest probability
        assert 0.5 <= result.confidence <= 1.0
        assert result.sum_range in ["0-9", "10-13", "14-17", "18-27"]
        assert len(result.probabilities) == len(self.config.states)
    
    def test_predict_sum_range(self):
        """Test sum range prediction"""
        # Test different probability distributions
        test_cases = [
            ({"大单": 0.5, "小双": 0.2, "小单": 0.2, "大双": 0.1, "极值": 0.0}, "14-17"),
            ({"大单": 0.2, "小双": 0.5, "小单": 0.2, "大双": 0.1, "极值": 0.0}, "10-13"),
            ({"大单": 0.1, "小双": 0.1, "小单": 0.1, "大双": 0.1, "极值": 0.6}, "18-27")
        ]
        
        for probs, expected_range in test_cases:
            result = self.engine._predict_sum_range(probs)
            assert result == expected_range
    
    def test_create_fallback_prediction(self):
        """Test fallback prediction creation"""
        fallback = self.engine._create_fallback_prediction()
        
        assert isinstance(fallback, PredictionResult)
        assert fallback.combination == "大单"
        assert fallback.confidence == 0.5
        assert fallback.sum_range == "10-17"
        assert len(fallback.probabilities) == len(self.config.states)
    
    @patch('prediction_engine.redis_client')
    def test_cache_operations(self, mock_redis):
        """Test caching operations"""
        # Test cache storage
        prediction = PredictionResult(
            sum_range="14-17",
            combination="大单",
            probabilities={"大单": 0.4, "小双": 0.3, "小单": 0.2, "大双": 0.1, "极值": 0.0},
            confidence=0.75,
            timestamp=datetime.now()
        )
        
        self.engine._cache_prediction(prediction)
        mock_redis.setex.assert_called_once()
        
        # Test cache retrieval
        mock_redis.get.return_value = json.dumps({
            'sum_range': '14-17',
            'combination': '大单',
            'probabilities': {"大单": 0.4, "小双": 0.3, "小单": 0.2, "大双": 0.1, "极值": 0.0},
            'confidence': 0.75,
            'timestamp': datetime.now().isoformat()
        })
        
        cached = self.engine._get_cached_prediction()
        assert cached is not None
        assert cached.combination == "大单"
        assert cached.confidence == 0.75
    
    def test_update_accuracy(self):
        """Test accuracy tracking"""
        # Test correct prediction
        accuracy = self.engine.update_accuracy("大单", "大单")
        assert accuracy >= 0.5  # Should be at least 50% for correct prediction
        
        # Test incorrect prediction
        accuracy = self.engine.update_accuracy("大单", "小双")
        assert len(self.engine.accuracy_history) == 2
        
        # Test accuracy calculation with more data
        for i in range(20):
            predicted = "大单" if i % 2 == 0 else "小双"
            actual = "大单" if i % 3 == 0 else "小双"
            self.engine.update_accuracy(predicted, actual)
        
        assert len(self.engine.accuracy_history) == 22
        final_accuracy = sum(self.engine.accuracy_history) / len(self.engine.accuracy_history)
        assert 0.0 <= final_accuracy <= 1.0
    
    def test_get_performance_metrics(self):
        """Test performance metrics calculation"""
        # Add some accuracy history
        self.engine.accuracy_history = [1] * 60 + [0] * 40  # 60% accuracy
        
        metrics = self.engine.get_performance_metrics()
        
        assert "total_predictions" in metrics
        assert "overall_accuracy" in metrics
        assert "recent_accuracy" in metrics
        assert "accuracy_trend" in metrics
        assert "last_updated" in metrics
        
        assert metrics["total_predictions"] == 100
        assert abs(metrics["overall_accuracy"] - 0.6) < 0.01
    
    def test_reset_performance_data(self):
        """Test performance data reset"""
        # Add some data
        self.engine.accuracy_history = [1, 0, 1, 0]
        self.engine.prediction_history = [{"test": "data"}]
        
        self.engine.reset_performance_data()
        
        assert len(self.engine.accuracy_history) == 0
        assert len(self.engine.prediction_history) == 0
        assert len(self.engine.performance_metrics) == 0

class TestIntegration:
    """Integration tests for the complete prediction system"""
    
    @patch('prediction_engine.fetch_realtime_data')
    @patch('prediction_engine.fetch_history_data')
    @patch('prediction_engine.process_features')
    def test_full_prediction_workflow(self, mock_process, mock_history, mock_realtime):
        """Test complete prediction workflow"""
        # Setup mocks
        mock_realtime.return_value = {"retdata": [{"number": [5, 5, 5], "period": "test1"}]}
        mock_history.return_value = {"retdata": [
            {"number": [7, 3, 4], "period": "test2"},
            {"number": [2, 2, 2], "period": "test3"},
            {"number": [8, 8, 8], "period": "test4"}
        ]}
        
        mock_process.side_effect = [
            [PC28Data(sum=15, tail=5, combination="大单", period="test1")],
            [
                PC28Data(sum=14, tail=4, combination="大双", period="test2"),
                PC28Data(sum=6, tail=6, combination="极值", period="test3"),
                PC28Data(sum=24, tail=4, combination="极值", period="test4")
            ]
        ]
        
        # Create engine and generate prediction
        engine = PC28PredictionEngine(PredictionConfig(cache_ttl=0))  # No caching for test
        prediction = engine.generate_prediction(use_cache=False)
        
        # Verify prediction structure
        assert isinstance(prediction, PredictionResult)
        assert prediction.combination in ["大单", "小双", "小单", "大双", "极值"]
        assert 0.0 <= prediction.confidence <= 1.0
        assert prediction.sum_range in ["0-9", "10-13", "14-17", "18-27"]
        assert len(prediction.probabilities) == 5
        assert abs(sum(prediction.probabilities.values()) - 1.0) < 1e-10
    
    def test_singleton_engine(self):
        """Test singleton pattern for prediction engine"""
        engine1 = get_prediction_engine()
        engine2 = get_prediction_engine()
        
        assert engine1 is engine2  # Should be the same instance
    
    @patch('prediction_engine.fetch_realtime_data')
    @patch('prediction_engine.fetch_history_data')
    def test_error_handling(self, mock_history, mock_realtime):
        """Test error handling in prediction workflow"""
        # Test API failure
        mock_realtime.side_effect = Exception("API Error")
        mock_history.side_effect = Exception("API Error")
        
        engine = PC28PredictionEngine()
        prediction = engine.generate_prediction(use_cache=False)
        
        # Should return fallback prediction
        assert isinstance(prediction, PredictionResult)
        assert prediction.confidence == 0.5  # Fallback confidence
    
    def test_performance_under_load(self):
        """Test prediction performance with large datasets"""
        # Create large feature dataset
        features = []
        for i in range(1000):
            sum_val = 10 + (i % 18)
            combination = ["大单", "小双", "小单", "大双", "极值"][i % 5]
            features.append(PC28Data(
                sum=sum_val,
                tail=sum_val % 10,
                combination=combination,
                period=f"test_{i}"
            ))
        
        engine = PC28PredictionEngine()
        
        # Test tail analysis performance
        start_time = time.time()
        tail_analysis = engine._analyze_tail_frequency(features)
        tail_time = time.time() - start_time
        
        # Test Markov prediction performance
        start_time = time.time()
        markov_prediction = engine._generate_markov_prediction(features)
        markov_time = time.time() - start_time
        
        # Verify performance (should complete within reasonable time)
        assert tail_time < 2.0  # Should complete within 2 seconds
        assert markov_time < 2.0  # Should complete within 2 seconds
        
        # Verify results
        assert len(tail_analysis["frequencies"]) == 10
        assert len(markov_prediction) == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])