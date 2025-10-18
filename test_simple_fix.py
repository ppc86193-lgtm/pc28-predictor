#!/usr/bin/env python3
"""
Simple test to verify the syntax fix
"""

import sys
sys.path.append('pc28_predictor')

def main():
    print("🧪 Testing syntax fix...")
    
    try:
        from prediction_engine import PC28PredictionEngine, PredictionConfig
        print("✅ Imports successful")
        
        config = PredictionConfig()
        print(f"✅ Config created: tail_window={config.tail_window}")
        
        engine = PC28PredictionEngine()
        print(f"✅ Engine created: accuracy_history length={len(engine.accuracy_history)}")
        
        print("🎉 All tests passed! Syntax error fixed.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)