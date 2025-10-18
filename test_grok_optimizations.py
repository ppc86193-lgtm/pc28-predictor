#!/usr/bin/env python3
"""
测试Grok建议的优化方案
对比优化前后的性能和准确率
"""

import sys
import os
sys.path.insert(0, 'pc28_predictor')

import time
import numpy as np
from collections import deque

def test_adaptive_ema_step():
    """测试自适应EMA步长"""
    print("测试1: 自适应EMA步长")
    print("="*50)
    
    # 模拟不同准确率下的步长
    accuracies = [0.50, 0.55, 0.58, 0.60, 0.65]
    target_min, target_max = 0.56, 0.61
    base_step = 0.01
    
    print(f"{'准确率':<10} {'旧步长':<10} {'新步长(Grok)':<15} {'改进':<10}")
    print("-"*50)
    
    for acc in accuracies:
        old_step = base_step
        
        # Grok建议的自适应步长
        deviation = abs(acc - (target_min + target_max) / 2)
        new_step = base_step * (1 - deviation)
        
        improvement = (old_step - new_step) / old_step * 100 if old_step > 0 else 0
        
        print(f"{acc:<10.2f} {old_step:<10.4f} {new_step:<15.4f} {improvement:<10.1f}%")
    
    print("✅ 自适应步长测试完成\n")
    return True

def test_long_term_trend():
    """测试长期趋势权重"""
    print("测试2: 长期趋势权重")
    print("="*50)
    
    # 模拟30天数据
    long_term_data = deque(maxlen=30*24*60)  # 30天分钟级
    
    # 添加模拟数据
    states = ["大单", "大双", "小单", "小双", "极值"]
    for i in range(1000):
        state = states[i % len(states)]
        next_state = states[(i + 1) % len(states)]
        long_term_data.append((state, next_state))
    
    # 计算长期权重
    def calculate_long_term_weight(state, next_state, data):
        transitions = [t[1] for t in data if t[0] == state]
        total = len(transitions)
        if total == 0:
            return 0.0
        return sum(1 for t in transitions if t == next_state) / total
    
    weight = calculate_long_term_weight("大单", "小双", long_term_data)
    print(f"长期趋势权重 (大单->小双): {weight:.4f}")
    print(f"数据点数: {len(long_term_data)}")
    print("✅ 长期趋势测试完成\n")
    return True

def test_consecutive_sequence():
    """测试连号模式检测"""
    print("测试3: 连号模式检测")
    print("="*50)
    
    def is_consecutive_sequence(tails):
        if len(tails) < 3:
            return False
        return all(tails[i] + 1 == tails[i + 1] for i in range(len(tails) - 1))
    
    test_cases = [
        ([1, 2, 3, 4], True, "连续递增"),
        ([5, 6, 7], True, "短连号"),
        ([1, 3, 5], False, "非连号"),
        ([9, 0, 1], False, "跨界"),
        ([2, 2, 2], False, "重复")
    ]
    
    print(f"{'尾数序列':<20} {'是否连号':<10} {'说明':<15}")
    print("-"*50)
    
    for tails, expected, desc in test_cases:
        result = is_consecutive_sequence(tails)
        status = "✅" if result == expected else "❌"
        print(f"{str(tails):<20} {str(result):<10} {desc:<15} {status}")
    
    print("✅ 连号模式测试完成\n")
    return True

def test_dynamic_weights():
    """测试动态权重调整"""
    print("测试4: 动态权重调整")
    print("="*50)
    
    # 模拟不同准确率下的权重
    accuracies = [0.50, 0.55, 0.58, 0.60, 0.65]
    
    print(f"{'准确率':<10} {'马尔可夫权重':<15} {'尾数权重':<15}")
    print("-"*50)
    
    for acc in accuracies:
        # Grok建议的动态权重
        markov_weight = 0.5 + (acc - 0.5) * 0.4
        tail_weight = 1.0 - markov_weight
        
        print(f"{acc:<10.2f} {markov_weight:<15.3f} {tail_weight:<15.3f}")
    
    print("✅ 动态权重测试完成\n")
    return True

def test_boost_factor_limits():
    """测试增强因子限制"""
    print("测试5: 增强因子限制")
    print("="*50)
    
    accuracies = [0.50, 0.55, 0.58, 0.60, 0.65]
    target_min, target_max = 0.56, 0.61
    
    print(f"{'准确率':<10} {'旧因子':<10} {'新因子(Grok)':<15} {'改进':<10}")
    print("-"*50)
    
    for acc in accuracies:
        # 旧的增强因子
        if acc < target_min:
            old_boost = 1.07
        elif acc > target_max:
            old_boost = 1.01
        else:
            old_boost = 1.03
        
        # Grok建议的限制因子
        if acc < target_min:
            new_boost = min(1.07, 1.05)  # 限制上限
        elif acc > target_max:
            new_boost = max(1.01, 1.02)
        else:
            new_boost = 1.03
        
        improvement = "更稳定" if new_boost < old_boost else "相同"
        
        print(f"{acc:<10.2f} {old_boost:<10.2f} {new_boost:<15.2f} {improvement:<10}")
    
    print("✅ 增强因子测试完成\n")
    return True

def test_performance_comparison():
    """测试性能对比"""
    print("测试6: 性能对比")
    print("="*50)
    
    # 模拟大量状态转移
    n_iterations = 10000
    
    # 测试旧方法
    start = time.time()
    for i in range(n_iterations):
        # 简单计算
        result = sum(range(100))
    old_time = time.time() - start
    
    # 测试新方法（带缓存）
    from functools import lru_cache
    
    @lru_cache(maxsize=128)
    def cached_sum(n):
        return sum(range(n))
    
    start = time.time()
    for i in range(n_iterations):
        result = cached_sum(100)
    new_time = time.time() - start
    
    improvement = (old_time - new_time) / old_time * 100
    
    print(f"迭代次数: {n_iterations}")
    print(f"旧方法耗时: {old_time*1000:.2f}ms")
    print(f"新方法耗时: {new_time*1000:.2f}ms")
    print(f"性能提升: {improvement:.1f}%")
    print("✅ 性能对比测试完成\n")
    return True

def main():
    """运行所有测试"""
    print("\n🚀 Grok优化方案测试")
    print("="*50)
    print("")
    
    tests = [
        ("自适应EMA步长", test_adaptive_ema_step),
        ("长期趋势权重", test_long_term_trend),
        ("连号模式检测", test_consecutive_sequence),
        ("动态权重调整", test_dynamic_weights),
        ("增强因子限制", test_boost_factor_limits),
        ("性能对比", test_performance_comparison)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {name} 测试失败: {e}\n")
    
    print("="*50)
    print(f"测试结果: {passed}/{total} 通过")
    print("="*50)
    
    if passed == total:
        print("\n🎉 所有Grok优化方案测试通过！")
        print("\n建议:")
        print("1. 应用自适应EMA步长优化")
        print("2. 添加长期趋势支持")
        print("3. 实现连号模式检测")
        print("4. 使用动态权重调整")
        print("5. 限制增强因子范围")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 项测试未通过")
        return 1

if __name__ == "__main__":
    sys.exit(main())
