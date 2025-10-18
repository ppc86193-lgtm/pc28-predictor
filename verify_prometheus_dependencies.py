#!/usr/bin/env python3
"""
验证Prometheus依赖是否正确安装
"""

import sys
import importlib

def check_dependency(module_name, description):
    """检查单个依赖"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description} ({module_name}) - 已安装")
        return True
    except ImportError as e:
        print(f"❌ {description} ({module_name}) - 未安装: {e}")
        return False

def main():
    """主验证函数"""
    print("🔍 验证Prometheus集成依赖...")
    print("=" * 50)
    
    dependencies = [
        ("prometheus_client", "Prometheus客户端"),
        ("psutil", "系统资源监控"),
        ("redis", "Redis客户端"),
        ("fastapi", "FastAPI框架"),
        ("uvicorn", "ASGI服务器"),
        ("requests", "HTTP请求库"),
        ("numpy", "数值计算"),
        ("scipy", "科学计算"),
        ("pydantic", "数据验证"),
        ("httpx", "异步HTTP客户端"),
        ("tenacity", "重试机制"),
        ("celery", "任务队列")
    ]
    
    success_count = 0
    total_count = len(dependencies)
    
    for module_name, description in dependencies:
        if check_dependency(module_name, description):
            success_count += 1
    
    print("=" * 50)
    print(f"📊 依赖检查结果: {success_count}/{total_count} 成功")
    
    if success_count == total_count:
        print("🎉 所有依赖已正确安装！")
        
        # 测试Prometheus客户端基本功能
        try:
            from prometheus_client import Counter, Histogram, Gauge, generate_latest
            
            # 创建测试指标
            test_counter = Counter('test_requests_total', 'Test requests')
            test_histogram = Histogram('test_duration_seconds', 'Test duration')
            test_gauge = Gauge('test_value', 'Test value')
            
            # 记录一些测试数据
            test_counter.inc()
            test_histogram.observe(0.1)
            test_gauge.set(42)
            
            # 生成指标输出
            metrics_output = generate_latest()
            
            if b'test_requests_total' in metrics_output:
                print("✅ Prometheus客户端功能测试通过")
            else:
                print("❌ Prometheus客户端功能测试失败")
                
        except Exception as e:
            print(f"❌ Prometheus客户端功能测试失败: {e}")
        
        # 测试psutil基本功能
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent()
            memory_info = psutil.virtual_memory()
            
            print(f"✅ psutil功能测试通过 - CPU: {cpu_percent}%, 内存: {memory_info.used // 1024 // 1024}MB")
            
        except Exception as e:
            print(f"❌ psutil功能测试失败: {e}")
            
        return True
    else:
        print("❌ 部分依赖缺失，请运行以下命令安装:")
        print("pip install -r pc28_predictor/requirements.txt")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)