#!/usr/bin/env python3
"""
Test script to verify main.py improvements
"""

import sys
sys.path.append('pc28_predictor')

def test_imports():
    """Test that all imports work correctly"""
    try:
        from main import app, AccuracyUpdateRequest, StandardResponse
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_structure():
    """Test FastAPI app structure"""
    try:
        from main import app
        
        # Check that app has the expected attributes
        assert hasattr(app, 'title')
        assert app.title == "PC28 Prediction System"
        assert hasattr(app, 'version')
        assert app.version == "1.0.0"
        
        print("✅ App structure is correct")
        return True
    except Exception as e:
        print(f"❌ App structure error: {e}")
        return False

def test_pydantic_models():
    """Test Pydantic models"""
    try:
        from main import AccuracyUpdateRequest, StandardResponse
        
        # Test AccuracyUpdateRequest
        request = AccuracyUpdateRequest(predicted="大单", actual="小双")
        assert request.predicted == "大单"
        assert request.actual == "小双"
        
        # Test StandardResponse
        response = StandardResponse(status="success", message="Test message")
        assert response.status == "success"
        assert response.message == "Test message"
        
        print("✅ Pydantic models work correctly")
        return True
    except Exception as e:
        print(f"❌ Pydantic models error: {e}")
        return False

def test_middleware():
    """Test that middleware is properly configured"""
    try:
        from main import app
        
        # Check that middleware is registered
        middleware_count = len(app.user_middleware)
        assert middleware_count > 0, "No middleware registered"
        
        print(f"✅ Middleware configured ({middleware_count} middleware(s))")
        return True
    except Exception as e:
        print(f"❌ Middleware error: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing main.py improvements...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_app_structure,
        test_pydantic_models,
        test_middleware
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All improvements working correctly!")
        return True
    else:
        print("⚠️  Some improvements need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)