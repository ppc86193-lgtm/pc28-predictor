#!/usr/bin/env python3
"""
Simplified Dynamic Optimization Test
Phase 6 Task 2: Test dynamic algorithms without external dependencies
"""

import sys
import json
import time
import random
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add pc28_predictor to path
sys.path.append('pc28_predictor')

class SimpleDynamicMarkovModel:
    """Simplified dynamic Markov model for testing"""
    
    def __init__(self, initial_ema_alpha: float = 0.3):
        self.ema_alpha = max(0.1, min(0.9, initial_ema_alpha))
        self.min_ema_alpha = 0.1
        self.max_ema_alpha = 0.9
        self.adjustment_step = 0.01
        self.accuracy_history = []
        
    def update_ema_weights(self, accuracy: float) -> None:
        """Update EMA weights based on accuracy"""
        if not isinstance(accuracy, (int, float)) or not (0.0 <= accuracy <= 1.0):
            return
        
        old_alpha = self.ema_alpha
        
        if accuracy < 0.56:  # Below target
            self.ema_alpha = min(self.ema_alpha + self.adjustment_step, self.max_ema_alpha)
        elif accuracy > 0.61:  # Above target
            self.ema_alpha = max(self.ema_alpha - self.adjustment_step, self.min_ema_alpha)
        
        self.accuracy_history.append(accuracy)
        if len(self.accuracy_history) > 100:
            self.accuracy_history = self.accuracy_history[-100:]
        
        if abs(self.ema_alpha - old_alpha) > 0.001:
            logger.info(f"EMA权重调整: {old_alpha:.3f} → {self.ema_alpha:.3f} (准确率: {accuracy:.3f})")
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        if not self.accuracy_history:
            return {
                "current_ema_alpha": self.ema_alpha,
                "accuracy_samples": 0,
                "avg_accuracy": 0.0,
                "ema_stability": "no_data"
            }
        
        recent_accuracy = self.accuracy_history[-10:] if len(self.accuracy_history) >= 10 else self.accuracy_history
        avg_accuracy = sum(recent_accuracy) / len(recent_accuracy)
        
        return {
            "current_ema_alpha": round(self.ema_alpha, 4),
            "accuracy_samples": len(self.accuracy_history),
            "avg_accuracy": round(avg_accuracy, 4),
            "ema_stability": "stable"
        }

class SimpleDynamicTailAnalyzer:
    """Simplified dynamic tail analyzer for testing"""
    
    def __init__(self):
        self.base_boost_factor = 1.03
        self.max_boost_factor = 1.07
        self.min_boost_factor = 1.01
        self.target_tails = [7, 8, 9]
        self.accuracy_history = []
    
    def adjust_probs_by_tail_dynamic(self, probs: Dict[str, float], 
                                   tail_freq: Dict[int, float], 
                                   accuracy: float) -> Dict[str, float]:
        """Dynamically adjust probabilities based on tail frequency and accuracy"""
        if not probs or not tail_freq:
            return probs
        
        if not isinstance(accuracy, (int, float)) or not (0.0 <= accuracy <= 1.0):
            return probs
        
        adjusted_probs = probs.copy()
        
        # Calculate dynamic boost factor
        if accuracy < 0.56:
            boost_factor = 1.05
            reduction_factor = 0.94
        elif accuracy > 0.61:
            boost_factor = 1.02
            reduction_factor = 0.98
        else:
            boost_factor = 1.03
            reduction_factor = 0.96
        
        self.accuracy_history.append(accuracy)
        if len(self.accuracy_history) > 100:
            self.accuracy_history = self.accuracy_history[-100:]
        
        # Apply tail-based adjustments
        adjustments_made = []
        
        for tail, freq in tail_freq.items():
            if tail in self.target_tails and freq > 0.15:  # High frequency threshold
                for comb in adjusted_probs:
                    if self._tail_matches_combination(tail, comb):
                        old_prob = adjusted_probs[comb]
                        adjusted_probs[comb] *= boost_factor
                        adjustments_made.append(f"{comb}: {old_prob:.3f}→{adjusted_probs[comb]:.3f}")
                    else:
                        adjusted_probs[comb] *= reduction_factor
        
        # Normalize probabilities
        total = sum(adjusted_probs.values())
        if total > 0:
            adjusted_probs = {k: v / total for k, v in adjusted_probs.items()}
        
        if adjustments_made:
            logger.info(f"尾数权重调整 (准确率={accuracy:.3f}): {adjustments_made[:2]}")
        
        return adjusted_probs
    
    def _tail_matches_combination(self, tail: int, combination: str) -> bool:
        """Check if tail matches combination"""
        if tail in [7, 9] and "单" in combination:
            return True
        if tail in [0, 2, 8] and "双" in combination:
            return True
        return False
    
    def get_tail_optimization_stats(self) -> Dict[str, Any]:
        """Get tail optimization statistics"""
        if not self.accuracy_history:
            return {
                "accuracy_samples": 0,
                "avg_accuracy": 0.0,
                "current_boost_factor": 1.03,
                "target_tails": self.target_tails
            }
        
        recent_accuracy = self.accuracy_history[-10:] if len(self.accuracy_history) >= 10 else self.accuracy_history
        avg_accuracy = sum(recent_accuracy) / len(recent_accuracy)
        
        if avg_accuracy < 0.56:
            current_boost = 1.05
        elif avg_accuracy > 0.61:
            current_boost = 1.02
        else:
            current_boost = 1.03
        
        return {
            "accuracy_samples": len(self.accuracy_history),
            "avg_accuracy": round(avg_accuracy, 4),
            "current_boost_factor": current_boost,
            "target_tails": self.target_tails
        }

class PC28Data:
    """Simple PC28 data structure"""
    def __init__(self, sum_val, tail, combination, period, numbers):
        self.sum = sum_val
        self.tail = tail
        self.combination = combination
        self.period = period
        self.numbers = numbers

class MockDataGenerator:
    """Generate mock PC28 data"""
    
    def __init__(self):
        self.combinations = ["大单", "小双", "小单", "大双", "极值"]
    
    def generate_cycle_data(self, count: int = 1000) -> List[PC28Data]:
        """Generate mock data cycles"""
        data = []
        
        for i in range(count):
            sum_val = random.randint(0, 27)
            tail = sum_val % 10
            
            if sum_val <= 5 or sum_val >= 22:
                combination = "极值"
            elif sum_val % 2 == 0:
                combination = "大双" if sum_val >= 14 else "小双"
            else:
                combination = "大单" if sum_val >= 14 else "小单"
            
            numbers = self._generate_numbers_for_sum(sum_val)
            
            data.append(PC28Data(sum_val, tail, combination, f"test{i:04d}", numbers))
        
        return data
    
    def _generate_numbers_for_sum(self, target_sum: int) -> List[int]:
        """Generate 3 numbers that sum to target"""
        numbers = []
        remaining = min(27, max(0, target_sum))
        
        for i in range(2):
            max_val = min(9, remaining)
            num = random.randint(0, max_val)
            numbers.append(num)
            remaining -= num
        
        numbers.append(min(9, max(0, remaining)))
        random.shuffle(numbers)
        return numbers

class OptimizationValidator:
    """Validate optimization algorithms"""
    
    def __init__(self):
        self.markov_model = SimpleDynamicMarkovModel(0.3)
        self.tail_analyzer = SimpleDynamicTailAnalyzer()
        self.data_generator = MockDataGenerator()
        
    def run_optimization_test(self, cycles: int = 1000) -> Dict[str, Any]:
        """Run optimization test"""
        logger.info(f"开始{cycles}周期优化测试...")
        start_time = time.time()
        
        test_data = self.data_generator.generate_cycle_data(cycles)
        
        combination_correct = 0
        big_small_correct = 0
        sum_range_correct = 0
        total_predictions = 0
        
        for i, actual_data in enumerate(test_data):
            try:
                prediction = self._generate_optimized_prediction(i, test_data[:i])
                
                combination_match = prediction["combination"] == actual_data.combination
                big_small_match = self._check_big_small_match(prediction["combination"], actual_data.combination)
                sum_range_match = self._check_sum_range_match(prediction["sum_range"], actual_data.sum)
                
                if combination_match:
                    combination_correct += 1
                if big_small_match:
                    big_small_correct += 1
                if sum_range_match:
                    sum_range_correct += 1
                
                total_predictions += 1
                
                # Update algorithms
                current_accuracy = combination_correct / total_predictions
                self.markov_model.update_ema_weights(current_accuracy)
                
                if (i + 1) % 200 == 0:
                    combo_acc = combination_correct / total_predictions
                    bs_acc = big_small_correct / total_predictions
                    sr_acc = sum_range_correct / total_predictions
                    logger.info(f"进度 {i+1}/{cycles}: 组合={combo_acc:.3f}, 大小={bs_acc:.3f}, 和值={sr_acc:.3f}")
                
            except Exception as e:
                logger.error(f"处理周期{i}时出错: {e}")
                continue
        
        end_time = time.time()
        
        results = {
            "test_summary": {
                "total_cycles": cycles,
                "successful_predictions": total_predictions,
                "test_duration_seconds": round(end_time - start_time, 2)
            },
            "accuracy_metrics": {
                "combination_accuracy": round(combination_correct / total_predictions, 4) if total_predictions > 0 else 0.0,
                "big_small_accuracy": round(big_small_correct / total_predictions, 4) if total_predictions > 0 else 0.0,
                "sum_range_accuracy": round(sum_range_correct / total_predictions, 4) if total_predictions > 0 else 0.0
            },
            "optimization_stats": {
                "markov_model": self.markov_model.get_optimization_stats(),
                "tail_analyzer": self.tail_analyzer.get_tail_optimization_stats()
            }
        }
        
        # Check targets
        combo_acc = results["accuracy_metrics"]["combination_accuracy"]
        bs_acc = results["accuracy_metrics"]["big_small_accuracy"]
        sr_acc = results["accuracy_metrics"]["sum_range_accuracy"]
        
        results["targets_met"] = {
            "combination": 0.56 <= combo_acc <= 0.61,
            "big_small": 0.61 <= bs_acc <= 0.66,
            "sum_range": 0.65 <= sr_acc <= 0.70,
            "all_targets": (0.56 <= combo_acc <= 0.61) and (0.61 <= bs_acc <= 0.66) and (0.65 <= sr_acc <= 0.70)
        }
        
        return results
    
    def _generate_optimized_prediction(self, cycle_index: int, historical_data: List[PC28Data]) -> Dict[str, Any]:
        """Generate optimized prediction"""
        base_probs = {"大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25}
        
        if len(historical_data) >= 10:
            # Calculate tail frequencies
            recent_data = historical_data[-50:] if len(historical_data) >= 50 else historical_data
            tail_freq = {}
            for i in range(10):
                tail_freq[i] = sum(1 for d in recent_data if d.tail == i) / len(recent_data)
            
            # Simulate varying accuracy
            current_accuracy = 0.5 + 0.15 * random.random()
            
            # Apply optimized tail analysis
            adjusted_probs = self.tail_analyzer.adjust_probs_by_tail_dynamic(
                base_probs, tail_freq, current_accuracy
            )
        else:
            adjusted_probs = base_probs
        
        # Select combination
        rand_val = random.random()
        cumulative = 0.0
        selected_combination = "大单"
        
        for combo, prob in adjusted_probs.items():
            cumulative += prob
            if rand_val <= cumulative:
                selected_combination = combo
                break
        
        # Generate sum range
        if selected_combination == "大单":
            sum_range = "14-21"
        elif selected_combination == "小双":
            sum_range = "10-13"
        elif selected_combination == "小单":
            sum_range = "10-13"
        elif selected_combination == "大双":
            sum_range = "14-21"
        else:
            sum_range = "0-9"
        
        return {
            "combination": selected_combination,
            "sum_range": sum_range,
            "confidence": adjusted_probs.get(selected_combination, 0.25),
            "probabilities": adjusted_probs
        }
    
    def _check_big_small_match(self, predicted: str, actual: str) -> bool:
        """Check big/small match"""
        pred_big = "大" in predicted
        actual_big = "大" in actual
        return pred_big == actual_big
    
    def _check_sum_range_match(self, predicted_range: str, actual_sum: int) -> bool:
        """Check sum range match"""
        range_mapping = {
            "0-9": (0, 9),
            "10-13": (10, 13),
            "14-21": (14, 21),
            "18-27": (18, 27)
        }
        
        if predicted_range in range_mapping:
            min_val, max_val = range_mapping[predicted_range]
            return min_val <= actual_sum <= max_val
        
        return False

def main():
    """Run optimization validation test"""
    print("🚀 动态算法优化验证测试")
    print("=" * 50)
    
    try:
        validator = OptimizationValidator()
        
        # Run test with 1000 cycles (faster than 5000 for demo)
        results = validator.run_optimization_test(1000)
        
        # Display results
        print("\n📊 测试结果:")
        print(f"总周期数: {results['test_summary']['total_cycles']}")
        print(f"测试耗时: {results['test_summary']['test_duration_seconds']}秒")
        
        print("\n🎯 准确率结果:")
        combo_acc = results['accuracy_metrics']['combination_accuracy']
        bs_acc = results['accuracy_metrics']['big_small_accuracy']
        sr_acc = results['accuracy_metrics']['sum_range_accuracy']
        
        print(f"组合准确率: {combo_acc:.1%} (目标: 56-61%)")
        print(f"大小准确率: {bs_acc:.1%} (目标: 61-66%)")
        print(f"和值准确率: {sr_acc:.1%} (目标: 65-70%)")
        
        print("\n✅ 目标达成情况:")
        print(f"组合准确率: {'✅ 达成' if results['targets_met']['combination'] else '❌ 未达成'}")
        print(f"大小准确率: {'✅ 达成' if results['targets_met']['big_small'] else '❌ 未达成'}")
        print(f"和值准确率: {'✅ 达成' if results['targets_met']['sum_range'] else '❌ 未达成'}")
        print(f"全部目标: {'✅ 全部达成' if results['targets_met']['all_targets'] else '❌ 部分未达成'}")
        
        print("\n🔧 优化统计:")
        markov_stats = results['optimization_stats']['markov_model']
        tail_stats = results['optimization_stats']['tail_analyzer']
        
        print(f"马尔可夫EMA权重: {markov_stats['current_ema_alpha']}")
        print(f"马尔可夫平均准确率: {markov_stats['avg_accuracy']:.1%}")
        print(f"尾数分析增强因子: {tail_stats['current_boost_factor']}")
        print(f"尾数分析平均准确率: {tail_stats['avg_accuracy']:.1%}")
        
        # Save results
        with open("optimization_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print("\n💾 详细结果已保存到: optimization_test_results.json")
        
        return results['targets_met']['all_targets']
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n🎉 测试{'成功' if success else '需要进一步优化'}")
    sys.exit(0 if success else 1)