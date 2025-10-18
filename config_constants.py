"""
Configuration Constants for PC28 Prediction System
Centralized configuration to eliminate hardcoded values
"""

from typing import Dict, Any
import os
from dataclasses import dataclass

@dataclass
class DynamicMarkovConfig:
    """Configuration for Dynamic Markov Model"""
    TARGET_ACCURACY_MIN: float = 0.56
    TARGET_ACCURACY_MAX: float = 0.61
    EMA_ALPHA_MIN: float = 0.1
    EMA_ALPHA_MAX: float = 0.9
    INITIAL_EMA_ALPHA: float = 0.3
    ADJUSTMENT_STEP: float = 0.01
    MAX_HISTORY_SIZE: int = 100
    SIGNIFICANT_CHANGE_THRESHOLD: float = 0.001
    STABILITY_VARIANCE_THRESHOLD: float = 0.001
    RECENT_STATS_WINDOW: int = 10

@dataclass
class DynamicTailConfig:
    """Configuration for Dynamic Tail Analyzer"""
    TARGET_ACCURACY_MIN: float = 0.56
    TARGET_ACCURACY_MAX: float = 0.61
    BASE_BOOST_FACTOR: float = 1.03
    MAX_BOOST_FACTOR: float = 1.07
    MIN_BOOST_FACTOR: float = 1.01
    HIGH_BOOST_FACTOR: float = 1.05  # For low accuracy
    LOW_BOOST_FACTOR: float = 1.02   # For high accuracy
    HIGH_REDUCTION_FACTOR: float = 0.94  # For low accuracy
    LOW_REDUCTION_FACTOR: float = 0.98   # For high accuracy
    BASE_REDUCTION_FACTOR: float = 0.96  # For target range
    TARGET_TAILS: list = None
    HIGH_FREQUENCY_THRESHOLD: float = 0.15
    MAX_HISTORY_SIZE: int = 100
    
    def __post_init__(self):
        if self.TARGET_TAILS is None:
            self.TARGET_TAILS = [7, 8, 9]

@dataclass
class HealthScoreConfig:
    """Configuration for System Health Scoring"""
    BASE_SCORE: float = 100.0
    
    # Response time thresholds and penalties
    RESPONSE_TIME_CRITICAL: float = 2.0    # >2s: -30 points
    RESPONSE_TIME_SLOW: float = 1.0        # >1s: -15 points  
    RESPONSE_TIME_MODERATE: float = 0.5    # >0.5s: -5 points
    
    PENALTY_CRITICAL: float = 30.0
    PENALTY_SLOW: float = 15.0
    PENALTY_MODERATE: float = 5.0
    
    # Accuracy thresholds and penalties
    ACCURACY_POOR: float = 0.4             # <40%: -20 points
    ACCURACY_LOW: float = 0.5              # <50%: -10 points
    
    ACCURACY_PENALTY_POOR: float = 20.0
    ACCURACY_PENALTY_LOW: float = 10.0
    ACCURACY_PENALTY_ERROR: float = 10.0   # Error getting accuracy

@dataclass
class MonitoringConfig:
    """Configuration for Monitoring System"""
    TREND_THRESHOLD: float = 0.05
    ACCURACY_WINDOW_SIZE: int = 1000
    RESPONSE_TIME_WINDOW_SIZE: int = 1000
    ALERT_WINDOW_SIZE: int = 100
    PREDICTION_RETENTION_DAYS: int = 30
    
    # Webhook configuration
    WEBHOOK_TIMEOUT: int = 10
    WEBHOOK_RETRY_COUNT: int = 3
    WEBHOOK_RETRY_BASE_DELAY: int = 2      # 指数退避基础延迟
    WEBHOOK_MAX_DELAY: int = 16            # 最大延迟时间
    
    # Performance thresholds
    SLOW_RESPONSE_THRESHOLD: float = 2.0   # seconds
    LOW_ACCURACY_THRESHOLD: float = 0.5    # 50%
    
    # 百分位数配置
    PERCENTILE_50: float = 0.50
    PERCENTILE_95: float = 0.95
    PERCENTILE_99: float = 0.99
    
    # 准确率分级阈值
    ACCURACY_EXCELLENT: float = 0.70       # 优秀 >=70%
    ACCURACY_GOOD_MIN: float = 0.60        # 良好 60-70%
    ACCURACY_GOOD_MAX: float = 0.70
    ACCURACY_AVERAGE_MIN: float = 0.50     # 一般 50-60%
    ACCURACY_AVERAGE_MAX: float = 0.60
    ACCURACY_POOR_MAX: float = 0.50        # 差 <50%

@dataclass
class TestConfig:
    """Configuration for Test Data"""
    DEFAULT_TAIL_FREQUENCIES: Dict[int, float] = None
    DEFAULT_STATE_PROBABILITIES: Dict[str, float] = None
    
    def __post_init__(self):
        if self.DEFAULT_TAIL_FREQUENCIES is None:
            self.DEFAULT_TAIL_FREQUENCIES = {
                7: 0.16, 8: 0.14, 9: 0.12, 0: 0.08, 1: 0.09, 
                2: 0.10, 3: 0.09, 4: 0.08, 5: 0.07, 6: 0.07
            }
        if self.DEFAULT_STATE_PROBABILITIES is None:
            self.DEFAULT_STATE_PROBABILITIES = {
                "大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25
            }

@dataclass
class MonitoringMetricsConfig:
    """Configuration for Monitoring Metrics Names"""
    MONITOR_REQUESTS_METRIC: str = "monitor_requests_total"
    MONITOR_DURATION_METRIC: str = "monitor_duration_seconds"
    ACCURACY_GAUGE_METRIC: str = "prediction_accuracy"
    RESPONSE_TIME_GAUGE_METRIC: str = "response_time_ms"
    SYSTEM_HEALTH_GAUGE_METRIC: str = "system_health_score"

@dataclass
class PrometheusConfig:
    """Configuration for Prometheus Integration"""
    CPU_SAMPLE_INTERVAL: float = 0.1       # seconds
    MEMORY_UNIT_DIVISOR: int = 1024 * 1024  # Convert bytes to MB
    METRICS_UPDATE_INTERVAL: float = 15.0   # seconds
    
    # Metric names (can be customized)
    PREDICT_REQUESTS_METRIC: str = "predict_requests_total"
    PREDICT_DURATION_METRIC: str = "predict_duration_seconds"
    CPU_USAGE_METRIC: str = "cpu_usage_percent"
    MEMORY_USAGE_METRIC: str = "memory_usage_mb"
    SYSTEM_UPTIME_METRIC: str = "system_uptime_seconds"
    ACTIVE_CONNECTIONS_METRIC: str = "active_connections"

@dataclass
class PredictionEngineConfig:
    """Configuration for Prediction Engine"""
    # 置信度因子
    HIGH_CONFIDENCE_FACTOR: float = 0.85    # 统计显著时
    LOW_CONFIDENCE_FACTOR: float = 0.50     # 统计不显著时
    
    # 概率强度置信度
    HIGH_PROB_CONFIDENCE: float = 0.9       # 高概率预测
    MEDIUM_PROB_CONFIDENCE: float = 0.75    # 中等概率预测
    LOW_PROB_CONFIDENCE: float = 0.6        # 低概率预测
    
    # 历史准确率置信度
    HIGH_ACCURACY_CONFIDENCE: float = 0.9   # 高准确率历史
    MEDIUM_ACCURACY_CONFIDENCE: float = 0.75 # 中等准确率历史
    LOW_ACCURACY_CONFIDENCE: float = 0.6    # 低准确率历史
    
    # 缓存配置
    CACHE_EXPIRY_SECONDS: int = 300         # 5分钟缓存
    MIN_ACCURACY_SAMPLES: int = 20          # 最小准确率样本数

@dataclass
class TestConfig:
    """Configuration for Test Data"""
    DEFAULT_TAIL_FREQUENCIES: Dict[int, float] = None
    DEFAULT_STATE_PROBABILITIES: Dict[str, float] = None
    
    def __post_init__(self):
        if self.DEFAULT_TAIL_FREQUENCIES is None:
            self.DEFAULT_TAIL_FREQUENCIES = {
                7: 0.16, 8: 0.14, 9: 0.12, 0: 0.08, 1: 0.09, 
                2: 0.10, 3: 0.09, 4: 0.08, 5: 0.07, 6: 0.07
            }
        if self.DEFAULT_STATE_PROBABILITIES is None:
            self.DEFAULT_STATE_PROBABILITIES = {
                "大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25
            }

@dataclass
class SystemConfig:
    """General System Configuration"""
    DEFAULT_HOST: str = "0.0.0.0"
    DEFAULT_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # API Configuration
    MAX_PREDICTION_HISTORY: int = 1000
    DEFAULT_ACCURACY_LIMIT: int = 100
    DEFAULT_TREND_DAYS: int = 7
    DEFAULT_ALERT_LIMIT: int = 50
    
    # Additional constants for backward compatibility
    DEFAULT_BOOST_FACTOR: float = 1.03
    P50_FACTOR: float = 0.50
    P95_FACTOR: float = 0.95
    P99_FACTOR: float = 0.99
    HIGH_ACCURACY_THRESHOLD: float = 0.65
    MIN_ACCURACY_THRESHOLD: float = 0.56
    TARGET_ACCURACY: float = 0.65
    BOOST_FACTOR_MAX: float = 1.07
    BOOST_FACTOR_MIN: float = 1.01
    BOOST_FACTOR_DEFAULT: float = 1.03
    RETRY_BACKOFF_BASE: int = 2

class ConfigManager:
    """Centralized configuration manager"""
    
    def __init__(self):
        self.markov = DynamicMarkovConfig()
        self.tail = DynamicTailConfig()
        self.health = HealthScoreConfig()
        self.monitoring = MonitoringConfig()
        self.prometheus = PrometheusConfig()
        self.prediction = PredictionEngineConfig()
        self.system = SystemConfig()
        self.test = TestConfig()
        
        # Load from environment variables if available
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Markov configuration
        self.markov.TARGET_ACCURACY_MIN = float(os.getenv('MARKOV_TARGET_ACCURACY_MIN', self.markov.TARGET_ACCURACY_MIN))
        self.markov.TARGET_ACCURACY_MAX = float(os.getenv('MARKOV_TARGET_ACCURACY_MAX', self.markov.TARGET_ACCURACY_MAX))
        self.markov.INITIAL_EMA_ALPHA = float(os.getenv('MARKOV_INITIAL_EMA_ALPHA', self.markov.INITIAL_EMA_ALPHA))
        
        # Tail configuration
        self.tail.TARGET_ACCURACY_MIN = float(os.getenv('TAIL_TARGET_ACCURACY_MIN', self.tail.TARGET_ACCURACY_MIN))
        self.tail.TARGET_ACCURACY_MAX = float(os.getenv('TAIL_TARGET_ACCURACY_MAX', self.tail.TARGET_ACCURACY_MAX))
        
        # Health score configuration
        self.health.RESPONSE_TIME_CRITICAL = float(os.getenv('HEALTH_RESPONSE_TIME_CRITICAL', self.health.RESPONSE_TIME_CRITICAL))
        self.health.RESPONSE_TIME_SLOW = float(os.getenv('HEALTH_RESPONSE_TIME_SLOW', self.health.RESPONSE_TIME_SLOW))
        
        # System configuration
        self.system.DEFAULT_PORT = int(os.getenv('PORT', self.system.DEFAULT_PORT))
        self.system.LOG_LEVEL = os.getenv('LOG_LEVEL', self.system.LOG_LEVEL)
    
    def get_markov_config(self) -> DynamicMarkovConfig:
        """Get Markov model configuration"""
        return self.markov
    
    def get_tail_config(self) -> DynamicTailConfig:
        """Get tail analyzer configuration"""
        return self.tail
    
    def get_health_config(self) -> HealthScoreConfig:
        """Get health score configuration"""
        return self.health
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration"""
        return self.monitoring
    
    def get_prometheus_config(self) -> PrometheusConfig:
        """Get Prometheus configuration"""
        return self.prometheus
    
    def get_prediction_config(self) -> PredictionEngineConfig:
        """Get prediction engine configuration"""
        return self.prediction
    
    def get_system_config(self) -> SystemConfig:
        """Get system configuration"""
        return self.system
    
    def get_test_config(self) -> TestConfig:
        """Get test configuration"""
        return self.test
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert all configurations to dictionary"""
        return {
            'markov': self.markov.__dict__,
            'tail': self.tail.__dict__,
            'health': self.health.__dict__,
            'monitoring': self.monitoring.__dict__,
            'prometheus': self.prometheus.__dict__,
            'prediction': self.prediction.__dict__,
            'system': self.system.__dict__,
            'test': self.test.__dict__
        }

# Global configuration instance
config = ConfigManager()

# Convenience functions for backward compatibility
def get_markov_config() -> DynamicMarkovConfig:
    return config.get_markov_config()

def get_tail_config() -> DynamicTailConfig:
    return config.get_tail_config()

def get_health_config() -> HealthScoreConfig:
    return config.get_health_config()

def get_monitoring_config() -> MonitoringConfig:
    return config.get_monitoring_config()

def get_prometheus_config() -> PrometheusConfig:
    return config.get_prometheus_config()

def get_prediction_config() -> PredictionEngineConfig:
    return config.get_prediction_config()

def get_system_config() -> SystemConfig:
    return config.get_system_config()

def get_test_config() -> TestConfig:
    return config.get_test_config()

def get_monitoring_metrics_config() -> MonitoringMetricsConfig:
    return MonitoringMetricsConfig()

# Backward compatibility - Top-level constants for production validation
TARGET_ACCURACY_MIN = config.markov.TARGET_ACCURACY_MIN
TARGET_ACCURACY_MAX = config.markov.TARGET_ACCURACY_MAX
BIG_SMALL_ACCURACY_MIN = 0.61  # 大单/小双准确率最小值
BIG_SMALL_ACCURACY_MAX = 0.66  # 大单/小双准确率最大值
SUM_RANGE_ACCURACY_MIN = 0.65  # 和值范围准确率最小值
SUM_RANGE_ACCURACY_MAX = 0.70  # 和值范围准确率最大值

# Safe divide default value
SAFE_DIVIDE_DEFAULT = 0.0