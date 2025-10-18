import requests
import json
import hashlib
import time
import logging
from pydantic import BaseModel
from typing import List, Dict, Any
from config import api_key_aimlapi, api_key_data, app_id, real_time_url, history_url, aimlapi_base

logger = logging.getLogger(__name__)

class PC28Data(BaseModel):
    """PC28 lottery data model"""
    sum: int
    tail: int
    combination: str

def generate_sign(params: Dict[str, str]) -> str:
    """Generate signature for PC28 API authentication"""
    sorted_params = ''.join(f"{k}{v}" for k, v in sorted(params.items()) if v) + api_key_data
    return hashlib.md5(sorted_params.encode()).hexdigest()

def fetch_realtime_data() -> Dict[str, Any]:
    """Fetch real-time PC28 lottery data"""
    try:
        timestamp = str(int(time.time()))
        params = {"appid": app_id, "format": "json", "time": timestamp}
        params["sign"] = generate_sign(params)
        
        response = requests.post(real_time_url, data=params, timeout=5)
        response.raise_for_status()
        
        logger.info("Successfully fetched real-time PC28 data")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch real-time data: {e}")
        raise

def fetch_history_data(date: str, limit: int = 1000) -> Dict[str, Any]:
    """Fetch historical PC28 lottery data"""
    try:
        params = {"appid": app_id, "date": date, "limit": str(limit), "format": "json"}
        params["sign"] = generate_sign(params)
        
        response = requests.post(history_url, data=params, timeout=5)
        response.raise_for_status()
        
        logger.info(f"Successfully fetched {limit} historical records for {date}")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch history data: {e}")
        raise

def get_model_list() -> Dict[str, Any]:
    """Fetch AI/ML model list from external API"""
    try:
        headers = {"Authorization": f"Bearer {api_key_aimlapi}"}
        response = requests.get(f"{aimlapi_base}/models", headers=headers)
        response.raise_for_status()
        
        logger.info("Successfully fetched AI/ML model list")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch model list: {e}")
        raise

def test_api_connections() -> Dict[str, bool]:
    """Test all API connections for system validation"""
    results = {}
    
    # Test AI/ML API
    try:
        get_model_list()
        results['aiml_api'] = True
        logger.info("AI/ML API connection: SUCCESS")
    except Exception as e:
        results['aiml_api'] = False
        logger.error(f"AI/ML API connection: FAILED - {e}")
    
    # Test PC28 real-time API
    try:
        fetch_realtime_data()
        results['pc28_realtime'] = True
        logger.info("PC28 real-time API connection: SUCCESS")
    except Exception as e:
        results['pc28_realtime'] = False
        logger.error(f"PC28 real-time API connection: FAILED - {e}")
    
    # Test PC28 history API
    try:
        fetch_history_data("2025-10-18", 10)  # Small test request
        results['pc28_history'] = True
        logger.info("PC28 history API connection: SUCCESS")
    except Exception as e:
        results['pc28_history'] = False
        logger.error(f"PC28 history API connection: FAILED - {e}")
    
    return results