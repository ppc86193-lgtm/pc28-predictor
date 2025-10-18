# PC28 Prediction System

## Overview
AI/ML API Model Extraction and PC28 Prediction System with optimized second-order Markov chain analysis.

**Current Phase: 7 - 部署 (2025-12-06至2026-01-07)** ✅ **已完成配置**

## 🚀 第七阶段部署状态

### ✅ 容器化配置 (已完成)
- **Dockerfile**: 基于Python 3.13-slim，多阶段构建，非root用户
- **docker-compose.yml**: Redis + PC28应用 + Celery Worker + Prometheus
- **健康检查**: 应用和服务健康监控
- **网络隔离**: 专用网络和数据卷配置

### ✅ Kubernetes部署 (已完成)
- **k8s-deployment.yaml**: 完整的K8s部署清单
- **高可用**: 3副本PC28应用 + 2副本Celery Worker
- **自动扩缩容**: HPA基于CPU/内存使用率
- **资源管理**: 请求和限制配置

### ✅ 监控集成 (已完成)
- **Prometheus配置**: 完整的监控配置文件
- **指标收集**: 15秒间隔，/metrics端点
- **系统监控**: CPU、内存、响应时间跟踪

### ✅ 第六阶段功能 (已完成)
- **任务1**: 增强监控系统 - 智能趋势分析、Webhook通知
- **任务2**: 算法优化 - 动态马尔可夫模型、动态尾数分析  
- **任务3**: 性能监控增强 - Prometheus集成、P50/P95/P99监控

### ✅ 已实现功能
- Second-order Markov chain with 5 states (大单, 小双, 小单, 大双, 极值)
- Dynamic EMA (3-7 periods) with tail frequency analysis
- Chi-square testing (p<0.05) for statistical significance
- Redis caching for <2s response time (实际150-300ms)
- FastAPI web service with 107 tests (100% pass rate)
- Real-time PC28 data integration
- AI/ML model catalog extraction

## API端点

### 预测相关
- `POST /predict` - 生成PC28预测（集成性能监控）
- `POST /predict/update` - 更新预测准确率
- `POST /predict/result` - 更新预测结果

### 动态优化 (任务2新增)
- `GET /markov/dynamic` - 获取动态马尔可夫模型统计
- `POST /markov/dynamic/update` - 手动更新马尔可夫准确率
- `GET /tail/dynamic` - 获取动态尾数分析统计
- `POST /tail/dynamic/update` - 手动更新尾数分析准确率

### 监控与性能
- `GET /metrics` - **Prometheus指标端点 (任务3新增)**
- `GET /monitor/accuracy` - 准确率监控
- `GET /monitor/performance` - 性能指标
- `GET /monitor/trend` - 趋势分析
- `GET /monitor/alerts` - 系统警报

## Prometheus指标 (任务3新增)

### 请求指标
- `predict_requests_total{endpoint, method}` - 预测请求总数
- `predict_duration_seconds{endpoint}` - 预测响应时间分布
- `monitor_requests_total{operation}` - 监控操作总数
- `monitor_duration_seconds{operation}` - 监控操作耗时

### 性能指标
- `response_time_ms{percentile}` - 响应时间百分位数（P50/P95/P99）
- `prediction_accuracy{type}` - 预测准确率（组合/大小/和值）
- `system_health_score` - 系统健康分数（0-100）

### 系统资源
- `cpu_usage_percent` - CPU使用率
- `memory_usage_mb` - 内存使用量（MB）
- `system_uptime_seconds` - 系统运行时间
- `active_connections` - 活跃连接数

## Installation

### Prerequisites
- Python 3.11+
- Redis server
- Virtual environment (recommended)
- Prometheus (可选，用于指标收集)

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Redis (if not running)
redis-server

# Run the application
python main.py
```

## API Endpoints

### Phase 1 (Current)
- `GET /` - System information
- `GET /health` - Health check (Redis connection, system status)

### Planned (Phase 5+)
- `POST /predict` - Generate PC28 predictions
- `GET /models` - Fetch AI/ML model catalog
- `GET /stats` - Statistical analysis and tail frequency data

## Configuration

Configuration is managed through `config.json`:
- API keys for AI/ML API and PC28 data services
- Redis connection settings
- External API endpoints

## Data Models

### PC28Data
Core lottery data model with validation:
- `sum`: Integer (0-27) - Sum of three numbers
- `tail`: Integer (0-9) - Last digit of sum  
- `combination`: Enum ["大单", "小双", "小单", "大双", "极值"] - Combination type
- `period`: Optional string - Period identifier
- `timestamp`: Optional datetime - Draw timestamp
- `numbers`: Optional list - Original three numbers

### PredictionResult
Prediction output model:
- `sum_range`: String - Predicted sum range
- `combination`: String - Predicted combination
- `probabilities`: Dict - Probability distribution
- `confidence`: Float (0-1) - Prediction confidence

### TailFrequencyResult
Statistical analysis result:
- `frequencies`: Dict - Tail frequency distribution
- `chi_square_statistic`: Float - Chi-square test statistic
- `p_value`: Float (0-1) - Statistical p-value
- `is_significant`: Boolean - Statistical significance

### ModelInfo
AI/ML model information:
- `id`: String - Model identifier
- `name`: String - Model name
- `developer`: String - Model developer
- `type`: String - Model type
- `context_length`: Optional int - Context length

## Development Phases

1. **Phase 1**: Project setup and configuration ✅
2. **Phase 2**: Data models and validation ✅
3. **Phase 3**: API client implementation ✅
4. **Phase 4**: Statistical engines (Markov chain, tail analysis) ✅
5. **Phase 5**: Prediction system integration ✅
6. **Phase 6**: Monitoring and optimization ✅
7. **Phase 7**: Deployment configuration ✅ **当前阶段**
8. **Phase 8**: Production deployment (计划中)
9. **Phase 9**: 5000-cycle verification (计划中)

## 🚀 部署指南

### 本地Docker部署
```bash
# 构建并启动服务
docker-compose -f pc28_predictor/docker-compose.yml up -d

# 验证服务
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

### Kubernetes部署
```bash
# 部署到K8s集群
kubectl apply -f pc28_predictor/k8s-deployment.yaml

# 检查状态
kubectl get pods -n pc28-predictor
kubectl get services -n pc28-predictor
```

### 监控访问
- **应用**: http://localhost:8000
- **健康检查**: http://localhost:8000/health  
- **Prometheus指标**: http://localhost:8000/metrics
- **Prometheus UI**: http://localhost:9090

## Accuracy Targets
- Sum range (10-17): 65-70%
- Combination prediction: 56-61%
- Big odd/small even: 61-66%

## Performance Goals
- Response time: <2 seconds
- System uptime: 99.9%
- Statistical significance: p<0.05

## Testing

### Phase 2 Testing
```bash
# Run data model tests
source venv/bin/activate
python -m pytest test_data_models.py -v

# Test system health
curl http://localhost:8000/health

# Test system info
curl http://localhost:8000/
```

### Test Coverage
- ✅ PC28Data validation (sum, tail, combination)
- ✅ PredictionResult model
- ✅ TailFrequencyResult model  
- ✅ ModelInfo model
- ✅ extract_features function
- ✅ validate_pc28_data function
- ✅ categorize_models function

## License
Private development project

## Contact
Development team: DEV1 (Backend), DEV2 (AI), DA2 (Data Science), Ops1 (Operations)