#!/bin/bash
# 监控Grok工作进度

echo "🔍 监控Grok工作进度"
echo "================================"
echo ""

echo "📋 Issue状态:"
gh issue view 1 --repo ppc86193-lgtm/pc28-predictor
echo ""

echo "================================"
echo "🔄 Pull Request状态:"
gh pr list --repo ppc86193-lgtm/pc28-predictor
echo ""

echo "================================"
echo "🌿 分支状态:"
git fetch origin --quiet
git branch -r | grep -i grok || echo "暂无grok分支"
echo ""

echo "================================"
echo "💡 提示:"
echo "  - 如果看到PR，说明Grok已完成"
echo "  - 运行 'gh pr checkout <PR号>' 查看代码"
echo "  - 运行 'pytest -v' 验证测试"
echo ""
echo "刷新: ./watch_grok.sh"
