#!/usr/bin/env python3
"""
让Grok自动优化代码
通过GitHub API创建Issue，Grok会自动响应并创建PR
"""

import os
import sys
import json
import subprocess

def create_grok_optimization_issue():
    """创建Grok优化Issue"""
    
    # 获取当前commit
    result = subprocess.run(['git', 'log', '-1', '--pretty=%h'], 
                          capture_output=True, text=True)
    current_commit = result.stdout.strip()
    
    # Issue内容
    issue_body = f"""
# 🤖 Grok自动化优化任务

@grok 请帮我优化PC28预测系统的代码

## 仓库信息
- **Commit**: {current_commit}
- **分支**: main

## 任务清单

### 1. 优化 `pc28_predictor/markov_model.py`
- [ ] 添加自适应EMA步长（根据准确率偏差）
- [ ] 添加30天长期趋势支持
- [ ] 优化`get_model_stats`性能（@lru_cache）
- [ ] 添加`_calculate_long_term_weight`方法

### 2. 优化 `pc28_predictor/tail_analyzer.py`
- [ ] 添加连号模式检测（`_is_consecutive_sequence`）
- [ ] 限制增强因子范围（1.02-1.05）
- [ ] 优化概率调整逻辑

### 3. 优化 `pc28_predictor/prediction_engine.py`
- [ ] 实现动态权重调整（基于准确率）
- [ ] 添加异常fallback机制
- [ ] 优化概率组合逻辑

### 4. 创建测试文件
创建 `test_grok_applied_optimizations.py` 包含：
- 自适应步长测试
- 连号检测测试
- 动态权重测试
- 性能对比测试

## 优化目标
- 组合准确率: 58% → 61%
- 大单/小双: 63% → 66%
- 响应时间: 0.5秒 → <0.2秒
- 性能提升: >50%

## 工作流程
1. 创建分支 `grok-optimization`
2. 应用所有优化
3. 运行测试验证
4. 创建Pull Request

## 验证标准
- ✅ 所有pytest测试通过
- ✅ 性能提升>50%
- ✅ 代码质量>9.0/10

请开始工作并创建PR。谢谢！
"""

    # 创建Issue
    print("🤖 创建Grok优化Issue...")
    print("")
    
    # 使用gh CLI创建issue
    try:
        result = subprocess.run([
            'gh', 'issue', 'create',
            '--repo', 'ppc86193-lgtm/pc28-predictor',
            '--title', '🤖 Grok自动化优化任务',
            '--body', issue_body,
            '--label', 'enhancement,grok-automation,priority-high'
        ], capture_output=True, text=True, check=True)
        
        print("✅ Issue创建成功！")
        print(result.stdout)
        
        # 提取Issue URL
        issue_url = result.stdout.strip()
        print(f"\n📋 Issue URL: {issue_url}")
        print("\n💡 Grok会自动看到这个Issue并开始工作")
        print("📊 监控进度: gh issue list")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 创建Issue失败: {e}")
        print(f"错误输出: {e.stderr}")
        
        print("\n📝 手动创建Issue:")
        print("1. 访问: https://github.com/ppc86193-lgtm/pc28-predictor/issues/new")
        print("2. 标题: 🤖 Grok自动化优化任务")
        print("3. 内容:")
        print("-" * 50)
        print(issue_body)
        print("-" * 50)
        
        return False

def watch_grok_progress():
    """监控Grok工作进度"""
    print("\n🔍 监控Grok工作进度...")
    print("=" * 50)
    
    # 列出所有Issue
    result = subprocess.run([
        'gh', 'issue', 'list',
        '--repo', 'ppc86193-lgtm/pc28-predictor',
        '--label', 'grok-automation'
    ], capture_output=True, text=True)
    
    print(result.stdout)
    
    # 列出所有PR
    result = subprocess.run([
        'gh', 'pr', 'list',
        '--repo', 'ppc86193-lgtm/pc28-predictor',
        '--head', 'grok-optimization'
    ], capture_output=True, text=True)
    
    if result.stdout.strip():
        print("\n🎉 Grok已创建PR:")
        print(result.stdout)
    else:
        print("\n⏳ Grok还在工作中...")

def main():
    """主函数"""
    print("🚀 Grok自动化优化工具")
    print("=" * 50)
    print("")
    
    # 检查gh CLI
    result = subprocess.run(['which', 'gh'], capture_output=True)
    if result.returncode != 0:
        print("❌ GitHub CLI未安装")
        print("请运行: brew install gh")
        print("然后运行: gh auth login")
        return 1
    
    # 检查gh认证
    result = subprocess.run(['gh', 'auth', 'status'], capture_output=True)
    if result.returncode != 0:
        print("❌ GitHub CLI未登录")
        print("请运行: gh auth login")
        return 1
    
    print("✅ GitHub CLI已就绪")
    print("")
    
    # 创建Issue
    if create_grok_optimization_issue():
        print("\n" + "=" * 50)
        print("✅ Grok优化任务已启动！")
        print("=" * 50)
        print("")
        print("下一步:")
        print("1. Grok会自动分析Issue")
        print("2. 创建分支 'grok-optimization'")
        print("3. 应用所有优化")
        print("4. 创建Pull Request")
        print("")
        print("监控命令:")
        print("  gh issue list --label grok-automation")
        print("  gh pr list --head grok-optimization")
        print("")
        print("或运行:")
        print("  python3 grok_auto_optimize.py --watch")
        
        return 0
    else:
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--watch':
        watch_grok_progress()
    else:
        sys.exit(main())
