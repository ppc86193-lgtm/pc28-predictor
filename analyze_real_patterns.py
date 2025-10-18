#!/usr/bin/env python3
"""
分析真实PC28数据的实际规律
找出为什么当前算法比随机还差
"""

import requests
import hashlib
import time
import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 导入配置
try:
    from config import api_key_data, app_id, history_url
    API_KEY = api_key_data
    APP_ID = app_id
    HISTORY_URL = history_url
except ImportError:
    # 回退到硬编码（仅用于独立运行）
    import os
    API_KEY = os.getenv("API_KEY_DATA", "ca9edbfee35c22a0d6c4cf6722506af0")
    APP_ID = os.getenv("APP_ID", "45928")
    HISTORY_URL = "https://rijb.api.storeapi.net/api/119/260"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_data(days: int = 30) -> List[Dict[str, Any]]:
    """
    获取最近N天的数据
    
    Args:
        days: 要获取的天数
        
    Returns:
        包含所有记录的列表
    """
    all_data = []
    
    for day_offset in range(days):
        date = (datetime.now() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
        
        sign_str = f"appid{APP_ID}date{date}{API_KEY}"
        sign = hashlib.md5(sign_str.encode()).hexdigest()
        
        params = {
            "appid": APP_ID,
            "date": date,
            "sign": sign
        }
        
        try:
            response = requests.get(HISTORY_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("codeid") == 10000:
                records = data.get("retdata", [])
                logger.info(f"日期 {date}: {len(records)}条")
                all_data.extend(records)
            else:
                logger.warning(f"日期 {date}: API返回错误码 {data.get('codeid')}")
            
            time.sleep(0.5)  # 避免API限流
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取{date}失败: {e}")
        except ValueError as e:
            logger.error(f"解析{date}数据失败: {e}")
    
    return all_data

def safe_percentage(count: int, total: int) -> float:
    """安全计算百分比，避免除零错误"""
    return (count / total * 100) if total > 0 else 0.0

def analyze_patterns(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    分析实际规律
    
    Args:
        data: 原始数据列表
        
    Returns:
        解析后的数据列表
    """
    print("\n" + "="*60)
    print("真实数据分析")
    print("="*60)
    
    # 解析数据
    parsed = []
    parse_errors = 0
    
    for record in data:
        try:
            numbers = record.get("number", [])
            if isinstance(numbers, list):
                numbers = [int(n) for n in numbers]
            
            if len(numbers) == 3:
                sum_val = sum(numbers)
                tail = sum_val % 10
                
                # 判断组合
                if sum_val <= 5 or sum_val >= 22:
                    combo = "极值"
                elif sum_val % 2 == 0:
                    combo = "大双" if sum_val >= 14 else "小双"
                else:
                    combo = "大单" if sum_val >= 14 else "小单"
                
                parsed.append({
                    'sum': sum_val,
                    'tail': tail,
                    'combo': combo,
                    'numbers': numbers
                })
        except (ValueError, TypeError, KeyError) as e:
            parse_errors += 1
            logger.debug(f"解析记录失败: {e}")
            continue
    
    if parse_errors > 0:
        logger.warning(f"解析失败: {parse_errors}条记录")
    
    total = len(parsed)
    print(f"\n总数据量: {total}")
    
    if total == 0:
        logger.error("没有有效数据可分析")
        return parsed
    
    # 1. 组合分布
    print("\n【组合分布】")
    combo_counts = Counter([d['combo'] for d in parsed])
    for combo, count in combo_counts.most_common():
        pct = safe_percentage(count, total)
        print(f"  {combo}: {count} ({pct:.1f}%)")
    
    # 2. 和值分布
    print("\n【和值分布】")
    sum_counts = Counter([d['sum'] for d in parsed])
    BAR_SCALE = 2  # 每1%显示2个字符
    for s in range(0, 28):
        count = sum_counts.get(s, 0)
        pct = safe_percentage(count, total)
        bar = "█" * int(pct * BAR_SCALE)
        print(f"  {s:2d}: {count:4d} ({pct:4.1f}%) {bar}")
    
    # 3. 尾数分布
    print("\n【尾数分布】")
    tail_counts = Counter([d['tail'] for d in parsed])
    for t in range(10):
        count = tail_counts.get(t, 0)
        pct = safe_percentage(count, total)
        print(f"  {t}: {count} ({pct:.1f}%)")
    
    # 4. 连号分析
    print("\n【连号分析】")
    tails = [d['tail'] for d in parsed]
    if len(tails) > 1:
        consecutive = sum(1 for i in range(len(tails)-1) if abs(tails[i] - tails[i+1]) == 1)
        consecutive_pct = safe_percentage(consecutive, len(tails)-1)
        print(f"  连号次数: {consecutive} ({consecutive_pct:.1f}%)")
        
        # 5. 重复分析
        repeats = sum(1 for i in range(len(tails)-1) if tails[i] == tails[i+1])
        repeats_pct = safe_percentage(repeats, len(tails)-1)
        print(f"  重复次数: {repeats} ({repeats_pct:.1f}%)")
    else:
        print("  数据不足，无法分析")
    
    # 6. 转移概率
    print("\n【组合转移概率】")
    transitions = {}
    combos = [d['combo'] for d in parsed]
    for i in range(len(combos)-1):
        curr = combos[i]
        next_combo = combos[i+1]
        if curr not in transitions:
            transitions[curr] = Counter()
        transitions[curr][next_combo] += 1
    
    for curr in ['大单', '小双', '小单', '大双', '极值']:
        if curr in transitions:
            print(f"\n  {curr} →")
            total_trans = sum(transitions[curr].values())
            for next_combo, count in transitions[curr].most_common():
                pct = count / total_trans * 100
                print(f"    {next_combo}: {pct:.1f}%")
    
    # 7. 最佳策略
    print("\n【最佳固定策略】")
    if combo_counts:
        best_combo = combo_counts.most_common(1)[0]
        best_pct = safe_percentage(best_combo[1], total)
        print(f"  始终预测 '{best_combo[0]}': {best_pct:.1f}%")
    else:
        print("  无数据")
    
    # 8. 大小单双分析
    print("\n【大小分析】")
    big_count = sum(1 for d in parsed if '大' in d['combo'])
    small_count = total - big_count
    print(f"  大: {big_count} ({safe_percentage(big_count, total):.1f}%)")
    print(f"  小: {small_count} ({safe_percentage(small_count, total):.1f}%)")
    
    print("\n【单双分析】")
    odd_count = sum(1 for d in parsed if '单' in d['combo'])
    even_count = total - odd_count
    print(f"  单: {odd_count} ({safe_percentage(odd_count, total):.1f}%)")
    print(f"  双: {even_count} ({safe_percentage(even_count, total):.1f}%)")
    
    return parsed

if __name__ == "__main__":
    print("开始获取真实数据...")
    data = fetch_data(days=30)
    
    if data:
        analyze_patterns(data)
    else:
        print("未获取到数据")
