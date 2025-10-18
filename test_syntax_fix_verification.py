#!/usr/bin/env python3
"""
Syntax Fix Verification Test
Verify that all syntax errors have been fixed
"""

import sys
import os

def test_syntax_fixes():
    """Test that all Python files have correct syntax"""
    print("🔧 Testing Syntax Fixes...")
    
    test_files = [
        'test_final_logic_fixes.py',
        'test_prediction_engine_review.py',
        'test_production_deployment.py',
        'test_5000_cycle_production.py'
    ]
    
    passed = 0
    failed = 0
    
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    code = f.read()
                
                # Try to compile the code
                compile(code, file_path, 'exec')
                print(f"✅ {file_path}: Syntax OK")
                passed += 1
                
            except SyntaxError as e:
                print(f"❌ {file_path}: Syntax Error - {e}")
                failed += 1
            except Exception as e:
                print(f"⚠️ {file_path}: Other Error - {e}")
                failed += 1
        else:
            print(f"⚠️ {file_path}: File not found")
    
    print(f"\n📊 Syntax Test Results: {passed} passed, {failed} failed")
    return failed == 0

def test_imports():
    """Test that key imports work"""
    print("🔧 Testing Key Imports...")
    
    try:
        sys.path.append('pc28_predictor')
        
        # Test configuration imports
        from config_constants import config, get_system_config
        print("✅ config_constants import successful")
        
        # Test that we can access configuration
        system_config = get_system_config()
        print(f"✅ System config accessible: {type(system_config)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def main():
    """Run all syntax verification tests"""
    print("🚀 Syntax Fix Verification")
    print("=" * 40)
    
    syntax_ok = test_syntax_fixes()
    print()
    imports_ok = test_imports()
    
    print("=" * 40)
    if syntax_ok and imports_ok:
        print("🎉 All syntax fixes verified!")
        print("✅ No syntax errors found")
        print("✅ Key imports working")
    else:
        print("❌ Some issues remain")
        sys.exit(1)

if __name__ == "__main__":
    main()