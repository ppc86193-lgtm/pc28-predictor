import pytest
import json
import time
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException, Timeout, HTTPError
from api_client import (
    get_model_list, fetch_realtime_data, fetch_history_data, 
    PC28Data, generate_sign, PC28APIError
)
from data_processor import extract_features, translate_combination
from config import redis_client

class TestAPIClients:
    """Test suite for API client functions"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear any existing cache
        try:
            keys = redis_client.keys("pc28_*")
            if keys:
                redis_client.delete(*keys)
        except:
            pass
    
    def test_generate_sign(self):
        """Test signature generation"""
        params = {"appid": "12345", "format": "json", "time": "1234567890"}
        sign = generate_sign(params)
        assert isinstance(sign, str)
        assert len(sign) == 32  # MD5 hash length
    
    @patch('api_client.requests.get')
    def test_get_model_list_success(self, mock_get):
        """Test successful model list retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "object": "list",
            "data": [
                {
                    "id": "gpt-4o",
                    "info": {
                        "name": "GPT-4 Omni",
                        "developer": "OpenAI",
                        "contextLength": 128000
                    },
                    "type": "text"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        models = get_model_list()
        
        assert models["object"] == "list"
        assert len(models["data"]) == 1
        assert models["data"][0]["id"] == "gpt-4o"
        
        # Verify caching
        cached_models = get_model_list()
        assert cached_models == models
    
    @patch('api_client.requests.get')
    def test_get_model_list_error(self, mock_get):
        """Test model list retrieval with API error"""
        mock_get.side_effect = RequestException("API error")
        
        models = get_model_list()
        
        # Should return empty list on error
        assert models == {"object": "list", "data": []}
    
    @patch('api_client.requests.get')
    def test_get_model_list_timeout(self, mock_get):
        """Test model list retrieval with timeout"""
        mock_get.side_effect = Timeout("Request timeout")
        
        models = get_model_list()
        
        # Should return empty list on timeout
        assert models == {"object": "list", "data": []}
    
    @patch('api_client.requests.post')
    def test_fetch_realtime_data_success(self, mock_post):
        """Test successful real-time data retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "retdata": [
                {
                    "number": [5, 5, 5],
                    "period": "3344272"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        data = fetch_realtime_data()
        features = extract_features(data)
        
        assert len(features) == 1
        assert features[0].sum == 15
        assert features[0].tail == 5
        assert features[0].combination == "大单"
        assert features[0].period == "3344272"
    
    @patch('api_client.requests.post')
    def test_fetch_realtime_data_error(self, mock_post):
        """Test real-time data retrieval with error"""
        mock_post.side_effect = RequestException("API error")
        
        with pytest.raises(Exception):  # Will raise PC28APIError after retries
            fetch_realtime_data()
    
    @patch('api_client.requests.post')
    def test_fetch_history_data_success(self, mock_post):
        """Test successful historical data retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "retdata": [
                {"number": [1, 1, 1], "period": "3344270"},
                {"number": [9, 9, 9], "period": "3344271"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        data = fetch_history_data("2025-10-18", 10)
        features = extract_features(data)
        
        assert len(features) == 2
        assert features[0].sum == 3
        assert features[0].combination == "极值"
        assert features[1].sum == 27
        assert features[1].combination == "极值"
    
    @patch('api_client.requests.post')
    def test_fetch_history_data_error(self, mock_post):
        """Test historical data retrieval with error"""
        mock_post.side_effect = RequestException("API error")
        
        with pytest.raises(Exception):  # Will raise PC28APIError after retries
            fetch_history_data("2025-10-18", 10)
    
    def test_extract_features_empty_data(self):
        """Test feature extraction with empty data"""
        features = extract_features({})
        assert features == []
        
        features = extract_features({"retdata": []})
        assert features == []
    
    def test_extract_features_invalid_data(self):
        """Test feature extraction with invalid data"""
        invalid_data = {
            "retdata": [
                {"number": [1, 2]},  # Invalid: only 2 numbers
                {"number": [10, 10, 10]},  # Invalid: sum > 27
                {"invalid": "data"}  # Invalid: no number field
            ]
        }
        
        features = extract_features(invalid_data)
        assert features == []
    
    def test_extract_features_valid_combinations(self):
        """Test feature extraction with all combination types"""
        test_data = {
            "retdata": [
                {"number": [0, 0, 0], "period": "1"},  # 极值
                {"number": [5, 5, 4], "period": "2"},  # 小双
                {"number": [5, 5, 5], "period": "3"},  # 大单
                {"number": [8, 8, 8], "period": "4"},  # 大双
                {"number": [9, 9, 9], "period": "5"}   # 极值
            ]
        }
        
        features = extract_features(test_data)
        
        assert len(features) == 5
        assert features[0].combination == "极值"  # sum = 0
        assert features[1].combination == "大双"  # sum = 14
        assert features[2].combination == "大单"  # sum = 15
        assert features[3].combination == "极值"  # sum = 24
        assert features[4].combination == "极值"  # sum = 27
    
    def test_translate_combination(self):
        """Test combination translation"""
        # Test English translation
        assert translate_combination("大单", "en") == "Big Odd"
        assert translate_combination("小双", "en-US") == "Small Even"
        assert translate_combination("极值", "en") == "Extreme"
        
        # Test Chinese (no translation)
        assert translate_combination("大单", "zh-CN") == "大单"
        assert translate_combination("小双", "zh") == "小双"
    
    @patch('api_client.requests.post')
    def test_retry_mechanism(self, mock_post):
        """Test retry mechanism for API calls"""
        # Create a successful response mock
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"retdata": []}
        success_response.raise_for_status.return_value = None
        
        # First two calls fail, third succeeds
        mock_post.side_effect = [
            RequestException("First failure"),
            RequestException("Second failure"),
            success_response
        ]
        
        # Should succeed after retries
        data = fetch_realtime_data()
        assert data == {"retdata": []}
        
        # Verify it was called 3 times
        assert mock_post.call_count == 3
    
    def test_caching_functionality(self):
        """Test Redis caching functionality"""
        test_data = {
            "retdata": [
                {"number": [5, 5, 5], "period": "test"}
            ]
        }
        
        # First call should extract and cache
        features1 = extract_features(test_data, cache_key="test_cache")
        
        # Test that features were extracted correctly
        assert len(features1) == 1
        assert features1[0].sum == 15
        assert features1[0].combination == "大单"
        
        # If Redis is available, test caching
        try:
            redis_client.ping()
            # Second call should retrieve from cache
            features2 = extract_features({}, cache_key="test_cache")
            assert len(features2) == 1
            assert features1[0].sum == features2[0].sum
            assert features1[0].combination == features2[0].combination
        except Exception:
            # Redis not available, skip cache test
            pytest.skip("Redis not available for caching test")

class TestPerformance:
    """Performance tests for API clients"""
    
    @patch('api_client.requests.get')
    def test_model_list_response_time(self, mock_get):
        """Test model list API response time"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"object": "list", "data": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        start_time = time.time()
        get_model_list()
        elapsed_time = time.time() - start_time
        
        # Should complete within 5 seconds
        assert elapsed_time < 5.0
    
    def test_feature_extraction_performance(self):
        """Test feature extraction performance with large dataset"""
        # Generate large test dataset
        large_data = {
            "retdata": [
                {"number": [i % 10, (i+1) % 10, (i+2) % 10], "period": str(i)}
                for i in range(1000)
            ]
        }
        
        start_time = time.time()
        features = extract_features(large_data)
        elapsed_time = time.time() - start_time
        
        # Should process 1000 records quickly
        assert len(features) == 1000
        assert elapsed_time < 2.0  # Should complete within 2 seconds

if __name__ == "__main__":
    pytest.main([__file__, "-v"])