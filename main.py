from fastapi import FastAPI, HTTPException, Request
import uvicorn
import json
import logging
from config import redis_client
from api_client import (
    check_system_health, ErrorResponse, SystemHealth, 
    get_model_list, fetch_realtime_data, fetch_history_data
)
from data_processor import extract_features, translate_combination

# Initialize FastAPI app
app = FastAPI(
    title="PC28 Prediction System",
    description="AI/ML API Model Extraction and PC28 Prediction System",
    version="1.0.0"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/health", response_model=SystemHealth)
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        health = check_system_health()
        
        if health.status == "unhealthy":
            raise HTTPException(status_code=503, detail=health.dict())
        elif health.status == "degraded":
            logger.warning(f"System degraded: {health.errors}")
            
        return health
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        error_response = ErrorResponse(
            error_code="HEALTH_CHECK_ERROR",
            message=f"Health check failed: {str(e)}"
        )
        raise HTTPException(status_code=503, detail=error_response.dict())

def get_language(request: Request) -> str:
    """Extract language from Accept-Language header"""
    accept_lang = request.headers.get("Accept-Language", "zh-CN")
    return accept_lang.split(",")[0].split(";")[0]

@app.get("/")
async def root(request: Request):
    """Root endpoint with system information"""
    lang = get_language(request)
    
    if lang.startswith("en"):
        return {
            "system": "PC28 Prediction System",
            "phase": "3 - API Clients",
            "status": "Development",
            "endpoints": ["/health", "/models", "/data/realtime", "/data/history"],
            "note": "Statistical engines will be available in Phase 4"
        }
    else:
        return {
            "system": "PC28预测系统",
            "phase": "3 - API客户端",
            "status": "开发中",
            "endpoints": ["/health", "/models", "/data/realtime", "/data/history"],
            "note": "统计引擎将在第4阶段提供"
        }

@app.get("/models")
async def get_models(request: Request):
    """Get AI/ML model list with caching"""
    lang = get_language(request)
    
    try:
        models = get_model_list()
        model_count = len(models.get("data", []))
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "message": f"Retrieved {model_count} models",
                "data": models.get("data", [])
            }
        else:
            return {
                "status": "成功",
                "message": f"获取到 {model_count} 个模型",
                "data": models.get("data", [])
            }
            
    except Exception as e:
        logger.error(f"Failed to fetch models: {e}")
        error_msg = f"Failed to fetch models: {e}" if lang.startswith("en") else f"获取模型失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/data/realtime")
async def get_realtime_data(request: Request):
    """Get real-time PC28 data"""
    lang = get_language(request)
    
    try:
        data = fetch_realtime_data()
        features = extract_features(data, cache_key="realtime")
        
        # Translate combinations based on language
        translated_features = []
        for feature in features:
            translated_features.append({
                "sum": feature.sum,
                "tail": feature.tail,
                "combination": translate_combination(feature.combination, lang),
                "period": feature.period,
                "numbers": feature.numbers
            })
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "message": f"Retrieved {len(translated_features)} real-time records",
                "data": translated_features
            }
        else:
            return {
                "status": "成功", 
                "message": f"获取到 {len(translated_features)} 条实时记录",
                "data": translated_features
            }
            
    except Exception as e:
        logger.error(f"Failed to fetch real-time data: {e}")
        error_msg = f"Failed to fetch real-time data: {e}" if lang.startswith("en") else f"获取实时数据失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/data/history")
async def get_history_data(date: str, limit: int = 1000, request: Request = None):
    """Get historical PC28 data"""
    lang = get_language(request)
    
    try:
        data = fetch_history_data(date, limit)
        cache_key = f"history_{date}_{limit}"
        features = extract_features(data, cache_key=cache_key)
        
        # Translate combinations based on language
        translated_features = []
        for feature in features:
            translated_features.append({
                "sum": feature.sum,
                "tail": feature.tail,
                "combination": translate_combination(feature.combination, lang),
                "period": feature.period,
                "numbers": feature.numbers
            })
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "message": f"Retrieved {len(translated_features)} historical records for {date}",
                "data": translated_features
            }
        else:
            return {
                "status": "成功",
                "message": f"获取到 {date} 的 {len(translated_features)} 条历史记录", 
                "data": translated_features
            }
            
    except Exception as e:
        logger.error(f"Failed to fetch historical data: {e}")
        error_msg = f"Failed to fetch historical data: {e}" if lang.startswith("en") else f"获取历史数据失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    logger.info("Starting PC28 Prediction System - Phase 3")
    uvicorn.run(app, host="0.0.0.0", port=8001)