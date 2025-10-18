"""
Test suite for statistical engines (Markov chain and tail analysis)
Phase 4: Statistical Engines Implementation
"""

import pytest
import numpy as np
from unittest.mock import patch
from collections import Counter

from tail_analyzer import (
    analyze_tail_frequency,
    adjust_probs_by_tail,
    calculate_tail_statistics,
    get_tail_prediction_weights
)

from markov_model import (
    build_markov_2nd_order_matrix,
    predict_combination,
    calculate_ema_weights,
    calculate_streak_adjustments,
    analyze_markov_performance,
    optimize_markov_parameters
)

class TestTailAnalyzer:
    """Test tail frequency analysis functions"""
    
    def test_analyze_tail_frequency_basic(self):
        """Test basic tail frequency analysis"""
        # Create test data with known tail distribution
        features = [
            {"tail": i % 10} for i in range(100)
        ]  # Uniform distribution
        
        freq_dist, p_value = analyze_tail_frequency(features, window=100)
        
        # Should be approximately uniform
        assert len(freq_dist) == 10
        for freq in freq_dist.values():
            assert 0.08 <= freq <= 0.12  # Allow some variance
        
        # P-value should be high (not significant)
        assert p_value > 0.05
    
    def test_analyze_tail_frequency_biased(self):
        """Test tail frequency analysis with biased data"""
        # Create biased data (tail 7 appears 50% of the time)
        features = []
        for i in range(100):
            if i < 50:
                features.append({"tail": 7})
            else:
                features.append({"tail": i % 9})  # Exclude 7 from remaining
        
        freq_dist, p_value = analyze_tail_frequency(features, window=100)
        
        # Tail 7 should have high frequency
        assert freq_dist[7] >= 0.4
        
        # Should be statistically significant
        assert p_value < 0.05
    
    def test_analyze_tail_frequency_insufficient_data(self):
        """Test with insufficient data"""
        features = [{"tail": 1}, {"tail": 2}]  # Only 2 features
        
        freq_dist, p_value = analyze_tail_frequency(features, window=16)
        
        # Should return uniform distribution
        assert all(freq == 0.1 for freq in freq_dist.values())
        assert p_value == 1.0
    
    def test_analyze_tail_frequency_invalid_format(self):
        """Test with invalid feature format"""
        features = [
            {"tail": 1},
            {"invalid": "data"},
            {"tail": 2}
        ]
        
        freq_dist, p_value = analyze_tail_frequency(features, window=10)
        
        # Should handle invalid data gracefully
        assert isinstance(freq_dist, dict)
        assert isinstance(p_value, float)
    
    def test_adjust_probs_by_tail_basic(self):
        """Test basic probability adjustment"""
        probs = {"大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25}
        tail_freq = {7: 0.2, 8: 0.05, 9: 0.15}  # High odd tails
        accuracy_history = [1] * 60 + [0] * 40  # 60% accuracy
        
        adjusted = adjust_probs_by_tail(probs, tail_freq, accuracy_history)
        
        # Odd combinations should be boosted
        assert adjusted["大单"] > probs["大单"]
        assert adjusted["小单"] > probs["小单"]
        
        # Probabilities should sum to 1
        assert abs(sum(adjusted.values()) - 1.0) < 1e-10
    
    def test_adjust_probs_by_tail_even_bias(self):
        """Test probability adjustment with even tail bias"""
        probs = {"大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25}
        tail_freq = {0: 0.2, 2: 0.18, 8: 0.16}  # High even tails
        accuracy_history = [1] * 55 + [0] * 45  # 55% accuracy
        
        adjusted = adjust_probs_by_tail(probs, tail_freq, accuracy_history)
        
        # Even combinations should be boosted
        assert adjusted["小双"] > probs["小双"]
        assert adjusted["大双"] > probs["大双"]
    
    def test_calculate_tail_statistics(self):
        """Test comprehensive tail statistics calculation"""
        features = [{"tail": i % 10} for i in range(200)]
        
        stats = calculate_tail_statistics(features, window_sizes=[16, 50, 100])
        
        assert "window_16" in stats
        assert "window_50" in stats
        assert "window_100" in stats
        
        for window_key in stats:
            window_stats = stats[window_key]
            assert "frequencies" in window_stats
            assert "p_value" in window_stats
            assert "variance" in window_stats
            assert "is_significant" in window_stats
    
    def test_get_tail_prediction_weights(self):
        """Test tail-based prediction weight generation"""
        tail_stats = {
            "window_16": {
                "frequencies": {7: 0.2, 8: 0.05, 9: 0.15},
                "is_significant": True
            }
        }
        
        weights = get_tail_prediction_weights(tail_stats)
        
        assert len(weights) == 5
        assert all(isinstance(w, float) for w in weights.values())
        assert abs(sum(weights.values()) - 1.0) < 1e-10

class TestMarkovModel:
    """Test Markov chain model functions"""
    
    def test_calculate_ema_weights(self):
        """Test EMA weight calculation"""
        weights = calculate_ema_weights(5)
        
        assert len(weights) == 5
        assert abs(sum(weights) - 1.0) < 1e-10
        assert weights[0] > weights[1] > weights[2]  # Decreasing weights
    
    def test_build_markov_2nd_order_matrix_basic(self):
        """Test basic Markov matrix construction"""
        features = [
            {"combination": "大单"},
            {"combination": "小双"},
            {"combination": "大单"},
            {"combination": "小双"},
            {"combination": "大单"}
        ]
        
        matrix, states, state_pairs = build_markov_2nd_order_matrix(features)
        
        assert matrix.shape[0] == len(state_pairs)
        assert matrix.shape[1] == len(states)
        assert len(state_pairs) == len(states) ** 2
    
    def test_build_markov_2nd_order_matrix_insufficient_data(self):
        """Test Markov matrix with insufficient data"""
        features = [{"combination": "大单"}]  # Only 1 feature
        
        matrix, states, state_pairs = build_markov_2nd_order_matrix(features)
        
        # Should return uniform distribution
        assert matrix.shape[0] == len(state_pairs)
        assert matrix.shape[1] == len(states)
    
    def test_predict_combination_basic(self):
        """Test basic combination prediction"""
        features = [
            {"combination": "大单"},
            {"combination": "小双"},
            {"combination": "大单"},
            {"combination": "小双"}
        ]
        
        matrix, states, state_pairs = build_markov_2nd_order_matrix(features)
        probs = predict_combination(features, matrix, states, state_pairs, [])
        
        assert len(probs) == len(states)
        assert abs(sum(probs.values()) - 1.0) < 1e-10
        assert all(0 <= p <= 1 for p in probs.values())
    
    def test_predict_combination_insufficient_data(self):
        """Test prediction with insufficient data"""
        features = [{"combination": "大单"}]  # Only 1 feature
        
        matrix, states, state_pairs = build_markov_2nd_order_matrix(features)
        probs = predict_combination(features, matrix, states, state_pairs, [])
        
        # Should return uniform distribution
        expected_prob = 1.0 / len(states)
        for prob in probs.values():
            assert abs(prob - expected_prob) < 1e-10
    
    def test_predict_combination_with_accuracy_history(self):
        """Test prediction with accuracy history"""
        features = [
            {"combination": "大单", "sum": 15},
            {"combination": "小双", "sum": 10},
            {"combination": "大单", "sum": 17}
        ]
        accuracy_history = [1] * 70 + [0] * 30  # 70% accuracy
        
        matrix, states, state_pairs = build_markov_2nd_order_matrix(features)
        probs = predict_combination(features, matrix, states, state_pairs, accuracy_history)
        
        assert len(probs) == len(states)
        assert abs(sum(probs.values()) - 1.0) < 1e-10
    
    def test_predict_combination_extreme_values(self):
        """Test prediction with extreme sum values"""
        features = [
            {"combination": "极值", "sum": 3},
            {"combination": "大单", "sum": 15},
            {"combination": "极值", "sum": 25}
        ]
        
        matrix, states, state_pairs = build_markov_2nd_order_matrix(features)
        probs = predict_combination(features, matrix, states, state_pairs, [])
        
        # Extreme values should boost "极值" probability
        if "极值" in probs:
            assert probs["极值"] > 0.2  # Should be higher than uniform (0.2)
    
    def test_calculate_streak_adjustments(self):
        """Test streak adjustment calculations"""
        # Test three consecutive same states
        last_three = ["大单", "大单", "大单"]
        adjustments = calculate_streak_adjustments(last_three, 0.6)
        
        assert "大单" in adjustments
        assert adjustments["大单"] < 0  # Anti-streak bias
        
        # Test alternating pattern
        last_three = ["大单", "小双", "大单"]
        adjustments = calculate_streak_adjustments(last_three, 0.6)
        
        if "大单" in adjustments:
            assert adjustments["大单"] > 0  # Pattern continuation bias
    
    def test_analyze_markov_performance(self):
        """Test Markov performance analysis"""
        predictions = [
            {"大单": 0.4, "小双": 0.3, "小单": 0.2, "大双": 0.1},
            {"小双": 0.5, "大单": 0.3, "小单": 0.1, "大双": 0.1},
            {"大单": 0.6, "小双": 0.2, "小单": 0.1, "大双": 0.1}
        ]
        actual_outcomes = ["大单", "小双", "小单"]
        
        analysis = analyze_markov_performance([], predictions, actual_outcomes)
        
        assert "overall_accuracy" in analysis
        assert "total_predictions" in analysis
        assert "state_accuracies" in analysis
        assert analysis["total_predictions"] == 3
        assert 0 <= analysis["overall_accuracy"] <= 1
    
    def test_analyze_markov_performance_invalid_input(self):
        """Test performance analysis with invalid input"""
        analysis = analyze_markov_performance([], [], ["outcome"])
        
        assert "error" in analysis
    
    def test_optimize_markov_parameters(self):
        """Test Markov parameter optimization"""
        # Create synthetic data
        features = []
        outcomes = []
        
        for i in range(50):
            combination = ["大单", "小双", "小单", "大双"][i % 4]
            features.append({"combination": combination})
            outcomes.append(combination)
        
        param_ranges = {
            "min_count": [3, 5],
            "ema_periods": [3, 5],
            "states": [["大单", "小双", "小单", "大双"]]
        }
        
        result = optimize_markov_parameters(features, outcomes, param_ranges)
        
        assert "best_params" in result
        assert "best_accuracy" in result
        assert "all_results" in result
        assert result["optimization_completed"] == True

class TestIntegration:
    """Integration tests for statistical engines"""
    
    def test_tail_and_markov_integration(self):
        """Test integration between tail analysis and Markov prediction"""
        # Create test data with patterns
        features = []
        for i in range(100):
            sum_val = 10 + (i % 18)  # Sum between 10-27
            tail = sum_val % 10
            
            if sum_val <= 5 or sum_val >= 22:
                combination = "极值"
            else:
                size = "大" if sum_val >= 14 else "小"
                parity = "单" if sum_val % 2 else "双"
                combination = size + parity
            
            features.append({
                "sum": sum_val,
                "tail": tail,
                "combination": combination
            })
        
        # Analyze tails
        tail_freq, p_value = analyze_tail_frequency(features, window=50)
        
        # Build Markov model
        matrix, states, state_pairs = build_markov_2nd_order_matrix(features)
        
        # Make prediction
        probs = predict_combination(features, matrix, states, state_pairs, [])
        
        # Adjust with tail analysis
        adjusted_probs = adjust_probs_by_tail(probs, tail_freq, [1] * 60)
        
        # Verify integration
        assert len(adjusted_probs) == len(states)
        assert abs(sum(adjusted_probs.values()) - 1.0) < 1e-10
        assert all(0 <= p <= 1 for p in adjusted_probs.values())
    
    def test_performance_with_real_patterns(self):
        """Test performance with realistic PC28 patterns"""
        # Simulate realistic PC28 data patterns
        features = []
        patterns = [
            ("大单", 15), ("小双", 12), ("大双", 16), ("小单", 13),
            ("极值", 3), ("大单", 17), ("小双", 10), ("极值", 25)
        ]
        
        for i in range(200):
            combination, sum_val = patterns[i % len(patterns)]
            features.append({
                "combination": combination,
                "sum": sum_val,
                "tail": sum_val % 10
            })
        
        # Test tail analysis
        tail_stats = calculate_tail_statistics(features)
        assert len(tail_stats) > 0
        
        # Test Markov prediction
        matrix, states, state_pairs = build_markov_2nd_order_matrix(features)
        probs = predict_combination(features, matrix, states, state_pairs, [])
        
        # Verify realistic results
        assert len(probs) == len(states)
        assert max(probs.values()) > 0.15  # Some state should have higher probability

if __name__ == "__main__":
    pytest.main([__file__, "-v"])