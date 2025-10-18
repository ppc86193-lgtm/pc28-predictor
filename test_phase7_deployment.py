#!/usr/bin/env python3
"""
第七阶段部署验证测试
Phase 7: Deployment Verification Tests
"""

import pytest
import requests
import time
import json
import subprocess
import os
from typing import Dict, Any

class TestPhase7Deployment:
    """第七阶段部署验证测试"""
    
    def test_docker_build(self):
        """测试Docker镜像构建"""
        print("🔨 测试Docker镜像构建...")
        
        # 构建Docker镜像
        result = subprocess.run([
            "docker", "build", "-t", "pc28-predictor:test", "pc28_predictor/"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Docker构建失败: {result.stderr}"
        print("✅ Docker镜像构建成功")
    
    def test_docker_compose_validation(self):
        """测试docker-compose配置验证"""
        print("🔍 验证docker-compose配置...")
        
        # 验证docker-compose.yml语法
        result = subprocess.run([
            "docker-compose", "-f", "pc28_predictor/docker-compose.yml", "config"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode == 0, f"docker-compose配置无效: {result.stderr}"
        print("✅ docker-compose配置验证通过")
    
    def test_kubernetes_manifest_validation(self):
        """测试Kubernetes清单验证"""
        print("🔍 验证Kubernetes清单...")
        
        # 检查kubectl是否可用
        try:
            result = subprocess.run(["kubectl", "version", "--client"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                pytest.skip("kubectl不可用，跳过Kubernetes验证")
        except FileNotFoundError:
            pytest.skip("kubectl未安装，跳过Kubernetes验证")
        
        # 验证Kubernetes清单语法
        result = subprocess.run([
            "kubectl", "apply", "--dry-run=client", "-f", "pc28_predictor/k8s-deployment.yaml"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Kubernetes清单无效: {result.stderr}"
        print("✅ Kubernetes清单验证通过")
    
    def test_prometheus_config_validation(self):
        """测试Prometheus配置验证"""
        print("🔍 验证Prometheus配置...")
        
        # 检查prometheus.yml文件存在
        prometheus_config = "pc28_predictor/prometheus.yml"
        assert os.path.exists(prometheus_config), "prometheus.yml文件不存在"
        
        # 读取并验证配置格式
        import yaml
        with open(prometheus_config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 验证必要的配置项
        assert 'global' in config, "缺少global配置"
        assert 'scrape_configs' in config, "缺少scrape_configs配置"
        
        # 验证PC28预测系统监控配置
        pc28_job = None
        for job in config['scrape_configs']:
            if job['job_name'] == 'pc28-predictor':
                pc28_job = job
                break
        
        assert pc28_job is not None, "缺少pc28-predictor监控配置"
        assert pc28_job['metrics_path'] == '/metrics', "metrics路径配置错误"
        
        print("✅ Prometheus配置验证通过")
    
    def test_deployment_files_structure(self):
        """测试部署文件结构"""
        print("📁 验证部署文件结构...")
        
        required_files = [
            "pc28_predictor/Dockerfile",
            "pc28_predictor/docker-compose.yml",
            "pc28_predictor/k8s-deployment.yaml",
            "pc28_predictor/prometheus.yml",
            "pc28_predictor/requirements.txt"
        ]
        
        for file_path in required_files:
            assert os.path.exists(file_path), f"缺少必要文件: {file_path}"
            assert os.path.getsize(file_path) > 0, f"文件为空: {file_path}"
        
        print("✅ 部署文件结构验证通过")
    
    def test_dockerfile_best_practices(self):
        """测试Dockerfile最佳实践"""
        print("🔍 验证Dockerfile最佳实践...")
        
        with open("pc28_predictor/Dockerfile", 'r') as f:
            dockerfile_content = f.read()
        
        # 检查最佳实践
        checks = [
            ("FROM python:3.13-slim", "使用轻量级基础镜像"),
            ("WORKDIR /app", "设置工作目录"),
            ("COPY requirements.txt", "分层复制依赖文件"),
            ("RUN pip install", "安装依赖"),
            ("USER app", "使用非root用户"),
            ("EXPOSE 8000", "暴露端口"),
            ("HEALTHCHECK", "健康检查"),
            ("CMD", "启动命令")
        ]
        
        for check, description in checks:
            assert check in dockerfile_content, f"Dockerfile缺少: {description}"
        
        print("✅ Dockerfile最佳实践验证通过")
    
    def test_docker_compose_services(self):
        """测试docker-compose服务配置"""
        print("🔍 验证docker-compose服务配置...")
        
        import yaml
        with open("pc28_predictor/docker-compose.yml", 'r') as f:
            compose_config = yaml.safe_load(f)
        
        # 验证必要服务
        required_services = ['redis', 'app', 'celery-worker', 'prometheus']
        services = compose_config.get('services', {})
        
        for service in required_services:
            assert service in services, f"缺少服务: {service}"
        
        # 验证网络配置
        assert 'networks' in compose_config, "缺少网络配置"
        assert 'pc28-network' in compose_config['networks'], "缺少pc28-network网络"
        
        # 验证数据卷配置
        assert 'volumes' in compose_config, "缺少数据卷配置"
        
        print("✅ docker-compose服务配置验证通过")
    
    def test_kubernetes_resources(self):
        """测试Kubernetes资源配置"""
        print("🔍 验证Kubernetes资源配置...")
        
        import yaml
        with open("pc28_predictor/k8s-deployment.yaml", 'r') as f:
            k8s_content = f.read()
        
        # 分割多个YAML文档
        k8s_docs = list(yaml.safe_load_all(k8s_content))
        
        # 验证资源类型
        resource_types = [doc.get('kind') for doc in k8s_docs if doc]
        expected_types = [
            'Namespace', 'ConfigMap', 'Deployment', 'Service', 
            'PersistentVolumeClaim', 'HorizontalPodAutoscaler'
        ]
        
        for expected_type in expected_types:
            assert expected_type in resource_types, f"缺少Kubernetes资源: {expected_type}"
        
        print("✅ Kubernetes资源配置验证通过")
    
    def test_environment_variables(self):
        """测试环境变量配置"""
        print("🔍 验证环境变量配置...")
        
        # 检查docker-compose环境变量
        import yaml
        with open("pc28_predictor/docker-compose.yml", 'r') as f:
            compose_config = yaml.safe_load(f)
        
        app_service = compose_config['services']['app']
        env_vars = app_service.get('environment', [])
        
        required_env_vars = ['REDIS_HOST', 'REDIS_PORT', 'LOG_LEVEL', 'WORKERS']
        for var in required_env_vars:
            found = any(var in env for env in env_vars)
            assert found, f"缺少环境变量: {var}"
        
        print("✅ 环境变量配置验证通过")
    
    def test_health_checks(self):
        """测试健康检查配置"""
        print("🔍 验证健康检查配置...")
        
        # 检查Dockerfile健康检查
        with open("pc28_predictor/Dockerfile", 'r') as f:
            dockerfile_content = f.read()
        
        assert "HEALTHCHECK" in dockerfile_content, "Dockerfile缺少健康检查"
        assert "/health" in dockerfile_content, "健康检查端点配置错误"
        
        # 检查docker-compose健康检查
        import yaml
        with open("pc28_predictor/docker-compose.yml", 'r') as f:
            compose_config = yaml.safe_load(f)
        
        services_with_healthcheck = ['redis', 'app']
        for service_name in services_with_healthcheck:
            service = compose_config['services'][service_name]
            assert 'healthcheck' in service, f"{service_name}服务缺少健康检查"
        
        print("✅ 健康检查配置验证通过")
    
    def test_resource_limits(self):
        """测试资源限制配置"""
        print("🔍 验证资源限制配置...")
        
        import yaml
        with open("pc28_predictor/k8s-deployment.yaml", 'r') as f:
            k8s_content = f.read()
        
        k8s_docs = list(yaml.safe_load_all(k8s_content))
        
        # 查找Deployment资源
        deployments = [doc for doc in k8s_docs if doc and doc.get('kind') == 'Deployment']
        
        for deployment in deployments:
            containers = deployment['spec']['template']['spec']['containers']
            for container in containers:
                resources = container.get('resources', {})
                assert 'requests' in resources, f"容器{container['name']}缺少资源请求"
                assert 'limits' in resources, f"容器{container['name']}缺少资源限制"
        
        print("✅ 资源限制配置验证通过")

def test_deployment_readiness():
    """测试部署就绪状态"""
    print("🚀 验证部署就绪状态...")
    
    # 检查所有必要文件
    deployment_files = [
        "pc28_predictor/Dockerfile",
        "pc28_predictor/docker-compose.yml", 
        "pc28_predictor/k8s-deployment.yaml",
        "pc28_predictor/prometheus.yml",
        "pc28_predictor/requirements.txt"
    ]
    
    missing_files = []
    for file_path in deployment_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    assert not missing_files, f"缺少部署文件: {missing_files}"
    
    print("✅ 第七阶段部署文件准备完成")
    print("📋 部署文件清单:")
    for file_path in deployment_files:
        size = os.path.getsize(file_path)
        print(f"  - {file_path} ({size} bytes)")

if __name__ == "__main__":
    print("🚀 第七阶段部署验证测试")
    print("=" * 50)
    pytest.main([__file__, "-v"])