#!/bin/bash
# PC28 Predictor - Kiro信任命令快速配置脚本
# 避免每次执行命令都需要手动授权

echo "🔧 配置Kiro信任命令"
echo "==================="
echo ""

# 检查Kiro配置目录
KIRO_DIR=".kiro/settings"
if [ ! -d "$KIRO_DIR" ]; then
    echo "📁 创建Kiro配置目录..."
    mkdir -p "$KIRO_DIR"
fi

# PC28项目常用命令列表
TRUSTED_COMMANDS=(
    # Docker相关
    "docker *"
    "docker-compose *"
    
    # Python开发
    "python3 *"
    "pip *"
    "pytest *"
    "uvicorn *"
    "celery *"
    
    # Git版本控制
    "git *"
    
    # 系统命令
    "curl *"
    "ls *"
    "cat *"
    "cd *"
    "mkdir *"
    "rm *"
    "cp *"
    "mv *"
    "chmod *"
    "source *"
    "export *"
    "echo *"
    "sleep *"
    
    # 监控和调试
    "df *"
    "ps *"
    "kill *"
    "killall *"
    "which *"
    "whereis *"
    "find *"
    "grep *"
    "tail *"
    "head *"
    
    # Kubernetes
    "kubectl *"
    
    # Node.js (用于GitHub MCP)
    "npm *"
    "node *"
    "yarn *"
    
    # Redis
    "redis-cli *"
    
    # 编辑器
    "vim *"
    "nano *"
    "code *"
    "open *"
)

echo "📋 推荐的信任命令配置："
echo ""
echo "针对PC28项目，建议添加以下命令到Kiro信任列表："
echo ""

for cmd in "${TRUSTED_COMMANDS[@]}"; do
    echo "  ✓ $cmd"
done

echo ""
echo "🎯 关键建议："
echo ""
echo "1. 选择 'docker *' (而不是完整命令)"
echo "   - 覆盖所有docker命令：build, run, push, pull, system等"
echo "   - 避免为每个docker子命令单独授权"
echo ""
echo "2. 选择 'python3 *'"
echo "   - 覆盖：python3 -m pytest, python3 verify_*.py等"
echo "   - 支持所有Python脚本执行"
echo ""
echo "3. 选择 'git *'"
echo "   - 覆盖：git add, git commit, git push, git pull等"
echo "   - 支持完整的Git工作流"
echo ""
echo "4. 选择 'kubectl *'"
echo "   - 支持Kubernetes部署和管理"
echo "   - 第七阶段生产部署必需"
echo ""

# 创建Kiro配置文件模板
cat > "$KIRO_DIR/trusted_commands_template.json" << 'EOF'
{
  "trustedCommands": [
    "docker *",
    "docker-compose *",
    "python3 *",
    "pip *",
    "pytest *",
    "git *",
    "curl *",
    "kubectl *",
    "npm *",
    "redis-cli *",
    "uvicorn *",
    "celery *"
  ],
  "autoApprove": true,
  "description": "PC28预测系统核心开发命令"
}
EOF

echo "📄 已创建配置模板：$KIRO_DIR/trusted_commands_template.json"
echo ""

echo "🚀 下一步操作："
echo ""
echo "方法1 - 通过Kiro界面："
echo "  1. 打开Kiro设置 (Preferences)"
echo "  2. 找到 'Trusted Commands' 或 '信任命令'"
echo "  3. 添加上述命令模式"
echo ""
echo "方法2 - 当Kiro询问时："
echo "  1. 选择 'Base' 或 'Partial' 选项"
echo "  2. 使用通配符 (*) 而不是完整命令"
echo "  3. 例如：选择 'docker *' 而不是 'docker system prune -a --volumes -f'"
echo ""
echo "方法3 - 批量导入："
echo "  1. 复制 trusted_commands_template.json 内容"
echo "  2. 粘贴到Kiro配置文件中"
echo ""

echo "⚠️  当前磁盘使用率99%，建议立即清理："
echo "  docker system prune -a --volumes -f"
echo ""
echo "✅ 配置完成后，所有命令将自动执行，无需手动授权！"