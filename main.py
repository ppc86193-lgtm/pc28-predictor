from fastapi import FastAPI, HTTPException
import uvicorn
import json
import logging
from config import redis_client
from api_client import check_system_health, ErrorResponse, SystemHealth

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

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "system": "PC28 Prediction System",
        "phase": "1 - Project Setup",
        "status": "Development",
        "endpoints": ["/health", "/predict", "/models", "/stats"],
        "note": "Prediction endpoints will be available in Phase 5"
    }

if __name__ == "__main__":
    logger.info("Starting PC28 Prediction System - Phase 1")
    uvicorn.run(app, host="0.0.0.0", port=8000)