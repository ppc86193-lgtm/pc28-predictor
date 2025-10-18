"""
PC28 Prediction System - Algorithm Optimization Module
Phase 6: Monitoring and Optimization
"""

import json
import logging
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from config import redis_client
from monitor import get_monitor

logger = logging.getLogger(__name__)

@dataclass
class OptimizationConfig:
    """优化配置"""
    min_accuracy_threshold: float = 0.56  # 最低准确率阈值
    target_accuracy: float = 0.65  # 目标准确率
    optimization_window: int = 100  # 优化窗口大小
    learning_rate: float = 0.01  # 学习率
    max_adjustment: float = 0.1  # 最大调整幅度

class PC28Optimizer:
    """PC28预测算法优化器"""
    
    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.cache_prefix = "pc28_optimizer:"
        self.parameters_key = f"{self.cache_prefix}parameters"
        
        # 默认参数
        self.default_parameters = {
            "markov_weight": 0.7,
            "tail_weight": 0.3,
            "tail_adjustment_factor": 0.03,
            "hang_adjustment_factor": 0.02,
            "confidence_threshold": 0.05,
            "ema_periods": 5,
            "tail_window": 16
        }
        
        logger.info("PC28 Optimizer initialized")
    
    def get_current_parameters(self) -> Dict[str, float]:
        """获取当前优化参数"""
        try:
            cached_params = redis_client.get(self.parameters_key)
            if cached_params:
                return json.loads(cached_params)
            else:
                # 返回默认参数并缓存
                self._save_parameters(self.default_parameters)
                return self.default_parameters.copy()
        except Exception as e:
            logger.error(f"Failed to get parameters: {e}")
            return self.default_parameters.copy()
    
    def _save_parameters(self, parameters: Dict[str, float]):
        """保存参数到缓存"""
        try:
            redis_client.setex(
                self.parameters_key,
                24 * 3600,  # 24小时过期
                json.dumps(parameters)
            )
        except Exception as e:
            logger.error(f"Failed to save parameters: {e}")
    
    def analyze_performance(self) -> Dict[str, Any]:
        """分析当前性能表现"""
        try:
            monitor = get_monitor()
            
            # 获取准确率指标
            accuracy_24h = monitor.get_accuracy_metrics("24h")
            accuracy_1h = monitor.get_accuracy_metrics("1h")
            
            # 获取性能指标
            performance = monitor.get_performance_metrics()
            
            # 分析结果
            analysis = {
                "current_accuracy": {
                    "24h": accuracy_24h.get("overall_accuracy", 0.0),
                    "1h": accuracy_1h.get("overall_accuracy", 0.0),
                    "combination": accuracy_24h.get("combination_accuracy", 0.0),
                    "sum_range": accuracy_24h.get("sum_range_accuracy", 0.0)
                },
                "performance": {
                    "avg_response_time": performance.get("response_time", {}).get("avg_ms", 0.0),
                    "accuracy_trend": performance.get("accuracy", {}).get("trend", "stable")
                },
                "recommendations": []
            }
            
            # 生成优化建议
            current_accuracy = analysis["current_accuracy"]["24h"]
            
            if current_accuracy < self.config.min_accuracy_threshold:
                analysis["recommendations"].append({
                    "type": "accuracy_low",
                    "message": f"准确率 {current_accuracy:.3f} 低于阈值 {self.config.min_accuracy_threshold}",
                    "action": "increase_markov_weight"
                })
            
            if analysis["performance"]["avg_response_time"] > 2000:  # 2秒
                analysis["recommendations"].append({
                    "type": "performance_slow",
                    "message": f"响应时间 {analysis['performance']['avg_response_time']:.1f}ms 过慢",
                    "action": "reduce_computation"
                })
            
            trend = analysis["performance"]["accuracy_trend"]
            if trend == "declining":
                analysis["recommendations"].append({
                    "type": "accuracy_declining",
                    "message": "准确率呈下降趋势",
                    "action": "adjust_parameters"
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {"error": str(e)}
    
    def optimize_parameters(self) -> Dict[str, Any]:
        """基于性能分析优化参数"""
        try:
            # 分析当前性能
            analysis = self.analyze_performance()
            
            if "error" in analysis:
                return analysis
            
            current_params = self.get_current_parameters()
            new_params = current_params.copy()
            adjustments = []
            
            current_accuracy = analysis["current_accuracy"]["24h"]
            combination_accuracy = analysis["current_accuracy"]["combination"]
            
            # 基于准确率调整参数
            if current_accuracy < self.config.min_accuracy_threshold:
                # 准确率过低，增加马尔可夫权重
                adjustment = min(self.config.learning_rate, self.config.max_adjustment)
                new_params["markov_weight"] = min(0.9, current_params["markov_weight"] + adjustment)
                new_params["tail_weight"] = 1.0 - new_params["markov_weight"]
                
                adjustments.append({
                    "parameter": "markov_weight",
                    "old_value": current_params["markov_weight"],
                    "new_value": new_params["markov_weight"],
                    "reason": "低准确率"
                })
            
            elif current_accuracy > self.config.target_accuracy:
                # 准确率较高，可以尝试平衡权重
                if current_params["markov_weight"] > 0.6:
                    adjustment = self.config.learning_rate / 2
                    new_params["markov_weight"] = max(0.6, current_params["markov_weight"] - adjustment)
                    new_params["tail_weight"] = 1.0 - new_params["markov_weight"]
                    
                    adjustments.append({
                        "parameter": "markov_weight",
                        "old_value": current_params["markov_weight"],
                        "new_value": new_params["markov_weight"],
                        "reason": "平衡权重"
                    })
            
            # 基于组合准确率调整尾数分析参数
            if combination_accuracy < 0.5:
                # 组合预测准确率低，增强尾数调整
                new_params["tail_adjustment_factor"] = min(0.05, 
                    current_params["tail_adjustment_factor"] + self.config.learning_rate)
                
                adjustments.append({
                    "parameter": "tail_adjustment_factor",
                    "old_value": current_params["tail_adjustment_factor"],
                    "new_value": new_params["tail_adjustment_factor"],
                    "reason": "组合准确率低"
                })
            
            # 基于趋势调整置信度阈值
            trend = analysis["performance"]["accuracy_trend"]
            if trend == "declining":
                # 准确率下降，降低置信度阈值（更保守）
                new_params["confidence_threshold"] = max(0.01,
                    current_params["confidence_threshold"] - 0.01)
                
                adjustments.append({
                    "parameter": "confidence_threshold",
                    "old_value": current_params["confidence_threshold"],
                    "new_value": new_params["confidence_threshold"],
                    "reason": "准确率下降趋势"
                })
            
            elif trend == "improving":
                # 准确率上升，可以提高置信度阈值
                new_params["confidence_threshold"] = min(0.1,
                    current_params["confidence_threshold"] + 0.005)
                
                adjustments.append({
                    "parameter": "confidence_threshold",
                    "old_value": current_params["confidence_threshold"],
                    "new_value": new_params["confidence_threshold"],
                    "reason": "准确率上升趋势"
                })
            
            # 保存新参数
            if adjustments:
                self._save_parameters(new_params)
                logger.info(f"Parameters optimized: {len(adjustments)} adjustments made")
            
            return {
                "status": "success",
                "adjustments": adjustments,
                "new_parameters": new_params,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Parameter optimization failed: {e}")
            return {"error": str(e)}
    
    def get_optimization_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取优化历史记录"""
        try:
            history_key = f"{self.cache_prefix}history"
            
            # 从Redis获取历史记录
            history_data = redis_client.lrange(history_key, 0, -1)
            
            history = []
            cutoff_time = datetime.now() - timedelta(days=days)
            
            for record_json in history_data:
                try:
                    record = json.loads(record_json)
                    record_time = datetime.fromisoformat(record["timestamp"])
                    
                    if record_time >= cutoff_time:
                        history.append(record)
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
            
            # 按时间倒序排序
            history.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get optimization history: {e}")
            return []
    
    def _save_optimization_record(self, optimization_result: Dict[str, Any]):
        """保存优化记录到历史"""
        try:
            history_key = f"{self.cache_prefix}history"
            
            # 添加到历史记录
            redis_client.lpush(history_key, json.dumps(optimization_result))
            
            # 保持最近100条记录
            redis_client.ltrim(history_key, 0, 99)
            
            # 设置过期时间
            redis_client.expire(history_key, 30 * 24 * 3600)  # 30天
            
        except Exception as e:
            logger.error(f"Failed to save optimization record: {e}")
    
    def run_optimization_cycle(self) -> Dict[str, Any]:
        """运行完整的优化周期"""
        try:
            logger.info("Starting optimization cycle")
            
            # 1. 分析性能
            analysis = self.analyze_performance()
            
            # 2. 检查是否需要优化
            if "error" in analysis:
                return analysis
            
            current_accuracy = analysis["current_accuracy"]["24h"]
            recommendations = analysis.get("recommendations", [])
            
            # 3. 决定是否进行优化
            should_optimize = (
                current_accuracy < self.config.min_accuracy_threshold or
                len(recommendations) > 0 or
                analysis["performance"]["accuracy_trend"] == "declining"
            )
            
            if not should_optimize:
                return {
                    "status": "no_optimization_needed",
                    "message": "系统性能良好，无需优化",
                    "analysis": analysis
                }
            
            # 4. 执行优化
            optimization_result = self.optimize_parameters()
            
            # 5. 保存优化记录
            if optimization_result.get("status") == "success":
                self._save_optimization_record(optimization_result)
            
            logger.info("Optimization cycle completed")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Optimization cycle failed: {e}")
            return {"error": str(e)}
    
    def reset_parameters(self) -> Dict[str, Any]:
        """重置参数到默认值"""
        try:
            self._save_parameters(self.default_parameters)
            
            logger.info("Parameters reset to defaults")
            return {
                "status": "success",
                "message": "参数已重置为默认值",
                "parameters": self.default_parameters
            }
            
        except Exception as e:
            logger.error(f"Failed to reset parameters: {e}")
            return {"error": str(e)}

# 全局优化器实例
_optimizer = None

def get_optimizer() -> PC28Optimizer:
    """获取单例优化器实例"""
    global _optimizer
    if _optimizer is None:
        _optimizer = PC28Optimizer()
    return _optimizer