# Grok开发调试指南

## 🔑 真实API密钥（无限Token）

### PC28数据API
- **密钥**: ca9edbfee35c22a0d6c4cf6722506af0
- **AppID**: 45928
- **实时接口**: https://rijb.api.storeapi.net/api/119/259
- **历史接口**: https://rijb.api.storeapi.net/api/119/260
- **限制**: 无限制，随意调用

### AI/ML聚合API
- **密钥**: 9030c9fcbc474c258dca7ff39b3a20e6
- **文档**: https://docs.aimlapi.com/?_gl=1*z329f4*_gcl_au*MjExNDY1MjA2OS4xNzU4MDQyNzI0
- **Base URL**: https://api.aimlapi.com/v1
- **Token**: 无限制

## 🎯 当前任务目标

### 准确率目标
- 组合准确率: 56-61% (当前: 22%)
- 大单/小双: 61-66% (当前: 48.4%)
- 和值范围: 65-70% (当前: 41.1%)

### 性能目标
- 响应时间: <0.2秒
- 内存使用: <2KB
- 系统可用性: 99.9%

## 🧪 测试环境

### 本地测试
```bash
# 安装依赖
pip install -r requirements.txt

# 运行真实数据测试
python3 test_5000_cycle_real_data.py

# 查看结果
cat 5000_cycle_real_data_results.json
```

### API测试示例
```python
import requests
import hashlib

# PC28历史数据
appid = "45928"
api_key = "ca9edbfee35c22a0d6c4cf6722506af0"
date = "2025-10-18"

sign_str = f"appid{appid}date{date}{api_key}"
sign = hashlib.md5(sign_str.encode()).hexdigest()

response = requests.get(
    "https://rijb.api.storeapi.net/api/119/260",
    params={"appid": appid, "date": date, "sign": sign}
)
data = response.json()
print(f"获取到 {len(data['retdata'])} 条数据")
```

## 📊 当前测试结果

### 真实数据测试（5000条）
- 数据来源: 2025-10-06 至 2025-10-18（13天）
- 训练数据: 4000条（80%）
- 测试数据: 1000条（20%）
- 测试耗时: 49秒

### 准确率分析
```json
{
  "combination_accuracy": 0.22,
  "big_small_accuracy": 0.484,
  "sum_range_accuracy": 0.411
}
```

## 🔧 需要优化的文件

### 1. markov_model.py
**当前问题**:
- 历史窗口太小（100条）
- 二阶马尔可夫链不够
- EMA权重调整过于激进

**优化建议**:
```python
# 增加历史窗口
HISTORY_WINDOW = 500  # 从100增加到500

# 实现三阶马尔可夫链
def calculate_third_order_transition():
    # 考虑前3个状态
    pass

# 添加时间衰减
def apply_time_decay(data, decay_rate=0.95):
    weights = [decay_rate ** i for i in range(len(data))]
    return weighted_average(data, weights)
```

### 2. tail_analyzer.py
**当前问题**:
- 固定增强因子（1.03）
- 未充分利用尾数模式
- 连号检测不够精准

**优化建议**:
```python
# 动态增强因子
def calculate_dynamic_boost(tail_freq, accuracy):
    if accuracy < 0.5:
        return 1.05  # 低准确率时增强更多
    elif accuracy > 0.6:
        return 1.02  # 高准确率时保守
    else:
        return 1.03

# 连号检测
def detect_consecutive_tails(history):
    consecutive_count = 0
    for i in range(len(history)-1):
        if abs(history[i].tail - history[i+1].tail) == 1:
            consecutive_count += 1
    return consecutive_count / len(history)

# 尾数组合模式
def analyze_tail_combinations(history):
    patterns = {}
    for i in range(len(history)-2):
        pattern = (history[i].tail, history[i+1].tail, history[i+2].tail)
        patterns[pattern] = patterns.get(pattern, 0) + 1
    return patterns
```

### 3. prediction_engine.py
**当前问题**:
- 单一预测模型
- 缺少模型融合
- 置信度计算不准确

**优化建议**:
```python
# 多模型融合
def ensemble_predict(markov_pred, tail_pred, time_pred):
    # 动态权重
    weights = calculate_dynamic_weights(
        markov_accuracy, tail_accuracy, time_accuracy
    )
    
    # 加权融合
    final_pred = (
        weights[0] * markov_pred +
        weights[1] * tail_pred +
        weights[2] * time_pred
    )
    
    return final_pred

# 置信度评估
def calculate_confidence(predictions, history):
    # 基于历史准确率
    historical_accuracy = get_recent_accuracy(history, window=100)
    
    # 基于预测一致性
    consistency = calculate_prediction_consistency(predictions)
    
    # 综合置信度
    confidence = 0.6 * historical_accuracy + 0.4 * consistency
    return confidence
```

## 🚀 Grok调试流程

### 1. 克隆仓库
```bash
git clone https://github.com/ppc86193-lgtm/pc28-predictor.git
cd pc28-predictor
git checkout pp998
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 运行测试
```bash
# 运行真实数据测试
python3 test_5000_cycle_real_data.py

# 查看结果
cat 5000_cycle_real_data_results.json | jq '.accuracy_metrics'
```

### 4. 优化代码
- 修改 markov_model.py
- 修改 tail_analyzer.py
- 修改 prediction_engine.py

### 5. 验证优化
```bash
# 重新运行测试
python3 test_5000_cycle_real_data.py

# 对比结果
# 目标: 组合>56%, 大小>61%, 范围>65%
```

### 6. 创建PR
```bash
git checkout -b grok-optimization
git add markov_model.py tail_analyzer.py prediction_engine.py
git commit -m "Grok优化: 提升准确率至目标范围"
git push origin grok-optimization

# 创建PR到pp998分支
gh pr create --base pp998 --title "🤖 Grok优化: 算法准确率提升" --body "..."
```

## 📝 测试数据示例

### 真实PC28数据格式
```json
{
  "kjtime": "2025-10-18 21:46:30",
  "number": ["3", "2", "3"],
  "long_issue": "3348914"
}
```

### 计算规则
```python
numbers = [3, 2, 3]
sum_val = sum(numbers)  # 8
tail = sum_val % 10     # 8

# 组合判断
if sum_val <= 5 or sum_val >= 22:
    combination = "极值"
elif sum_val % 2 == 0:  # 偶数
    combination = "大双" if sum_val >= 14 else "小双"  # 小双
else:  # 奇数
    combination = "大单" if sum_val >= 14 else "小单"
```

## 🎯 成功标准

### 准确率达标
- ✅ 组合准确率: 56-61%
- ✅ 大单/小双: 61-66%
- ✅ 和值范围: 65-70%

### 性能达标
- ✅ 响应时间: <0.2秒
- ✅ 内存使用: <2KB
- ✅ 测试通过: 5000周期验证

## 💡 提示

1. **所有密钥都是真实的**，可以直接调用API测试
2. **无限Token**，不用担心配额
3. **真实数据**，test_5000_cycle_real_data.py会自动获取
4. **可以直接调试**，修改代码后立即测试
5. **创建PR**，优化完成后提交到pp998分支

## 📞 联系方式

- **Issue**: https://github.com/ppc86193-lgtm/pc28-predictor/issues/2
- **分支**: pp998
- **最新提交**: 3785749

---

**Grok，开始优化吧！所有资源都准备好了，直接调试测试即可。** 🚀
