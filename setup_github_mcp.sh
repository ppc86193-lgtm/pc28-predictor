#!/bin/bash
# 配置GitHub MCP服务器

echo "🚀 配置GitHub MCP服务器..."
echo ""

# 检查gh CLI是否已登录
if ! gh auth status &>/dev/null; then
    echo "❌ GitHub CLI未登录"
    echo "请先运行: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI已登录"
echo ""

# 获取当前token
echo "📝 获取GitHub token..."
TOKEN=$(gh auth token)

if [ -z "$TOKEN" ]; then
    echo "❌ 无法获取GitHub token"
    exit 1
fi

echo "✅ Token获取成功"
echo ""

# 更新工作区MCP配置
echo "📝 更新工作区MCP配置..."
cat > .kiro/settings/mcp.json << EOF
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "$TOKEN"
      }
    }
  }
}
EOF

echo "✅ 工作区配置已更新: .kiro/settings/mcp.json"
echo ""

# 更新用户级MCP配置
echo "📝 更新用户级MCP配置..."
mkdir -p ~/.kiro/settings

cat > ~/.kiro/settings/mcp.json << EOF
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "$TOKEN"
      }
    }
  }
}
EOF

echo "✅ 用户级配置已更新: ~/.kiro/settings/mcp.json"
echo ""

# 测试npx是否可用
echo "🔍 检查Node.js和npx..."
if ! command -v npx &> /dev/null; then
    echo "❌ npx未安装"
    echo "请安装Node.js: brew install node"
    exit 1
fi

echo "✅ npx可用: $(which npx)"
echo ""

echo "🎉 GitHub MCP配置完成！"
echo ""
echo "现在可以使用以下功能："
echo "  - 读取GitHub仓库代码"
echo "  - 创建和更新文件"
echo "  - 创建Issue和PR"
echo "  - 搜索仓库"
echo ""
echo "仓库信息："
echo "  URL: https://github.com/ppc86193-lgtm/pc28-predictor"
echo "  Commit: b13b471"
echo ""
echo "重启Kiro以应用配置！"
