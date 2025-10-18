"""
Test suite for Phase 6 Task 2: Algorithm Optimization
Dynamic EMA weights and tail frequency adjustments
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from markov_model import DynamicMarkovModel, calculate_ema_weights
from tail_analyzer import DynamicTailAnalyzer, adjust_probs_by_tail

class TestDynamicMarkovModel:
    """Test dynamic Markov model with adaptive EMA weights"""
    
    def setup_method(self):
        """Setup for each test"""
        self.model = DynamicMarkovModel(initial_ema_alpha=0.3)
    
    def test_initialization(self):
        """Test model initialization"""
        assert 0.1 <= self.model.ema_alpha <= 0.9
        assert self.model.min_ema_alpha == 0.1
        assert self.model.max_ema_alpha == 0.9
        assert self.model.adjustment_step == 0.01
        assert len(self.model.accuracy_history) == 0
    
    def test_update_ema_weights_low_accuracy(self):
        """Test EMA weight adjustment for low accuracy"""
        initial_alpha = self.model.ema_alpha
        
        # Low accuracy should increase alpha (more responsive)
        self.model.update_ema_weights(0.50)  # Below 0.56 target
        assert self.model.ema_alpha > initial_alpha
        
        # Multiple low accuracy updates
        for _ in range(10):
            self.model.update_ema_weights(0.45)
        
        # Should not exceed maximum
        assert self.model.ema_alpha <= self.model.max_ema_alpha
    
    def test_update_ema_weights_high_accuracy(self):
        """Test EMA weight adjustment for high accuracy"""
        # Start with higher alpha
        self.model.ema_alpha = 0.7
        initial_alpha = self.model.ema_alpha
        
        # High accuracy should decrease alpha (less responsive)
        self.model.update_ema_weights(0.65)  # Above 0.61 target
        assert self.model.ema_alpha < initial_alpha
        
        # Multiple high accuracy updates
        for _ in range(20):
            self.model.update_ema_weights(0.70)
        
        # Should not go below minimum
        assert self.model.ema_alpha >= self.model.min_ema_alpha
    
    def test_update_ema_weights_optimal_range(self):
        """Test EMA weight stability in optimal accuracy range"""
        initial_alpha = self.model.ema_alpha
        
        # Accuracy in optimal range (0.56-0.61) should not change alpha
        self.model.update_ema_weights(0.58)
        assert self.model.ema_alpha == initial_alpha
        
        self.model.update_ema_weights(0.60)
        assert self.model.ema_alpha == initial_alpha
    
    def test_update_ema_weights_invalid_input(self):
        """Test EMA weight update with invalid input"""
        initial_alpha = self.model.ema_alpha
        
        # Invalid accuracy values should not change alpha
        self.model.update_ema_weights(-0.1)
        assert self.model.ema_alpha == initial_alpha
        
        self.model.update_ema_weights(1.5)
        assert self.model.ema_alpha == initial_alpha
        
        self.model.update_ema_weights("invalid")
        assert self.model.ema_alpha == initial_alpha
    
    def test_get_dynamic_ema_weights(self):
        """Test dynamic EMA weight calculation"""
        # Test with different alpha values
        self.model.ema_alpha = 0.3
        weights = self.model.get_dynamic_ema_weights(5)
        
        assert len(weights) == 5
        assert abs(weights.sum() - 1.0) < 1e-10  # Should sum to 1
        assert all(w >= 0 for w in weights)  # All weights positive
        assert weights[0] > weights[-1]  # Decreasing weights
    
    def test_get_optimization_stats(self):
        """Test optimization statistics"""
        # Test with no history
        stats = self.model.get_optimization_stats()
        assert stats["accuracy_samples"] == 0
        assert stats["avg_accuracy"] == 0.0
        assert stats["ema_stability"] == "no_data"
        
        # Add some accuracy history
        accuracies = [0.55, 0.58, 0.52, 0.60, 0.57]
        for acc in accuracies:
            self.model.update_ema_weights(acc)
        
        stats = self.model.get_optimization_stats()
        assert stats["accuracy_samples"] == len(accuracies)
        assert 0.0 <= stats["avg_accuracy"] <= 1.0
        assert stats["ema_stability"] in ["stable", "adjusting"]

class TestDynamicTailAnalyzer:
    """Test dynamic tail analyzer with adaptive probability adjustments"""
    
    def setup_method(self):
        """Setup for each test"""
        self.analyzer = DynamicTailAnalyzer()
    
    def test_initialization(self):
        """Test analyzer initialization"""
        assert self.analyzer.base_tail_factor == 0.03
        assert self.analyzer.max_boost_factor == 1.07
        assert self.analyzer.min_boost_factor == 1.01
        assert self.analyzer.target_tails == [7, 8, 9]
        assert len(self.analyzer.accuracy_history) == 0
    
    def test_adjust_probs_by_tail_dynamic_low_accuracy(self):
        """Test probability adjustment for low accuracy"""
        probs = {"大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25}
        tail_freq = {7: 0.16, 8: 0.17, 9: 0.18}  # High frequency tails (>0.15)
        
        adjusted = self.analyzer.adjust_probs_by_tail_dynamic(probs, tail_freq, 0.50)
        
        # Should boost odd combinations for tails 7, 9
        assert adjusted["大单"] > probs["大单"]
        assert adjusted["小单"] > probs["小单"]
        
        # Probabilities should sum to 1
        assert abs(sum(adjusted.values()) - 1.0) < 1e-10
    
    def test_adjust_probs_by_tail_dynamic_high_accuracy(self):
        """Test probability adjustment for high accuracy"""
        probs = {"大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25}
        tail_freq = {0: 0.16, 2: 0.17, 8: 0.18}  # High frequency even tails (>0.15)
        
        adjusted = self.analyzer.adjust_probs_by_tail_dynamic(probs, tail_freq, 0.70)
        
        # Should boost even combinations for tails 0, 2, 8
        assert adjusted["小双"] > probs["小双"]
        assert adjusted["大双"] > probs["大双"]
        
        # Probabilities should sum to 1
        assert abs(sum(adjusted.values()) - 1.0) < 1e-10
    
    def test_adjust_probs_by_tail_dynamic_optimal_accuracy(self):
        """Test probability adjustment for optimal accuracy range"""
        probs = {"大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25}
        tail_freq = {7: 0.16, 9: 0.17}  # High frequency target tails (7,9 in target_tails)
        
        adjusted = self.analyzer.adjust_probs_by_tail_dynamic(probs, tail_freq, 0.58)
        
        # Should apply moderate adjustments for target tails
        assert adjusted != probs  # Some adjustment should occur
        assert abs(sum(adjusted.values()) - 1.0) < 1e-10
    
    def test_adjust_probs_by_tail_dynamic_invalid_input(self):
        """Test probability adjustment with invalid input"""
        probs = {"大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25}
        tail_freq = {7: 0.13}
        
        # Invalid accuracy should return original probabilities
        result = self.analyzer.adjust_probs_by_tail_dynamic(probs, tail_freq, -0.1)
        assert result == probs
        
        result = self.analyzer.adjust_probs_by_tail_dynamic(probs, tail_freq, 1.5)
        assert result == probs
        
        # Empty inputs should return original probabilities
        result = self.analyzer.adjust_probs_by_tail_dynamic({}, tail_freq, 0.5)
        assert result == {}
        
        result = self.analyzer.adjust_probs_by_tail_dynamic(probs, {}, 0.5)
        assert result == probs
    
    def test_tail_matches_combination(self):
        """Test tail-combination matching logic"""
        # Odd tails (7, 9) should match odd combinations (单)
        assert self.analyzer._tail_matches_combination(7, "大单") == True
        assert self.analyzer._tail_matches_combination(9, "小单") == True
        assert self.analyzer._tail_matches_combination(7, "大双") == False
        
        # Even tails (0, 2, 8) should match even combinations (双)
        assert self.analyzer._tail_matches_combination(0, "小双") == True
        assert self.analyzer._tail_matches_combination(8, "大双") == True
        assert self.analyzer._tail_matches_combination(2, "大单") == False
        
        # Other tails should not match
        assert self.analyzer._tail_matches_combination(5, "大单") == False
        assert self.analyzer._tail_matches_combination(3, "小双") == False
    
    def test_get_tail_optimization_stats(self):
        """Test tail optimization statistics"""
        # Test with no history
        stats = self.analyzer.get_tail_optimization_stats()
        assert stats["accuracy_samples"] == 0
        assert stats["avg_accuracy"] == 0.0
        assert stats["target_tails"] == [7, 8, 9]
        
        # Add some accuracy history
        probs = {"大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25}
        tail_freq = {7: 0.13}
        
        accuracies = [0.55, 0.58, 0.52, 0.60, 0.57]
        for acc in accuracies:
            self.analyzer.adjust_probs_by_tail_dynamic(probs, tail_freq, acc)
        
        stats = self.analyzer.get_tail_optimization_stats()
        assert stats["accuracy_samples"] == len(accuracies)
        assert 0.0 <= stats["avg_accuracy"] <= 1.0
        assert 1.0 <= stats["current_boost_factor"] <= 1.1

class TestLegacyCompatibility:
    """Test backward compatibility with legacy functions"""
    
    def test_calculate_ema_weights_legacy(self):
        """Test legacy EMA weight calculation"""
        weights = calculate_ema_weights(5)
        assert len(weights) == 5
        assert abs(weights.sum() - 1.0) < 1e-10
        assert all(w >= 0 for w in weights)
    
    def test_adjust_probs_by_tail_legacy(self):
        """Test legacy tail probability adjustment"""
        probs = {"大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25}
        tail_freq = {7: 0.13, 8: 0.11}
        accuracy_history = [1] * 60 + [0] * 40  # 60% accuracy
        
        adjusted = adjust_probs_by_tail(probs, tail_freq, accuracy_history)
        
        # Should return some adjustment (exact behavior depends on implementation)
        assert isinstance(adjusted, dict)
        assert len(adjusted) == len(probs)

class TestIntegrationOptimization:
    """Integration tests for algorithm optimization"""
    
    def test_combined_optimization_cycle(self):
        """Test combined EMA and tail optimization"""
        # Initialize components
        markov_model = DynamicMarkovModel(0.3)
        tail_analyzer = DynamicTailAnalyzer()
        
        # Simulate optimization cycle
        probs = {"大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25}
        tail_freq = {7: 0.13, 8: 0.11, 9: 0.12}
        
        # Test with different accuracy scenarios
        test_accuracies = [0.45, 0.52, 0.58, 0.63, 0.70]
        
        for accuracy in test_accuracies:
            # Update EMA weights
            markov_model.update_ema_weights(accuracy)
            
            # Adjust tail probabilities
            adjusted_probs = tail_analyzer.adjust_probs_by_tail_dynamic(
                probs, tail_freq, accuracy
            )
            
            # Get dynamic EMA weights
            ema_weights = markov_model.get_dynamic_ema_weights(5)
            
            # Verify results
            assert 0.1 <= markov_model.ema_alpha <= 0.9
            assert abs(sum(adjusted_probs.values()) - 1.0) < 1e-10
            assert abs(ema_weights.sum() - 1.0) < 1e-10
        
        # Check optimization statistics
        markov_stats = markov_model.get_optimization_stats()
        tail_stats = tail_analyzer.get_tail_optimization_stats()
        
        assert markov_stats["accuracy_samples"] == len(test_accuracies)
        assert tail_stats["accuracy_samples"] == len(test_accuracies)
    
    def test_performance_under_load(self):
        """Test optimization performance with many updates"""
        markov_model = DynamicMarkovModel(0.3)
        tail_analyzer = DynamicTailAnalyzer()
        
        probs = {"大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25}
        tail_freq = {7: 0.13, 8: 0.11}
        
        # Simulate 1000 optimization cycles
        import time
        start_time = time.time()
        
        for i in range(1000):
            accuracy = 0.5 + 0.1 * (i % 10) / 10  # Varying accuracy
            markov_model.update_ema_weights(accuracy)
            tail_analyzer.adjust_probs_by_tail_dynamic(probs, tail_freq, accuracy)
        
        end_time = time.time()
        
        # Should complete within reasonable time (< 1 second)
        assert end_time - start_time < 1.0
        
        # Memory should be bounded
        assert len(markov_model.accuracy_history) <= 100
        assert len(tail_analyzer.accuracy_history) <= 100

if __name__ == "__main__":
    pytest.main([__file__, "-v"])