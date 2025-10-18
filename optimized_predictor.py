#!/usr/bin/env python3
"""
优化的PC28预测器 - 基于真实数据模式
目标：组合56-61%，大小61-66%，范围65-70%
"""

import numpy as np
from collections import Counter, deque
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class OptimizedPC28Predictor:
    """优化的PC28预测器"""
    
    def __init__(self):
        self.history_window = 200  # 历史窗口
        self.pattern_cache = {}
        
    def predict(self, historical_data: List[Dict]) -> Dict:
        """
        基于真实数据模式的预测
        
        Args:
            historical_data: 历史数据列表，每项包含sum, tail, combination
            
        Returns:
            预测结果：combination, sum_range, confidence
        """
        if len(historical_data) < 20:
            return self._default_prediction()
        
        # 使用最近的数据
        recent = historical_data[-self.history_window:]
        
        # 1. 分析组合频率分布
        combo_freq = self._analyze_combination_frequency(recent)
        
        # 2. 分析尾数模式
        tail_pattern = self._analyze_tail_pattern(recent)
        
        # 3. 分析和值分布
        sum_distribution = self._analyze_sum_distribution(recent)
        
        # 4. 检测周期性模式
        periodicity = self._detect_periodicity(recent)
        
        # 5. 综合预测
        prediction = self._综合预测(
            combo_freq, tail_pattern, sum_distribution, periodicity
        )
        
        return prediction
    
    def _analyze_combination_frequency(self, data: List[Dict]) -> Dict[str, float]:
        """分析组合频率"""
        combos = [d['combination'] for d in data]
        counter = Counter(combos)
        total = len(combos)
        
        # 计算频率并应用平滑
        freq = {}
        for combo in ['大单', '小双', '小单', '大双', '极值']:
            count = counter.get(combo, 0)
            # 拉普拉斯平滑
            freq[combo] = (count + 1) / (total + 5)
        
        return freq
    
    def _analyze_tail_pattern(self, data: List[Dict]) -> Dict:
        """分析尾数模式"""
        tails = [d['tail'] for d in data[-50:]]  # 最近50条
        
        # 尾数频率
        tail_freq = Counter(tails)
        
        # 检测连号
        consecutive = 0
        for i in range(len(tails) - 1):
            if abs(tails[i] - tails[i+1]) == 1:
                consecutive += 1
        
        # 检测重复
        repeats = sum(1 for i in range(len(tails)-1) if tails[i] == tails[i+1])
        
        # 奇偶分布
        odd_count = sum(1 for t in tails if t % 2 == 1)
        even_count = len(tails) - odd_count
        
        return {
            'freq': tail_freq,
            'consecutive_rate': consecutive / max(len(tails)-1, 1),
            'repeat_rate': repeats / max(len(tails)-1, 1),
            'odd_ratio': odd_count / len(tails),
            'even_ratio': even_count / len(tails)
        }
    
    def _analyze_sum_distribution(self, data: List[Dict]) -> Dict:
        """分析和值分布"""
        sums = [d['sum'] for d in data[-100:]]
        
        # 分段统计
        ranges = {
            '0-5': sum(1 for s in sums if 0 <= s <= 5),
            '6-9': sum(1 for s in sums if 6 <= s <= 9),
            '10-13': sum(1 for s in sums if 10 <= s <= 13),
            '14-17': sum(1 for s in sums if 14 <= s <= 17),
            '18-21': sum(1 for s in sums if 18 <= s <= 21),
            '22-27': sum(1 for s in sums if 22 <= s <= 27)
        }
        
        total = len(sums)
        return {k: v/total for k, v in ranges.items()}
    
    def _detect_periodicity(self, data: List[Dict]) -> Dict:
        """检测周期性模式"""
        combos = [d['combination'] for d in data[-60:]]
        
        # 检测3期、5期、7期周期
        patterns = {}
        for period in [3, 5, 7]:
            if len(combos) >= period * 3:
                # 检查是否有重复模式
                chunks = [combos[i:i+period] for i in range(0, len(combos)-period, period)]
                if len(chunks) >= 3:
                    # 计算最近3个周期的相似度
                    recent_chunks = chunks[-3:]
                    similarity = self._calculate_pattern_similarity(recent_chunks)
                    patterns[f'period_{period}'] = similarity
        
        return patterns
    
    def _calculate_pattern_similarity(self, chunks: List[List]) -> float:
        """计算模式相似度"""
        if len(chunks) < 2:
            return 0.0
        
        # 比较最后两个chunk
        last = chunks[-1]
        prev = chunks[-2]
        
        matches = sum(1 for i in range(min(len(last), len(prev))) 
                     if last[i] == prev[i])
        return matches / max(len(last), len(prev))
    
    def _综合预测(self, combo_freq, tail_pattern, sum_dist, periodicity) -> Dict:
        """综合各种分析进行预测"""
        
        # 基础概率（来自历史频率）
        probs = combo_freq.copy()
        
        # 根据尾数模式调整
        if tail_pattern['odd_ratio'] > 0.55:
            # 奇数尾多，增强单的概率
            probs['大单'] *= 1.3
            probs['小单'] *= 1.3
            probs['大双'] *= 0.8
            probs['小双'] *= 0.8
        elif tail_pattern['even_ratio'] > 0.55:
            # 偶数尾多，增强双的概率
            probs['大双'] *= 1.3
            probs['小双'] *= 1.3
            probs['大单'] *= 0.8
            probs['小单'] *= 0.8
        
        # 连号调整
        if tail_pattern['consecutive_rate'] > 0.3:
            probs['小双'] *= 1.2
            probs['小单'] *= 1.2
        
        # 重复调整
        if tail_pattern['repeat_rate'] > 0.2:
            probs['极值'] *= 0.7
        
        # 归一化
        total = sum(probs.values())
        probs = {k: v/total for k, v in probs.items()}
        
        # 选择最高概率
        predicted_combo = max(probs.items(), key=lambda x: x[1])[0]
        confidence = probs[predicted_combo]
        
        # 预测和值范围
        sum_range = self._predict_sum_range(predicted_combo, sum_dist)
        
        return {
            'combination': predicted_combo,
            'sum_range': sum_range,
            'confidence': confidence,
            'probabilities': probs
        }
    
    def _predict_sum_range(self, combo: str, sum_dist: Dict) -> str:
        """根据组合预测和值范围"""
        if combo == '极值':
            # 极值倾向于0-5或22-27
            if sum_dist.get('0-5', 0) > sum_dist.get('22-27', 0):
                return '0-5'
            else:
                return '22-27'
        elif combo == '小单':
            return '7-13'
        elif combo == '小双':
            return '6-12'
        elif combo == '大单':
            return '15-21'
        elif combo == '大双':
            return '14-20'
        else:
            return '10-17'
    
    def _default_prediction(self) -> Dict:
        """默认预测"""
        return {
            'combination': '大单',
            'sum_range': '14-21',
            'confidence': 0.25,
            'probabilities': {
                '大单': 0.25,
                '小双': 0.25,
                '小单': 0.25,
                '大双': 0.25,
                '极值': 0.0
            }
        }


def get_optimized_predictor():
    """获取优化预测器实例"""
    return OptimizedPC28Predictor()
