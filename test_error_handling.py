"""
Test suite for error handling mechanisms
Phase 2.2: Error Handling Implementation
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from api_client import (
    ErrorResponse,
    SystemHealth,
    PC28APIError,
    AIMLAPIError,
    DataValidationError,
    RedisConnectionError,
    log_error,
    reset_error_counts,
    check_system_health
)

class TestErrorResponse:
    """Test ErrorResponse model"""
    
    def test_valid_error_response(self):
        """Test valid error response creation"""
        error = ErrorResponse(
            error_code="TEST_ERROR",
            message="Test error message",
            details={"context": "test"}
        )
        assert error.error_code == "TEST_ERROR"
        assert error.message == "Test error message"
        assert error.details["context"] == "test"
        assert isinstance(error.timestamp, datetime)
    
    def test_error_response_minimal(self):
        """Test error response with minimal fields"""
        error = ErrorResponse(
            error_code="MINIMAL_ERROR",
            message="Minimal error"
        )
        assert error.error_code == "MINIMAL_ERROR"
        assert error.message == "Minimal error"
        assert error.details is None

class TestSystemHealth:
    """Test SystemHealth model"""
    
    def test_healthy_system(self):
        """Test healthy system status"""
        health = SystemHealth(
            status="healthy",
            redis_connected=True,
            aiml_api_available=True,
            pc28_api_available=True
        )
        assert health.status == "healthy"
        assert health.redis_connected == True
        assert len(health.errors) == 0
    
    def test_degraded_system(self):
        """Test degraded system status"""
        health = SystemHealth(
            status="degraded",
            redis_connected=True,
            aiml_api_available=False,
            pc28_api_available=True,
            errors=["AI/ML API unavailable"]
        )
        assert health.status == "degraded"
        assert len(health.errors) == 1
    
    def test_unhealthy_system(self):
        """Test unhealthy system status"""
        health = SystemHealth(
            status="unhealthy",
            redis_connected=False,
            aiml_api_available=False,
            pc28_api_available=False,
            errors=["Redis down", "All APIs unavailable"]
        )
        assert health.status == "unhealthy"
        assert len(health.errors) == 2

class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_pc28_api_error(self):
        """Test PC28APIError exception"""
        error = PC28APIError(
            "API timeout",
            "PC28_TIMEOUT",
            {"url": "test.com", "timeout": 5}
        )
        assert error.message == "API timeout"
        assert error.error_code == "PC28_TIMEOUT"
        assert error.details["timeout"] == 5
    
    def test_aiml_api_error(self):
        """Test AIMLAPIError exception"""
        error = AIMLAPIError("Authentication failed")
        assert error.message == "Authentication failed"
        assert error.error_code == "AIML_API_ERROR"
        assert error.details == {}
    
    def test_data_validation_error(self):
        """Test DataValidationError exception"""
        error = DataValidationError(
            "Invalid sum value",
            "INVALID_SUM",
            {"sum": 28, "max": 27}
        )
        assert error.message == "Invalid sum value"
        assert error.error_code == "INVALID_SUM"
        assert error.details["sum"] == 28
    
    def test_redis_connection_error(self):
        """Test RedisConnectionError exception"""
        error = RedisConnectionError("Connection refused")
        assert error.message == "Connection refused"
        assert error.error_code == "REDIS_CONNECTION_ERROR"

class TestErrorLogging:
    """Test error logging functionality"""
    
    def setup_method(self):
        """Reset error counts before each test"""
        reset_error_counts()
    
    def test_log_error_basic(self):
        """Test basic error logging"""
        error = PC28APIError("Test error")
        response = log_error("pc28_api", error)
        
        assert isinstance(response, ErrorResponse)
        assert response.error_code == "PC28_API_ERROR"
        assert response.message == "Test error"
        assert response.details["error_type"] == "pc28_api"
        assert response.details["error_count"] == 1
    
    def test_log_error_with_context(self):
        """Test error logging with context"""
        error = AIMLAPIError("Auth failed")
        context = {"api_key": "hidden", "endpoint": "/models"}
        response = log_error("aiml_api", error, context)
        
        assert response.details["context"] == context
        assert response.details["error_count"] == 1
    
    def test_error_count_increment(self):
        """Test error count incrementation"""
        error1 = PC28APIError("First error")
        error2 = PC28APIError("Second error")
        
        response1 = log_error("pc28_api", error1)
        response2 = log_error("pc28_api", error2)
        
        assert response1.details["error_count"] == 1
        assert response2.details["error_count"] == 2
    
    def test_reset_error_counts(self):
        """Test error count reset"""
        error = PC28APIError("Test error")
        log_error("pc28_api", error)
        
        reset_error_counts()
        
        response = log_error("pc28_api", error)
        assert response.details["error_count"] == 1

class TestSystemHealthCheck:
    """Test system health check functionality"""
    
    @patch('config.redis_client')
    @patch('api_client.get_model_list')
    @patch('api_client.fetch_history_data')
    @patch('api_client.categorize_models')
    @patch('api_client.extract_features')
    def test_healthy_system_check(self, mock_extract, mock_categorize, 
                                 mock_history, mock_models, mock_redis):
        """Test health check with all systems healthy"""
        # Mock successful responses
        mock_redis.ping.return_value = True
        mock_models.return_value = {"data": []}
        mock_history.return_value = {"retdata": []}
        mock_categorize.return_value = {}
        mock_extract.return_value = []
        
        health = check_system_health()
        
        assert health.status == "healthy"
        assert health.redis_connected == True
        assert health.aiml_api_available == True
        assert health.pc28_api_available == True
        assert len(health.errors) == 0
    
    @patch('config.redis_client')
    @patch('api_client.get_model_list')
    @patch('api_client.fetch_history_data')
    def test_degraded_system_check(self, mock_history, mock_models, mock_redis):
        """Test health check with degraded system"""
        # Mock Redis working, AI/ML API failing, PC28 API working
        mock_redis.ping.return_value = True
        mock_models.side_effect = AIMLAPIError("API unavailable")
        mock_history.return_value = {"retdata": []}
        
        health = check_system_health()
        
        assert health.status == "degraded"
        assert health.redis_connected == True
        assert health.aiml_api_available == False
        assert health.pc28_api_available == True
        assert len(health.errors) > 0
    
    @patch('config.redis_client')
    @patch('api_client.get_model_list')
    @patch('api_client.fetch_history_data')
    def test_unhealthy_system_check(self, mock_history, mock_models, mock_redis):
        """Test health check with unhealthy system"""
        # Mock all systems failing
        mock_redis.ping.side_effect = Exception("Connection refused")
        mock_models.side_effect = AIMLAPIError("API unavailable")
        mock_history.side_effect = PC28APIError("API unavailable")
        
        health = check_system_health()
        
        assert health.status == "unhealthy"
        assert health.redis_connected == False
        assert health.aiml_api_available == False
        assert health.pc28_api_available == False
        assert len(health.errors) >= 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"])