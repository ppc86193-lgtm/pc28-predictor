"""
PC28 Prediction System - Monitoring and Performance Tracking Module
Phase 6: Monitoring and Optimization
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics

from config import redis_client
from api_client import fetch_realtime_data

logger = logging.getLogger(__name__)

# Constants
DEFAULT_CACHE_TTL = 3600  # 1 hour
PREDICTION_RETENTION_DAYS = 30
MAX_RESPONSE_TIMES = 1000
MAX_ACCURACY_WINDOW = 100
BATCH_SIZE = 100
TREND_THRESHOLD = 0.05

# Alert and trend analysis constants
MAX_TREND_DAYS = 30
MIN_TREND_DAYS = 1
LOW_ACCURACY_THRESHOLD = 0.50
TREND_COMPARISON_THRESHOLD = 0.05
MAX_ALERTS_STORED = 100
ALERT_RETENTION_DAYS = 7
MIN_TREND_DATA_POINTS = 3

@dataclass
class PredictionRecord:
    """记录单次预测的完整信息"""
    timestamp: datetime
    predicted_combination: str
    predicted_sum_range: str
    confidence: float
    actual_combination: Optional[str] = None
    actual_sum: Optional[int] = None
    is_correct: Optional[bool] = None
    response_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式用于存储"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PredictionRecord':
        """从字典创建实例"""
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class AccuracyMetrics:
    """准确率指标"""
    combination_accuracy: float
    sum_range_accuracy: float
    overall_accuracy: float
    total_predictions: int
    correct_predictions: int
    time_period: str
    
class PC28Monitor:
    """PC28预测系统监控器"""
    
    def __init__(self):
        self.cache_prefix = "pc28_monitor:"
        self.prediction_history_key = f"{self.cache_prefix}predictions"
        self.accuracy_metrics_key = f"{self.cache_prefix}accuracy"
        self.performance_metrics_key = f"{self.cache_prefix}performance"
        
        # 内存中的性能数据（用于实时监控）
        self.response_times = deque(maxlen=MAX_RESPONSE_TIMES)  # 最近1000次请求的响应时间
        self.accuracy_window = deque(maxlen=MAX_ACCURACY_WINDOW)  # 最近100次预测的准确率
        
        logger.info("PC28 Monitor initialized")
    
    def record_prediction(self, predicted_combination: str, predicted_sum_range: str, 
                         confidence: float, response_time_ms: float) -> str:
        """
        记录新的预测
        
        Args:
            predicted_combination: 预测的组合
            predicted_sum_range: 预测的和值范围
            confidence: 置信度
            response_time_ms: 响应时间（毫秒）
            
        Returns:
            预测记录的唯一ID
        """
        # Input validation
        if not predicted_combination or not isinstance(predicted_combination, str):
            logger.error("Invalid predicted_combination")
            return ""
        
        if not predicted_sum_range or not isinstance(predicted_sum_range, str):
            logger.error("Invalid predicted_sum_range")
            return ""
        
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            logger.error(f"Invalid confidence value: {confidence}")
            return ""
        
        if not isinstance(response_time_ms, (int, float)) or response_time_ms < 0:
            logger.error(f"Invalid response_time_ms: {response_time_ms}")
            return ""
        
        try:
            # 创建预测记录
            record = PredictionRecord(
                timestamp=datetime.now(),
                predicted_combination=predicted_combination,
                predicted_sum_range=predicted_sum_range,
                confidence=confidence,
                response_time_ms=response_time_ms
            )
            
            # 生成唯一ID
            record_id = f"pred_{int(time.time() * 1000)}"
            
            # 存储到Redis
            try:
                redis_client.hset(
                    self.prediction_history_key,
                    record_id,
                    json.dumps(record.to_dict())
                )
                
                # 设置过期时间（保留30天）
                redis_client.expire(self.prediction_history_key, PREDICTION_RETENTION_DAYS * 24 * 3600)
            except Exception as redis_error:
                logger.error(f"Redis storage failed for {record_id}: {redis_error}")
                # Continue execution even if Redis fails
            
            # 更新内存中的性能数据
            self.response_times.append(response_time_ms)
            
            logger.info(f"Prediction recorded: {record_id} - {predicted_combination} ({confidence:.3f})")
            return record_id
            
        except Exception as e:
            logger.error(f"Failed to record prediction: {e}")
            return ""
    
    def update_prediction_result(self, record_id: str, actual_combination: str, 
                               actual_sum: int) -> bool:
        """
        更新预测结果（当实际结果出来后）
        
        Args:
            record_id: 预测记录ID
            actual_combination: 实际组合
            actual_sum: 实际和值
            
        Returns:
            更新是否成功
        """
        # Input validation
        if not record_id or not isinstance(record_id, str):
            logger.error("Invalid record_id")
            return False
        
        if not actual_combination or not isinstance(actual_combination, str):
            logger.error("Invalid actual_combination")
            return False
        
        if not isinstance(actual_sum, int) or not (0 <= actual_sum <= 27):
            logger.error(f"Invalid actual_sum: {actual_sum}")
            return False
        
        try:
            # 从Redis获取预测记录
            record_data = redis_client.hget(self.prediction_history_key, record_id)
            if not record_data:
                logger.warning(f"Prediction record not found: {record_id}")
                return False
            
            # 解析记录
            record_dict = json.loads(record_data)
            record = PredictionRecord.from_dict(record_dict)
            
            # 更新实际结果
            record.actual_combination = actual_combination
            record.actual_sum = actual_sum
            
            # 计算准确性
            combination_correct = record.predicted_combination == actual_combination
            sum_range_correct = self._is_sum_in_range(actual_sum, record.predicted_sum_range)
            record.is_correct = combination_correct and sum_range_correct
            
            # 更新Redis中的记录
            redis_client.hset(
                self.prediction_history_key,
                record_id,
                json.dumps(record.to_dict())
            )
            
            # 更新内存中的准确率数据
            self.accuracy_window.append(1 if record.is_correct else 0)
            
            # 更新准确率指标
            self._update_accuracy_metrics()
            
            logger.info(f"Prediction result updated: {record_id} - Correct: {record.is_correct}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update prediction result: {e}")
            return False
    
    def _is_sum_in_range(self, actual_sum: int, predicted_range: str) -> bool:
        """检查实际和值是否在预测范围内"""
        range_mapping = {
            "0-9": (0, 9),
            "10-13": (10, 13),
            "10-17": (10, 17),
            "14-17": (14, 17),
            "14-21": (14, 21),
            "18-27": (18, 27)
        }
        
        if predicted_range in range_mapping:
            min_val, max_val = range_mapping[predicted_range]
            return min_val <= actual_sum <= max_val
        
        return False
    
    def _update_accuracy_metrics(self):
        """更新准确率指标"""
        try:
            # 获取最近的预测记录
            recent_records = self._get_recent_predictions(hours=24)
            
            if not recent_records:
                return
            
            # 计算各种准确率
            total_predictions = len(recent_records)
            combination_correct = sum(1 for r in recent_records 
                                   if r.actual_combination and 
                                   r.predicted_combination == r.actual_combination)
            
            sum_range_correct = sum(1 for r in recent_records 
                                  if r.actual_sum is not None and 
                                  self._is_sum_in_range(r.actual_sum, r.predicted_sum_range))
            
            overall_correct = sum(1 for r in recent_records if r.is_correct)
            
            # 创建准确率指标
            metrics = AccuracyMetrics(
                combination_accuracy=combination_correct / total_predictions if total_predictions > 0 else 0.0,
                sum_range_accuracy=sum_range_correct / total_predictions if total_predictions > 0 else 0.0,
                overall_accuracy=overall_correct / total_predictions if total_predictions > 0 else 0.0,
                total_predictions=total_predictions,
                correct_predictions=overall_correct,
                time_period="24h"
            )
            
            # 存储到Redis
            redis_client.setex(
                self.accuracy_metrics_key,
                3600,  # 1小时过期
                json.dumps(asdict(metrics))
            )
            
            logger.info(f"Accuracy metrics updated: {metrics.overall_accuracy:.3f}")
            
        except Exception as e:
            logger.error(f"Failed to update accuracy metrics: {e}")
    
    def _get_recent_predictions(self, hours: int = 24) -> List[PredictionRecord]:
        """获取最近指定小时内的预测记录"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # 从Redis获取所有预测记录
            all_records = redis_client.hgetall(self.prediction_history_key)
            recent_records = []
            
            # Process records in batches to avoid memory issues
            batch_size = BATCH_SIZE
            record_items = list(all_records.items())
            
            for i in range(0, len(record_items), batch_size):
                batch = record_items[i:i + batch_size]
                
                for record_id, record_data in batch:
                    try:
                        record_dict = json.loads(record_data)
                        record = PredictionRecord.from_dict(record_dict)
                        
                        if record.timestamp >= cutoff_time:
                            recent_records.append(record)
                    except (json.JSONDecodeError, KeyError, ValueError) as parse_error:
                        logger.warning(f"Failed to parse record {record_id}: {parse_error}")
                        continue
            
            # 按时间排序
            recent_records.sort(key=lambda x: x.timestamp)
            logger.debug(f"Retrieved {len(recent_records)} recent predictions from last {hours}h")
            return recent_records
            
        except Exception as e:
            logger.error(f"Failed to get recent predictions: {e}")
            return []
    
    def get_accuracy_metrics(self, time_period: str = "24h") -> Dict[str, Any]:
        """
        获取准确率指标
        
        Args:
            time_period: 时间周期 ("1h", "24h", "7d")
            
        Returns:
            准确率指标字典
        """
        try:
            # 从缓存获取
            cached_metrics = redis_client.get(self.accuracy_metrics_key)
            if cached_metrics:
                return json.loads(cached_metrics)
            
            # 如果缓存不存在，重新计算
            hours_mapping = {"1h": 1, "24h": 24, "7d": 168}
            hours = hours_mapping.get(time_period, 24)
            
            recent_records = self._get_recent_predictions(hours)
            
            if not recent_records:
                return {
                    "combination_accuracy": 0.0,
                    "sum_range_accuracy": 0.0,
                    "overall_accuracy": 0.0,
                    "total_predictions": 0,
                    "correct_predictions": 0,
                    "time_period": time_period
                }
            
            # 计算指标
            total = len(recent_records)
            combination_correct = sum(1 for r in recent_records 
                                   if r.actual_combination and 
                                   r.predicted_combination == r.actual_combination)
            
            sum_range_correct = sum(1 for r in recent_records 
                                  if r.actual_sum is not None and 
                                  self._is_sum_in_range(r.actual_sum, r.predicted_sum_range))
            
            overall_correct = sum(1 for r in recent_records if r.is_correct)
            
            return {
                "combination_accuracy": combination_correct / total,
                "sum_range_accuracy": sum_range_correct / total,
                "overall_accuracy": overall_correct / total,
                "total_predictions": total,
                "correct_predictions": overall_correct,
                "time_period": time_period
            }
            
        except Exception as e:
            logger.error(f"Failed to get accuracy metrics: {e}")
            return {"error": str(e)}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            metrics = {
                "response_time": {
                    "avg_ms": 0.0,
                    "min_ms": 0.0,
                    "max_ms": 0.0,
                    "p95_ms": 0.0,
                    "p99_ms": 0.0
                },
                "throughput": {
                    "requests_per_minute": 0.0,
                    "predictions_per_hour": 0.0
                },
                "accuracy": {
                    "current_window": 0.0,
                    "trend": "stable"
                },
                "system": {
                    "redis_connected": False,
                    "cache_hit_rate": 0.0
                }
            }
            
            # 响应时间统计
            if self.response_times:
                response_times_list = list(self.response_times)
                metrics["response_time"]["avg_ms"] = statistics.mean(response_times_list)
                metrics["response_time"]["min_ms"] = min(response_times_list)
                metrics["response_time"]["max_ms"] = max(response_times_list)
                
                # 计算百分位数
                sorted_times = sorted(response_times_list)
                n = len(sorted_times)
                metrics["response_time"]["p95_ms"] = sorted_times[int(n * 0.95)] if n > 0 else 0.0
                metrics["response_time"]["p99_ms"] = sorted_times[int(n * 0.99)] if n > 0 else 0.0
            
            # 准确率统计
            if self.accuracy_window:
                current_accuracy = sum(self.accuracy_window) / len(self.accuracy_window)
                metrics["accuracy"]["current_window"] = current_accuracy
                
                # 计算趋势
                if len(self.accuracy_window) >= 20:
                    first_half = sum(list(self.accuracy_window)[:10]) / 10
                    second_half = sum(list(self.accuracy_window)[-10:]) / 10
                    
                    if second_half > first_half + TREND_THRESHOLD:
                        metrics["accuracy"]["trend"] = "improving"
                    elif second_half < first_half - TREND_THRESHOLD:
                        metrics["accuracy"]["trend"] = "declining"
                    else:
                        metrics["accuracy"]["trend"] = "stable"
            
            # 系统状态
            try:
                redis_client.ping()
                metrics["system"]["redis_connected"] = True
            except:
                metrics["system"]["redis_connected"] = False
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e)}
    
    def get_prediction_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取预测历史记录"""
        try:
            recent_records = self._get_recent_predictions(hours=168)  # 7天
            
            # 按时间倒序排序，取最新的记录
            recent_records.sort(key=lambda x: x.timestamp, reverse=True)
            limited_records = recent_records[:limit]
            
            return [record.to_dict() for record in limited_records]
            
        except Exception as e:
            logger.error(f"Failed to get prediction history: {e}")
            return []
    
    def cleanup_old_data(self, days: int = PREDICTION_RETENTION_DAYS):
        """清理旧数据"""
        if days <= 0:
            logger.error("Invalid days parameter for cleanup")
            return
        
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            # 获取所有记录
            all_records = redis_client.hgetall(self.prediction_history_key)
            deleted_count = 0
            
            for record_id, record_data in all_records.items():
                try:
                    record_dict = json.loads(record_data)
                    record_time = datetime.fromisoformat(record_dict['timestamp'])
                    
                    if record_time < cutoff_time:
                        redis_client.hdel(self.prediction_history_key, record_id)
                        deleted_count += 1
                except (json.JSONDecodeError, KeyError, ValueError) as parse_error:
                    logger.warning(f"Failed to parse record {record_id} during cleanup: {parse_error}")
                    # Delete corrupted records
                    redis_client.hdel(self.prediction_history_key, record_id)
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old prediction records")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    def get_accuracy_trend(self, days: int = 7) -> Dict[str, Any]:
        """
        计算最近days天的准确率趋势和智能方向分析
        
        Args:
            days: 分析天数（默认7天）
            
        Returns:
            每日准确率趋势数据，包含智能方向分析
        """
        if days < MIN_TREND_DAYS or days > MAX_TREND_DAYS:
            logger.error(f"Invalid days parameter: {days}")
            return {"error": f"天数必须在{MIN_TREND_DAYS}-{MAX_TREND_DAYS}之间"}
        
        try:
            # 获取最近的预测记录
            recent_records = self._get_recent_predictions(hours=days * 24)
            
            if not recent_records:
                return {
                    "trend": [],
                    "direction": "stable",
                    "summary": {
                        "total_days": 0,
                        "avg_accuracy": 0.0,
                        "trend_direction": "stable"
                    }
                }
            
            # 按日期分组统计
            daily_stats = defaultdict(lambda: {"correct": 0, "total": 0})
            
            for record in recent_records:
                if record.is_correct is not None:  # 只统计已有结果的记录
                    date_key = record.timestamp.strftime("%Y-%m-%d")
                    daily_stats[date_key]["total"] += 1
                    if record.is_correct:
                        daily_stats[date_key]["correct"] += 1
            
            # 计算每日准确率
            trend_data = []
            for date_str in sorted(daily_stats.keys())[-days:]:
                stats = daily_stats[date_str]
                accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
                trend_data.append({
                    "date": date_str,
                    "accuracy": round(accuracy, 4),
                    "total_predictions": stats["total"],
                    "correct_predictions": stats["correct"]
                })
            
            # 智能趋势方向分析
            trend_direction = self._analyze_trend_direction(trend_data)
            
            # 计算总体统计
            total_correct = sum(d["correct_predictions"] for d in trend_data)
            total_predictions = sum(d["total_predictions"] for d in trend_data)
            avg_accuracy = total_correct / total_predictions if total_predictions > 0 else 0.0
            
            result = {
                "trend": trend_data,
                "direction": trend_direction,
                "summary": {
                    "total_days": len(trend_data),
                    "avg_accuracy": round(avg_accuracy, 4),
                    "trend_direction": trend_direction,
                    "total_predictions": total_predictions,
                    "total_correct": total_correct
                }
            }
            
            # 触发趋势警报
            self.trigger_alert("trend", {
                "direction": trend_direction,
                "accuracy": avg_accuracy,
                "days": days
            })
            
            # 触发低准确率警报
            if avg_accuracy < LOW_ACCURACY_THRESHOLD:
                self.trigger_alert("low_accuracy", {
                    "accuracy": avg_accuracy,
                    "threshold": LOW_ACCURACY_THRESHOLD,
                    "days": days
                })
            
            logger.info(f"Accuracy trend calculated: {avg_accuracy:.3f} over {days} days, direction: {trend_direction}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate accuracy trend: {e}")
            return {"error": str(e)}
    
    def _analyze_trend_direction(self, trend_data: List[Dict[str, Any]]) -> str:
        """
        智能分析趋势方向
        
        Args:
            trend_data: 趋势数据列表
            
        Returns:
            趋势方向: improving/declining/stable
        """
        if len(trend_data) < 2:
            return "stable"
        
        # 方法1: 对比前后期平均值（优先使用）
        if len(trend_data) >= 4:  # 至少4个数据点
            mid_point = len(trend_data) // 2
            recent_avg = sum(d["accuracy"] for d in trend_data[mid_point:]) / len(trend_data[mid_point:])
            earlier_avg = sum(d["accuracy"] for d in trend_data[:mid_point]) / mid_point
            
            delta = recent_avg - earlier_avg
            if abs(delta) > 0.05:  # 5%阈值，更明显的趋势
                return "improving" if delta > 0 else "declining"
        
        # 方法2: 简单对比最近两天（作为备选）
        recent_accuracy = trend_data[-1]["accuracy"]
        previous_accuracy = trend_data[-2]["accuracy"]
        delta = recent_accuracy - previous_accuracy
        
        if abs(delta) > 0.10:  # 10%阈值，避免噪音
            return "improving" if delta > 0 else "declining"
        
        return "stable"
    
    def trigger_alert(self, alert_type: str, data: Dict[str, Any], webhook_url: str = "https://webhook.example.com") -> None:
        """
        触发系统警报并发送Webhook通知
        
        Args:
            alert_type: 警报类型 (low_accuracy/trend/system)
            data: 警报数据
            webhook_url: Webhook通知URL
        """
        # Input validation
        if not isinstance(alert_type, str) or not alert_type.strip():
            logger.error(f"Invalid alert_type: {alert_type}")
            return
        
        if not isinstance(data, dict):
            logger.error(f"Invalid data type for alert: {type(data)}")
            return
        
        if alert_type not in ["low_accuracy", "trend", "system"]:
            logger.error(f"Invalid alert_type: {alert_type}")
            return
        
        try:
            # 确定警报严重性
            severity = self._determine_alert_severity(alert_type, data)
            
            alert = {
                "type": alert_type,
                "timestamp": datetime.now().isoformat(),
                "data": data,
                "severity": severity
            }
            
            # 记录警报到Redis
            alert_key = f"{self.cache_prefix}alerts"
            redis_client.lpush(alert_key, json.dumps(alert))
            redis_client.ltrim(alert_key, 0, MAX_ALERTS_STORED - 1)  # 保留最近100个警报
            redis_client.expire(alert_key, ALERT_RETENTION_DAYS * 24 * 3600)  # 7天过期
            
            # 发送Webhook通知（仅对warning级别）
            if severity == "warning":
                self._send_webhook_notification(webhook_url, alert)
            
            # 根据警报类型记录不同级别的日志
            if alert_type == "low_accuracy":
                logger.warning(f"低准确率警报：{data.get('accuracy', 0):.2%} < {data.get('threshold', 0.5):.2%} (过去{data.get('days', 0)}天)")
            elif alert_type == "trend":
                logger.info(f"趋势警报：方向={data.get('direction', 'unknown')}, 准确率={data.get('accuracy', 0):.2%}")
            else:
                logger.info(f"系统警报 [{alert_type}]: {data}")
                
        except Exception as e:
            logger.error(f"Failed to trigger alert: {e}")
    
    def _determine_alert_severity(self, alert_type: str, data: Dict[str, Any]) -> str:
        """
        确定警报严重性级别
        
        Args:
            alert_type: 警报类型
            data: 警报数据
            
        Returns:
            严重性级别: info/warning/error
        """
        if alert_type == "low_accuracy":
            accuracy = data.get("accuracy", 1.0)
            if accuracy < 0.40:
                return "error"
            elif accuracy < LOW_ACCURACY_THRESHOLD:
                return "warning"
        elif alert_type == "trend":
            direction = data.get("direction", "stable")
            accuracy = data.get("accuracy", 1.0)
            if direction == "declining" and accuracy < 0.45:
                return "warning"
        elif alert_type == "system":
            return data.get("severity", "info")
        
        return "info"
    
    def _send_webhook_notification(self, webhook_url: str, alert: Dict[str, Any]) -> None:
        """
        发送Webhook通知
        
        Args:
            webhook_url: Webhook URL
            alert: 警报数据
        """
        try:
            import requests
            
            response = requests.post(
                webhook_url,
                json=alert,
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            logger.info(f"Webhook通知发送成功: {webhook_url}")
            
        except ImportError:
            logger.warning("requests库未安装，跳过Webhook通知")
        except Exception as e:
            logger.error(f"Webhook通知失败 ({webhook_url}): {e}")
            # 实现重试机制
            self._retry_webhook_notification(webhook_url, alert)
    
    def _retry_webhook_notification(self, webhook_url: str, alert: Dict[str, Any], max_retries: int = 3) -> None:
        """
        Webhook通知重试机制
        
        Args:
            webhook_url: Webhook URL
            alert: 警报数据
            max_retries: 最大重试次数
        """
        import time
        import requests
        
        for attempt in range(max_retries):
            try:
                time.sleep(2 ** attempt)  # 指数退避: 2, 4, 8秒
                response = requests.post(webhook_url, json=alert, timeout=5)
                response.raise_for_status()
                logger.info(f"Webhook重试成功 (第{attempt + 1}次): {webhook_url}")
                return
            except Exception as e:
                logger.warning(f"Webhook重试失败 (第{attempt + 1}次): {e}")
        
        logger.error(f"Webhook通知最终失败，已重试{max_retries}次: {webhook_url}")
    
    def get_alerts(self, limit: int = 50, severity: str = None) -> Dict[str, Any]:
        """
        获取系统警报历史，支持按严重性过滤
        
        Args:
            limit: 返回警报数量限制 (1-1000)
            severity: 严重性级别过滤 (info/warning/error)
            
        Returns:
            警报列表和统计信息
        """
        # Input validation
        if not isinstance(limit, int) or limit < 1 or limit > 1000:
            logger.error(f"Invalid limit parameter: {limit}")
            return {"alerts": [], "error": "limit必须在1-1000之间"}
        
        if severity and severity not in ["info", "warning", "error"]:
            logger.error(f"Invalid severity parameter: {severity}")
            return {"alerts": [], "error": "severity必须是info/warning/error之一"}
        
        try:
            alert_key = f"{self.cache_prefix}alerts"
            alerts_data = redis_client.lrange(alert_key, 0, limit * 2 - 1)  # 获取更多数据以便过滤
            
            alerts = []
            for alert_data in alerts_data:
                try:
                    alert = json.loads(alert_data)
                    
                    # 按严重性过滤
                    if severity and alert.get("severity") != severity:
                        continue
                    
                    alerts.append(alert)
                    
                    # 达到限制数量就停止
                    if len(alerts) >= limit:
                        break
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse alert data: {e}")
                    continue
            
            # 统计信息
            stats = self._calculate_alert_stats(alerts_data)
            
            return {
                "alerts": alerts,
                "stats": stats,
                "total_count": len(alerts),
                "filtered_by": severity
            }
            
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return {"alerts": [], "error": str(e)}
    
    def get_visualization_data(self, days: int = 7) -> Dict[str, Any]:
        """
        生成监控数据可视化，供前端图表渲染
        
        Args:
            days: 趋势分析天数
            
        Returns:
            可视化数据包含趋势、警报统计、性能指标
        """
        try:
            # 获取趋势数据
            trend_result = self.get_accuracy_trend(days)
            
            # 获取警报统计
            alerts_result = self.get_alerts(limit=100)
            alert_stats = alerts_result.get("stats", {"info": 0, "warning": 0, "error": 0})
            
            # 获取性能指标
            performance_metrics = self.get_performance_metrics()
            
            # 计算准确率分布
            accuracy_distribution = self._calculate_accuracy_distribution(trend_result.get("trend", []))
            
            # 生成时间序列数据
            time_series = self._generate_time_series_data(trend_result.get("trend", []))
            
            visualization_data = {
                "trend": {
                    "data": trend_result.get("trend", []),
                    "direction": trend_result.get("direction", "stable"),
                    "summary": trend_result.get("summary", {})
                },
                "alerts": {
                    "stats": alert_stats,
                    "recent_alerts": alerts_result.get("alerts", [])[:10]  # 最近10个警报
                },
                "performance": {
                    "response_times": performance_metrics.get("response_times", {}),
                    "accuracy_metrics": performance_metrics.get("accuracy_metrics", {})
                },
                "distribution": accuracy_distribution,
                "time_series": time_series,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "days_analyzed": days,
                    "data_points": len(trend_result.get("trend", []))
                }
            }
            
            logger.info(f"Generated visualization data for {days} days")
            return visualization_data
            
        except Exception as e:
            logger.error(f"Failed to generate visualization data: {e}")
            return {"error": str(e)}
    
    def _calculate_accuracy_distribution(self, trend_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算准确率分布统计
        
        Args:
            trend_data: 趋势数据
            
        Returns:
            准确率分布信息
        """
        if not trend_data:
            return {"ranges": {}, "average": 0.0, "std_dev": 0.0}
        
        accuracies = [d["accuracy"] for d in trend_data]
        
        # 分区间统计
        ranges = {
            "excellent": sum(1 for a in accuracies if a >= 0.70),  # >=70%
            "good": sum(1 for a in accuracies if 0.60 <= a < 0.70),  # 60-70%
            "average": sum(1 for a in accuracies if 0.50 <= a < 0.60),  # 50-60%
            "poor": sum(1 for a in accuracies if a < 0.50)  # <50%
        }
        
        # 统计指标
        import statistics
        avg_accuracy = statistics.mean(accuracies)
        std_dev = statistics.stdev(accuracies) if len(accuracies) > 1 else 0.0
        
        return {
            "ranges": ranges,
            "average": round(avg_accuracy, 4),
            "std_dev": round(std_dev, 4),
            "min": min(accuracies),
            "max": max(accuracies)
        }
    
    def _generate_time_series_data(self, trend_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        生成时间序列数据，适合图表展示
        
        Args:
            trend_data: 趋势数据
            
        Returns:
            时间序列数据
        """
        time_series = []
        
        for i, data_point in enumerate(trend_data):
            time_series.append({
                "x": data_point["date"],
                "y": data_point["accuracy"],
                "predictions": data_point["total_predictions"],
                "correct": data_point["correct_predictions"],
                "day_index": i + 1
            })
        
        return time_series
    
    def _calculate_alert_stats(self, alerts_data: List[str]) -> Dict[str, int]:
        """
        计算警报统计信息
        
        Args:
            alerts_data: 原始警报数据列表
            
        Returns:
            按严重性分组的统计信息
        """
        stats = {"info": 0, "warning": 0, "error": 0, "total": 0}
        
        for alert_data in alerts_data:
            try:
                alert = json.loads(alert_data)
                severity = alert.get("severity", "info")
                if severity in stats:
                    stats[severity] += 1
                stats["total"] += 1
            except json.JSONDecodeError:
                continue
        
        return stats

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态概览"""
        try:
            status = {
                "monitor_status": "healthy",
                "redis_connected": False,
                "total_predictions": 0,
                "memory_usage": {
                    "response_times_count": len(self.response_times),
                    "accuracy_window_count": len(self.accuracy_window)
                },
                "last_updated": datetime.now().isoformat()
            }
            
            # Test Redis connection
            try:
                redis_client.ping()
                status["redis_connected"] = True
                
                # Get total prediction count
                all_records = redis_client.hgetall(self.prediction_history_key)
                status["total_predictions"] = len(all_records)
                
                # Get recent alerts count
                alert_key = f"{self.cache_prefix}alerts"
                recent_alerts = redis_client.llen(alert_key)
                status["recent_alerts"] = recent_alerts
                
            except Exception as redis_error:
                logger.warning(f"Redis connection failed: {redis_error}")
                status["monitor_status"] = "degraded"
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                "monitor_status": "error",
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }

# 全局监控器实例
_monitor = None

def get_monitor() -> PC28Monitor:
    """获取单例监控器实例"""
    global _monitor
    if _monitor is None:
        _monitor = PC28Monitor()
    return _monitor