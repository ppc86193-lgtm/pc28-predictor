import numpy as np
from collections import Counter
from scipy.stats import chi2_contingency, chisquare
from typing import List, Dict, Tuple, Any
import logging
from config_constants import get_tail_config

logger = logging.getLogger(__name__)

# Load configuration constants
tail_config = get_tail_config()
EXPECTED_TAIL_FREQUENCY = 0.1  # 10% uniform distribution
SIGNIFICANCE_THRESHOLD = 0.05
HIGH_FREQUENCY_THRESHOLD = tail_config.HIGH_FREQUENCY_THRESHOLD
VARIANCE_SCALE_FACTOR = 10
MIN_SAMPLE_SIZE = 10

def analyze_tail_frequency(features: List[Dict[str, Any]], window: int = 16) -> Tuple[Dict[int, float], float]:
    """
    Analyze tail frequency distribution and perform chi-square test
    
    Args:
        features: List of PC28 feature dictionaries with 'tail' key
        window: Analysis window size (default 16)
        
    Returns:
        Tuple of (tail_frequencies, p_value)
    """
    # Enhanced input validation
    if not isinstance(features, list):
        raise TypeError("Features must be a list")
    if not isinstance(window, int):
        raise TypeError("Window must be an integer")
    if window <= 0:
        raise ValueError("Window size must be positive")
    if window > 1000:
        logger.warning(f"Large window size {window} may impact performance")
    
    if not features or len(features) < window:
        logger.warning(f"Insufficient data for tail analysis: {len(features) if features else 0} < {window}")
        return {i: EXPECTED_TAIL_FREQUENCY for i in range(10)}, 1.0
    
    # Extract tails from the most recent window
    recent_features = features[-window:]
    tails = []
    
    for feature in recent_features:
        if isinstance(feature, dict) and 'tail' in feature:
            tails.append(feature['tail'])
        elif hasattr(feature, 'tail'):
            tails.append(feature.tail)
        else:
            logger.warning(f"Invalid feature format: {feature}")
            continue
    
    if not tails:
        logger.warning("No valid tail data found")
        return {i: EXPECTED_TAIL_FREQUENCY for i in range(10)}, 1.0
    
    # Check minimum sample size for statistical validity
    if len(tails) < MIN_SAMPLE_SIZE:
        logger.warning(f"Sample size {len(tails)} below minimum {MIN_SAMPLE_SIZE} for reliable statistics")
        return {i: EXPECTED_TAIL_FREQUENCY for i in range(10)}, 1.0
    
    # Count tail frequencies
    tail_counts = Counter(tails)
    total_count = len(tails)
    
    # Calculate frequency distribution
    tail_frequencies = {}
    for i in range(10):
        tail_frequencies[i] = tail_counts.get(i, 0) / total_count
    
    # Prepare data for chi-square test
    observed = [tail_counts.get(i, 0) for i in range(10)]
    expected = [total_count / 10] * 10  # Uniform distribution
    
    # Perform chi-square goodness-of-fit test
    try:
        if sum(observed) > 0 and all(e > 0 for e in expected):
            chi2_stat, p_value = chisquare(observed, expected)
            logger.info(f"Tail frequency analysis: chi2={chi2_stat:.4f}, p={p_value:.4f}")
        else:
            chi2_stat, p_value = 0.0, 1.0
            logger.warning("Invalid data for chi-square test")
    except Exception as e:
        logger.error(f"Chi-square test failed: {e}")
        chi2_stat, p_value = 0.0, 1.0
    
    # Log significant deviations
    if p_value < SIGNIFICANCE_THRESHOLD:
        significant_tails = [i for i in range(10) if tail_frequencies[i] > HIGH_FREQUENCY_THRESHOLD]
        if significant_tails:
            logger.info(f"Significant tail deviations detected: {significant_tails}")
    
    return tail_frequencies, p_value

class DynamicTailAnalyzer:
    """
    Dynamic Tail Analyzer with adaptive probability adjustments
    Phase 6 Task 2: Algorithm Optimization
    """
    
    def __init__(self):
        """Initialize dynamic tail analyzer"""
        # Load configuration
        self.config = get_tail_config()
        
        self.base_tail_factor = 0.03
        self.base_hang_factor = 0.02
        self.base_boost_factor = self.config.BASE_BOOST_FACTOR
        self.max_boost_factor = self.config.MAX_BOOST_FACTOR
        self.min_boost_factor = self.config.MIN_BOOST_FACTOR
        self.target_tails = self.config.TARGET_TAILS.copy()
        self.accuracy_history = []
        
        logger.info("Dynamic Tail Analyzer initialized")
    
    def adjust_probs_by_tail_dynamic(self, probs: Dict[str, float], 
                                   tail_freq: Dict[int, float], 
                                   accuracy: float) -> Dict[str, float]:
        """
        Dynamically adjust prediction probabilities based on tail frequency and accuracy
        
        Args:
            probs: Current probability distribution
            tail_freq: Tail frequency distribution  
            accuracy: Current prediction accuracy (0.0-1.0)
            
        Returns:
            Adjusted probability distribution
        """
        if not probs or not tail_freq:
            logger.warning("Empty probabilities or tail frequencies")
            return probs
        
        if not isinstance(accuracy, (int, float)) or not (0.0 <= accuracy <= 1.0):
            logger.error(f"Invalid accuracy value: {accuracy}")
            return probs
        
        try:
            adjusted_probs = probs.copy()
            
            # Calculate dynamic boost factor based on accuracy
            if accuracy < self.config.TARGET_ACCURACY_MIN:  # Below target, increase boost
                boost_factor = min(self.config.HIGH_BOOST_FACTOR, self.max_boost_factor)
                reduction_factor = self.config.HIGH_REDUCTION_FACTOR
            elif accuracy > self.config.TARGET_ACCURACY_MAX:  # Above target, decrease boost  
                boost_factor = max(self.config.LOW_BOOST_FACTOR, self.min_boost_factor)
                reduction_factor = self.config.LOW_REDUCTION_FACTOR
            else:  # In target range, moderate boost
                boost_factor = self.config.BASE_BOOST_FACTOR
                reduction_factor = self.config.BASE_REDUCTION_FACTOR
            
            # Record accuracy for monitoring
            self.accuracy_history.append(accuracy)
            if len(self.accuracy_history) > self.config.MAX_HISTORY_SIZE:
                self.accuracy_history = self.accuracy_history[-self.config.MAX_HISTORY_SIZE:]
            
            # Apply tail-based adjustments
            adjustments_made = []
            
            for tail, freq in tail_freq.items():
                if tail in self.target_tails and freq > HIGH_FREQUENCY_THRESHOLD:
                    # Boost probabilities for combinations matching high-frequency tails
                    for comb in adjusted_probs:
                        if self._tail_matches_combination(tail, comb):
                            old_prob = adjusted_probs[comb]
                            adjusted_probs[comb] *= boost_factor
                            adjustments_made.append(f"{comb}: {old_prob:.3f}→{adjusted_probs[comb]:.3f}")
                        else:
                            # Slightly reduce other combinations
                            adjusted_probs[comb] *= reduction_factor
            
            # Normalize probabilities to sum to 1.0
            total = sum(adjusted_probs.values())
            if total > 0:
                adjusted_probs = {k: v / total for k, v in adjusted_probs.items()}
            else:
                logger.warning("Total probability is zero, returning uniform distribution")
                adjusted_probs = {k: 1.0/len(adjusted_probs) for k in adjusted_probs.keys()} if adjusted_probs else {}
            
            if adjustments_made:
                logger.info(f"尾数权重调整 (准确率={accuracy:.3f}, 增强={boost_factor:.3f}): {adjustments_made[:3]}")
            
            return adjusted_probs
            
        except Exception as e:
            logger.error(f"Failed to adjust probabilities by tail: {e}")
            return probs
    
    def _tail_matches_combination(self, tail: int, combination: str) -> bool:
        """
        Check if a tail digit matches a combination type
        
        Args:
            tail: Tail digit (0-9)
            combination: Combination string (大单, 小双, etc.)
            
        Returns:
            True if tail matches combination pattern
        """
        try:
            # Tail 7, 9 favor odd combinations (单)
            if tail in [7, 9] and "单" in combination:
                return True
            
            # Tail 0, 2, 8 favor even combinations (双)  
            if tail in [0, 2, 8] and "双" in combination:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to match tail to combination: {e}")
            return False
    
    def get_tail_optimization_stats(self) -> Dict[str, Any]:
        """
        Get tail optimization statistics
        
        Returns:
            Dictionary with tail optimization metrics
        """
        try:
            if not self.accuracy_history:
                return {
                    "accuracy_samples": 0,
                    "avg_accuracy": 0.0,
                    "boost_factor_range": f"{self.min_boost_factor}-{self.max_boost_factor}",
                    "target_tails": self.target_tails
                }
            
            recent_accuracy = self.accuracy_history[-10:] if len(self.accuracy_history) >= 10 else self.accuracy_history
            avg_accuracy = sum(recent_accuracy) / len(recent_accuracy) if recent_accuracy else 0.5
            
            # Determine current boost factor based on average accuracy
            if avg_accuracy < self.config.TARGET_ACCURACY_MIN:
                current_boost = self.config.HIGH_BOOST_FACTOR
            elif avg_accuracy > self.config.TARGET_ACCURACY_MAX:
                current_boost = self.config.LOW_BOOST_FACTOR
            else:
                current_boost = self.config.BASE_BOOST_FACTOR
            
            return {
                "accuracy_samples": len(self.accuracy_history),
                "avg_accuracy": round(avg_accuracy, 4),
                "current_boost_factor": current_boost,
                "boost_factor_range": f"{self.min_boost_factor}-{self.max_boost_factor}",
                "target_tails": self.target_tails,
                "high_freq_threshold": HIGH_FREQUENCY_THRESHOLD
            }
            
        except Exception as e:
            logger.error(f"Failed to get tail optimization stats: {e}")
            return {"error": str(e)}

def adjust_probs_by_tail(probs: Dict[str, float], 
                        tail_freq: Dict[int, float], 
                        accuracy_history: List[int]) -> Dict[str, float]:
    """
    Legacy function - maintained for backward compatibility
    Use DynamicTailAnalyzer.adjust_probs_by_tail_dynamic for new implementations
    """
    if not probs or not tail_freq:
        return probs
    
    # Calculate dynamic adjustment factor based on recent accuracy
    recent_accuracy = 0.5  # Default
    if accuracy_history and len(accuracy_history) >= 100:
        recent_accuracy = sum(accuracy_history[-100:]) / 100
    
    # Base adjustment factors
    base_tail_factor = 0.03
    base_hang_factor = 0.02
    
    # Dynamic adjustment based on accuracy (using constants)
    tail_config = get_tail_config()
    if recent_accuracy > tail_config.TARGET_ACCURACY_MAX:
        tail_factor = 0.04
        hang_factor = 0.025
    elif recent_accuracy > tail_config.TARGET_ACCURACY_MIN:
        tail_factor = 0.035
        hang_factor = 0.022
    else:
        tail_factor = base_tail_factor
        hang_factor = base_hang_factor
    
    adjusted_probs = probs.copy()
    
    # Adjust based on high-frequency tails
    # Tails 7, 8, 9 tend to favor odd combinations
    high_odd_tails = [7, 9]
    high_even_tails = [0, 2, 8]
    
    for tail in high_odd_tails:
        if tail_freq.get(tail, 0) > HIGH_FREQUENCY_THRESHOLD:
            if "大单" in adjusted_probs:
                adjusted_probs["大单"] += tail_factor
            if "小单" in adjusted_probs:
                adjusted_probs["小单"] += tail_factor / 2
            logger.debug(f"Tail {tail} adjustment: +{tail_factor} to odd combinations")
    
    for tail in high_even_tails:
        if tail_freq.get(tail, 0) > HIGH_FREQUENCY_THRESHOLD:
            if "小双" in adjusted_probs:
                adjusted_probs["小双"] += tail_factor
            if "大双" in adjusted_probs:
                adjusted_probs["大双"] += tail_factor / 2
            logger.debug(f"Tail {tail} adjustment: +{tail_factor} to even combinations")
    
    # Normalize probabilities
    total = sum(adjusted_probs.values())
    if total > 0:
        adjusted_probs = {k: v / total for k, v in adjusted_probs.items()}
    else:
        # Fallback for zero total
        logger.warning("Total probability is zero, returning uniform distribution")
        adjusted_probs = {k: 1.0/len(adjusted_probs) for k in adjusted_probs.keys()} if adjusted_probs else {}
    
    return adjusted_probs

def calculate_tail_statistics(features: List[Dict[str, Any]], 
                            window_sizes: List[int] = [16, 50, 100]) -> Dict[str, Any]:
    """
    Calculate comprehensive tail statistics for multiple window sizes
    
    Args:
        features: List of PC28 feature data
        window_sizes: List of analysis window sizes
        
    Returns:
        Dictionary with statistics for each window size
    """
    stats = {}
    
    for window in window_sizes:
        tail_frequencies, p_value = analyze_tail_frequency(features, window)
        
        # Calculate additional statistics
        if tail_frequencies:
            frequency_values = list(tail_frequencies.values())
            variance = np.var(frequency_values)
            max_freq = max(frequency_values)
            min_freq = min(frequency_values)
            
            stats[f"window_{window}"] = {
                "frequencies": tail_frequencies,
                "p_value": p_value,
                "variance": variance,
                "max_frequency": max_freq,
                "min_frequency": min_freq,
                "is_significant": p_value < SIGNIFICANCE_THRESHOLD,
                "deviation_score": variance * VARIANCE_SCALE_FACTOR
            }
    
    return stats

def get_tail_prediction_weights(tail_stats: Dict[str, Any]) -> Dict[str, float]:
    """
    Generate prediction weights based on tail statistics
    
    Args:
        tail_stats: Tail statistics from calculate_tail_statistics
        
    Returns:
        Dictionary of combination weights
    """
    weights = {
        "大单": 0.25,
        "小双": 0.25,
        "小单": 0.25,
        "大双": 0.25,
        "极值": 0.0
    }
    
    # Use the most recent window (smallest) for primary adjustments
    primary_window = min(tail_stats.keys()) if tail_stats else None
    
    if primary_window and tail_stats[primary_window]["is_significant"]:
        tail_frequencies = tail_stats[primary_window]["frequencies"]
        
        # Adjust weights based on significant tail patterns
        for tail, freq in tail_frequencies.items():
            if freq > HIGH_FREQUENCY_THRESHOLD:
                if tail in [1, 3, 5, 7, 9]:  # Odd tails
                    weights["大单"] += 0.02
                    weights["小单"] += 0.01
                else:  # Even tails
                    weights["大双"] += 0.02
                    weights["小双"] += 0.01
    
    # Normalize weights
    total = sum(weights.values())
    if total > 0:
        weights = {k: v / total for k, v in weights.items()}
    
    return weights

# Global dynamic tail analyzer instance
_dynamic_tail_analyzer = None

def get_dynamic_tail_analyzer() -> DynamicTailAnalyzer:
    """Get singleton dynamic tail analyzer instance"""
    global _dynamic_tail_analyzer
    if _dynamic_tail_analyzer is None:
        _dynamic_tail_analyzer = DynamicTailAnalyzer()
    return _dynamic_tail_analyzer