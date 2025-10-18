import json
import redis
import os

# Load configuration
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

# API Configuration
api_key_aimlapi = config['api_key_aimlapi']
api_key_data = config['api_key_data']
app_id = config['app_id']
real_time_url = config['real_time_url']
history_url = config['history_url']
aimlapi_base = config['aimlapi_base']

# Redis Configuration
redis_host = config['redis_host']
redis_port = config['redis_port']

# Initialize Redis client
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)