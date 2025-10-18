#!/bin/bash
# 生产部署脚本
# Production Deployment Script

set -e  # 遇到错误立即退出

echo "🚀 PC28预测系统生产部署"
echo "=================================="

# 配置变量
IMAGE_NAME="pc28-predictor"
IMAGE_TAG="latest"
NAMESPACE="pc28-predictor"
COMPOSE_FILE="pc28_predictor/docker-compose.yml"
K8S_MANIFEST="pc28_predictor/k8s-deployment.yaml"

# 函数：检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 未安装或不在PATH中"
        return 1
    fi
    return 0
}

# 函数：检查Docker环境
check_docker() {
    echo "🐳 检查Docker环境..."
    
    if ! check_command docker; then
        echo "请安装Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "❌ Docker守护进程未运行"
        echo "请启动Docker Desktop或运行: sudo systemctl start docker"
        exit 1
    fi
    
    echo "✅ Docker环境正常"
}

# 函数：检查Kubernetes环境
check_kubernetes() {
    echo "☸️ 检查Kubernetes环境..."
    
    if ! check_command kubectl; then
        echo "⚠️ kubectl未安装，将使用Docker Compose部署"
        return 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        echo "⚠️ Kubernetes集群未连接，将使用Docker Compose部署"
        return 1
    fi
    
    echo "✅ Kubernetes环境正常"
    return 0
}

# 函数：构建Docker镜像
build_image() {
    echo "🔨 构建Docker镜像..."
    
    cd pc28_predictor
    
    # 构建镜像
    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
    
    if [ $? -eq 0 ]; then
        echo "✅ Docker镜像构建成功"
        
        # 显示镜像信息
        docker images ${IMAGE_NAME}:${IMAGE_TAG}
    else
        echo "❌ Docker镜像构建失败"
        exit 1
    fi
    
    cd ..
}

# 函数：Docker Compose部署
deploy_docker_compose() {
    echo "🐳 使用Docker Compose部署..."
    
    # 停止现有服务
    echo "停止现有服务..."
    docker-compose -f ${COMPOSE_FILE} down --remove-orphans || true
    
    # 启动服务
    echo "启动服务..."
    docker-compose -f ${COMPOSE_FILE} up -d
    
    if [ $? -eq 0 ]; then
        echo "✅ Docker Compose部署成功"
        
        # 等待服务启动
        echo "等待服务启动..."
        sleep 15
        
        # 检查服务状态
        echo "📊 服务状态:"
        docker-compose -f ${COMPOSE_FILE} ps
        
        # 检查健康状态
        check_health_docker_compose
    else
        echo "❌ Docker Compose部署失败"
        exit 1
    fi
}

# 函数：Kubernetes部署
deploy_kubernetes() {
    echo "☸️ 使用Kubernetes部署..."
    
    # 创建命名空间（如果不存在）
    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    
    # 应用清单
    kubectl apply -f ${K8S_MANIFEST}
    
    if [ $? -eq 0 ]; then
        echo "✅ Kubernetes部署成功"
        
        # 等待Pod就绪
        echo "等待Pod就绪..."
        kubectl wait --for=condition=ready pod -l app=pc28-predictor -n ${NAMESPACE} --timeout=300s
        
        # 检查部署状态
        echo "📊 部署状态:"
        kubectl get pods -n ${NAMESPACE}
        kubectl get services -n ${NAMESPACE}
        
        # 检查健康状态
        check_health_kubernetes
    else
        echo "❌ Kubernetes部署失败"
        exit 1
    fi
}

# 函数：检查Docker Compose健康状态
check_health_docker_compose() {
    echo "🏥 检查服务健康状态..."
    
    # 等待服务完全启动
    sleep 10
    
    # 检查健康端点
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo "✅ 健康检查通过"
        
        # 显示健康信息
        curl -s http://localhost:8000/health | jq '.' || curl -s http://localhost:8000/health
    else
        echo "❌ 健康检查失败"
        echo "检查服务日志:"
        docker-compose -f ${COMPOSE_FILE} logs app
    fi
    
    # 检查Prometheus指标
    if curl -f http://localhost:8000/metrics &> /dev/null; then
        echo "✅ Prometheus指标端点正常"
    else
        echo "⚠️ Prometheus指标端点异常"
    fi
}

# 函数：检查Kubernetes健康状态
check_health_kubernetes() {
    echo "🏥 检查服务健康状态..."
    
    # 获取服务端点
    SERVICE_IP=$(kubectl get service pc28-predictor-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    
    if [ -z "$SERVICE_IP" ]; then
        # 使用端口转发进行测试
        echo "使用端口转发进行健康检查..."
        kubectl port-forward service/pc28-predictor-service 8080:80 -n ${NAMESPACE} &
        PORT_FORWARD_PID=$!
        
        sleep 5
        
        if curl -f http://localhost:8080/health &> /dev/null; then
            echo "✅ 健康检查通过"
            curl -s http://localhost:8080/health | jq '.' || curl -s http://localhost:8080/health
        else
            echo "❌ 健康检查失败"
            kubectl logs -l app=pc28-predictor -n ${NAMESPACE} --tail=50
        fi
        
        # 清理端口转发
        kill $PORT_FORWARD_PID 2>/dev/null || true
    else
        # 直接访问LoadBalancer IP
        if curl -f http://${SERVICE_IP}/health &> /dev/null; then
            echo "✅ 健康检查通过"
            curl -s http://${SERVICE_IP}/health | jq '.' || curl -s http://${SERVICE_IP}/health
        else
            echo "❌ 健康检查失败"
        fi
    fi
}

# 函数：运行验证测试
run_verification_tests() {
    echo "🧪 运行验证测试..."
    
    # 检查Python环境
    if [ -d "pc28_venv" ]; then
        source pc28_venv/bin/activate
    fi
    
    # 运行生产部署测试
    if [ -f "test_production_deployment.py" ]; then
        python test_production_deployment.py
    else
        echo "⚠️ 验证测试文件不存在"
    fi
}

# 函数：显示部署信息
show_deployment_info() {
    echo ""
    echo "🎉 部署完成！"
    echo "=================================="
    echo "📋 访问信息:"
    
    if check_kubernetes &> /dev/null; then
        echo "  Kubernetes部署:"
        echo "  - 命名空间: ${NAMESPACE}"
        echo "  - 服务: pc28-predictor-service"
        echo "  - 端口转发: kubectl port-forward service/pc28-predictor-service 8000:80 -n ${NAMESPACE}"
    else
        echo "  Docker Compose部署:"
        echo "  - 应用: http://localhost:8000"
        echo "  - 健康检查: http://localhost:8000/health"
        echo "  - Prometheus指标: http://localhost:8000/metrics"
        echo "  - Prometheus UI: http://localhost:9090"
    fi
    
    echo ""
    echo "📊 监控命令:"
    echo "  - 查看日志: docker-compose -f ${COMPOSE_FILE} logs -f"
    echo "  - 查看状态: docker-compose -f ${COMPOSE_FILE} ps"
    echo "  - 停止服务: docker-compose -f ${COMPOSE_FILE} down"
    
    echo ""
    echo "🔄 下一步:"
    echo "  1. 运行5000周期验证测试"
    echo "  2. 监控系统性能和准确率"
    echo "  3. 配置生产环境告警"
}

# 主函数
main() {
    echo "开始部署流程..."
    
    # 检查环境
    check_docker
    
    # 构建镜像
    build_image
    
    # 选择部署方式
    if check_kubernetes; then
        deploy_kubernetes
    else
        deploy_docker_compose
    fi
    
    # 运行验证测试
    run_verification_tests
    
    # 显示部署信息
    show_deployment_info
}

# 处理命令行参数
case "${1:-}" in
    "docker")
        echo "强制使用Docker Compose部署"
        check_docker
        build_image
        deploy_docker_compose
        show_deployment_info
        ;;
    "k8s"|"kubernetes")
        echo "强制使用Kubernetes部署"
        check_docker
        check_kubernetes || (echo "❌ Kubernetes环境不可用" && exit 1)
        build_image
        deploy_kubernetes
        show_deployment_info
        ;;
    "build")
        echo "仅构建Docker镜像"
        check_docker
        build_image
        ;;
    "test")
        echo "仅运行验证测试"
        run_verification_tests
        ;;
    "help"|"-h"|"--help")
        echo "用法: $0 [docker|k8s|build|test|help]"
        echo "  docker    - 使用Docker Compose部署"
        echo "  k8s       - 使用Kubernetes部署"
        echo "  build     - 仅构建Docker镜像"
        echo "  test      - 仅运行验证测试"
        echo "  help      - 显示帮助信息"
        echo "  (无参数)  - 自动选择部署方式"
        ;;
    *)
        main
        ;;
esac