from fastapi import FastAPI, HTTPException, Request, Query
from pydantic import BaseModel, Field
import uvicorn
import json
import logging
import time
from datetime import datetime
from typing import Optional
from config import redis_client
from api_client import (
    check_system_health, ErrorResponse, SystemHealth, 
    get_model_list, fetch_realtime_data, fetch_history_data, categorize_models
)
from data_processor import extract_features, translate_combination, get_cache_stats, clear_cache
from prediction_engine import get_prediction_engine, PredictionConfig
from monitor import get_monitor
from optimizer import get_optimizer

# Request/Response Models
class AccuracyUpdateRequest(BaseModel):
    predicted: str = Field(..., description="Predicted combination")
    actual: str = Field(..., description="Actual combination")

class StandardResponse(BaseModel):
    status: str
    message: str

# Initialize FastAPI app
app = FastAPI(
    title="PC28 Prediction System",
    description="AI/ML API Model Extraction and PC28 Prediction System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("PC28 Prediction System starting up...")
    try:
        # Test Redis connection
        redis_client.ping()
        logger.info("Redis connection established")
        
        # Initialize prediction engine
        global prediction_engine
        prediction_engine = get_prediction_engine()
        logger.info("Prediction engine initialized")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("PC28 Prediction System shutting down...")
    try:
        # Cleanup prediction engine if needed
        if 'prediction_engine' in globals():
            prediction_engine.cleanup_old_data()
        logger.info("Cleanup completed")
    except Exception as e:
        logger.warning(f"Shutdown cleanup warning: {e}")

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        health = check_system_health()
        
        # Convert to dict with proper datetime serialization
        health_dict = {
            "status": health.status,
            "redis_connected": health.redis_connected,
            "aiml_api_available": health.aiml_api_available,
            "pc28_api_available": health.pc28_api_available,
            "last_check": health.last_check.isoformat() if hasattr(health.last_check, 'isoformat') else str(health.last_check),
            "errors": health.errors
        }
        
        if health.status == "unhealthy":
            raise HTTPException(status_code=503, detail=health_dict)
        elif health.status == "degraded":
            logger.warning(f"System degraded: {health.errors}")
            
        return health_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        error_response = {
            "error_code": "HEALTH_CHECK_ERROR",
            "message": f"Health check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        raise HTTPException(status_code=503, detail=error_response)

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
            "phase": "6 - Monitoring and Optimization",
            "status": "Development",
            "endpoints": [
                "/health", "/predict", "/models", "/data/realtime", "/data/history", 
                "/stats", "/performance", "/monitor/accuracy", "/monitor/performance", 
                "/monitor/history", "/optimize/analyze", "/optimize/run"
            ],
            "note": "Monitoring and optimization system integrated with real-time performance tracking"
        }
    else:
        return {
            "system": "PC28预测系统",
            "phase": "6 - 监控与优化",
            "status": "开发中",
            "endpoints": [
                "/health", "/predict", "/models", "/data/realtime", "/data/history", 
                "/stats", "/performance", "/monitor/accuracy", "/monitor/performance", 
                "/monitor/history", "/optimize/analyze", "/optimize/run"
            ],
            "note": "监控和优化系统已集成，支持实时性能跟踪和参数调优"
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
async def get_history_data(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    limit: int = Query(1000, ge=1, le=10000, description="Number of records to retrieve"),
    request: Request = None
):
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

# Prediction engine will be initialized in startup event
prediction_engine = None

@app.post("/predict")
async def generate_prediction(request: Request):
    """Generate PC28 prediction using integrated engine"""
    if prediction_engine is None:
        raise HTTPException(status_code=503, detail="Prediction engine not initialized")
    
    lang = get_language(request)
    start_time = time.time()
    
    try:
        # Generate prediction
        prediction = prediction_engine.generate_prediction()
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Record prediction for monitoring
        monitor = get_monitor()
        record_id = monitor.record_prediction(
            predicted_combination=prediction.combination,
            predicted_sum_range=prediction.sum_range,
            confidence=prediction.confidence,
            response_time_ms=response_time_ms
        )
        
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
                    "timestamp": prediction.timestamp.isoformat(),
                    "record_id": record_id
                },
                "message": f"Prediction generated with {prediction.confidence:.1%} confidence",
                "response_time_ms": round(response_time_ms, 2)
            }
        else:
            return {
                "status": "成功",
                "prediction": {
                    "sum_range": prediction.sum_range,
                    "combination": translated_combination,
                    "probabilities": translated_probs,
                    "confidence": round(prediction.confidence, 3),
                    "timestamp": prediction.timestamp.isoformat(),
                    "record_id": record_id
                },
                "message": f"预测生成完成，置信度 {prediction.confidence:.1%}",
                "response_time_ms": round(response_time_ms, 2)
            }
            
    except Exception as e:
        logger.error(f"Prediction generation failed: {e}")
        error_msg = f"Prediction failed: {e}" if lang.startswith("en") else f"预测失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/predict/update")
async def update_prediction_accuracy(predicted: str, actual: str, request: Request):
    """Update prediction accuracy with actual result"""
    if prediction_engine is None:
        raise HTTPException(status_code=503, detail="Prediction engine not initialized")
    
    # Validate input parameters
    valid_combinations = ["大单", "小双", "小单", "大双", "极值"]
    if predicted not in valid_combinations or actual not in valid_combinations:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid combination. Must be one of: {valid_combinations}"
        )
    
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
    if prediction_engine is None:
        raise HTTPException(status_code=503, detail="Prediction engine not initialized")
    
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

@app.post("/predict/result")
async def update_prediction_result(
    record_id: str,
    actual_combination: str,
    actual_sum: int = Query(..., ge=0, le=27, description="Actual sum (0-27)"),
    request: Request = None
):
    """Update prediction result with actual outcome"""
    lang = get_language(request)
    
    try:
        monitor = get_monitor()
        success = monitor.update_prediction_result(record_id, actual_combination, actual_sum)
        
        if not success:
            raise ValueError("Failed to update prediction result")
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "message": f"Prediction result updated for {record_id}"
            }
        else:
            return {
                "status": "成功",
                "message": f"预测结果已更新: {record_id}"
            }
            
    except Exception as e:
        logger.error(f"Failed to update prediction result: {e}")
        error_msg = f"Update failed: {e}" if lang.startswith("en") else f"更新失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/monitor/accuracy")
async def get_accuracy_metrics(
    period: str = Query("24h", regex="^(1h|24h|7d)$", description="Time period"),
    request: Request = None
):
    """Get prediction accuracy metrics"""
    lang = get_language(request)
    
    try:
        monitor = get_monitor()
        metrics = monitor.get_accuracy_metrics(period)
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "metrics": metrics,
                "message": f"Accuracy metrics for {period}"
            }
        else:
            return {
                "status": "成功",
                "metrics": metrics,
                "message": f"{period} 准确率指标"
            }
            
    except Exception as e:
        logger.error(f"Failed to get accuracy metrics: {e}")
        error_msg = f"Metrics failed: {e}" if lang.startswith("en") else f"指标获取失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/monitor/performance")
async def get_system_performance(request: Request):
    """Get system performance metrics"""
    lang = get_language(request)
    
    try:
        monitor = get_monitor()
        metrics = monitor.get_performance_metrics()
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "performance": metrics,
                "message": "System performance metrics"
            }
        else:
            return {
                "status": "成功",
                "performance": metrics,
                "message": "系统性能指标"
            }
            
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        error_msg = f"Performance metrics failed: {e}" if lang.startswith("en") else f"性能指标获取失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/monitor/history")
async def get_prediction_history(
    limit: int = Query(50, ge=1, le=1000, description="Number of records"),
    request: Request = None
):
    """Get prediction history"""
    lang = get_language(request)
    
    try:
        monitor = get_monitor()
        history = monitor.get_prediction_history(limit)
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "history": history,
                "message": f"Retrieved {len(history)} prediction records"
            }
        else:
            return {
                "status": "成功",
                "history": history,
                "message": f"获取到 {len(history)} 条预测记录"
            }
            
    except Exception as e:
        logger.error(f"Failed to get prediction history: {e}")
        error_msg = f"History failed: {e}" if lang.startswith("en") else f"历史记录获取失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/monitor/trend")
async def get_accuracy_trend(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    request: Request = None
):
    """Get accuracy trend analysis"""
    lang = get_language(request)
    
    try:
        monitor = get_monitor()
        trend = monitor.get_accuracy_trend(days)
        
        if "error" in trend:
            raise ValueError(trend["error"])
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "trend": trend,
                "message": f"Accuracy trend for {days} days"
            }
        else:
            return {
                "status": "成功",
                "trend": trend,
                "message": f"{days} 天准确率趋势分析"
            }
            
    except Exception as e:
        logger.error(f"Failed to get accuracy trend: {e}")
        error_msg = f"Trend analysis failed: {e}" if lang.startswith("en") else f"趋势分析失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/monitor/alerts")
async def get_system_alerts(
    limit: int = Query(20, ge=1, le=100, description="Number of alerts to retrieve"),
    request: Request = None
):
    """Get system alerts"""
    lang = get_language(request)
    
    try:
        monitor = get_monitor()
        alerts = monitor.get_alerts(limit)
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "alerts": alerts,
                "message": f"Retrieved {len(alerts)} system alerts"
            }
        else:
            return {
                "status": "成功",
                "alerts": alerts,
                "message": f"获取到 {len(alerts)} 条系统警报"
            }
            
    except Exception as e:
        logger.error(f"Failed to get system alerts: {e}")
        error_msg = f"Alerts failed: {e}" if lang.startswith("en") else f"警报获取失败: {e}"
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

@app.get("/optimize/analyze")
async def analyze_performance(request: Request):
    """Analyze system performance for optimization"""
    lang = get_language(request)
    
    try:
        optimizer = get_optimizer()
        analysis = optimizer.analyze_performance()
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "analysis": analysis,
                "message": "Performance analysis completed"
            }
        else:
            return {
                "status": "成功",
                "analysis": analysis,
                "message": "性能分析完成"
            }
            
    except Exception as e:
        logger.error(f"Performance analysis failed: {e}")
        error_msg = f"Analysis failed: {e}" if lang.startswith("en") else f"分析失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/optimize/run")
async def run_optimization(request: Request):
    """Run optimization cycle"""
    lang = get_language(request)
    
    try:
        optimizer = get_optimizer()
        result = optimizer.run_optimization_cycle()
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "optimization": result,
                "message": "Optimization cycle completed"
            }
        else:
            return {
                "status": "成功",
                "optimization": result,
                "message": "优化周期完成"
            }
            
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        error_msg = f"Optimization failed: {e}" if lang.startswith("en") else f"优化失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/optimize/parameters")
async def get_optimization_parameters(request: Request):
    """Get current optimization parameters"""
    lang = get_language(request)
    
    try:
        optimizer = get_optimizer()
        parameters = optimizer.get_current_parameters()
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "parameters": parameters,
                "message": "Current optimization parameters"
            }
        else:
            return {
                "status": "成功",
                "parameters": parameters,
                "message": "当前优化参数"
            }
            
    except Exception as e:
        logger.error(f"Failed to get parameters: {e}")
        error_msg = f"Parameters failed: {e}" if lang.startswith("en") else f"参数获取失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/optimize/history")
async def get_optimization_history(
    days: int = Query(7, ge=1, le=30, description="Number of days"),
    request: Request = None
):
    """Get optimization history"""
    lang = get_language(request)
    
    try:
        optimizer = get_optimizer()
        history = optimizer.get_optimization_history(days)
        
        if lang.startswith("en"):
            return {
                "status": "success",
                "history": history,
                "message": f"Optimization history for {days} days"
            }
        else:
            return {
                "status": "成功",
                "history": history,
                "message": f"{days} 天优化历史"
            }
            
    except Exception as e:
        logger.error(f"Failed to get optimization history: {e}")
        error_msg = f"History failed: {e}" if lang.startswith("en") else f"历史记录获取失败: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    logger.info("Starting PC28 Prediction System - Phase 5")
    uvicorn.run(app, host="0.0.0.0", port=8000)