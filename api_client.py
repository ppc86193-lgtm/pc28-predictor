import requests
import json
import hashlib
import time
import logging
from pydantic import BaseModel, Field, ValidationError, conint
from typing import List, Dict, Any, Literal, Optional
from datetime import datetime
from config import api_key_aimlapi, api_key_data, app_id, real_time_url, history_url, aimlapi_base

logger = logging.getLogger(__name__)

# Error tracking will be defined after classes

class PC28Data(BaseModel):
    """PC28 lottery data model with validation"""
    sum: conint(ge=0, le=27) = Field(..., description="Sum of three numbers (0-27)")
    tail: conint(ge=0, le=9) = Field(..., description="Last digit of sum (0-9)")
    combination: Literal["大单", "小双", "小单", "大双", "极值"] = Field(..., description="Combination type")
    period: Optional[str] = Field(None, description="Period identifier")
    timestamp: Optional[datetime] = Field(None, description="Draw timestamp")
    numbers: Optional[List[int]] = Field(None, description="Original three numbers")

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

class PredictionResult(BaseModel):
    """Prediction result data model"""
    sum_range: str = Field(..., description="Predicted sum range")
    combination: str = Field(..., description="Predicted combination")
    probabilities: Dict[str, float] = Field(..., description="Probability distribution")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence (0-1)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Prediction timestamp")
    
class TailFrequencyResult(BaseModel):
    """Tail frequency analysis result"""
    frequencies: Dict[int, float] = Field(..., description="Tail frequency distribution")
    chi_square_statistic: float = Field(..., description="Chi-square test statistic")
    p_value: float = Field(..., ge=0.0, le=1.0, description="Statistical p-value")
    is_significant: bool = Field(..., description="Whether deviation is statistically significant")
    window_size: int = Field(..., description="Analysis window size")

class ModelInfo(BaseModel):
    """AI/ML model information"""
    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Model name")
    developer: str = Field(..., description="Model developer")
    type: str = Field(..., description="Model type (text, image, etc.)")
    context_length: Optional[int] = Field(None, description="Context length")
    description: Optional[str] = Field(None, description="Model description")
    features: List[str] = Field(default_factory=list, description="Model features")
    url: Optional[str] = Field(None, description="Model documentation URL")

class ErrorResponse(BaseModel):
    """Standard error response format"""
    error_code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")
    
class SystemHealth(BaseModel):
    """System health status"""
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Overall system status")
    redis_connected: bool = Field(..., description="Redis connection status")
    aiml_api_available: bool = Field(False, description="AI/ML API availability")
    pc28_api_available: bool = Field(False, description="PC28 API availability")
    last_check: datetime = Field(default_factory=datetime.now, description="Last health check timestamp")
    errors: List[str] = Field(default_factory=list, description="Current system errors")

# Custom Exception Classes
class PC28APIError(Exception):
    """PC28 API related errors"""
    def __init__(self, message: str, error_code: str = "PC28_API_ERROR", details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class AIMLAPIError(Exception):
    """AI/ML API related errors"""
    def __init__(self, message: str, error_code: str = "AIML_API_ERROR", details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class DataValidationError(Exception):
    """Data validation related errors"""
    def __init__(self, message: str, error_code: str = "DATA_VALIDATION_ERROR", details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class RedisConnectionError(Exception):
    """Redis connection related errors"""
    def __init__(self, message: str, error_code: str = "REDIS_CONNECTION_ERROR", details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

# Error tracking
error_counts = {
    "pc28_api": 0,
    "aiml_api": 0,
    "redis": 0,
    "validation": 0
}

def log_error(error_type: str, error: Exception, context: Dict[str, Any] = None) -> ErrorResponse:
    """Log error and create standardized error response"""
    error_counts[error_type] = error_counts.get(error_type, 0) + 1
    
    error_response = ErrorResponse(
        error_code=getattr(error, 'error_code', f"{error_type.upper()}_ERROR"),
        message=str(error),
        details={
            "error_type": error_type,
            "error_count": error_counts[error_type],
            "context": context or {}
        }
    )
    
    logger.error(f"[{error_type.upper()}] {error_response.message}", 
                extra={"error_details": error_response.details})
    
    return error_response

def reset_error_counts():
    """Reset error counters (useful for testing)"""
    global error_counts
    error_counts = {key: 0 for key in error_counts}

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
        
        data = response.json()
        logger.info("Successfully fetched real-time PC28 data")
        return data
        
    except requests.exceptions.Timeout as e:
        error = PC28APIError("Real-time API request timeout", "PC28_TIMEOUT", 
                           {"url": real_time_url, "timeout": 5})
        log_error("pc28_api", error)
        raise error
    except requests.exceptions.HTTPError as e:
        error = PC28APIError(f"Real-time API HTTP error: {e.response.status_code}", 
                           "PC28_HTTP_ERROR", {"status_code": e.response.status_code})
        log_error("pc28_api", error)
        raise error
    except Exception as e:
        error = PC28APIError(f"Real-time API error: {str(e)}", "PC28_GENERAL_ERROR")
        log_error("pc28_api", error)
        raise error

def fetch_history_data(date: str, limit: int = 1000) -> Dict[str, Any]:
    """Fetch historical PC28 lottery data"""
    try:
        params = {"appid": app_id, "date": date, "limit": str(limit), "format": "json"}
        params["sign"] = generate_sign(params)
        
        response = requests.post(history_url, data=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Successfully fetched {limit} historical records for {date}")
        return data
        
    except requests.exceptions.Timeout as e:
        error = PC28APIError("History API request timeout", "PC28_TIMEOUT", 
                           {"url": history_url, "timeout": 5, "date": date, "limit": limit})
        log_error("pc28_api", error)
        raise error
    except requests.exceptions.HTTPError as e:
        error = PC28APIError(f"History API HTTP error: {e.response.status_code}", 
                           "PC28_HTTP_ERROR", {"status_code": e.response.status_code, "date": date})
        log_error("pc28_api", error)
        raise error
    except Exception as e:
        error = PC28APIError(f"History API error: {str(e)}", "PC28_GENERAL_ERROR", {"date": date})
        log_error("pc28_api", error)
        raise error

def get_model_list() -> Dict[str, Any]:
    """Fetch AI/ML model list from external API"""
    try:
        headers = {"Authorization": f"Bearer {api_key_aimlapi}"}
        response = requests.get(f"{aimlapi_base}/models", headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info("Successfully fetched AI/ML model list")
        return data
        
    except requests.exceptions.Timeout as e:
        error = AIMLAPIError("AI/ML API request timeout", "AIML_TIMEOUT", 
                           {"url": f"{aimlapi_base}/models", "timeout": 10})
        log_error("aiml_api", error)
        raise error
    except requests.exceptions.HTTPError as e:
        error = AIMLAPIError(f"AI/ML API HTTP error: {e.response.status_code}", 
                           "AIML_HTTP_ERROR", {"status_code": e.response.status_code})
        log_error("aiml_api", error)
        raise error
    except Exception as e:
        error = AIMLAPIError(f"AI/ML API error: {str(e)}", "AIML_GENERAL_ERROR")
        log_error("aiml_api", error)
        raise error

def extract_features(data: Dict[str, Any]) -> List[PC28Data]:
    """Extract and validate PC28 features from API response data"""
    features = []
    
    if not data or 'retdata' not in data:
        logger.warning("No valid data found in API response")
        return features
    
    for period_data in data.get('retdata', []):
        try:
            # Extract basic information
            numbers = period_data.get('number', [])
            period = period_data.get('period', '')
            
            if not numbers or len(numbers) != 3:
                logger.warning(f"Invalid numbers in period {period}: {numbers}")
                continue
            
            # Calculate sum and tail
            sum_value = sum(numbers)
            tail = sum_value % 10
            
            # Determine combination type
            if sum_value in [0, 1, 2, 3, 4, 23, 24, 25, 26, 27]:
                combination = "极值"
            else:
                size = "大" if sum_value >= 14 else "小"
                parity = "单" if sum_value % 2 == 1 else "双"
                combination = size + parity
            
            # Create PC28Data instance with validation
            pc28_data = PC28Data(
                sum=sum_value,
                tail=tail,
                combination=combination,
                period=period,
                timestamp=datetime.now(),
                numbers=numbers
            )
            
            features.append(pc28_data)
            
        except (KeyError, TypeError, ValidationError, ValueError) as e:
            logger.warning(f"Skipping invalid period data: {e}")
            continue
    
    logger.info(f"Successfully extracted {len(features)} valid PC28 data points")
    return features

def validate_pc28_data(sum_val: int, numbers: List[int]) -> bool:
    """Validate PC28 data consistency"""
    if not (0 <= sum_val <= 27):
        return False
    
    if len(numbers) != 3:
        return False
    
    if sum(numbers) != sum_val:
        return False
    
    if not all(0 <= num <= 9 for num in numbers):
        return False
    
    return True

def categorize_models(models_data: Dict[str, Any]) -> Dict[str, List[ModelInfo]]:
    """Categorize AI/ML models by type"""
    categories = {
        "text": [],
        "image": [],
        "video": [],
        "audio": [],
        "multimodal": [],
        "other": []
    }
    
    if not models_data or 'data' not in models_data:
        logger.warning("No model data found in API response")
        return categories
    
    for model_data in models_data.get('data', []):
        try:
            model_info = ModelInfo(
                id=model_data.get('id', ''),
                name=model_data.get('info', {}).get('name', ''),
                developer=model_data.get('info', {}).get('developer', ''),
                type=model_data.get('type', 'other'),
                context_length=model_data.get('info', {}).get('contextLength'),
                description=model_data.get('info', {}).get('description', ''),
                features=model_data.get('features', []),
                url=model_data.get('info', {}).get('url')
            )
            
            model_type = model_info.type.lower()
            if model_type in categories:
                categories[model_type].append(model_info)
            else:
                categories['other'].append(model_info)
                
        except (KeyError, ValidationError) as e:
            logger.warning(f"Skipping invalid model data: {e}")
            continue
    
    logger.info(f"Categorized models: {sum(len(models) for models in categories.values())} total")
    return categories

def check_system_health() -> SystemHealth:
    """Comprehensive system health check"""
    from config import redis_client
    
    errors = []
    redis_connected = False
    aiml_api_available = False
    pc28_api_available = False
    
    # Test Redis connection
    try:
        redis_connected = redis_client.ping()
        if not redis_connected:
            errors.append("Redis ping failed")
    except Exception as e:
        errors.append(f"Redis connection error: {str(e)}")
        log_error("redis", RedisConnectionError(str(e)))
    
    # Test AI/ML API
    try:
        models_data = get_model_list()
        categorize_models(models_data)  # Test model processing
        aiml_api_available = True
        logger.info("AI/ML API health check: SUCCESS")
    except Exception as e:
        errors.append(f"AI/ML API unavailable: {str(e)}")
        aiml_api_available = False
    
    # Test PC28 API (use smaller request for health check)
    try:
        history_data = fetch_history_data("2025-10-18", 5)  # Small test request
        extract_features(history_data)  # Test data processing
        pc28_api_available = True
        logger.info("PC28 API health check: SUCCESS")
    except Exception as e:
        errors.append(f"PC28 API unavailable: {str(e)}")
        pc28_api_available = False
    
    # Determine overall status
    if redis_connected and aiml_api_available and pc28_api_available:
        status = "healthy"
    elif redis_connected and (aiml_api_available or pc28_api_available):
        status = "degraded"
    else:
        status = "unhealthy"
    
    return SystemHealth(
        status=status,
        redis_connected=redis_connected,
        aiml_api_available=aiml_api_available,
        pc28_api_available=pc28_api_available,
        errors=errors
    )

def test_api_connections() -> Dict[str, bool]:
    """Test all API connections for system validation (legacy function)"""
    health = check_system_health()
    return {
        'redis': health.redis_connected,
        'aiml_api': health.aiml_api_available,
        'pc28_api': health.pc28_api_available
    }