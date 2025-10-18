from fastapi import FastAPI, HTTPException
import uvicorn
import json
import logging
from config import redis_client

# Initialize FastAPI app
app = FastAPI(
    title="PC28 Prediction System",
    description="AI/ML API Model Extraction and PC28 Prediction System",
    version="1.0.0"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/health")
async def health_check():
    """Health check endpoint to verify system status"""
    try:
        # Test Redis connection
        redis_status = redis_client.ping()
        return {
            "status": "healthy",
            "redis": "connected" if redis_status else "disconnected",
            "phase": "1 - Project Setup",
            "message": "System initialized successfully"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"System unhealthy: {str(e)}")

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