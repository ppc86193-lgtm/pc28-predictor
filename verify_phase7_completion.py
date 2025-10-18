#!/usr/bin/env python3
"""
第七阶段完成验证脚本
Phase 7 Completion Verification Script
"""

import os
import json
import yaml
from datetime import datetime
from typing import Dict, List, Any

def check_file_exists(file_path: str, description: str) -> bool:
    """检查文件是否存在"""
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✅ {description}: {file_path} ({size} bytes)")
        return True
    else:
        print(f"❌ {description}: {file_path} - 文件不存在")
        return False

def validate_yaml_file(file_path: str, description: str) -> bool:
    """验证YAML文件格式"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        print(f"✅ {description}: YAML格式有效")
        return True
    except Exception as e:
        print(f"❌ {description}: YAML格式错误 - {e}")
        return False

def validate_dockerfile(file_path: str) -> bool:
    """验证Dockerfile内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_instructions = [
            'FROM python:3.13-slim',
            'WORKDIR /app',
            'COPY requirements.txt',
            'RUN pip install',
            'USER app',
            'EXPOSE 8000',
            'HEALTHCHECK',
            'CMD'
        ]
        
        missing = []
        for instruction in required_instructions:
            if instruction not in content:
                missing.append(instruction)
        
        if missing:
            print(f"❌ Dockerfile缺少指令: {missing}")
            return False
        else:
            print("✅ Dockerfile: 所有必要指令存在")
            return True
            
    except Exception as e:
        print(f"❌ Dockerfile验证失败: {e}")
        return False

def validate_docker_compose(file_path: str) -> bool:
    """验证docker-compose配置"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        required_services = ['redis', 'app', 'celery-worker', 'prometheus']
        services = config.get('services', {})
        
        missing_services = []
        for service in required_services:
            if service not in services:
                missing_services.append(service)
        
        if missing_services:
            print(f"❌ docker-compose缺少服务: {missing_services}")
            return False
        
        # 检查网络配置
        if 'networks' not in config:
            print("❌ docker-compose缺少网络配置")
            return False
        
        # 检查数据卷配置
        if 'volumes' not in config:
            print("❌ docker-compose缺少数据卷配置")
            return False
        
        print("✅ docker-compose: 配置完整")
        return True
        
    except Exception as e:
        print(f"❌ docker-compose验证失败: {e}")
        return False

def validate_kubernetes_manifest(file_path: str) -> bool:
    """验证Kubernetes清单"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分割多个YAML文档
        docs = list(yaml.safe_load_all(content))
        
        # 检查资源类型
        resource_types = [doc.get('kind') for doc in docs if doc]
        expected_types = [
            'Namespace', 'ConfigMap', 'Deployment', 'Service', 
            'PersistentVolumeClaim', 'HorizontalPodAutoscaler'
        ]
        
        missing_types = []
        for expected_type in expected_types:
            if expected_type not in resource_types:
                missing_types.append(expected_type)
        
        if missing_types:
            print(f"❌ Kubernetes清单缺少资源类型: {missing_types}")
            return False
        
        print("✅ Kubernetes清单: 所有必要资源类型存在")
        return True
        
    except Exception as e:
        print(f"❌ Kubernetes清单验证失败: {e}")
        return False

def validate_prometheus_config(file_path: str) -> bool:
    """验证Prometheus配置"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 检查必要配置
        if 'global' not in config:
            print("❌ Prometheus配置缺少global部分")
            return False
        
        if 'scrape_configs' not in config:
            print("❌ Prometheus配置缺少scrape_configs部分")
            return False
        
        # 检查PC28监控配置
        pc28_job = None
        for job in config['scrape_configs']:
            if job.get('job_name') == 'pc28-predictor':
                pc28_job = job
                break
        
        if not pc28_job:
            print("❌ Prometheus配置缺少pc28-predictor监控任务")
            return False
        
        if pc28_job.get('metrics_path') != '/metrics':
            print("❌ Prometheus配置metrics路径错误")
            return False
        
        print("✅ Prometheus配置: 配置完整")
        return True
        
    except Exception as e:
        print(f"❌ Prometheus配置验证失败: {e}")
        return False

def validate_requirements(file_path: str) -> bool:
    """验证requirements.txt"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_packages = [
            'prometheus-client',
            'psutil',
            'celery',
            'fastapi',
            'uvicorn',
            'redis',
            'numpy',
            'scipy',
            'pydantic',
            'httpx',
            'tenacity'
        ]
        
        missing_packages = []
        for package in required_packages:
            if package not in content:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ requirements.txt缺少依赖: {missing_packages}")
            return False
        
        print("✅ requirements.txt: 所有必要依赖存在")
        return True
        
    except Exception as e:
        print(f"❌ requirements.txt验证失败: {e}")
        return False

def generate_completion_summary() -> Dict[str, Any]:
    """生成完成总结"""
    return {
        "phase": "Phase 7 - Deployment",
        "completion_date": datetime.now().isoformat(),
        "status": "completed",
        "deployment_files": {
            "dockerfile": "pc28_predictor/Dockerfile",
            "docker_compose": "pc28_predictor/docker-compose.yml",
            "kubernetes": "pc28_predictor/k8s-deployment.yaml",
            "prometheus": "pc28_predictor/prometheus.yml",
            "requirements": "pc28_predictor/requirements.txt"
        },
        "next_steps": [
            "生产环境部署",
            "5000周期验证测试",
            "性能监控验证",
            "准确率目标验证"
        ],
        "performance_targets": {
            "response_time_p95": "<2s",
            "uptime": "99.9%",
            "combination_accuracy": "56-61%",
            "big_small_accuracy": "61-66%",
            "sum_range_accuracy": "65-70%"
        }
    }

def main():
    """主验证函数"""
    print("🚀 第七阶段部署完成验证")
    print("=" * 50)
    
    # 验证部署文件
    deployment_files = [
        ("pc28_predictor/Dockerfile", "Dockerfile"),
        ("pc28_predictor/docker-compose.yml", "Docker Compose配置"),
        ("pc28_predictor/k8s-deployment.yaml", "Kubernetes部署清单"),
        ("pc28_predictor/prometheus.yml", "Prometheus监控配置"),
        ("pc28_predictor/requirements.txt", "Python依赖文件")
    ]
    
    print("\n📁 检查部署文件...")
    file_checks = []
    for file_path, description in deployment_files:
        file_checks.append(check_file_exists(file_path, description))
    
    print("\n🔍 验证配置文件格式...")
    
    # 验证各个配置文件
    validations = []
    
    # Dockerfile验证
    if os.path.exists("pc28_predictor/Dockerfile"):
        validations.append(validate_dockerfile("pc28_predictor/Dockerfile"))
    
    # docker-compose验证
    if os.path.exists("pc28_predictor/docker-compose.yml"):
        validations.append(validate_docker_compose("pc28_predictor/docker-compose.yml"))
    
    # Kubernetes验证
    if os.path.exists("pc28_predictor/k8s-deployment.yaml"):
        validations.append(validate_kubernetes_manifest("pc28_predictor/k8s-deployment.yaml"))
    
    # Prometheus验证
    if os.path.exists("pc28_predictor/prometheus.yml"):
        validations.append(validate_prometheus_config("pc28_predictor/prometheus.yml"))
    
    # requirements.txt验证
    if os.path.exists("pc28_predictor/requirements.txt"):
        validations.append(validate_requirements("pc28_predictor/requirements.txt"))
    
    # 统计结果
    files_passed = sum(file_checks)
    files_total = len(file_checks)
    validations_passed = sum(validations)
    validations_total = len(validations)
    
    print("\n📊 验证结果总结:")
    print(f"文件检查: {files_passed}/{files_total} 通过")
    print(f"配置验证: {validations_passed}/{validations_total} 通过")
    
    overall_success = files_passed == files_total and validations_passed == validations_total
    
    if overall_success:
        print("\n🎉 第七阶段部署配置验证通过！")
        print("✅ 所有部署文件已准备就绪")
        print("✅ 配置格式验证通过")
        print("✅ 系统已准备好生产部署")
        
        # 生成完成总结
        summary = generate_completion_summary()
        with open("phase7_completion_summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 完成总结已保存到: phase7_completion_summary.json")
        
        print("\n🚀 下一步行动:")
        print("1. 部署到生产环境")
        print("2. 运行5000周期验证测试")
        print("3. 验证性能和准确率目标")
        
        return True
    else:
        print("\n❌ 第七阶段部署配置验证失败")
        print("请修复上述问题后重新验证")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)