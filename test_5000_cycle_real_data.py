#!/usr/bin/env python3
"""
5000周期真实数据验证测试
使用真实PC28历史数据进行准确率验证
"""

import sys
import json
import time
import requests
import hashlib
import logging
import random
from datetime import datetime
from typing import List, Dict, Any
from collections import deque
from unittest.mock import patch

# Configuration constants
HISTORICAL_WINDOW_SIZE = 100
MIN_DATA_FOR_PREDICTION = 10
TRAIN_TEST_SPLIT_RATIO = 0.8
PROGRESS_LOG_INTERVAL = 100
RANDOM_SEED = 42

# Set random seed for reproducibility
random.seed(RANDOM_SEED)

# Import our optimized components
from markov_model import get_dynamic_markov_model
from tail_analyzer import get_dynamic_tail_analyzer
from monitor import get_monitor
from api_client import PC28Data
from optimized_predictor import get_optimized_predictor
from config import api_key_data, app_id, history_url

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealPC28DataFetcher:
    """获取真实PC28历史数据"""
    
    def __init__(self):
        self.api_key = api_key_data
        self.app_id = app_id
        self.history_url = history_url
        logger.info(f"初始化真实数据获取器: {self.history_url}")
    
    def fetch_historical_data(self, limit: int = 5000) -> List[PC28Data]:
        """
        从API获取真实历史数据（使用日期回填）
        
        Args:
            limit: 获取数据条数
            
        Returns:
            PC28Data列表
        """
        from datetime import datetime, timedelta
        
        all_data = []
        
        try:
            # 计算需要获取多少天的数据
            # 每天约280期（每5分钟一期，24小时）
            days_needed = min((limit // 280) + 1, 30)  # 限制最多30天，避免过多请求
            
            logger.info(f"请求历史数据: {limit}条，预计需要{days_needed}天")
            
            # 从今天开始往前获取
            for day_offset in range(days_needed):
                # 提前检查是否已获取足够数据
                if len(all_data) >= limit:
                    logger.info(f"已获取足够数据: {len(all_data)}条，停止请求")
                    break
                
                date = (datetime.now() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
                
                # 构建请求参数 - 按字典序排序: appid, date
                sign_str = f"appid{self.app_id}date{date}{self.api_key}"
                sign = hashlib.md5(sign_str.encode()).hexdigest()
                
                params = {
                    "appid": self.app_id,
                    "date": date,
                    "sign": sign
                }
                
                logger.info(f"请求日期 {date} 的数据...")
                
                try:
                    response = requests.get(self.history_url, params=params, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    if data.get("codeid") != 10000:
                        logger.warning(f"日期 {date} API返回错误: {data.get('message')}")
                        continue
                except requests.exceptions.RequestException as req_err:
                    logger.warning(f"日期 {date} 请求失败: {req_err}")
                    continue
            
                # 解析数据
                records = data.get("retdata", [])
                logger.info(f"日期 {date} 获取到 {len(records)} 条数据")
                
                for record in records:
                    try:
                        # 解析开奖号码
                        numbers = record.get("number", [])
                        if isinstance(numbers, str):
                            numbers = [int(n) for n in numbers.split(",") if n.isdigit()]
                        elif isinstance(numbers, list):
                            numbers = [int(n) for n in numbers if str(n).isdigit()]
                        
                        if len(numbers) != 3:
                            continue
                        
                        # 计算和值和尾数
                        sum_val = sum(numbers)
                        tail = sum_val % 10
                        
                        # 确定组合类型
                        if sum_val <= 5 or sum_val >= 22:
                            combination = "极值"
                        elif sum_val % 2 == 0:  # 偶数
                            combination = "大双" if sum_val >= 14 else "小双"
                        else:  # 奇数
                            combination = "大单" if sum_val >= 14 else "小单"
                        
                        # 创建PC28Data对象
                        pc28_data = PC28Data(
                            sum=sum_val,
                            tail=tail,
                            combination=combination,
                            period=record.get("long_issue", ""),
                            numbers=numbers
                        )
                        
                        all_data.append(pc28_data)
                        
                        # 达到目标数量就停止
                        if len(all_data) >= limit:
                            break
                        
                    except Exception as e:
                        logger.warning(f"解析记录失败: {e}")
                        continue
                
                # 达到目标数量就停止
                if len(all_data) >= limit:
                    break
                
                # 避免请求过快
                time.sleep(0.5)
            
            logger.info(f"成功获取 {len(all_data)} 条真实历史数据")
            return all_data[:limit]  # 返回指定数量
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"数据获取失败: {e}")
            raise

class RealDataValidator:
    """使用真实数据验证算法"""
    
    def __init__(self):
        self.markov_model = get_dynamic_markov_model()
        self.tail_analyzer = get_dynamic_tail_analyzer()
        self.monitor = get_monitor()
        self.data_fetcher = RealPC28DataFetcher()
        self.optimized_predictor = get_optimized_predictor()  # 新增优化预测器
        
        # 准确率跟踪
        self.predictions = []
        self.results = []
        
        logger.info("真实数据验证器初始化完成（使用优化预测器）")
    
    def run_validation(self, limit: int = 5000) -> Dict[str, Any]:
        """
        运行真实数据验证
        
        Args:
            limit: 验证数据条数
            
        Returns:
            验证结果
        """
        logger.info(f"开始真实数据验证测试 (数据量: {limit})")
        start_time = time.time()
        
        # 获取真实历史数据
        try:
            test_data = self.data_fetcher.fetch_historical_data(limit)
        except Exception as e:
            logger.error(f"获取真实数据失败: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
        
        if len(test_data) < 100:
            logger.error(f"数据量不足: {len(test_data)}")
            return {
                "error": f"数据量不足: {len(test_data)}",
                "status": "failed"
            }
        
        # 初始化计数器
        combination_correct = 0
        big_small_correct = 0
        sum_range_correct = 0
        total_predictions = 0
        
        # 使用前80%数据训练，后20%数据测试
        train_size = int(len(test_data) * TRAIN_TEST_SPLIT_RATIO)
        train_data = test_data[:train_size]
        test_data_subset = test_data[train_size:]
        
        logger.info(f"训练数据: {len(train_data)}条, 测试数据: {len(test_data_subset)}条")
        
        # 使用deque优化历史窗口管理
        historical_window = deque(train_data[-HISTORICAL_WINDOW_SIZE:], maxlen=HISTORICAL_WINDOW_SIZE)
        
        # 处理每个测试周期
        for i, actual_data in enumerate(test_data_subset):
            try:
                # 使用优化预测器生成预测
                hist_data = [{'sum': d.sum, 'tail': d.tail, 'combination': d.combination} 
                            for d in historical_window]
                prediction = self.optimized_predictor.predict(hist_data)
                
                # 检查准确率
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
                
                # 更新历史窗口（deque自动管理大小）
                historical_window.append(actual_data)
                
                # 更新算法
                current_accuracy = combination_correct / total_predictions
                self.markov_model.update_ema_weights(current_accuracy)
                
                # 存储结果（可选：只存储摘要以节省内存）
                # self.results.append({
                #     "predicted": prediction,
                #     "actual": actual_data,
                #     "combination_correct": combination_match,
                #     "big_small_correct": big_small_match,
                #     "sum_range_correct": sum_range_match
                # })
                
                # 每100条记录日志
                if (i + 1) % PROGRESS_LOG_INTERVAL == 0:
                    current_combo_acc = combination_correct / total_predictions
                    current_bs_acc = big_small_correct / total_predictions
                    current_sr_acc = sum_range_correct / total_predictions
                    logger.info(f"进度 {i+1}/{len(test_data_subset)}: 组合={current_combo_acc:.3f}, 大小={current_bs_acc:.3f}, 范围={current_sr_acc:.3f}")
                
            except Exception as e:
                logger.error(f"处理周期 {i} 失败: {e}")
                continue
        
        # 计算最终结果
        end_time = time.time()
        
        results = {
            "test_summary": {
                "total_data": len(test_data),
                "train_data": len(train_data),
                "test_data": len(test_data_subset),
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
            },
            "data_source": "real_pc28_api",
            "api_url": self.data_fetcher.history_url
        }
        
        # 检查目标达成
        combo_acc = results["accuracy_metrics"]["combination_accuracy"]
        bs_acc = results["accuracy_metrics"]["big_small_accuracy"]
        sr_acc = results["accuracy_metrics"]["sum_range_accuracy"]
        
        results["targets_met"] = {
            "combination": 0.56 <= combo_acc <= 0.61,
            "big_small": 0.61 <= bs_acc <= 0.66,
            "sum_range": 0.65 <= sr_acc <= 0.70,
            "all_targets": (0.56 <= combo_acc <= 0.61) and (0.61 <= bs_acc <= 0.66) and (0.65 <= sr_acc <= 0.70)
        }
        
        logger.info(f"真实数据验证完成，耗时 {results['test_summary']['test_duration_seconds']}秒")
        return results
    
    def _generate_prediction(self, historical_data: List[PC28Data]) -> Dict[str, Any]:
        """基于历史数据生成预测（优化版 - 提升准确率）"""
        
        if len(historical_data) < MIN_DATA_FOR_PREDICTION:
            return {
                "combination": "大单",
                "sum_range": "14-21",
                "confidence": 0.25,
                "probabilities": {"大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25}
            }
        
        data_len = len(historical_data)
        if data_len == 0:
            return {
                "combination": "大单",
                "sum_range": "14-21",
                "confidence": 0.25,
                "probabilities": {"大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25}
            }
        
        # Constants for probability bounds
        MIN_BASE_PROB = 0.15
        MAX_BASE_PROB = 0.35
        HIGH_FREQ_THRESHOLD = 0.12
        TAIL_BOOST_FACTOR = 1.15  # Reduced from 1.2 to avoid over-boosting
        CONSECUTIVE_BOOST_FACTOR = 1.10  # Reduced from 1.15
        
        # 1. 计算组合历史频率（基于真实数据分布）
        from collections import Counter
        combo_counts = Counter(d.combination for d in historical_data)
        
        # 基础概率使用历史频率，限制在合理范围内
        base_probs = {
            k: max(MIN_BASE_PROB, min(MAX_BASE_PROB, v/data_len)) 
            for k, v in combo_counts.items()
        }
        # 确保所有组合都有概率
        for combo in ["大单", "小双", "小单", "大双", "极值"]:
            if combo not in base_probs:
                base_probs[combo] = MIN_BASE_PROB
        
        total = sum(base_probs.values())
        base_probs = {k: v/total for k, v in base_probs.items()}
        
        # 2. 计算尾数频率
        tail_freq = {i: sum(1 for d in historical_data if d.tail == i) / data_len 
                     for i in range(10)}
        
        # 3. 检测连号模式（最近10条）
        recent_tails = [d.tail for d in historical_data[-10:]]
        consecutive_count = sum(1 for i in range(len(recent_tails)-1) 
                               if abs(recent_tails[i] - recent_tails[i+1]) == 1)
        has_consecutive = consecutive_count >= 3
        
        # 4. 尾数调整（增强高频尾数）- 使用累积调整因子避免重复乘法
        adjusted_probs = base_probs.copy()
        high_freq_tails = [t for t, f in tail_freq.items() if f > HIGH_FREQ_THRESHOLD]
        
        if high_freq_tails:
            # 计算偶数和奇数高频尾数的数量
            even_count = sum(1 for t in high_freq_tails if t % 2 == 0)
            odd_count = sum(1 for t in high_freq_tails if t % 2 == 1)
            
            # 根据高频尾数数量调整，避免过度增强
            if even_count > 0:
                even_boost = 1.0 + (TAIL_BOOST_FACTOR - 1.0) * min(even_count / 3, 1.0)
                adjusted_probs["小双"] *= even_boost
                adjusted_probs["大双"] *= even_boost
            
            if odd_count > 0:
                odd_boost = 1.0 + (TAIL_BOOST_FACTOR - 1.0) * min(odd_count / 3, 1.0)
                adjusted_probs["大单"] *= odd_boost
                adjusted_probs["小单"] *= odd_boost
        
        # 5. 连号调整
        if has_consecutive:
            adjusted_probs["小双"] *= CONSECUTIVE_BOOST_FACTOR
            adjusted_probs["小单"] *= CONSECUTIVE_BOOST_FACTOR
        
        # 6. 归一化（确保总和为1.0）
        total = sum(adjusted_probs.values())
        if total > 0:
            adjusted_probs = {k: v/total for k, v in adjusted_probs.items()}
        else:
            # Fallback to uniform distribution
            adjusted_probs = {k: 0.2 for k in ["大单", "小双", "小单", "大双", "极值"]}
        
        # 7. 选择最高概率组合（不使用随机）
        selected_combination = max(adjusted_probs.items(), key=lambda x: x[1])[0]
        
        # 8. 生成和值范围（更精确）
        if selected_combination == "大单":
            sum_range = "15-21"
        elif selected_combination == "小双":
            sum_range = "6-12"
        elif selected_combination == "小单":
            sum_range = "7-13"
        elif selected_combination == "大双":
            sum_range = "14-20"
        else:  # 极值
            sum_range = "0-5"
        
        confidence = adjusted_probs.get(selected_combination, 0.25)
        
        return {
            "combination": selected_combination,
            "sum_range": sum_range,
            "confidence": confidence,
            "probabilities": adjusted_probs
        }
    
    def _check_big_small_match(self, predicted: str, actual: str) -> bool:
        """检查大小预测是否匹配"""
        pred_big = "大" in predicted
        actual_big = "大" in actual
        return pred_big == actual_big
    
    def _check_sum_range_match(self, predicted_range: str, actual_sum: int) -> bool:
        """检查和值范围是否匹配"""
        try:
            if "-" in predicted_range:
                min_val, max_val = map(int, predicted_range.split("-"))
                return min_val <= actual_sum <= max_val
            return False
        except:
            return False
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """生成详细验证报告"""
        report = f"""
# 5000周期真实数据验证报告

## 数据来源
- API: {results.get('api_url', 'N/A')}
- 数据类型: 真实PC28历史数据
- 总数据量: {results['test_summary']['total_data']}
- 训练数据: {results['test_summary']['train_data']}
- 测试数据: {results['test_summary']['test_data']}

## 测试概览
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
    """运行真实数据验证测试"""
    print("🚀 启动5000周期真实数据验证测试...")
    print("=" * 60)
    
    try:
        # 初始化验证器
        validator = RealDataValidator()
        
        # 运行验证测试
        results = validator.run_validation(limit=5000)
        
        if "error" in results:
            print(f"❌ 测试失败: {results['error']}")
            return False
        
        # 生成并显示报告
        report = validator.generate_report(results)
        print(report)
        
        # 保存结果
        with open("5000_cycle_real_data_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print("📊 详细结果已保存到: 5000_cycle_real_data_results.json")
        
        # 返回成功状态
        all_targets_met = results['targets_met']['all_targets']
        if all_targets_met:
            print("🎉 所有准确率目标已达成！")
            return True
        else:
            print("⚠️  部分准确率目标未达成，需要进一步优化")
            return False
        
    except Exception as e:
        print(f"❌ 验证测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
