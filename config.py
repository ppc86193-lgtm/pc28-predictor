#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 伪随机心理学分析系统 - 配置文件
"""

import os
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class SystemConfig:
    """系统配置"""
    
    # 应用配置
    APP_TITLE: str = "伪随机心理学分析系统"
    APP_ICON: str = "🧠"
    VERSION: str = "1.0.0"
    
    # 页面配置
    PAGE_LAYOUT: str = "wide"
    SIDEBAR_STATE: str = "expanded"
    
    # 分析参数
    DEFAULT_MEMORY_WINDOW: int = 10
    DEFAULT_REPAIR_WINDOW: int = 3
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.75
    
    # 记忆半衰模型参数
    MEMORY_DECAY_RATE: float = 0.7
    STRONG_MEMORY_WINDOW: int = 3
    FORGET_THRESHOLD: float = 0.1
    
    # 转折点检测参数
    PRESSURE_THRESHOLD: float = 0.75
    REVERSAL_CONFIDENCE: float = 0.8
    LAG_DETECTION_WINDOW: int = 8
    
    # 错频陷阱参数
    HUMAN_WINDOW: int = 5
    AI_WINDOW: int = 50
    FREQUENCY_GAP_THRESHOLD: float = 0.15
    TRAP_DANGER_THRESHOLD: float = 0.6
    
    # 数据处理参数
    MIN_DATA_LENGTH: int = 20
    MAX_DATA_LENGTH: int = 1000
    DATA_VALIDATION_RANGE: tuple = (0, 27)
    
    # 可视化配置
    CHART_HEIGHT: int = 400
    CHART_COLORS: Dict[str, str] = None
    
    # 文件路径
    DATA_DIR: str = "data"
    RESULTS_DIR: str = "results"
    LOGS_DIR: str = "logs"
    
    # 缓存配置
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 3600  # 1小时
    
    def __post_init__(self):
        """初始化后处理"""
        if self.CHART_COLORS is None:
            self.CHART_COLORS = {
                'big': '#FF6B6B',      # 红色 - 大
                'small': '#4ECDC4',    # 蓝绿色 - 小
                'odd': '#45B7D1',      # 蓝色 - 单
                'even': '#96CEB4',     # 绿色 - 双
                'turning_point': '#FECA57',  # 黄色 - 转折点
                'memory_weight': '#A8E6CF',  # 浅绿 - 记忆权重
                'pressure': '#FFB6C1',       # 粉色 - 压力
                'trap': '#DDA0DD'            # 紫色 - 陷阱
            }
        
        # 创建必要目录
        for dir_path in [self.DATA_DIR, self.RESULTS_DIR, self.LOGS_DIR]:
            os.makedirs(dir_path, exist_ok=True)

# 全局配置实例
config = SystemConfig()

# 主题配置
STREAMLIT_THEME = {
    "primaryColor": "#1f77b4",
    "backgroundColor": "#ffffff", 
    "secondaryBackgroundColor": "#f0f2f6",
    "textColor": "#262730",
    "font": "sans serif"
}

# 分析模式配置
ANALYSIS_MODES = {
    "快速模式": {
        "memory_window": 8,
        "repair_window": 2,
        "confidence_threshold": 0.7,
        "description": "快速分析，适合实时决策"
    },
    "标准模式": {
        "memory_window": 10,
        "repair_window": 3,
        "confidence_threshold": 0.75,
        "description": "平衡准确性和速度"
    },
    "深度模式": {
        "memory_window": 15,
        "repair_window": 5,
        "confidence_threshold": 0.8,
        "description": "深度分析，更高准确性"
    }
}

# 系统状态
SYSTEM_STATUS = {
    "INITIALIZING": "🟡 系统初始化中",
    "READY": "🟢 系统就绪",
    "ANALYZING": "🔄 分析进行中", 
    "ERROR": "🔴 系统错误",
    "MAINTENANCE": "🟠 维护模式"
}