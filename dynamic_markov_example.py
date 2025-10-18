#!/usr/bin/env python3
"""
Example usage of DynamicMarkovModel for Phase 6 Task 2: Algorithm Optimization
"""

import sys
import numpy as np
from markov_model import DynamicMarkovModel, get_dynamic_markov_model

def demonstrate_dynamic_ema():
    """Demonstrate dynamic EMA weight adjustment"""
    print("🔧 Dynamic Markov Model Demonstration")
    print("=" * 50)
    
    # Create a dynamic model
    model = DynamicMarkovModel(initial_ema_alpha=0.3)
    print(f"Initial EMA alpha: {model.ema_alpha:.3f}")
    
    # Simulate accuracy feedback over time
    accuracy_scenarios = [
        (0.45, "Low accuracy - should increase responsiveness"),
        (0.50, "Still low - continue increasing"),
        (0.58, "In target range - should stabilize"),
        (0.59, "Still in range - no change"),
        (0.65, "High accuracy - should decrease responsiveness"),
        (0.70, "Very high - continue decreasing"),
        (0.57, "Back to target - should stabilize")
    ]
    
    print("\n📊 Accuracy Feedback Simulation:")
    print("Accuracy | EMA Alpha | Change | Status")
    print("-" * 45)
    
    for accuracy, description in accuracy_scenarios:
        old_alpha = model.ema_alpha
        model.update_ema_weights(accuracy)
        change = model.ema_alpha - old_alpha
        
        status = "↑" if change > 0.001 else "↓" if change < -0.001 else "→"
        print(f"{accuracy:8.3f} | {model.ema_alpha:9.3f} | {change:+6.3f} | {status} {description}")
    
    # Show optimization stats
    print(f"\n📈 Final Optimization Stats:")
    stats = model.get_optimization_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Demonstrate dynamic EMA weights
    print(f"\n⚖️  Dynamic EMA Weights (5 periods):")
    weights = model.get_dynamic_ema_weights(5)
    for i, weight in enumerate(weights):
        print(f"  Period {i+1}: {weight:.4f}")
    print(f"  Sum: {sum(weights):.6f}")
    
    return model

def compare_static_vs_dynamic():
    """Compare static vs dynamic EMA calculations"""
    print("\n🔄 Static vs Dynamic EMA Comparison")
    print("=" * 50)
    
    from markov_model import calculate_ema_weights
    
    # Static EMA weights
    static_weights = calculate_ema_weights(5)
    print("Static EMA weights:")
    for i, weight in enumerate(static_weights):
        print(f"  Period {i+1}: {weight:.4f}")
    
    # Dynamic EMA weights (high responsiveness)
    dynamic_model_high = DynamicMarkovModel(0.8)
    dynamic_weights_high = dynamic_model_high.get_dynamic_ema_weights(5)
    print("\nDynamic EMA weights (high α=0.8):")
    for i, weight in enumerate(dynamic_weights_high):
        print(f"  Period {i+1}: {weight:.4f}")
    
    # Dynamic EMA weights (low responsiveness)
    dynamic_model_low = DynamicMarkovModel(0.2)
    dynamic_weights_low = dynamic_model_low.get_dynamic_ema_weights(5)
    print("\nDynamic EMA weights (low α=0.2):")
    for i, weight in enumerate(dynamic_weights_low):
        print(f"  Period {i+1}: {weight:.4f}")

def test_singleton_pattern():
    """Test the singleton pattern"""
    print("\n🔗 Singleton Pattern Test")
    print("=" * 50)
    
    model1 = get_dynamic_markov_model()
    model2 = get_dynamic_markov_model()
    
    print(f"Model 1 ID: {id(model1)}")
    print(f"Model 2 ID: {id(model2)}")
    print(f"Same instance: {model1 is model2}")
    
    # Update through one reference
    model1.update_ema_weights(0.65)
    print(f"Model 1 alpha after update: {model1.ema_alpha:.3f}")
    print(f"Model 2 alpha (should be same): {model2.ema_alpha:.3f}")

def main():
    """Run all demonstrations"""
    try:
        # Main demonstration
        model = demonstrate_dynamic_ema()
        
        # Comparison
        compare_static_vs_dynamic()
        
        # Singleton test
        test_singleton_pattern()
        
        print("\n✅ Dynamic Markov Model demonstration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)