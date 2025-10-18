from fastapi import FastAPI, HTTPException, Request
import uvicorn
import json
import logging
from datetime import datetime
from config import redis_client
from api_client import (
    check_system_health, ErrorResponse, SystemHealth, 
    get_model_list, fetch_realtime_data, fetch_history_data, categorize_models
)
from data_processor import extract_features, translate_combination, get_cache_stats, clear_cache
from prediction_engine import get_prediction_engine, PredictionConfig

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
            "phase": "5 - Prediction System Integration",
            "status": "Development",
            "endpoints": ["/health", "/predict", "/models", "/data/realtime", "/data/history", "/stats", "/performance"],
            "note": "Prediction engine integrated with real-time predictions"
        }
    else:
        return {
            "system": "PC28预测系统",
            "phase": "5 - 预测系统集成",
            "status": "开发中",
            "endpoints": ["/health", "/predict", "/models", "/data/realtime", "/data/history", "/stats", "/performance"],
            "note": "预测引擎已集成，支持实时预测"
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

# Initialize prediction engine
prediction_engine = get_prediction_engine()

@app.post("/predict")
async def generate_prediction(request: Request):
    """Generate PC28 prediction using integrated engine"""
    lang = get_language(request)
    
    try:
        # Generate prediction
        prediction = prediction_engine.generate_prediction()
        
        # Translate combination if needed
        translated_combination = translate_combination(prediction.combination, lang)
        
        # Translate probabilities
        translated_probs = {}
        for combo, prob in prediction.probabilities.items():
            translated_probs[translate_combination(combo, lang)] = round(prob, 3)
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "prediction": {
                    "sum_range": prediction.sum_range,
                    "combination": translated_combination,
                    "probabilities": translated_probs,
                    "confidence": round(prediction.confidence, 3),
                    "timestamp": prediction.timestamp.isoformat()
                },
                "message": f"Prediction generated with {prediction.confidence:.1%} confidence"
            }
        else:
            return {
                "status": "成功",
                "prediction": {
                    "sum_range": prediction.sum_range,
                    "combination": translated_combination,
                    "probabilities": translated_probs,
                    "confidence": round(prediction.confidence, 3),
                    "timestamp": prediction.timestamp.isoformat()
                },
                "message": f"预测生成完成，置信度 {prediction.confidence:.1%}"
            }
            
    except Exception as e:
        logger.error(f"Prediction generation failed: {e}")
        error_msg = f"Prediction failed: {e}" if lang.startswith("en") else f"预测失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/predict/update")
async def update_prediction_accuracy(predicted: str, actual: str, request: Request):
    """Update prediction accuracy with actual result"""
    lang = get_language(request)
    
    try:
        # Update accuracy
        current_accuracy = prediction_engine.update_accuracy(predicted, actual)
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "message": f"Accuracy updated to {current_accuracy:.1%}",
                "current_accuracy": round(current_accuracy, 3)
            }
        else:
            return {
                "status": "成功",
                "message": f"准确率已更新至 {current_accuracy:.1%}",
                "current_accuracy": round(current_accuracy, 3)
            }
            
    except Exception as e:
        logger.error(f"Accuracy update failed: {e}")
        error_msg = f"Accuracy update failed: {e}" if lang.startswith("en") else f"准确率更新失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/stats")
async def get_statistics(request: Request):
    """Get comprehensive system statistics"""
    lang = get_language(request)
    
    try:
        # Get cache statistics
        cache_stats = get_cache_stats()
        
        # Get model statistics
        models = get_model_list()
        model_categories = categorize_models(models)
        model_stats = {category: len(models) for category, models in model_categories.items()}
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "statistics": {
                    "cache": cache_stats,
                    "models": model_stats,
                    "system_phase": "5 - Prediction System Integration",
                    "last_updated": datetime.now().isoformat()
                }
            }
        else:
            return {
                "status": "成功",
                "statistics": {
                    "cache": cache_stats,
                    "models": model_stats,
                    "system_phase": "5 - 预测系统集成",
                    "last_updated": datetime.now().isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"Statistics retrieval failed: {e}")
        error_msg = f"Statistics failed: {e}" if lang.startswith("en") else f"统计信息获取失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/performance")
async def get_performance_metrics(request: Request):
    """Get prediction performance metrics"""
    lang = get_language(request)
    
    try:
        metrics = prediction_engine.get_performance_metrics()
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "performance": metrics,
                "message": f"Performance data for {metrics.get('total_predictions', 0)} predictions"
            }
        else:
            return {
                "status": "成功",
                "performance": metrics,
                "message": f"{metrics.get('total_predictions', 0)} 次预测的性能数据"
            }
            
    except Exception as e:
        logger.error(f"Performance metrics failed: {e}")
        error_msg = f"Performance metrics failed: {e}" if lang.startswith("en") else f"性能指标获取失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.delete("/cache")
async def clear_system_cache(pattern: str = None, request: Request = None):
    """Clear system cache"""
    lang = get_language(request)
    
    try:
        result = clear_cache(pattern)
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "result": result,
                "message": f"Cache cleared: {result.get('deleted', 0)} keys"
            }
        else:
            return {
                "status": "成功",
                "result": result,
                "message": f"缓存已清理: {result.get('deleted', 0)} 个键"
            }
            
    except Exception as e:
        logger.error(f"Cache clearing failed: {e}")
        error_msg = f"Cache clearing failed: {e}" if lang.startswith("en") else f"缓存清理失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    logger.info("Starting PC28 Prediction System - Phase 5")
    uvicorn.run(app, host="0.0.0.0", port=8000)