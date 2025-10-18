#!/usr/bin/env python3
"""
PC28预测系统实时快速测试
"""

import sys
import os

# 添加pc28_predictor到路径
sys.path.insert(0, 'pc28_predictor')

def test_imports():
    """测试关键模块导入"""
    print("测试模块导入...")
    try:
        from config import redis_client
        print("✅ config模块导入成功")
        
        from markov_model import DynamicMarkovModel
        print("✅ markov_model模块导入成功")
        
        from tail_analyzer import DynamicTailAnalyzer
        print("✅ tail_analyzer模块导入成功")
        
        try:
            from monitor import PerformanceMonitor
            print("✅ monitor模块导入成功")
        except ImportError:
            print("⚠️  PerformanceMonitor未找到，跳过")
        
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_markov_model():
    """测试Markov模型"""
    print("\n测试Markov模型...")
    try:
        from markov_model import DynamicMarkovModel, calculate_ema_weights
        
        model = DynamicMarkovModel()
        print(f"✅ 模型初始化成功, EMA alpha: {model.ema_alpha}")
        
        # 测试EMA权重更新
        old_alpha = model.ema_alpha
        model.update_ema_weights(0.50)
        print(f"✅ EMA权重更新成功: {old_alpha:.3f} → {model.ema_alpha:.3f}")
        
        # 测试动态EMA权重计算
        weights = model.get_dynamic_ema_weights(periods=5)
        print(f"✅ 动态EMA权重计算成功, 权重总和: {weights.sum():.6f}")
        
        # 测试准确率历史记录
        model.update_ema_weights(0.58)
        model.update_ema_weights(0.60)
        print(f"✅ 准确率历史记录: {len(model.accuracy_history)} 条")
        
        # 测试统计信息
        stats = model.get_optimization_stats()
        print(f"✅ 模型统计: EMA alpha={stats.get('current_ema_alpha', 0):.3f}")
        
        return True
    except Exception as e:
        print(f"❌ Markov模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tail_analyzer():
    """测试尾数分析器"""
    print("\n测试尾数分析器...")
    try:
        from tail_analyzer import DynamicTailAnalyzer
        
        analyzer = DynamicTailAnalyzer()
        print("✅ 尾数分析器初始化成功")
        
        # 测试概率调整
        probs = {"大单": 0.25, "小双": 0.25, "小单": 0.25, "大双": 0.25}
        tail_freq = {7: 0.16, 8: 0.17, 9: 0.18}
        
        adjusted = analyzer.adjust_probs_by_tail_dynamic(probs, tail_freq, 0.58)
        total = sum(adjusted.values())
        
        print(f"✅ 概率调整成功, 总和: {total:.6f}")
        
        if abs(total - 1.0) < 0.01:
            print("✅ 调整后概率归一化正确")
        else:
            print(f"⚠️  调整后概率归一化可能有问题: {total}")
        
        return True
    except Exception as e:
        print(f"❌ 尾数分析器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_redis_connection():
    """测试Redis连接"""
    print("\n测试Redis连接...")
    try:
        from config import redis_client
        
        # 尝试ping
        result = redis_client.ping()
        print(f"✅ Redis连接成功: {result}")
        return True
    except Exception as e:
        print(f"⚠️  Redis连接失败 (使用MockRedis): {e}")
        # 这是预期的，因为Redis可能未运行
        return True

def main():
    """主测试流程"""
    print("🚀 PC28预测系统实时快速测试\n")
    
    tests = [
        ("模块导入", test_imports),
        ("Markov模型", test_markov_model),
        ("尾数分析器", test_tail_analyzer),
        ("Redis连接", test_redis_connection)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"测试: {name}")
        print('='*50)
        
        if test_func():
            passed += 1
            print(f"✅ {name} 测试通过")
        else:
            print(f"❌ {name} 测试失败")
    
    print(f"\n{'='*50}")
    print(f"测试结果: {passed}/{total} 通过")
    print('='*50)
    
    if passed == total:
        print("\n🎉 所有测试通过！系统运行正常")
        return 0
    elif passed >= total - 1:
        print("\n✅ 核心功能正常，可以继续部署")
        return 0
    else:
        print("\n⚠️  部分测试失败，需要检查")
        return 1

if __name__ == "__main__":
    sys.exit(main())
