"""
PC28 Prediction Engine - Orchestrates all prediction components
Phase 5: Prediction System Integration
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from api_client import (
    PC28Data, PredictionResult, TailFrequencyResult, 
    fetch_realtime_data, fetch_history_data
)
from tail_analyzer import (
    analyze_tail_frequency, adjust_probs_by_tail, 
    calculate_tail_statistics, get_tail_prediction_weights
)
from markov_model import (
    build_markov_2nd_order_matrix, predict_combination,
    calculate_ema_weights, analyze_markov_performance
)
from data_processor import extract_features as process_features
from config import redis_client

logger = logging.getLogger(__name__)

# Constants
MARKOV_WEIGHT = 0.7
TAIL_WEIGHT = 0.3
HIGH_CONFIDENCE_THRESHOLD = 0.4
MEDIUM_CONFIDENCE_THRESHOLD = 0.3
HIGH_ACCURACY_THRESHOLD = 0.65
MEDIUM_ACCURACY_THRESHOLD = 0.55

@dataclass
class PredictionConfig:
    """Configuration for prediction engine"""
    tail_window: int = 16
    markov_min_count: int = 5
    ema_periods: int = 5
    confidence_threshold: float = 0.05
    accuracy_window: int = 100
    cache_ttl: int = 10
    states: List[str] = None
    
    def __post_init__(self):
        if self.states is None:
            self.states = ["大单", "小双", "小单", "大双", "极值"]

class PC28PredictionEngine:
    """
    Main prediction engine that orchestrates all components
    """
    
    def __init__(self, config: PredictionConfig = None):
        self.config = config or PredictionConfig()
        self.accuracy_history: List[int] = []
        self.prediction_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {}
        
        # Cache keys
        self.cache_prefix = "pc28_engine:"
        self.accuracy_key = f"{self.cache_prefix}accuracy"
        self.performance_key = f"{self.cache_prefix}performance"
        
        logger.info(f"PC28 Prediction Engine initialized with config: {self.config}")
    
    def _convert_features_to_dicts(self, features: List[PC28Data]) -> List[Dict[str, Any]]:
        """Convert PC28Data objects to dictionaries efficiently"""
        feature_dicts = []
        for feature in features:
            if hasattr(feature, 'model_dump'):
                feature_dicts.append(feature.model_dump())
            else:
                feature_dicts.append({
                    'tail': feature.tail,
                    'sum': feature.sum,
                    'combination': feature.combination
                })
        return feature_dicts
    
    def generate_prediction(self, use_cache: bool = True) -> PredictionResult:
        """
        Generate comprehensive PC28 prediction
        
        Args:
            use_cache: Whether to use cached predictions
            
        Returns:
            PredictionResult with prediction and confidence
        """
        start_time = time.time()
        
        # Check cache first
        if use_cache:
            cached_prediction = self._get_cached_prediction()
            if cached_prediction:
                logger.info("Returning cached prediction")
                return cached_prediction
        
        try:
            # Step 1: Fetch and process data
            features = self._fetch_and_process_data()
            if not features:
                raise ValueError("No valid features extracted from data")
            
            # Step 2: Perform tail frequency analysis
            tail_analysis = self._analyze_tail_frequency(features)
            
            # Step 3: Build and use Markov chain
            markov_prediction = self._generate_markov_prediction(features)
            
            # Step 4: Combine predictions with tail adjustments
            combined_probs = self._combine_predictions(markov_prediction, tail_analysis)
            
            # Step 5: Calculate confidence and determine final prediction
            final_prediction = self._finalize_prediction(combined_probs, tail_analysis)
            
            # Step 6: Cache and log results
            if use_cache:
                self._cache_prediction(final_prediction)
            
            elapsed_time = time.time() - start_time
            logger.info(f"Prediction generated in {elapsed_time:.2f}s: {final_prediction.combination} ({final_prediction.confidence:.3f})")
            
            return final_prediction
            
        except Exception as e:
            logger.error(f"Prediction generation failed: {e}")
            # Return fallback prediction
            return self._create_fallback_prediction()
    
    def _fetch_and_process_data(self) -> List[PC28Data]:
        """Fetch real-time and historical data, extract features"""
        try:
            # Fetch real-time data
            realtime_data = fetch_realtime_data()
            
            # Fetch recent historical data
            today = datetime.now().strftime("%Y-%m-%d")
            history_data = fetch_history_data(today, limit=200)
            
            # Extract features from both datasets
            realtime_features = process_features(realtime_data, cache_key=f"realtime_{int(time.time())}")
            history_features = process_features(history_data, cache_key=f"history_{today}")
            
            # Combine features (history first, then realtime)
            all_features = history_features + realtime_features
            
            logger.info(f"Processed {len(all_features)} total features")
            return all_features
            
        except Exception as e:
            logger.error(f"Data fetching failed: {e}")
            return []
    
    def _analyze_tail_frequency(self, features: List[PC28Data]) -> Dict[str, Any]:
        """Perform comprehensive tail frequency analysis"""
        try:
            # Convert PC28Data to dict format for tail analyzer (optimized)
            feature_dicts = self._convert_features_to_dicts(features)
            
            # Basic tail frequency analysis
            tail_freq, p_value = analyze_tail_frequency(feature_dicts, self.config.tail_window)
            
            # Comprehensive statistics
            tail_stats = calculate_tail_statistics(feature_dicts, [16, 50, 100])
            
            # Generate prediction weights
            prediction_weights = get_tail_prediction_weights(tail_stats)
            
            return {
                'frequencies': tail_freq,
                'p_value': p_value,
                'statistics': tail_stats,
                'prediction_weights': prediction_weights,
                'is_significant': p_value < self.config.confidence_threshold
            }
            
        except Exception as e:
            logger.error(f"Tail analysis failed: {e}")
            return {
                'frequencies': {i: 0.1 for i in range(10)},
                'p_value': 1.0,
                'statistics': {},
                'prediction_weights': {state: 0.2 for state in self.config.states},
                'is_significant': False
            }
    
    def _generate_markov_prediction(self, features: List[PC28Data]) -> Dict[str, float]:
        """Generate prediction using second-order Markov chain"""
        try:
            # Convert PC28Data to dict format for Markov model (reuse conversion)
            feature_dicts = self._convert_features_to_dicts(features)
            
            # Build transition matrix
            transition_matrix, states, state_pairs = build_markov_2nd_order_matrix(
                feature_dicts, self.config.states, self.config.markov_min_count
            )
            
            # Generate prediction
            prediction = predict_combination(
                feature_dicts, transition_matrix, states, state_pairs, self.accuracy_history
            )
            
            logger.debug(f"Markov prediction: {prediction}")
            return prediction
            
        except Exception as e:
            logger.error(f"Markov prediction failed: {e}")
            # Return uniform distribution
            uniform_prob = 1.0 / len(self.config.states)
            return {state: uniform_prob for state in self.config.states}
    
    def _combine_predictions(self, markov_probs: Dict[str, float], 
                           tail_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Combine Markov and tail analysis predictions"""
        try:
            # Apply tail frequency adjustments to Markov probabilities
            adjusted_probs = adjust_probs_by_tail(
                markov_probs, 
                tail_analysis['frequencies'], 
                self.accuracy_history
            )
            
            # Apply tail-based prediction weights
            tail_weights = tail_analysis['prediction_weights']
            
            # Weighted combination using constants
            markov_weight = MARKOV_WEIGHT
            tail_weight = TAIL_WEIGHT
            
            combined_probs = {}
            for state in self.config.states:
                markov_contrib = adjusted_probs.get(state, 0) * markov_weight
                tail_contrib = tail_weights.get(state, 0) * tail_weight
                combined_probs[state] = markov_contrib + tail_contrib
            
            # Normalize
            total = sum(combined_probs.values())
            if total > 0:
                combined_probs = {k: v / total for k, v in combined_probs.items()}
            
            logger.debug(f"Combined prediction: {combined_probs}")
            return combined_probs
            
        except Exception as e:
            logger.error(f"Prediction combination failed: {e}")
            return markov_probs
    
    def _finalize_prediction(self, probabilities: Dict[str, float], 
                           tail_analysis: Dict[str, Any]) -> PredictionResult:
        """Create final prediction result with confidence scoring"""
        try:
            # Determine predicted combination
            predicted_combination = max(probabilities, key=probabilities.get)
            predicted_probability = probabilities[predicted_combination]
            
            # Calculate confidence based on multiple factors
            confidence_factors = []
            
            # Factor 1: Statistical significance of tail analysis
            if tail_analysis['is_significant']:
                confidence_factors.append(0.85)
            else:
                confidence_factors.append(0.50)
            
            # Factor 2: Prediction probability strength
            if predicted_probability > HIGH_CONFIDENCE_THRESHOLD:
                confidence_factors.append(0.9)
            elif predicted_probability > MEDIUM_CONFIDENCE_THRESHOLD:
                confidence_factors.append(0.75)
            else:
                confidence_factors.append(0.6)
            
            # Factor 3: Recent accuracy history
            if len(self.accuracy_history) >= 20:
                recent_accuracy = sum(self.accuracy_history[-20:]) / 20
                if recent_accuracy > HIGH_ACCURACY_THRESHOLD:
                    confidence_factors.append(0.9)
                elif recent_accuracy > MEDIUM_ACCURACY_THRESHOLD:
                    confidence_factors.append(0.75)
                else:
                    confidence_factors.append(0.6)
            else:
                confidence_factors.append(0.7)  # Default for insufficient history
            
            # Calculate weighted confidence
            final_confidence = sum(confidence_factors) / len(confidence_factors)
            
            # Determine sum range prediction
            sum_range = self._predict_sum_range(probabilities)
            
            return PredictionResult(
                sum_range=sum_range,
                combination=predicted_combination,
                probabilities=probabilities,
                confidence=final_confidence,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Prediction finalization failed: {e}")
            return self._create_fallback_prediction()
    
    def _predict_sum_range(self, probabilities: Dict[str, float]) -> str:
        """Predict sum range based on combination probabilities"""
        # Weight ranges based on combination probabilities
        range_weights = {
            "0-9": probabilities.get("极值", 0) * 0.3,  # Low extreme
            "10-13": probabilities.get("小单", 0) + probabilities.get("小双", 0),
            "14-17": probabilities.get("大单", 0) + probabilities.get("大双", 0),
            "18-27": probabilities.get("极值", 0) * 0.7   # High extreme
        }
        
        predicted_range = max(range_weights, key=range_weights.get)
        return predicted_range
    
    def _create_fallback_prediction(self) -> PredictionResult:
        """Create fallback prediction when main prediction fails"""
        uniform_prob = 1.0 / len(self.config.states)
        probabilities = {state: uniform_prob for state in self.config.states}
        
        return PredictionResult(
            sum_range="10-17",  # Most common range
            combination="大单",  # Default combination
            probabilities=probabilities,
            confidence=0.5,     # Low confidence for fallback
            timestamp=datetime.now()
        )
    
    def _get_cached_prediction(self) -> Optional[PredictionResult]:
        """Retrieve cached prediction if available and valid"""
        try:
            cached_data = redis_client.get(f"{self.cache_prefix}prediction")
            if cached_data:
                data = json.loads(cached_data)
                # Convert timestamp string back to datetime
                if 'timestamp' in data and isinstance(data['timestamp'], str):
                    data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                return PredictionResult(**data)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Cache data parsing failed: {e}")
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        return None
    
    def _cache_prediction(self, prediction: PredictionResult):
        """Cache prediction result"""
        try:
            # Convert to dict for JSON serialization
            data = {
                'sum_range': prediction.sum_range,
                'combination': prediction.combination,
                'probabilities': prediction.probabilities,
                'confidence': prediction.confidence,
                'timestamp': prediction.timestamp.isoformat()
            }
            
            redis_client.setex(
                f"{self.cache_prefix}prediction", 
                self.config.cache_ttl, 
                json.dumps(data)
            )
            logger.debug("Prediction cached successfully")
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    def update_accuracy(self, predicted: str, actual: str) -> float:
        """Update accuracy history with new prediction result"""
        if not predicted or not actual:
            raise ValueError("Predicted and actual values cannot be empty")
        
        if predicted not in self.config.states or actual not in self.config.states:
            logger.warning(f"Invalid state values: predicted={predicted}, actual={actual}")
        
        is_correct = 1 if predicted == actual else 0
        self.accuracy_history.append(is_correct)
        
        # Keep only recent history
        if len(self.accuracy_history) > self.config.accuracy_window * 2:
            self.accuracy_history = self.accuracy_history[-self.config.accuracy_window:]
        
        # Calculate current accuracy
        if len(self.accuracy_history) >= 10:
            current_accuracy = sum(self.accuracy_history[-self.config.accuracy_window:]) / min(len(self.accuracy_history), self.config.accuracy_window)
        else:
            current_accuracy = 0.5  # Default when insufficient data
        
        # Update cached accuracy
        try:
            redis_client.setex(self.accuracy_key, 3600, str(current_accuracy))
        except Exception as e:
            logger.warning(f"Failed to cache accuracy: {e}")
        
        logger.info(f"Accuracy updated: {current_accuracy:.3f} (correct: {is_correct})")
        return current_accuracy
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        try:
            metrics = {
                'total_predictions': len(self.accuracy_history),
                'overall_accuracy': 0.0,
                'recent_accuracy': 0.0,
                'accuracy_trend': 'stable',
                'confidence_calibration': 'unknown',
                'last_updated': datetime.now().isoformat()
            }
            
            if len(self.accuracy_history) >= 10:
                # Overall accuracy
                metrics['overall_accuracy'] = sum(self.accuracy_history) / len(self.accuracy_history)
                
                # Recent accuracy (last 50 predictions)
                recent_window = min(50, len(self.accuracy_history))
                metrics['recent_accuracy'] = sum(self.accuracy_history[-recent_window:]) / recent_window
                
                # Accuracy trend
                if len(self.accuracy_history) >= 20:
                    first_half = sum(self.accuracy_history[-20:-10]) / 10
                    second_half = sum(self.accuracy_history[-10:]) / 10
                    
                    if second_half > first_half + 0.05:
                        metrics['accuracy_trend'] = 'improving'
                    elif second_half < first_half - 0.05:
                        metrics['accuracy_trend'] = 'declining'
                    else:
                        metrics['accuracy_trend'] = 'stable'
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate performance metrics: {e}")
            return {'error': str(e)}
    
    def reset_performance_data(self):
        """Reset all performance tracking data"""
        self.accuracy_history.clear()
        self.prediction_history.clear()
        self.performance_metrics.clear()
        
        # Clear cached data
        try:
            keys_to_delete = [
                f"{self.cache_prefix}prediction",
                self.accuracy_key,
                self.performance_key
            ]
            for key in keys_to_delete:
                redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Failed to clear cached data: {e}")
        
        logger.info("Performance data reset successfully")
    
    def cleanup_old_data(self, max_age_hours: int = 24):
        """Clean up old cached data and trim history"""
        try:
            # Trim accuracy history if too large
            max_history = self.config.accuracy_window * 3
            if len(self.accuracy_history) > max_history:
                self.accuracy_history = self.accuracy_history[-max_history:]
                logger.info(f"Trimmed accuracy history to {len(self.accuracy_history)} entries")
            
            # Clean up old prediction history
            if len(self.prediction_history) > 1000:
                self.prediction_history = self.prediction_history[-500:]
                logger.info("Trimmed prediction history")
                
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")

# Global prediction engine instance
_prediction_engine = None

def get_prediction_engine(config: PredictionConfig = None) -> PC28PredictionEngine:
    """Get singleton prediction engine instance"""
    global _prediction_engine
    if _prediction_engine is None:
        _prediction_engine = PC28PredictionEngine(config)
    return _prediction_engine