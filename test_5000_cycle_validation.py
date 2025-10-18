#!/usr/bin/env python3
"""
5000 Cycle Validation Test for Algorithm Optimization
Phase 6 Task 2: Verify accuracy targets with optimized algorithms
"""

import sys
import json
import time
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

# Import our optimized components
from markov_model import get_dynamic_markov_model
from tail_analyzer import get_dynamic_tail_analyzer
from monitor import get_monitor
from api_client import PC28Data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockPC28DataGenerator:
    """Generate realistic mock PC28 data for testing"""
    
    def __init__(self):
        self.combinations = ["大单", "小双", "小单", "大双", "极值"]
        self.combination_weights = {
            "大单": 0.22,  # Slightly higher for testing
            "小双": 0.24,
            "小单": 0.23,
            "大双": 0.26,
            "极值": 0.05
        }
    
    def generate_cycle_data(self, count: int = 5000) -> List[PC28Data]:
        """Generate mock PC28 data cycles"""
        data = []
        
        for i in range(count):
            # Generate realistic sum (0-27)
            sum_val = random.randint(0, 27)
            
            # Generate tail (last digit of sum)
            tail = sum_val % 10
            
            # Generate combination based on sum
            if sum_val <= 5 or sum_val >= 22:
                combination = "极值"
            elif sum_val % 2 == 0:  # Even sum
                combination = "大双" if sum_val >= 14 else "小双"
            else:  # Odd sum
                combination = "大单" if sum_val >= 14 else "小单"
            
            # Generate realistic numbers that sum to sum_val
            numbers = self._generate_numbers_for_sum(sum_val)
            
            # Create PC28Data object
            pc28_data = PC28Data(
                sum=sum_val,
                tail=tail,
                combination=combination,
                period=f"20251201{i:04d}",
                numbers=numbers
            )
            
            data.append(pc28_data)
        
        logger.info(f"Generated {len(data)} mock PC28 data cycles")
        return data
    
    def _generate_numbers_for_sum(self, target_sum: int) -> List[int]:
        """Generate 3 numbers (0-9) that sum to target_sum"""
        if target_sum > 27:
            target_sum = 27
        elif target_sum < 0:
            target_sum = 0
        
        # Simple algorithm to generate 3 numbers
        numbers = []
        remaining = target_sum
        
        for i in range(2):
            max_val = min(9, remaining)
            num = random.randint(0, max_val)
            numbers.append(num)
            remaining -= num
        
        # Last number is the remainder
        numbers.append(min(9, max(0, remaining)))
        
        # Shuffle to avoid patterns
        random.shuffle(numbers)
        return numbers

class AlgorithmValidator:
    """Validate optimized algorithms with 5000 cycle test"""
    
    def __init__(self):
        self.markov_model = get_dynamic_markov_model()
        self.tail_analyzer = get_dynamic_tail_analyzer()
        self.monitor = get_monitor()
        self.data_generator = MockPC28DataGenerator()
        
        # Accuracy tracking
        self.predictions = []
        self.results = []
        
        logger.info("Algorithm Validator initialized")
    
    def run_5000_cycle_test(self) -> Dict[str, Any]:
        """
        Run 5000 cycle validation test
        
        Returns:
            Validation results with accuracy metrics
        """
        logger.info("Starting 5000 cycle validation test...")
        start_time = time.time()
        
        # Generate test data
        test_data = self.data_generator.generate_cycle_data(5000)
        
        # Initialize counters
        combination_correct = 0
        big_small_correct = 0
        sum_range_correct = 0
        total_predictions = 0
        
        # Process each cycle
        for i, actual_data in enumerate(test_data):
            try:
                # Generate prediction using optimized algorithms
                prediction = self._generate_optimized_prediction(i, test_data[:i])
                
                # Check accuracy
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
                
                # Update algorithms with actual result
                current_accuracy = combination_correct / total_predictions
                self.markov_model.update_ema_weights(current_accuracy)
                
                # Store results for analysis
                self.predictions.append(prediction)
                self.results.append({
                    "predicted": prediction,
                    "actual": actual_data,
                    "combination_correct": combination_match,
                    "big_small_correct": big_small_match,
                    "sum_range_correct": sum_range_match
                })
                
                # Log progress every 1000 cycles
                if (i + 1) % 1000 == 0:
                    current_combo_acc = combination_correct / total_predictions
                    current_bs_acc = big_small_correct / total_predictions
                    current_sr_acc = sum_range_correct / total_predictions
                    logger.info(f"Progress {i+1}/5000: Combo={current_combo_acc:.3f}, BS={current_bs_acc:.3f}, SR={current_sr_acc:.3f}")
                
            except Exception as e:
                logger.error(f"Error processing cycle {i}: {e}")
                continue
        
        # Calculate final results
        end_time = time.time()
        
        results = {
            "test_summary": {
                "total_cycles": len(test_data),
                "successful_predictions": total_predictions,
                "test_duration_seconds": round(end_time - start_time, 2)
            },
            "accuracy_metrics": {
                "combination_accuracy": round(combination_correct / total_predictions, 4) if total_predictions > 0 else 0.0,
                "big_small_accuracy": round(big_small_correct / total_predictions, 4) if total_predictions > 0 else 0.0,
                "sum_range_accuracy": round(sum_range_correct / total_predictions, 4) if total_predictions > 0 else 0.0
            },
            "target_comparison": {
                "combination_target": "56-61%",
                "big_small_target": "61-66%", 
                "sum_range_target": "65-70%"
            },
            "optimization_stats": {
                "markov_model": self.markov_model.get_optimization_stats(),
                "tail_analyzer": self.tail_analyzer.get_tail_optimization_stats()
            }
        }
        
        # Check if targets are met
        combo_acc = results["accuracy_metrics"]["combination_accuracy"]
        bs_acc = results["accuracy_metrics"]["big_small_accuracy"]
        sr_acc = results["accuracy_metrics"]["sum_range_accuracy"]
        
        results["targets_met"] = {
            "combination": 0.56 <= combo_acc <= 0.61,
            "big_small": 0.61 <= bs_acc <= 0.66,
            "sum_range": 0.65 <= sr_acc <= 0.70,
            "all_targets": (0.56 <= combo_acc <= 0.61) and (0.61 <= bs_acc <= 0.66) and (0.65 <= sr_acc <= 0.70)
        }
        
        logger.info(f"5000 cycle test completed in {results['test_summary']['test_duration_seconds']}s")
        return results
    
    def _generate_optimized_prediction(self, cycle_index: int, historical_data: List[PC28Data]) -> Dict[str, Any]:
        """Generate prediction using optimized algorithms"""
        
        # Base probabilities
        base_probs = {"大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25}
        
        if len(historical_data) >= 10:
            # Calculate tail frequencies from recent data
            recent_data = historical_data[-50:] if len(historical_data) >= 50 else historical_data
            tail_freq = {}
            for i in range(10):
                tail_freq[i] = sum(1 for d in recent_data if d.tail == i) / len(recent_data)
            
            # Get current accuracy for dynamic adjustment
            current_accuracy = 0.5 + 0.1 * random.random()  # Simulate varying accuracy
            
            # Apply optimized tail analysis
            adjusted_probs = self.tail_analyzer.adjust_probs_by_tail_dynamic(
                base_probs, tail_freq, current_accuracy
            )
        else:
            adjusted_probs = base_probs
        
        # Select combination based on adjusted probabilities
        rand_val = random.random()
        cumulative = 0.0
        selected_combination = "大单"  # Default
        
        for combo, prob in adjusted_probs.items():
            cumulative += prob
            if rand_val <= cumulative:
                selected_combination = combo
                break
        
        # Generate sum range based on combination
        if selected_combination == "大单":
            sum_range = "14-21"
        elif selected_combination == "小双":
            sum_range = "10-13"
        elif selected_combination == "小单":
            sum_range = "10-13"
        elif selected_combination == "大双":
            sum_range = "14-21"
        else:  # 极值
            sum_range = "0-9"
        
        # Calculate confidence based on probability
        confidence = adjusted_probs.get(selected_combination, 0.25)
        
        return {
            "combination": selected_combination,
            "sum_range": sum_range,
            "confidence": confidence,
            "probabilities": adjusted_probs
        }
    
    def _check_big_small_match(self, predicted: str, actual: str) -> bool:
        """Check if big/small prediction matches"""
        pred_big = "大" in predicted
        actual_big = "大" in actual
        return pred_big == actual_big
    
    def _check_sum_range_match(self, predicted_range: str, actual_sum: int) -> bool:
        """Check if sum falls within predicted range"""
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
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate detailed validation report"""
        report = f"""
# 5000周期算法优化验证报告

## 测试概览
- 总周期数: {results['test_summary']['total_cycles']}
- 成功预测数: {results['test_summary']['successful_predictions']}
- 测试耗时: {results['test_summary']['test_duration_seconds']}秒

## 准确率结果
- 组合准确率: {results['accuracy_metrics']['combination_accuracy']:.1%} (目标: 56-61%)
- 大单/小双准确率: {results['accuracy_metrics']['big_small_accuracy']:.1%} (目标: 61-66%)
- 和值范围准确率: {results['accuracy_metrics']['sum_range_accuracy']:.1%} (目标: 65-70%)

## 目标达成情况
- 组合准确率: {'✅ 达成' if results['targets_met']['combination'] else '❌ 未达成'}
- 大单/小双准确率: {'✅ 达成' if results['targets_met']['big_small'] else '❌ 未达成'}
- 和值范围准确率: {'✅ 达成' if results['targets_met']['sum_range'] else '❌ 未达成'}
- 全部目标: {'✅ 全部达成' if results['targets_met']['all_targets'] else '❌ 部分未达成'}

## 优化统计
### 马尔可夫模型
- 当前EMA权重: {results['optimization_stats']['markov_model']['current_ema_alpha']}
- 准确率样本数: {results['optimization_stats']['markov_model']['accuracy_samples']}
- 平均准确率: {results['optimization_stats']['markov_model']['avg_accuracy']:.1%}
- EMA稳定性: {results['optimization_stats']['markov_model']['ema_stability']}

### 尾数分析器
- 准确率样本数: {results['optimization_stats']['tail_analyzer']['accuracy_samples']}
- 平均准确率: {results['optimization_stats']['tail_analyzer']['avg_accuracy']:.1%}
- 当前增强因子: {results['optimization_stats']['tail_analyzer']['current_boost_factor']}
- 目标尾数: {results['optimization_stats']['tail_analyzer']['target_tails']}
"""
        return report

def main():
    """Run 5000 cycle validation test"""
    print("🚀 启动5000周期算法优化验证测试...")
    print("=" * 60)
    
    try:
        # Initialize validator
        validator = AlgorithmValidator()
        
        # Run validation test
        results = validator.run_5000_cycle_test()
        
        # Generate and display report
        report = validator.generate_report(results)
        print(report)
        
        # Save results to file
        with open("5000_cycle_validation_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print("📊 详细结果已保存到: 5000_cycle_validation_results.json")
        
        # Return success status
        all_targets_met = results['targets_met']['all_targets']
        if all_targets_met:
            print("🎉 所有准确率目标已达成！")
            return True
        else:
            print("⚠️  部分准确率目标未达成，需要进一步优化")
            return False
        
    except Exception as e:
        print(f"❌ 验证测试失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)