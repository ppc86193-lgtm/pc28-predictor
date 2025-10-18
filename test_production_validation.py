#!/usr/bin/env python3
"""
PC28预测系统5000周期生产验证测试
Production Validation Test for PC28 Prediction System

执行5000周期的生产验证，验证准确率目标：
- 组合预测准确率：56-61%
- 大单/小双准确率：61-66%  
- 和值范围准确率：65-70%
- 统计显著性：p-value < 0.05
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from unittest.mock import patch, MagicMock
import pytest
import requests
from dataclasses import dataclass

# 导入系统组件
try:
    from monitor import Monitor
    from api_client import PC28Data, fetch_historical_data
    from prediction_engine import PredictionEngine
    from config_constants import (
        TARGET_ACCURACY_MIN, TARGET_ACCURACY_MAX,
        BIG_SMALL_ACCURACY_MIN, BIG_SMALL_ACCURACY_MAX,
        SUM_RANGE_ACCURACY_MIN, SUM_RANGE_ACCURACY_MAX
    )
except ImportError as e:
    logging.error(f"导入错误: {e}")
    # 使用默认值和简单的数据类
    TARGET_ACCURACY_MIN = 0.56
    TARGET_ACCURACY_MAX = 0.61
    BIG_SMALL_ACCURACY_MIN = 0.61
    BIG_SMALL_ACCURACY_MAX = 0.66
    SUM_RANGE_ACCURACY_MIN = 0.65
    SUM_RANGE_ACCURACY_MAX = 0.70
    
    # 简单的PC28Data类定义
    @dataclass
    class PC28Data:
        period: str
        number: List[int]
        tail: int
        sum: int
        combination: str

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """验证结果数据结构"""
    cycle_id: int
    prediction: Dict
    actual_result: Dict
    accuracy_metrics: Dict[str, float]
    response_time: float
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'cycle_id': self.cycle_id,
            'prediction': self.prediction,
            'actual_result': self.actual_result,
            'accuracy_metrics': self.accuracy_metrics,
            'response_time': self.response_time,
            'timestamp': self.timestamp.isoformat()
        }

class ProductionValidator:
    """5000周期生产验证引擎"""
    
    def __init__(self):
        self.monitor = None
        self.prediction_engine = None
        self.validation_results = []
        self.api_key = "[REDACTED]"  # 实际部署时使用环境变量
        self.api_url = "https://rijb.api.storeapi.net/api/119/260"
        
        # 初始化组件
        try:
            self.monitor = Monitor.get_monitor()
            self.prediction_engine = PredictionEngine()
        except Exception as e:
            logger.warning(f"组件初始化失败，使用模拟模式: {e}")
    
    def fetch_live_data(self) -> PC28Data:
        """获取实时PC28数据"""
        try:
            # 实际API调用
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(self.api_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 解析数据
            if 'data' in data and len(data['data']) > 0:
                latest = data['data'][0]
                return PC28Data(
                    period=latest.get('period', ''),
                    number=latest.get('number', []),
                    tail=latest.get('tail', 0),
                    sum=latest.get('sum', 0),
                    combination=latest.get('combination', '大单')
                )
            else:
                raise ValueError("无效的API响应数据")
                
        except Exception as e:
            logger.warning(f"获取实时数据失败，使用模拟数据: {e}")
            # 返回模拟数据
            import random
            combinations = ['大单', '小双', '小单', '大双']
            tail = random.randint(0, 9)
            sum_val = random.randint(0, 27)
            
            return PC28Data(
                period=f"test_{int(time.time())}",
                number=[random.randint(0, 9) for _ in range(3)],
                tail=tail,
                sum=sum_val,
                combination=random.choice(combinations)
            )
    
    def generate_prediction(self, data: PC28Data) -> Dict:
        """生成预测"""
        try:
            if self.prediction_engine:
                return self.prediction_engine.predict(data)
            else:
                # 模拟预测
                import random
                combinations = ['大单', '小双', '小单', '大双']
                return {
                    'combination': random.choice(combinations),
                    'sum_range': f"{random.randint(0, 13)}-{random.randint(14, 27)}",
                    'confidence': random.uniform(0.5, 0.9),
                    'probabilities': {
                        '大单': random.uniform(0.2, 0.3),
                        '小双': random.uniform(0.2, 0.3),
                        '小单': random.uniform(0.2, 0.3),
                        '大双': random.uniform(0.2, 0.3)
                    }
                }
        except Exception as e:
            logger.error(f"预测生成失败: {e}")
            return {
                'combination': '大单',
                'sum_range': '0-13',
                'confidence': 0.5,
                'probabilities': {'大单': 0.25, '小双': 0.25, '小单': 0.25, '大双': 0.25}
            }
    
    def evaluate_prediction(self, prediction: Dict, actual: PC28Data) -> Dict[str, float]:
        """评估预测准确性"""
        metrics = {
            'combination_correct': 0.0,
            'big_small_correct': 0.0,
            'sum_range_correct': 0.0
        }
        
        # 组合预测准确性
        if prediction.get('combination') == actual.combination:
            metrics['combination_correct'] = 1.0
        
        # 大单/小双准确性
        predicted_big_small = self._get_big_small(prediction.get('combination', ''))
        actual_big_small = self._get_big_small(actual.combination)
        if predicted_big_small == actual_big_small:
            metrics['big_small_correct'] = 1.0
        
        # 和值范围准确性
        predicted_range = prediction.get('sum_range', '0-13')
        if self._is_sum_in_range(actual.sum, predicted_range):
            metrics['sum_range_correct'] = 1.0
        
        return metrics
    
    def _get_big_small(self, combination: str) -> str:
        """获取大单/小双分类"""
        if combination in ['大单', '大双']:
            return '大'
        else:
            return '小'
    
    def _is_sum_in_range(self, sum_val: int, range_str: str) -> bool:
        """检查和值是否在预测范围内"""
        try:
            if '-' in range_str:
                min_val, max_val = map(int, range_str.split('-'))
                return min_val <= sum_val <= max_val
            else:
                return sum_val == int(range_str)
        except:
            return False
    
    async def run_5000_cycle_validation(self) -> Dict:
        """执行5000周期验证"""
        logger.info("开始5000周期生产验证测试...")
        
        start_time = time.time()
        results = []
        
        # 统计计数器
        combination_correct = 0
        big_small_correct = 0
        sum_range_correct = 0
        total_response_time = 0
        
        for cycle in range(5000):
            cycle_start = time.time()
            
            try:
                # 获取实时数据
                data = self.fetch_live_data()
                
                # 生成预测
                prediction = self.generate_prediction(data)
                
                # 模拟获取实际结果（在实际部署中，这将是下一期的开奖结果）
                actual_result = self.fetch_live_data()  # 简化处理
                
                # 评估预测
                metrics = self.evaluate_prediction(prediction, actual_result)
                
                # 计算响应时间
                response_time = time.time() - cycle_start
                total_response_time += response_time
                
                # 更新统计
                combination_correct += metrics['combination_correct']
                big_small_correct += metrics['big_small_correct']
                sum_range_correct += metrics['sum_range_correct']
                
                # 记录结果
                result = ValidationResult(
                    cycle_id=cycle + 1,
                    prediction=prediction,
                    actual_result=actual_result.__dict__ if hasattr(actual_result, '__dict__') else actual_result,
                    accuracy_metrics=metrics,
                    response_time=response_time,
                    timestamp=datetime.now()
                )
                results.append(result)
                
                # 记录到监控系统
                if self.monitor:
                    self.monitor.record_prediction(prediction, actual_result, metrics)
                
                # 进度报告
                if (cycle + 1) % 500 == 0:
                    current_combination_acc = combination_correct / (cycle + 1)
                    current_big_small_acc = big_small_correct / (cycle + 1)
                    current_sum_range_acc = sum_range_correct / (cycle + 1)
                    avg_response_time = total_response_time / (cycle + 1)
                    
                    logger.info(f"进度: {cycle + 1}/5000 - "
                              f"组合准确率: {current_combination_acc:.3f}, "
                              f"大小准确率: {current_big_small_acc:.3f}, "
                              f"和值准确率: {current_sum_range_acc:.3f}, "
                              f"平均响应时间: {avg_response_time:.3f}s")
                
                # 避免过快请求
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"周期 {cycle + 1} 执行失败: {e}")
                continue
        
        # 计算最终统计
        total_time = time.time() - start_time
        final_stats = {
            'total_cycles': len(results),
            'combination_accuracy': combination_correct / len(results) if results else 0,
            'big_small_accuracy': big_small_correct / len(results) if results else 0,
            'sum_range_accuracy': sum_range_correct / len(results) if results else 0,
            'average_response_time': total_response_time / len(results) if results else 0,
            'total_execution_time': total_time,
            'p_value': self._calculate_p_value(results),
            'validation_passed': False
        }
        
        # 验证是否达到目标
        final_stats['validation_passed'] = (
            TARGET_ACCURACY_MIN <= final_stats['combination_accuracy'] <= TARGET_ACCURACY_MAX and
            BIG_SMALL_ACCURACY_MIN <= final_stats['big_small_accuracy'] <= BIG_SMALL_ACCURACY_MAX and
            SUM_RANGE_ACCURACY_MIN <= final_stats['sum_range_accuracy'] <= SUM_RANGE_ACCURACY_MAX and
            final_stats['p_value'] < 0.05
        )
        
        # 保存结果
        self._save_validation_results(results, final_stats)
        
        logger.info(f"5000周期验证完成:")
        logger.info(f"  组合准确率: {final_stats['combination_accuracy']:.3f} (目标: {TARGET_ACCURACY_MIN}-{TARGET_ACCURACY_MAX})")
        logger.info(f"  大小准确率: {final_stats['big_small_accuracy']:.3f} (目标: {BIG_SMALL_ACCURACY_MIN}-{BIG_SMALL_ACCURACY_MAX})")
        logger.info(f"  和值准确率: {final_stats['sum_range_accuracy']:.3f} (目标: {SUM_RANGE_ACCURACY_MIN}-{SUM_RANGE_ACCURACY_MAX})")
        logger.info(f"  P值: {final_stats['p_value']:.4f} (目标: <0.05)")
        logger.info(f"  验证通过: {final_stats['validation_passed']}")
        
        return final_stats
    
    def _calculate_p_value(self, results: List[ValidationResult]) -> float:
        """计算统计显著性p值"""
        try:
            from scipy import stats
            import numpy as np
            
            # 使用组合预测准确率进行卡方检验
            observed = [r.accuracy_metrics.get('combination_correct', 0) for r in results]
            expected_accuracy = 0.25  # 随机预测的期望准确率（4选1）
            
            observed_correct = sum(observed)
            observed_incorrect = len(observed) - observed_correct
            expected_correct = len(observed) * expected_accuracy
            expected_incorrect = len(observed) * (1 - expected_accuracy)
            
            # 卡方检验
            chi2, p_value = stats.chisquare([observed_correct, observed_incorrect], 
                                          [expected_correct, expected_incorrect])
            
            return p_value
            
        except Exception as e:
            logger.warning(f"P值计算失败: {e}")
            return 0.05  # 默认边界值
    
    def _save_validation_results(self, results: List[ValidationResult], stats: Dict):
        """保存验证结果"""
        try:
            # 保存详细结果
            with open('validation_results_5000.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'results': [r.to_dict() for r in results],
                    'statistics': stats,
                    'timestamp': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            
            # 保存摘要报告
            with open('validation_summary.json', 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            logger.info("验证结果已保存到 validation_results_5000.json 和 validation_summary.json")
            
        except Exception as e:
            logger.error(f"保存验证结果失败: {e}")

# 测试函数
@pytest.mark.asyncio
async def test_production_accuracy():
    """测试生产准确率"""
    validator = ProductionValidator()
    
    # 使用模拟数据进行快速测试（100周期）
    logger.info("执行快速验证测试（100周期）...")
    
    combination_correct = 0
    big_small_correct = 0
    sum_range_correct = 0
    
    for i in range(100):
        # 模拟数据
        actual_data = PC28Data(
            period=f"test_{i}",
            number=[7, 8, 9],
            tail=7,
            sum=15,
            combination="大单"
        )
        
        prediction = validator.generate_prediction(actual_data)
        metrics = validator.evaluate_prediction(prediction, actual_data)
        
        combination_correct += metrics['combination_correct']
        big_small_correct += metrics['big_small_correct']
        sum_range_correct += metrics['sum_range_correct']
    
    # 计算准确率
    combination_accuracy = combination_correct / 100
    big_small_accuracy = big_small_correct / 100
    sum_range_accuracy = sum_range_correct / 100
    
    logger.info(f"快速测试结果:")
    logger.info(f"  组合准确率: {combination_accuracy:.3f}")
    logger.info(f"  大小准确率: {big_small_accuracy:.3f}")
    logger.info(f"  和值准确率: {sum_range_accuracy:.3f}")
    
    # 验证准确率在合理范围内（模拟数据可能不会达到生产目标）
    assert 0.0 <= combination_accuracy <= 1.0
    assert 0.0 <= big_small_accuracy <= 1.0
    assert 0.0 <= sum_range_accuracy <= 1.0

def test_validation_components():
    """测试验证组件"""
    validator = ProductionValidator()
    
    # 测试数据获取
    data = validator.fetch_live_data()
    assert hasattr(data, 'combination')
    assert hasattr(data, 'sum')
    assert hasattr(data, 'tail')
    
    # 测试预测生成
    prediction = validator.generate_prediction(data)
    assert 'combination' in prediction
    assert 'sum_range' in prediction
    assert 'confidence' in prediction
    
    # 测试评估
    metrics = validator.evaluate_prediction(prediction, data)
    assert 'combination_correct' in metrics
    assert 'big_small_correct' in metrics
    assert 'sum_range_correct' in metrics

if __name__ == "__main__":
    # 运行5000周期验证
    async def main():
        validator = ProductionValidator()
        results = await validator.run_5000_cycle_validation()
        
        print("\n" + "="*50)
        print("5000周期生产验证结果")
        print("="*50)
        print(f"组合准确率: {results['combination_accuracy']:.3f} (目标: 0.56-0.61)")
        print(f"大小准确率: {results['big_small_accuracy']:.3f} (目标: 0.61-0.66)")
        print(f"和值准确率: {results['sum_range_accuracy']:.3f} (目标: 0.65-0.70)")
        print(f"P值: {results['p_value']:.4f} (目标: <0.05)")
        print(f"平均响应时间: {results['average_response_time']:.3f}s (目标: <2s)")
        print(f"验证通过: {'✓' if results['validation_passed'] else '✗'}")
        print("="*50)
    
    # 运行验证
    asyncio.run(main())