# GitHub推送指南

## 快速推送步骤

### 方法1：创建Personal Access Token（推荐）

1. **访问GitHub创建Token**
   - 打开：https://github.com/settings/tokens/new
   - Token名称：`pc28-predictor-push`
   - 过期时间：选择你需要的（建议30天或更长）
   - 权限勾选：
     - ✅ `repo` (完整仓库访问权限)
   - 点击 "Generate token"
   - **复制生成的token**（只显示一次！）

2. **使用Token推送**
   ```bash
   # 推送时会提示输入用户名和密码
   git push -u origin main
   
   # 输入：
   # Username: Ww62215764
   # Password: [粘贴你的token]
   ```

### 方法2：使用GitHub CLI（最简单）

```bash
# 安装GitHub CLI（如果未安装）
brew install gh

# 登录
gh auth login

# 推送
git push -u origin main
```

### 方法3：修复SSH密钥问题

你的SSH密钥可能被设置为deploy key，需要重新添加为账户级别的密钥：

1. **复制你的公钥**
   ```bash
   cat ~/.ssh/id_rsa.pub | pbcopy
   ```

2. **添加到GitHub账户**
   - 访问：https://github.com/settings/keys
   - 点击 "New SSH key"
   - Title: `MacBook Air - pc28`
   - Key: 粘贴公钥
   - 点击 "Add SSH key"

3. **切换回SSH并推送**
   ```bash
   git remote set-url origin git@github.com:Ww62215764/9987.git
   git push -u origin main
   ```

## 当前仓库信息

- **仓库URL**: https://github.com/Ww62215764/9987.git
- **分支**: main
- **最新Commit**: b13b471
- **提交信息**: 添加Git推送就绪报告和完整系统状态

## 推送后验证

推送成功后，访问：
https://github.com/Ww62215764/9987

你应该能看到所有文件，包括：
- ✅ pc28_predictor/ 目录
- ✅ test_realtime_quick.py
- ✅ GIT_PUSH_READY.md
- ✅ QUICK_FIX_REPORT.md
- ✅ 等等...

## 需要帮助？

如果遇到问题，告诉我你选择了哪个方法，我会继续帮你！
