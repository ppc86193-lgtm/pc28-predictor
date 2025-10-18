#!/usr/bin/env python3
"""
Logic Error Detection Test
Check for common logic errors and hardcoded values
"""

import sys
import re
import os
from typing import List, Dict, Tuple

def check_hardcoded_values(file_path: str) -> List[Dict[str, str]]:
    """Check for hardcoded values in a file"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Common hardcoded patterns to check
        patterns = [
            (r'\b0\.5[6-9]\b', 'Hardcoded accuracy threshold'),
            (r'\b0\.6[0-9]\b', 'Hardcoded accuracy threshold'),
            (r'\b1\.0[1-9]\b', 'Hardcoded boost factor'),
            (r'\b0\.9[0-9]\b', 'Hardcoded reduction factor'),
            (r'\b[2-9]\.0\b', 'Hardcoded time threshold'),
            (r'\b100\.0\b', 'Hardcoded base score'),
            (r'\b[1-3][0-9]\.0\b', 'Hardcoded penalty value'),
            (r'localhost', 'Hardcoded host'),
            (r':8000\b', 'Hardcoded port'),
            (r'/1024/1024', 'Hardcoded memory conversion')
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, description in patterns:
                if re.search(pattern, line) and not line.strip().startswith('#'):
                    # Skip if it's in a comment or string literal context
                    if '"""' not in line and "'''" not in line and not line.strip().startswith('*'):
                        issues.append({
                            'file': file_path,
                            'line': i,
                            'issue': description,
                            'code': line.strip(),
                            'type': 'hardcoded_value'
                        })
    
    except Exception as e:
        issues.append({
            'file': file_path,
            'line': 0,
            'issue': f'Failed to read file: {e}',
            'code': '',
            'type': 'file_error'
        })
    
    return issues

def check_logic_errors(file_path: str) -> List[Dict[str, str]]:
    """Check for common logic errors"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Logic error patterns
        logic_patterns = [
            (r'if.*==.*and.*==', 'Potential logic error: multiple equality checks'),
            (r'if.*<.*and.*>', 'Potential logic error: contradictory conditions'),
            (r'if.*>.*and.*<', 'Check range logic'),
            (r'len\([^)]+\)\s*==\s*0', 'Use "not list" instead of "len(list) == 0"'),
            (r'==\s*True\b', 'Use "if variable" instead of "if variable == True"'),
            (r'==\s*False\b', 'Use "if not variable" instead of "if variable == False"'),
            (r'except:', 'Bare except clause - should specify exception type'),
            (r'return\s*$', 'Empty return statement - consider returning None explicitly')
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, description in logic_patterns:
                if re.search(pattern, line) and not line.strip().startswith('#'):
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'issue': description,
                        'code': line.strip(),
                        'type': 'logic_error'
                    })
    
    except Exception as e:
        issues.append({
            'file': file_path,
            'line': 0,
            'issue': f'Failed to read file: {e}',
            'code': '',
            'type': 'file_error'
        })
    
    return issues

def check_potential_bugs(file_path: str) -> List[Dict[str, str]]:
    """Check for potential bugs"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Potential bug patterns
        bug_patterns = [
            (r'\.get\([^)]+\)\[', 'Potential KeyError: accessing dict.get() result with []'),
            (r'/\s*len\(', 'Potential division by zero if list is empty'),
            (r'int\([^)]*\)', 'Potential ValueError: int() conversion without validation'),
            (r'float\([^)]*\)', 'Potential ValueError: float() conversion without validation'),
            (r'\.split\(\)\[', 'Potential IndexError: accessing split result without length check'),
            (r'list\[[0-9]+\]', 'Potential IndexError: hardcoded list index access'),
            (r'dict\[["\'][^"\']*["\']\]', 'Potential KeyError: direct dict access without get()'),
            (r'time\.sleep\([1-9]', 'Long sleep in code - consider if this is intentional')
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, description in bug_patterns:
                if re.search(pattern, line) and not line.strip().startswith('#'):
                    issues.append({
                        'file': file_path,
                        'line': i,
                        'issue': description,
                        'code': line.strip(),
                        'type': 'potential_bug'
                    })
    
    except Exception as e:
        issues.append({
            'file': file_path,
            'line': 0,
            'issue': f'Failed to read file: {e}',
            'code': '',
            'type': 'file_error'
        })
    
    return issues

def check_configuration_usage(file_path: str) -> List[Dict[str, str]]:
    """Check if configuration is properly used"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file uses hardcoded values but doesn't import config
        has_config_import = 'config_constants' in content or 'get_.*_config' in content
        
        # Patterns that suggest configuration should be used
        config_patterns = [
            (r'0\.5[6-9]', 'accuracy threshold'),
            (r'0\.6[0-9]', 'accuracy threshold'),
            (r'1\.0[1-9]', 'boost factor'),
            (r'100\.0', 'base score'),
            (r'8000', 'port number'),
            (r'"0\.0\.0\.0"', 'host address')
        ]
        
        if not has_config_import:
            for pattern, description in config_patterns:
                if re.search(pattern, content):
                    issues.append({
                        'file': file_path,
                        'line': 0,
                        'issue': f'File contains {description} but does not import configuration',
                        'code': f'Pattern: {pattern}',
                        'type': 'config_missing'
                    })
                    break  # Only report once per file
    
    except Exception as e:
        issues.append({
            'file': file_path,
            'line': 0,
            'issue': f'Failed to read file: {e}',
            'code': '',
            'type': 'file_error'
        })
    
    return issues

def main():
    """Run logic error detection"""
    print("🔍 Logic Error and Hardcoded Value Detection")
    print("=" * 60)
    
    # Files to check
    files_to_check = [
        'pc28_predictor/main.py',
        'pc28_predictor/monitor.py',
        'pc28_predictor/prediction_engine.py',
        'pc28_predictor/markov_model.py',
        'pc28_predictor/tail_analyzer.py',
        'pc28_predictor/optimizer.py'
    ]
    
    all_issues = []
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"\n📁 Checking {file_path}...")
            
            # Check for hardcoded values
            hardcoded_issues = check_hardcoded_values(file_path)
            
            # Check for logic errors
            logic_issues = check_logic_errors(file_path)
            
            # Check for potential bugs
            bug_issues = check_potential_bugs(file_path)
            
            # Check configuration usage
            config_issues = check_configuration_usage(file_path)
            
            file_issues = hardcoded_issues + logic_issues + bug_issues + config_issues
            all_issues.extend(file_issues)
            
            if file_issues:
                for issue in file_issues:
                    icon = {
                        'hardcoded_value': '🔢',
                        'logic_error': '🧠',
                        'potential_bug': '🐛',
                        'config_missing': '⚙️',
                        'file_error': '❌'
                    }.get(issue['type'], '❓')
                    
                    if issue['line'] > 0:
                        print(f"  {icon} Line {issue['line']}: {issue['issue']}")
                        print(f"     Code: {issue['code']}")
                    else:
                        print(f"  {icon} {issue['issue']}")
            else:
                print("  ✅ No issues found")
        else:
            print(f"  ❌ File not found: {file_path}")
    
    print("\n" + "=" * 60)
    print(f"Summary: {len(all_issues)} total issues found")
    
    # Group issues by type
    issue_types = {}
    for issue in all_issues:
        issue_type = issue['type']
        if issue_type not in issue_types:
            issue_types[issue_type] = 0
        issue_types[issue_type] += 1
    
    if issue_types:
        print("\nIssue breakdown:")
        for issue_type, count in issue_types.items():
            icon = {
                'hardcoded_value': '🔢',
                'logic_error': '🧠',
                'potential_bug': '🐛',
                'config_missing': '⚙️',
                'file_error': '❌'
            }.get(issue_type, '❓')
            print(f"  {icon} {issue_type}: {count}")
    
    # Check if config_constants.py exists
    if os.path.exists('pc28_predictor/config_constants.py'):
        print("\n✅ Configuration file exists: pc28_predictor/config_constants.py")
    else:
        print("\n❌ Configuration file missing: pc28_predictor/config_constants.py")
    
    print(f"\n🏁 Logic Error Detection {'COMPLETED' if len(all_issues) == 0 else 'FOUND ISSUES'}")
    
    return len(all_issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)