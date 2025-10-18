import json
import time
import logging
from typing import List, Dict, Any
from pydantic import ValidationError
from config import redis_client
from api_client import PC28Data

logger = logging.getLogger(__name__)

CACHE_PREFIX = "pc28_data:"

def extract_features(data: Dict[str, Any], cache_key: str = None) -> List[PC28Data]:
    """
    Extract and validate PC28 data from API response with optional caching.
    
    Args:
        data: API response containing 'retdata' with number arrays
        cache_key: Optional Redis cache key for storing results
        
    Returns:
        List of validated PC28Data objects
    """
    # Try cache first if cache_key provided
    if cache_key:
        try:
            cached_data = redis_client.get(CACHE_PREFIX + cache_key)
            if cached_data:
                cached_features = json.loads(cached_data)
                logger.info(f"Features retrieved from cache: {cache_key}")
                return [PC28Data(**item) for item in cached_features]
        except Exception as e:
            logger.warning(f"Cache read failed for {cache_key}: {e}")
    
    start_time = time.time()
    features = []
    
    if not data or 'retdata' not in data:
        logger.warning("No valid data found in API response")
        return features
    
    # Optimized feature extraction using list comprehension
    for period_data in data.get('retdata', []):
        try:
            numbers = period_data.get('number', [])
            if not numbers or len(numbers) != 3:
                continue
                
            sum_value = sum(numbers)
            if not (0 <= sum_value <= 27):
                continue
                
            # Determine combination type efficiently
            if sum_value <= 5 or sum_value >= 22:  # 0-5 极小, 22-27 极大
                combination = "极值"
            else:
                size = "大" if sum_value >= 14 else "小"
                parity = "单" if sum_value % 2 else "双"
                combination = size + parity
            
            pc28_data = PC28Data(
                sum=sum_value,
                tail=sum_value % 10,
                combination=combination,
                period=period_data.get('period', ''),
                numbers=numbers
            )
            
            features.append(pc28_data)
            
        except (KeyError, TypeError, ValidationError) as e:
            logger.debug(f"Skipping invalid period data: {e}")
            continue
    
    elapsed_time = time.time() - start_time
    logger.info(f"Extracted {len(features)} features in {elapsed_time:.2f}s")
    
    # Cache results if cache_key provided and features exist
    if cache_key and features:
        try:
            cache_data = [f.model_dump() for f in features]
            redis_client.setex(CACHE_PREFIX + cache_key, 300, json.dumps(cache_data))
            logger.info(f"Features cached for {cache_key}")
        except Exception as e:
            logger.warning(f"Cache write failed for {cache_key}: {e}")
    
    return features

def translate_combination(combination: str, lang: str) -> str:
    """Translate combination to specified language"""
    translations = {
        "en": {
            "大单": "Big Odd",
            "小双": "Small Even", 
            "小单": "Small Odd",
            "大双": "Big Even",
            "极值": "Extreme"
        }
    }
    
    if lang.startswith("en"):
        return translations["en"].get(combination, combination)
    return combination

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics for monitoring"""
    try:
        keys = redis_client.keys(CACHE_PREFIX + "*")
        return {
            "total_cached_keys": len(keys),
            "cache_prefix": CACHE_PREFIX,
            "keys": keys[:10]  # Show first 10 keys
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"error": str(e)}

def clear_cache(pattern: str = None) -> Dict[str, Any]:
    """Clear cache entries matching pattern"""
    try:
        if pattern:
            keys = redis_client.keys(CACHE_PREFIX + pattern)
        else:
            keys = redis_client.keys(CACHE_PREFIX + "*")
        
        if keys:
            deleted = redis_client.delete(*keys)
            logger.info(f"Cleared {deleted} cache entries")
            return {"deleted": deleted, "keys": keys}
        else:
            return {"deleted": 0, "message": "No keys found"}
            
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return {"error": str(e)}