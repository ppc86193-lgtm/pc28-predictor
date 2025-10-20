# 🧠 伪随机心理学分析系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 基于心理学理论的智能数据分析平台，集成记忆半衰模型、转折点检测和AI认知差异分析

## 🎯 项目概述

这是一个专业的伪随机心理学分析系统，结合了三大核心理论：

- 🧠 **人类记忆半衰模型** - 基于时间衰减的记忆权重分析
- 🎯 **心理转折点检测** - 识别大小、单双转折点和滞后效应  
- 🔍 **AI与人脑错频陷阱** - 多时间窗口的认知差异研究

## ✨ 核心特性

### 🔬 理论模块
- **记忆半衰分析** - 时间权重衰减模型
- **转折点检测** - 心理压力和修复区间识别
- **错频陷阱分析** - 人脑5期 vs AI50期视角对比
- **综合大师分析** - 多维度智能决策建议

### 📊 可视化界面
- **Streamlit Web应用** - 现代化交互界面
- **Plotly图表** - 动态可视化展示
- **实时分析** - 即时数据处理和结果展示
- **多模式支持** - 快速/标准/深度分析模式

### 🤖 AI增强功能
- **AIMLAPI集成** - 无限Token深度分析
- **智能数据维护** - 自动质量检查和异常检测
- **预测分析** - 基于历史数据的趋势预测
- **智能建议** - AI驱动的优化建议

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 8GB+ RAM (推荐)
- 现代浏览器

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动方式

#### 方法1: 一键启动 (推荐)
```bash
python start.py
```

#### 方法2: Streamlit直接启动
```bash
streamlit run streamlit_app.py
```

#### 方法3: AIMLAPI增强模式
```bash
# 设置API密钥
export AIMLAPI_KEY="your-api-key"

# 启动增强分析
python start_aimlapi_system.py --mode interactive
```

## 🛠 开发脚本

| 脚本 | 说明 |
| --- | --- |
| `scripts/run_tests.sh` | 运行生产级模块自检，并在本地执行 `pytest`；设定 `ENABLE_MCP_TESTS=1` 时会自动启动 Mock MCP 服务并执行集成测试。 |
| `scripts/format_code.sh` | 调用 `black` 与 `flake8` 对关键目录进行格式化与静态检查，可通过环境变量自定义目标与参数。 |
| `scripts/build_release.sh` | 将核心模块、配置与文档打包至 `dist/` 目录，支持 `BUILD_INCLUDE`/`ARCHIVE_PREFIX` 等变量调整输出。 |

> 所有脚本默认使用当前环境的 `python3`，如需指定解释器可设置 `PYTHON=/path/to/python`。

## 📁 项目结构

```
伪随机心理学分析系统/
├── 📊 核心应用
│   ├── streamlit_app.py          # 主Web应用
│   ├── module_adapter.py         # 模块适配器
│   └── config.py                 # 系统配置
│
├── 🧠 理论模块
│   ├── 人类记忆半衰模型.py        # 记忆衰减分析
│   ├── 心理转折点检测系统.py      # 转折点检测
│   ├── 错频陷阱分析器.py          # 错频分析
│   └── 伪随机心理学破解大师.py    # 综合分析
│
├── 🤖 AI增强模块
│   ├── aimlapi_data_manager.py   # AIMLAPI数据管理
│   ├── aimlapi_config.py         # AI配置
│   └── start_aimlapi_system.py   # AI系统启动器
│
├── 🔧 工具和脚本
│   ├── start.py                  # 一键启动
│   ├── run_system.py            # 系统运行器
│   └── test_system.py           # 系统测试
│
├── 📊 数据文件
│   ├── 伪随机生成.csv           # 主数据文件(5000+期)
│   ├── data/                    # 数据目录
│   └── results/                 # 结果目录
│
└── 📚 文档
    ├── README.md                # 项目说明
    ├── 项目说明.md              # 详细文档
    ├── AIMLAPI使用指南.md       # AI功能指南
    └── docs/                    # 其他文档
```

## 🎮 使用指南

### 基础分析流程

1. **数据准备**
   - 支持CSV文件导入
   - 手动数据输入
   - 随机数据生成

2. **选择分析模式**
   - 快速模式: 实时决策
   - 标准模式: 平衡准确性
   - 深度模式: 最高精度

3. **执行分析**
   - 记忆半衰分析
   - 转折点检测
   - 错频陷阱识别
   - 综合大师建议

4. **结果解读**
   - 可视化图表
   - 数值指标
   - 智能建议

### 高级功能

#### AIMLAPI增强分析
```bash
# 批量深度分析
python start_aimlapi_system.py --mode full --batch-size 500

# 持续监控模式
python start_aimlapi_system.py --mode monitor
```

#### 自定义配置
```python
# 修改 config.py 中的参数
MEMORY_DECAY_RATE = 0.7        # 记忆衰减率
PRESSURE_THRESHOLD = 0.75      # 压力阈值
HUMAN_WINDOW = 5               # 人脑分析窗口
AI_WINDOW = 50                 # AI分析窗口
```

## 📊 分析维度

### 数据处理标准
- **数值范围**: 0-27整数
- **最小数据量**: 20期
- **大小分界**: ≥14为大，<14为小
- **单双分界**: 奇数为单，偶数为双

### 分析指标
- **记忆权重**: 基于时间衰减的权重分布
- **心理压力**: 大小、单双维度的压力值
- **转折点**: 状态转换的关键节点
- **错频强度**: 人脑与AI认知差异程度
- **置信度**: 分析结果的可信度

## 🔧 配置选项

### 系统配置
```python
# 基础参数
APP_TITLE = "伪随机心理学分析系统"
PAGE_LAYOUT = "wide"
DEFAULT_CONFIDENCE_THRESHOLD = 0.75

# 分析参数
MEMORY_DECAY_RATE = 0.7
PRESSURE_THRESHOLD = 0.75
FREQUENCY_GAP_THRESHOLD = 0.15
```

### 可视化配置
```python
CHART_COLORS = {
    'big': '#FF6B6B',          # 大 - 红色
    'small': '#4ECDC4',        # 小 - 蓝绿色
    'odd': '#45B7D1',          # 单 - 蓝色
    'even': '#96CEB4',         # 双 - 绿色
}
```

## 🧪 测试和验证

### 运行测试
```bash
# 系统功能测试
python test_system.py

# 模块单元测试
python -m pytest tests/

# 性能测试
python quick_test.py
```

### 验证数据质量
```bash
# 数据质量检查
python aimlapi_data_manager.py --check-quality

# 异常检测
python 维护状态检查器.py
```

## 📈 性能优化

### 系统要求
- **内存**: 8GB+ (处理大数据集)
- **CPU**: 多核处理器 (并行分析)
- **存储**: 1GB+ 可用空间

### 优化建议
- 使用批量处理模式处理大数据
- 启用缓存加速重复分析
- 调整分析窗口大小平衡精度和性能
- 定期清理临时文件和日志

## 🤝 贡献指南

### 开发环境设置
```bash
# 克隆项目
git clone <repository-url>

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行开发服务器
streamlit run streamlit_app.py --server.runOnSave true
```

### 代码规范
- 遵循PEP 8编码规范
- 使用中文注释和文档字符串
- 函数名英文，变量名可用拼音
- 所有分析函数必须包含输入验证

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- 感谢心理学理论研究的贡献者
- 感谢开源社区的支持
- 感谢所有测试用户的反馈

## 📚 完整文档

### 📖 文档中心
- [📚 文档中心](docs/README.md) - 完整文档导航
- [🏗️ 项目架构](docs/项目架构文档.md) - 系统架构设计
- [📡 API文档](docs/API文档.md) - 接口说明
- [🚀 部署指南](docs/部署指南.md) - 部署方案
- [📝 更新日志](docs/更新日志.md) - 版本历史

### 🤖 AI功能文档
- [🧠 AIMLAPI使用指南](AIMLAPI使用指南.md) - AI增强功能
- [⚙️ 配置说明](docs/配置说明.md) - 系统配置

### 📊 理论文档
- [🧠 心理学理论](docs/心理学理论说明.md) - 核心理论
- [🔢 算法原理](docs/算法原理文档.md) - 数学模型

## 📞 支持

- 📧 邮箱: [项目邮箱]
- 💬 讨论: [GitHub Discussions]
- 🐛 问题报告: [GitHub Issues]
- 📖 完整文档: [docs/README.md](docs/README.md)

---

⭐ 如果这个项目对你有帮助，请给个星标支持！
