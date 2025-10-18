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

def test_api_connections() -> Dict[str, bool]:
    """Test all API connections for system validation"""
    results = {}
    
    # Test AI/ML API
    try:
        models_data = get_model_list()
        categorize_models(models_data)  # Test model processing
        results['aiml_api'] = True
        logger.info("AI/ML API connection: SUCCESS")
    except Exception as e:
        results['aiml_api'] = False
        logger.error(f"AI/ML API connection: FAILED - {e}")
    
    # Test PC28 real-time API
    try:
        realtime_data = fetch_realtime_data()
        extract_features(realtime_data)  # Test data processing
        results['pc28_realtime'] = True
        logger.info("PC28 real-time API connection: SUCCESS")
    except Exception as e:
        results['pc28_realtime'] = False
        logger.error(f"PC28 real-time API connection: FAILED - {e}")
    
    # Test PC28 history API
    try:
        history_data = fetch_history_data("2025-10-18", 10)  # Small test request
        extract_features(history_data)  # Test data processing
        results['pc28_history'] = True
        logger.info("PC28 history API connection: SUCCESS")
    except Exception as e:
        results['pc28_history'] = False
        logger.error(f"PC28 history API connection: FAILED - {e}")
    
    return results