import numpy as np
from collections import Counter
from scipy.stats import chi2_contingency, chisquare
from typing import List, Dict, Tuple, Any
import logging

logger = logging.getLogger(__name__)

# Constants for better maintainability
EXPECTED_TAIL_FREQUENCY = 0.1  # 10% uniform distribution
SIGNIFICANCE_THRESHOLD = 0.05
HIGH_FREQUENCY_THRESHOLD = 0.15
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
    # Input validation
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

def adjust_probs_by_tail(probs: Dict[str, float], 
                        tail_freq: Dict[int, float], 
                        accuracy_history: List[int]) -> Dict[str, float]:
    """
    Adjust prediction probabilities based on tail frequency analysis
    
    Args:
        probs: Current probability distribution
        tail_freq: Tail frequency distribution
        accuracy_history: Recent accuracy history for dynamic adjustment
        
    Returns:
        Adjusted probability distribution
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
    
    # Dynamic adjustment based on accuracy
    if recent_accuracy > 0.60:
        tail_factor = 0.04
        hang_factor = 0.025
    elif recent_accuracy > 0.55:
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
        adjusted_probs = {k: 1.0/len(adjusted_probs) for k in adjusted_probs.keys()}
    
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