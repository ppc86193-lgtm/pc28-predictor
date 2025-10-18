"""
Configuration management for PC28 Prediction System.

This module handles:
- Loading configuration from config.json
- Setting up Redis client with fallback to MockRedis
- Environment variable support for Docker deployments
"""

import json
import redis
import os
import logging
from typing import Dict, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

# Load configuration
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
try:
    with open(config_path, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    raise FileNotFoundError(f"Configuration file not found: {config_path}")
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid JSON in configuration file: {e}")

# Validate required configuration keys
required_keys = [
    'api_key_aimlapi', 'api_key_data', 'app_id', 
    'real_time_url', 'history_url', 'aimlapi_base'
]
missing_keys = [key for key in required_keys if key not in config]
if missing_keys:
    raise ValueError(f"Missing required configuration keys: {missing_keys}")

# API Configuration
api_key_aimlapi = config['api_key_aimlapi']
api_key_data = config['api_key_data']
app_id = config['app_id']
real_time_url = config['real_time_url']
history_url = config['history_url']
aimlapi_base = config['aimlapi_base']

# Redis Configuration - Use environment variables for Docker deployment
redis_host = os.getenv('REDIS_HOST', config.get('redis_host', 'redis'))
redis_port = int(os.getenv('REDIS_PORT', config.get('redis_port', 6379)))

# Initialize Redis client with connection retry
try:
    redis_client = redis.Redis(
        host=redis_host, 
        port=redis_port, 
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30
    )
    # Test connection
    redis_client.ping()
    logger.info(f"Redis连接成功: {redis_host}:{redis_port}")
except redis.ConnectionError as e:
    logger.warning(f"Redis连接失败: {e}")
    # 创建一个模拟的Redis客户端用于开发环境
    class MockRedis:
        def __init__(self):
            self._data = {}
        
        def get(self, key):
            return self._data.get(key)
        
        def set(self, key, value, ex=None):
            self._data[key] = value
            return True
        
        def delete(self, key):
            return self._data.pop(key, None) is not None
        
        def exists(self, key):
            return key in self._data
        
        def keys(self, pattern="*"):
            if pattern == "*":
                return list(self._data.keys())
            # Simple pattern matching for basic cases
            import fnmatch
            return [k for k in self._data.keys() if fnmatch.fnmatch(k, pattern)]
        
        def ping(self):
            return True
    redis_client = MockRedis()
    logger.info("使用模拟Redis客户端")