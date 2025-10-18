#!/usr/bin/env python3
"""
PC28预测系统生产就绪验证
Production Readiness Verification for PC28 Prediction System

验证系统是否准备好进行生产部署：
1. 检查所有核心组件
2. 验证配置文件
3. 测试API端点
4. 检查监控指标
5. 验证Docker和Kubernetes配置
"""

import os
import sys
import json
import time
import logging
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionReadinessChecker:
    """生产就绪检查器"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'overall_status': 'UNKNOWN',
            'recommendations': []
        }
    
    def check_core_files(self) -> bool:
        """检查核心文件是否存在"""
        logger.info("检查核心文件...")
        
        required_files = [
            'main.py',
            'monitor.py', 
            'markov_model.py',
            'tail_analyzer.py',
            'config_constants.py',
            'data_processor.py',
            'prediction_engine.py',
            'api_client.py',
            'requirements.txt'
        ]
        
        missing_files = []
        for file in required_files:
            if not (self.base_path / file).exists():
                missing_files.append(file)
        
        status = len(missing_files) == 0
        self.results['checks']['core_files'] = {
            'status': 'PASS' if status else 'FAIL',
            'missing_files': missing_files,
            'total_required': len(required_files),
            'found': len(required_files) - len(missing_files)
        }
        
        if missing_files:
            self.results['recommendations'].append(f"缺少核心文件: {', '.join(missing_files)}")
        
        logger.info(f"核心文件检查: {'通过' if status else '失败'} ({len(required_files) - len(missing_files)}/{len(required_files)})")
        return status
    
    def check_deployment_files(self) -> bool:
        """检查部署文件"""
        logger.info("检查部署配置文件...")
        
        deployment_files = [
            'Dockerfile',
            'docker-compose.yml',
            'k8s-deployment.yaml',
            'prometheus.yml'
        ]
        
        missing_files = []
        for file in deployment_files:
            if not (self.base_path / file).exists():
                missing_files.append(file)
        
        status = len(missing_files) == 0
        self.results['checks']['deployment_files'] = {
            'status': 'PASS' if status else 'FAIL',
            'missing_files': missing_files,
            'total_required': len(deployment_files),
            'found': len(deployment_files) - len(missing_files)
        }
        
        if missing_files:
            self.results['recommendations'].append(f"缺少部署文件: {', '.join(missing_files)}")
        
        logger.info(f"部署文件检查: {'通过' if status else '失败'} ({len(deployment_files) - len(missing_files)}/{len(deployment_files)})")
        return status
    
    def check_dependencies(self) -> bool:
        """检查Python依赖"""
        logger.info("检查Python依赖...")
        
        try:
            # 读取requirements.txt
            requirements_file = self.base_path / 'requirements.txt'
            if not requirements_file.exists():
                self.results['checks']['dependencies'] = {
                    'status': 'FAIL',
                    'error': 'requirements.txt not found'
                }
                return False
            
            with open(requirements_file, 'r') as f:
                requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            # 检查关键依赖
            key_packages = ['fastapi', 'uvicorn', 'redis', 'prometheus-client', 'numpy', 'scipy']
            installed_packages = []
            missing_packages = []
            
            for package in key_packages:
                try:
                    __import__(package.replace('-', '_'))
                    installed_packages.append(package)
                except ImportError:
                    missing_packages.append(package)
            
            status = len(missing_packages) == 0
            self.results['checks']['dependencies'] = {
                'status': 'PASS' if status else 'FAIL',
                'total_requirements': len(requirements),
                'key_packages_installed': installed_packages,
                'missing_packages': missing_packages
            }
            
            if missing_packages:
                self.results['recommendations'].append(f"安装缺少的依赖: pip install {' '.join(missing_packages)}")
            
            logger.info(f"依赖检查: {'通过' if status else '失败'} (关键包: {len(installed_packages)}/{len(key_packages)})")
            return status
            
        except Exception as e:
            self.results['checks']['dependencies'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            logger.error(f"依赖检查失败: {e}")
            return False
    
    def check_configuration(self) -> bool:
        """检查配置"""
        logger.info("检查系统配置...")
        
        try:
            # 检查config_constants.py
            config_file = self.base_path / 'config_constants.py'
            if not config_file.exists():
                self.results['checks']['configuration'] = {
                    'status': 'FAIL',
                    'error': 'config_constants.py not found'
                }
                return False
            
            # 尝试导入配置
            sys.path.insert(0, str(self.base_path))
            try:
                import config_constants
                
                # 检查关键配置项
                required_configs = [
                    'TARGET_ACCURACY_MIN',
                    'TARGET_ACCURACY_MAX', 
                    'BIG_SMALL_ACCURACY_MIN',
                    'BIG_SMALL_ACCURACY_MAX',
                    'SUM_RANGE_ACCURACY_MIN',
                    'SUM_RANGE_ACCURACY_MAX'
                ]
                
                missing_configs = []
                for config in required_configs:
                    if not hasattr(config_constants, config):
                        missing_configs.append(config)
                
                status = len(missing_configs) == 0
                self.results['checks']['configuration'] = {
                    'status': 'PASS' if status else 'FAIL',
                    'missing_configs': missing_configs,
                    'found_configs': len(required_configs) - len(missing_configs)
                }
                
                if missing_configs:
                    self.results['recommendations'].append(f"配置文件缺少: {', '.join(missing_configs)}")
                
                logger.info(f"配置检查: {'通过' if status else '失败'}")
                return status
                
            except ImportError as e:
                self.results['checks']['configuration'] = {
                    'status': 'ERROR',
                    'error': f'Cannot import config_constants: {e}'
                }
                return False
                
        except Exception as e:
            self.results['checks']['configuration'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            logger.error(f"配置检查失败: {e}")
            return False
    
    def check_api_health(self) -> bool:
        """检查API健康状态"""
        logger.info("检查API健康状态...")
        
        try:
            # 尝试启动API服务进行健康检查
            import subprocess
            import time
            
            # 检查是否有API进程在运行
            try:
                response = requests.get('http://localhost:8000/health', timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    self.results['checks']['api_health'] = {
                        'status': 'PASS',
                        'response': health_data,
                        'response_time': response.elapsed.total_seconds()
                    }
                    logger.info("API健康检查: 通过")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            # API未运行，记录状态
            self.results['checks']['api_health'] = {
                'status': 'WARNING',
                'message': 'API服务未运行，需要启动服务进行完整验证'
            }
            self.results['recommendations'].append("启动API服务: python main.py 或 uvicorn main:app --host 0.0.0.0 --port 8000")
            
            logger.info("API健康检查: 警告（服务未运行）")
            return True  # 不阻止其他检查
            
        except Exception as e:
            self.results['checks']['api_health'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            logger.error(f"API健康检查失败: {e}")
            return False
    
    def check_docker_readiness(self) -> bool:
        """检查Docker就绪状态"""
        logger.info("检查Docker配置...")
        
        try:
            # 检查Dockerfile
            dockerfile = self.base_path / 'Dockerfile'
            if not dockerfile.exists():
                self.results['checks']['docker'] = {
                    'status': 'FAIL',
                    'error': 'Dockerfile not found'
                }
                return False
            
            # 检查Docker是否可用
            try:
                result = subprocess.run(['docker', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                docker_available = result.returncode == 0
                docker_version = result.stdout.strip() if docker_available else None
            except (subprocess.TimeoutExpired, FileNotFoundError):
                docker_available = False
                docker_version = None
            
            # 检查docker-compose
            try:
                result = subprocess.run(['docker-compose', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                compose_available = result.returncode == 0
                compose_version = result.stdout.strip() if compose_available else None
            except (subprocess.TimeoutExpired, FileNotFoundError):
                compose_available = False
                compose_version = None
            
            status = docker_available and compose_available
            self.results['checks']['docker'] = {
                'status': 'PASS' if status else 'WARNING',
                'docker_available': docker_available,
                'docker_version': docker_version,
                'compose_available': compose_available,
                'compose_version': compose_version,
                'dockerfile_exists': True
            }
            
            if not docker_available:
                self.results['recommendations'].append("安装Docker: https://docs.docker.com/get-docker/")
            if not compose_available:
                self.results['recommendations'].append("安装Docker Compose: https://docs.docker.com/compose/install/")
            
            logger.info(f"Docker检查: {'通过' if status else '警告'}")
            return True  # 不阻止部署，只是警告
            
        except Exception as e:
            self.results['checks']['docker'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            logger.error(f"Docker检查失败: {e}")
            return False
    
    def check_kubernetes_readiness(self) -> bool:
        """检查Kubernetes就绪状态"""
        logger.info("检查Kubernetes配置...")
        
        try:
            # 检查k8s配置文件
            k8s_file = self.base_path / 'k8s-deployment.yaml'
            if not k8s_file.exists():
                self.results['checks']['kubernetes'] = {
                    'status': 'FAIL',
                    'error': 'k8s-deployment.yaml not found'
                }
                return False
            
            # 检查kubectl是否可用
            try:
                result = subprocess.run(['kubectl', 'version', '--client'], 
                                      capture_output=True, text=True, timeout=10)
                kubectl_available = result.returncode == 0
                kubectl_version = result.stdout.strip() if kubectl_available else None
            except (subprocess.TimeoutExpired, FileNotFoundError):
                kubectl_available = False
                kubectl_version = None
            
            # 检查集群连接
            cluster_accessible = False
            if kubectl_available:
                try:
                    result = subprocess.run(['kubectl', 'cluster-info'], 
                                          capture_output=True, text=True, timeout=10)
                    cluster_accessible = result.returncode == 0
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    cluster_accessible = False
            
            self.results['checks']['kubernetes'] = {
                'status': 'PASS' if kubectl_available else 'WARNING',
                'kubectl_available': kubectl_available,
                'kubectl_version': kubectl_version,
                'cluster_accessible': cluster_accessible,
                'deployment_file_exists': True
            }
            
            if not kubectl_available:
                self.results['recommendations'].append("安装kubectl: https://kubernetes.io/docs/tasks/tools/")
            if kubectl_available and not cluster_accessible:
                self.results['recommendations'].append("配置Kubernetes集群访问或启动minikube: minikube start")
            
            logger.info(f"Kubernetes检查: {'通过' if kubectl_available else '警告'}")
            return True  # 不阻止部署，只是警告
            
        except Exception as e:
            self.results['checks']['kubernetes'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            logger.error(f"Kubernetes检查失败: {e}")
            return False
    
    def run_all_checks(self) -> Dict:
        """运行所有检查"""
        logger.info("开始生产就绪验证...")
        
        checks = [
            ('核心文件', self.check_core_files),
            ('部署文件', self.check_deployment_files),
            ('Python依赖', self.check_dependencies),
            ('系统配置', self.check_configuration),
            ('API健康', self.check_api_health),
            ('Docker配置', self.check_docker_readiness),
            ('Kubernetes配置', self.check_kubernetes_readiness)
        ]
        
        passed = 0
        failed = 0
        warnings = 0
        
        for name, check_func in checks:
            try:
                result = check_func()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"{name}检查异常: {e}")
                failed += 1
        
        # 统计状态
        for check_name, check_result in self.results['checks'].items():
            if check_result['status'] == 'WARNING':
                warnings += 1
        
        # 确定总体状态
        if failed == 0 and warnings == 0:
            self.results['overall_status'] = 'READY'
        elif failed == 0:
            self.results['overall_status'] = 'READY_WITH_WARNINGS'
        else:
            self.results['overall_status'] = 'NOT_READY'
        
        self.results['summary'] = {
            'total_checks': len(checks),
            'passed': passed,
            'failed': failed,
            'warnings': warnings
        }
        
        # 保存结果
        self.save_results()
        
        # 打印摘要
        self.print_summary()
        
        return self.results
    
    def save_results(self):
        """保存检查结果"""
        try:
            with open(self.base_path / 'production_readiness_report.json', 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            logger.info("检查结果已保存到 production_readiness_report.json")
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
    
    def print_summary(self):
        """打印检查摘要"""
        print("\n" + "="*60)
        print("PC28预测系统生产就绪验证报告")
        print("="*60)
        
        summary = self.results['summary']
        print(f"总检查项: {summary['total_checks']}")
        print(f"通过: {summary['passed']}")
        print(f"失败: {summary['failed']}")
        print(f"警告: {summary['warnings']}")
        print(f"总体状态: {self.results['overall_status']}")
        
        print("\n详细结果:")
        print("-" * 40)
        
        for check_name, check_result in self.results['checks'].items():
            status_icon = {
                'PASS': '✓',
                'FAIL': '✗',
                'WARNING': '⚠',
                'ERROR': '✗'
            }.get(check_result['status'], '?')
            
            print(f"{status_icon} {check_name}: {check_result['status']}")
            
            if 'error' in check_result:
                print(f"    错误: {check_result['error']}")
            elif 'message' in check_result:
                print(f"    信息: {check_result['message']}")
        
        if self.results['recommendations']:
            print("\n建议:")
            print("-" * 40)
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"{i}. {rec}")
        
        print("\n" + "="*60)
        
        # 根据状态给出下一步建议
        if self.results['overall_status'] == 'READY':
            print("🎉 系统已准备好进行生产部署！")
            print("\n下一步:")
            print("1. 构建Docker镜像: docker build -t pc28-predictor:latest .")
            print("2. 部署到Kubernetes: kubectl apply -f k8s-deployment.yaml")
            print("3. 运行5000周期验证: python test_production_validation.py")
        elif self.results['overall_status'] == 'READY_WITH_WARNINGS':
            print("⚠️  系统基本就绪，但有一些警告需要注意")
            print("可以继续部署，但建议解决警告项以获得最佳体验")
        else:
            print("❌ 系统尚未准备好生产部署")
            print("请解决上述失败项后重新检查")
        
        print("="*60)

def main():
    """主函数"""
    checker = ProductionReadinessChecker()
    results = checker.run_all_checks()
    
    # 返回适当的退出码
    if results['overall_status'] in ['READY', 'READY_WITH_WARNINGS']:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()