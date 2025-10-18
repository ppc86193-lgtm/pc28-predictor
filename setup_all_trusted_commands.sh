#!/bin/bash
# 自动配置工作区和用户区的trusted commands

echo "🚀 配置Kiro Trusted Commands..."

# 用户级配置文件路径
USER_CONFIG="$HOME/.kiro/settings/trusted_commands.json"

# 工作区配置文件路径
WORKSPACE_CONFIG=".kiro/settings/trusted_commands.json"

# 创建用户级目录
mkdir -p "$HOME/.kiro/settings"

# 完整的trusted commands列表
cat > /tmp/trusted_commands.json << 'EOF'
{
  "trustedCommands": [
    "git *",
    "docker *",
    "docker-compose *",
    "python *",
    "python3 *",
    "pip *",
    "pip3 *",
    "pytest *",
    "curl *",
    "wget *",
    "ls *",
    "cat *",
    "cd *",
    "mkdir *",
    "rm *",
    "cp *",
    "mv *",
    "chmod *",
    "chown *",
    "source *",
    "export *",
    "echo *",
    "sleep *",
    "uvicorn *",
    "celery *",
    "redis-cli *",
    "redis-server *",
    "kubectl *",
    "npm *",
    "node *",
    "yarn *",
    "df *",
    "du *",
    "ps *",
    "top *",
    "htop *",
    "kill *",
    "killall *",
    "which *",
    "whereis *",
    "find *",
    "grep *",
    "egrep *",
    "fgrep *",
    "tail *",
    "head *",
    "less *",
    "more *",
    "vim *",
    "vi *",
    "nano *",
    "code *",
    "open *",
    "ssh *",
    "scp *",
    "rsync *",
    "tar *",
    "gzip *",
    "gunzip *",
    "zip *",
    "unzip *",
    "make *",
    "cmake *",
    "gcc *",
    "g++ *",
    "clang *",
    "rustc *",
    "cargo *",
    "go *",
    "java *",
    "javac *",
    "mvn *",
    "gradle *",
    "ruby *",
    "gem *",
    "bundle *",
    "php *",
    "composer *",
    "perl *",
    "bash *",
    "sh *",
    "zsh *",
    "fish *",
    "awk *",
    "sed *",
    "sort *",
    "uniq *",
    "wc *",
    "xargs *",
    "date *",
    "time *",
    "watch *",
    "screen *",
    "tmux *",
    "systemctl *",
    "service *",
    "journalctl *",
    "netstat *",
    "ss *",
    "lsof *",
    "ifconfig *",
    "ip *",
    "ping *",
    "traceroute *",
    "nslookup *",
    "dig *",
    "host *",
    "nc *",
    "telnet *",
    "ftp *",
    "sftp *"
  ],
  "description": "完整的开发环境信任命令列表 - 自动配置",
  "version": "2.0",
  "lastUpdated": "2024-10-18"
}
EOF

# 复制到用户级配置
cp /tmp/trusted_commands.json "$USER_CONFIG"
echo "✅ 用户级配置已更新: $USER_CONFIG"

# 复制到工作区配置
cp /tmp/trusted_commands.json "$WORKSPACE_CONFIG"
echo "✅ 工作区配置已更新: $WORKSPACE_CONFIG"

# 清理临时文件
rm /tmp/trusted_commands.json

echo ""
echo "🎉 Trusted Commands配置完成！"
echo ""
echo "已配置的命令包括："
echo "  - Git命令 (git *)"
echo "  - Docker命令 (docker *, docker-compose *)"
echo "  - Python命令 (python*, pip*, pytest*)"
echo "  - 系统命令 (ls, cat, mkdir, rm, cp, mv等)"
echo "  - 网络命令 (curl, wget, ssh, scp等)"
echo "  - 开发工具 (npm, node, kubectl等)"
echo ""
echo "下次执行这些命令时将不再需要授权！"
