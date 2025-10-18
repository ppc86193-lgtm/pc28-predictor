import numpy as np
from scipy.sparse import csr_matrix, lil_matrix
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)

def calculate_ema_weights(periods: int = 5) -> np.ndarray:
    """Calculate exponential moving average weights"""
    if periods <= 0:
        periods = 5
    
    decay = np.exp(-np.log(2) / periods)
    weights = np.array([decay ** i for i in range(periods)])
    return weights / weights.sum()

def build_markov_2nd_order_matrix(features: List[Dict[str, Any]], 
                                 states: List[str] = ["大单", "小双", "小单", "大双", "极值"], 
                                 min_count: int = 5) -> Tuple[csr_matrix, List[str], List[Tuple[str, str]]]:
    """
    Build second-order Markov transition matrix with sparse matrix optimization
    
    Args:
        features: List of PC28 feature data with 'combination' key
        states: List of possible states
        min_count: Minimum count threshold for reliable transitions
        
    Returns:
        Tuple of (transition_matrix, states, state_pairs)
    """
    logger.info(f"Building second-order Markov chain matrix with {len(features)} features")
    
    if len(features) < 3:
        logger.warning("Insufficient data for second-order Markov chain")
        # Return uniform distribution matrix
        state_pairs = [(s1, s2) for s1 in states for s2 in states]
        transitions = np.ones((len(state_pairs), len(states))) / len(states)
        return csr_matrix(transitions), states, state_pairs
    
    # Create state pairs (all combinations of two consecutive states)
    state_pairs = [(s1, s2) for s1 in states for s2 in states]
    pair_to_idx = {pair: idx for idx, pair in enumerate(state_pairs)}
    state_to_idx = {state: idx for idx, state in enumerate(states)}
    
    # Use sparse matrix for memory efficiency
    transitions = lil_matrix((len(state_pairs), len(states)))
    pair_counts = Counter()
    transition_counts = defaultdict(Counter)
    
    # Extract combinations from features
    combinations = []
    for feature in features:
        if isinstance(feature, dict) and 'combination' in feature:
            combinations.append(feature['combination'])
        elif hasattr(feature, 'combination'):
            combinations.append(feature.combination)
        else:
            logger.warning(f"Invalid feature format: {feature}")
            continue
    
    if len(combinations) < 3:
        logger.warning("Insufficient valid combinations for analysis")
        transitions = np.ones((len(state_pairs), len(states))) / len(states)
        return csr_matrix(transitions), states, state_pairs
    
    # Count transitions: (state_t-2, state_t-1) -> state_t
    for i in range(len(combinations) - 2):
        prev_pair = (combinations[i], combinations[i + 1])
        next_state = combinations[i + 2]
        
        if prev_pair[0] in states and prev_pair[1] in states and next_state in states:
            pair_counts[prev_pair] += 1
            transition_counts[prev_pair][next_state] += 1
    
    # Build transition matrix
    for pair_idx, pair in enumerate(state_pairs):
        total_count = pair_counts.get(pair, 0)
        
        if total_count >= min_count:
            # Use observed transitions
            for state_idx, state in enumerate(states):
                count = transition_counts[pair].get(state, 0)
                transitions[pair_idx, state_idx] = count / total_count
        else:
            # Use uniform distribution for sparse data
            for state_idx in range(len(states)):
                transitions[pair_idx, state_idx] = 1.0 / len(states)
    
    # Convert to compressed sparse row format for efficiency
    transitions_csr = csr_matrix(transitions)
    
    # Log matrix statistics
    non_zero_count = transitions_csr.nnz
    total_elements = transitions_csr.shape[0] * transitions_csr.shape[1]
    sparsity = 1.0 - (non_zero_count / total_elements)
    
    logger.info(f"Markov matrix built: {transitions_csr.shape}, sparsity: {sparsity:.3f}")
    logger.info(f"Reliable transitions: {sum(1 for count in pair_counts.values() if count >= min_count)}/{len(state_pairs)}")
    
    return transitions_csr, states, state_pairs

def predict_combination(features: List[Dict[str, Any]], 
                       transition_matrix: csr_matrix, 
                       states: List[str], 
                       state_pairs: List[Tuple[str, str]], 
                       accuracy_history: List[int]) -> Dict[str, float]:
    """
    Predict next combination using second-order Markov chain with dynamic adjustments
    
    Args:
        features: Recent feature data
        transition_matrix: Pre-built transition matrix
        states: List of possible states
        state_pairs: List of state pairs
        accuracy_history: Recent prediction accuracy for dynamic adjustment
        
    Returns:
        Dictionary of state probabilities
    """
    if len(features) < 2:
        logger.warning("Insufficient data for second-order prediction")
        return {state: 1.0 / len(states) for state in states}
    
    # Extract recent combinations
    recent_combinations = []
    for feature in features[-2:]:
        if isinstance(feature, dict) and 'combination' in feature:
            recent_combinations.append(feature['combination'])
        elif hasattr(feature, 'combination'):
            recent_combinations.append(feature.combination)
        else:
            logger.warning(f"Invalid feature format: {feature}")
            return {state: 1.0 / len(states) for state in states}
    
    current_pair = (recent_combinations[0], recent_combinations[1])
    
    # Initialize with uniform distribution
    probs = {state: 1.0 / len(states) for state in states}
    
    # Get probabilities from transition matrix
    if current_pair in state_pairs:
        pair_idx = state_pairs.index(current_pair)
        matrix_row = transition_matrix.getrow(pair_idx).toarray().flatten()
        
        for state_idx, state in enumerate(states):
            probs[state] = matrix_row[state_idx]
        
        logger.debug(f"Markov prediction for {current_pair}: {probs}")
    else:
        logger.debug(f"Unknown state pair {current_pair}, using uniform distribution")
    
    # Apply dynamic adjustments based on recent accuracy
    recent_accuracy = 0.5  # Default
    if accuracy_history and len(accuracy_history) >= 50:
        recent_accuracy = sum(accuracy_history[-50:]) / 50
    
    # Streak detection and adjustment
    if len(features) >= 3:
        last_three = []
        for feature in features[-3:]:
            if isinstance(feature, dict) and 'combination' in feature:
                last_three.append(feature['combination'])
            elif hasattr(feature, 'combination'):
                last_three.append(feature.combination)
        
        if len(last_three) == 3:
            # Check for streaks
            streak_adjustments = calculate_streak_adjustments(last_three, recent_accuracy)
            for state, adjustment in streak_adjustments.items():
                if state in probs:
                    probs[state] += adjustment
    
    # Extreme value detection
    if len(features) >= 1:
        last_feature = features[-1]
        if isinstance(last_feature, dict):
            last_sum = last_feature.get('sum', 14)
        elif hasattr(last_feature, 'sum'):
            last_sum = last_feature.sum
        else:
            last_sum = 14
        
        # Adjust for extreme values
        if last_sum <= 5 or last_sum >= 22:
            extreme_factor = 0.05 if recent_accuracy > 0.55 else 0.03
            if "极值" in probs:
                probs["极值"] += extreme_factor
                # Redistribute from other states
                for state in states:
                    if state != "极值":
                        probs[state] -= extreme_factor / (len(states) - 1)
    
    # Normalize probabilities
    total = sum(probs.values())
    if total > 0:
        probs = {k: max(0, v) / total for k, v in probs.items()}
    
    return probs

def calculate_streak_adjustments(last_three: List[str], accuracy: float) -> Dict[str, float]:
    """Calculate probability adjustments based on streak patterns"""
    adjustments = {}
    
    # Base adjustment factors
    base_factor = 0.02
    if accuracy > 0.60:
        streak_factor = 0.025
    elif accuracy > 0.55:
        streak_factor = 0.022
    else:
        streak_factor = base_factor
    
    # Check for consecutive patterns
    if len(set(last_three)) == 1:
        # Three consecutive same states - slight anti-streak bias
        repeated_state = last_three[0]
        adjustments[repeated_state] = -streak_factor * 0.5
    elif len(set(last_three[-2:])) == 1:
        # Two consecutive same states - moderate anti-streak bias
        repeated_state = last_three[-1]
        adjustments[repeated_state] = -streak_factor * 0.3
    
    # Check for alternating patterns
    if len(last_three) == 3 and last_three[0] == last_three[2] and last_three[0] != last_three[1]:
        # Alternating pattern detected
        pattern_state = last_three[0]
        adjustments[pattern_state] = streak_factor * 0.4
    
    return adjustments

def analyze_markov_performance(features: List[Dict[str, Any]], 
                              predictions: List[Dict[str, float]], 
                              actual_outcomes: List[str]) -> Dict[str, Any]:
    """
    Analyze Markov chain prediction performance
    
    Args:
        features: Historical feature data
        predictions: Historical predictions
        actual_outcomes: Actual outcomes
        
    Returns:
        Performance analysis dictionary
    """
    if not predictions or not actual_outcomes or len(predictions) != len(actual_outcomes):
        return {"error": "Invalid input data for performance analysis"}
    
    # Calculate accuracy metrics
    correct_predictions = 0
    total_predictions = len(predictions)
    state_accuracies = defaultdict(list)
    confidence_calibration = []
    
    for i, (pred_dict, actual) in enumerate(zip(predictions, actual_outcomes)):
        # Get predicted state (highest probability)
        predicted_state = max(pred_dict, key=pred_dict.get)
        confidence = pred_dict[predicted_state]
        
        is_correct = predicted_state == actual
        if is_correct:
            correct_predictions += 1
        
        state_accuracies[actual].append(is_correct)
        confidence_calibration.append((confidence, is_correct))
    
    overall_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
    
    # Calculate per-state accuracies
    state_acc_summary = {}
    for state, results in state_accuracies.items():
        state_acc_summary[state] = {
            "accuracy": sum(results) / len(results) if results else 0,
            "count": len(results)
        }
    
    # Analyze confidence calibration
    confidence_bins = np.linspace(0, 1, 11)
    calibration_data = []
    
    for i in range(len(confidence_bins) - 1):
        bin_start, bin_end = confidence_bins[i], confidence_bins[i + 1]
        bin_predictions = [(conf, correct) for conf, correct in confidence_calibration 
                          if bin_start <= conf < bin_end]
        
        if bin_predictions:
            avg_confidence = np.mean([conf for conf, _ in bin_predictions])
            avg_accuracy = np.mean([correct for _, correct in bin_predictions])
            calibration_data.append({
                "confidence_range": f"{bin_start:.1f}-{bin_end:.1f}",
                "avg_confidence": avg_confidence,
                "avg_accuracy": avg_accuracy,
                "count": len(bin_predictions)
            })
    
    return {
        "overall_accuracy": overall_accuracy,
        "total_predictions": total_predictions,
        "state_accuracies": state_acc_summary,
        "confidence_calibration": calibration_data,
        "analysis_timestamp": np.datetime64('now').astype(str)
    }

def optimize_markov_parameters(features: List[Dict[str, Any]], 
                              validation_outcomes: List[str],
                              param_ranges: Dict[str, List] = None) -> Dict[str, Any]:
    """
    Optimize Markov chain parameters using grid search
    
    Args:
        features: Training feature data
        validation_outcomes: Validation outcomes for testing
        param_ranges: Parameter ranges to search
        
    Returns:
        Best parameters and performance metrics
    """
    if param_ranges is None:
        param_ranges = {
            "min_count": [3, 5, 7, 10],
            "ema_periods": [3, 5, 7, 10],
            "states": [
                ["大单", "小双", "小单", "大双"],
                ["大单", "小双", "小单", "大双", "极值"]
            ]
        }
    
    best_accuracy = 0
    best_params = {}
    results = []
    
    # Grid search over parameter combinations
    for min_count in param_ranges["min_count"]:
        for ema_periods in param_ranges["ema_periods"]:
            for states in param_ranges["states"]:
                try:
                    # Build model with current parameters
                    transition_matrix, _, state_pairs = build_markov_2nd_order_matrix(
                        features, states, min_count
                    )
                    
                    # Test on validation data
                    correct = 0
                    total = 0
                    
                    for i in range(2, len(features)):
                        if i - 2 < len(validation_outcomes):
                            test_features = features[:i]
                            probs = predict_combination(
                                test_features, transition_matrix, states, state_pairs, []
                            )
                            
                            predicted = max(probs, key=probs.get)
                            actual = validation_outcomes[i - 2]
                            
                            if predicted == actual:
                                correct += 1
                            total += 1
                    
                    accuracy = correct / total if total > 0 else 0
                    
                    result = {
                        "min_count": min_count,
                        "ema_periods": ema_periods,
                        "states": states,
                        "accuracy": accuracy,
                        "total_tests": total
                    }
                    results.append(result)
                    
                    if accuracy > best_accuracy:
                        best_accuracy = accuracy
                        best_params = {
                            "min_count": min_count,
                            "ema_periods": ema_periods,
                            "states": states
                        }
                        
                except Exception as e:
                    logger.error(f"Parameter optimization error: {e}")
                    continue
    
    return {
        "best_params": best_params,
        "best_accuracy": best_accuracy,
        "all_results": results,
        "optimization_completed": True
    }