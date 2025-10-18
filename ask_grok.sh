#!/bin/bash
# 快速生成Grok请求的脚本

echo "🤖 Grok代码修改请求生成器"
echo ""
echo "仓库信息："
echo "  URL: https://github.com/ppc86193-lgtm/pc28-predictor"
echo "  Commit: $(git log -1 --pretty=%h)"
echo "  分支: $(git branch --show-current)"
echo ""

# 选择任务类型
echo "请选择任务类型："
echo "1) 完整代码审计"
echo "2) 性能优化"
echo "3) Bug修复"
echo "4) 添加新功能"
echo "5) 自定义请求"
echo ""
read -p "选择 (1-5): " choice

case $choice in
    1)
        cat << 'EOF'
你好Grok，请帮我进行完整的代码审计。

仓库：https://github.com/ppc86193-lgtm/pc28-predictor
Commit: $(git log -1 --pretty=%h)

请分析以下文件并提供优化建议：
1. pc28_predictor/markov_model.py
2. pc28_predictor/tail_analyzer.py
3. pc28_predictor/prediction_engine.py
4. pc28_predictor/monitor.py

重点检查：
- 逻辑错误
- 性能问题
- 安全漏洞
- 代码质量

项目目标：
- 组合准确率: 56-61%
- 响应时间: <2秒
- 系统可用性: 99.9%

请提供详细的分析报告和优化代码。
EOF
        ;;
    2)
        cat << 'EOF'
你好Grok，请帮我优化系统性能。

仓库：https://github.com/ppc86193-lgtm/pc28-predictor

当前性能：
- 单次预测时间: ~0.5秒
- 目标: <0.2秒

请：
1. 识别性能瓶颈
2. 优化算法和数据结构
3. 添加缓存机制
4. 提供优化后的代码

重点文件：
- pc28_predictor/prediction_engine.py
- pc28_predictor/markov_model.py
EOF
        ;;
    3)
        cat << 'EOF'
你好Grok，请帮我修复Bug。

仓库：https://github.com/ppc86193-lgtm/pc28-predictor

问题描述：
[请在这里描述具体的Bug]

相关文件：
[请列出相关文件]

请分析问题原因并提供修复代码。
EOF
        ;;
    4)
        cat << 'EOF'
你好Grok，请帮我添加新功能。

仓库：https://github.com/ppc86193-lgtm/pc28-predictor

功能需求：
[请在这里描述新功能]

技术要求：
[请列出技术要求]

请提供完整的实现代码和测试用例。
EOF
        ;;
    5)
        echo ""
        echo "请输入你的自定义请求："
        echo "(输入完成后按Ctrl+D)"
        cat
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo ""
echo "📋 请求已生成！"
echo ""
echo "下一步："
echo "1. 复制上面的内容"
echo "2. 访问 https://grok.x.ai"
echo "3. 粘贴并发送给Grok"
echo ""
echo "或者在Kiro中直接使用GitHub MCP"
