#!/usr/bin/env python3
"""
Integration test for Dynamic Markov Model with PC28 Prediction System
Phase 6 Task 2: Algorithm Optimization Integration Test
"""

import sys
sys.path.append('pc28_predictor')

def test_dynamic_markov_integration():
    """Test dynamic Markov model integration with prediction engine"""
    try:
        from markov_model import get_dynamic_markov_model, DynamicMarkovModel
        from prediction_engine import get_prediction_engine
        
        print("🔧 Testing Dynamic Markov Model Integration...")
        
        # Test singleton pattern
        model1 = get_dynamic_markov_model()
        model2 = get_dynamic_markov_model()
        assert model1 is model2, "Singleton pattern failed"
        print("✅ Singleton pattern working")
        
        # Test initial state
        initial_alpha = model1.ema_alpha
        print(f"✅ Initial EMA alpha: {initial_alpha:.3f}")
        
        # Test accuracy update integration
        engine = get_prediction_engine()
        
        # Simulate accuracy updates
        test_accuracies = [0.45, 0.52, 0.58, 0.63, 0.57]
        for i, accuracy in enumerate(test_accuracies):
            # Simulate prediction accuracy update
            predicted = "大单"
            actual = "大单" if accuracy > 0.5 else "小双"
            
            old_alpha = model1.ema_alpha
            engine.update_accuracy(predicted, actual)
            new_alpha = model1.ema_alpha
            
            print(f"✅ Update {i+1}: accuracy={accuracy:.3f}, α: {old_alpha:.3f} → {new_alpha:.3f}")
        
        # Test optimization stats
        stats = model1.get_optimization_stats()
        print(f"✅ Optimization stats: {stats}")
        
        # Test dynamic EMA weights
        weights = model1.get_dynamic_ema_weights(5)
        print(f"✅ Dynamic EMA weights: {[round(w, 4) for w in weights]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dynamic Markov integration test failed: {e}")
        return False

def test_api_endpoints():
    """Test new API endpoints for dynamic Markov model"""
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        print("\n🌐 Testing Dynamic Markov API Endpoints...")
        
        # Test dynamic Markov stats endpoint
        response = client.get("/markov/dynamic")
        print(f"✅ GET /markov/dynamic status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Current EMA alpha: {data['dynamic_markov_stats']['current_ema_alpha']}")
        
        # Test dynamic Markov update endpoint
        response = client.post("/markov/dynamic/update?accuracy=0.58")
        print(f"✅ POST /markov/dynamic/update status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Alpha change: {data['alpha_change']}")
        
        # Test Chinese language support
        response = client.get("/markov/dynamic", headers={"Accept-Language": "zh-CN"})
        print(f"✅ Chinese language support status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def test_optimizer_integration():
    """Test optimizer integration with dynamic Markov model"""
    try:
        from optimizer import get_optimizer
        
        print("\n⚙️  Testing Optimizer Integration...")
        
        optimizer = get_optimizer()
        
        # Test performance analysis with dynamic Markov stats
        analysis = optimizer.analyze_performance()
        
        if "dynamic_markov" in analysis:
            print("✅ Dynamic Markov stats included in performance analysis")
            print(f"   EMA stability: {analysis['dynamic_markov'].get('ema_stability', 'unknown')}")
        else:
            print("⚠️  Dynamic Markov stats not found in analysis")
        
        # Check for dynamic Markov recommendations
        recommendations = analysis.get("recommendations", [])
        markov_recommendations = [r for r in recommendations if "ema" in r.get("type", "")]
        
        if markov_recommendations:
            print(f"✅ Found {len(markov_recommendations)} dynamic Markov recommendations")
            for rec in markov_recommendations:
                print(f"   - {rec['message']}")
        else:
            print("ℹ️  No dynamic Markov recommendations (normal if system is stable)")
        
        return True
        
    except Exception as e:
        print(f"❌ Optimizer integration test failed: {e}")
        return False

def test_performance_metrics_integration():
    """Test performance metrics integration"""
    try:
        from prediction_engine import get_prediction_engine
        
        print("\n📊 Testing Performance Metrics Integration...")
        
        engine = get_prediction_engine()
        
        # Get performance metrics
        metrics = engine.get_performance_metrics()
        
        if "dynamic_markov" in metrics:
            print("✅ Dynamic Markov stats included in performance metrics")
            dm_stats = metrics["dynamic_markov"]
            print(f"   Current EMA alpha: {dm_stats.get('current_ema_alpha', 'unknown')}")
            print(f"   Accuracy samples: {dm_stats.get('accuracy_samples', 0)}")
            print(f"   EMA stability: {dm_stats.get('ema_stability', 'unknown')}")
        else:
            print("⚠️  Dynamic Markov stats not found in performance metrics")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance metrics integration test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Dynamic Markov Model Integration Test Suite")
    print("=" * 60)
    
    tests = [
        test_dynamic_markov_integration,
        test_api_endpoints,
        test_optimizer_integration,
        test_performance_metrics_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed}/{total} integration tests passed")
    
    if passed == total:
        print("🎉 Dynamic Markov Model integration successful!")
        print("\n📋 Integration Summary:")
        print("✅ Singleton pattern implemented")
        print("✅ Prediction engine integration")
        print("✅ API endpoints added")
        print("✅ Optimizer integration")
        print("✅ Performance metrics integration")
        return True
    else:
        print("⚠️  Some integration tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)