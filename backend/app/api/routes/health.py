"""
Health Check Router
Simple health check endpoint
"""

from fastapi import APIRouter
from datetime import datetime
from app_database import test_connection

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns API status and component health
    """
    # Check database
    db_healthy = test_connection()
    
    # Overall status
    status = "healthy" if db_healthy else "degraded"
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": "healthy" if db_healthy else "unhealthy",
            "api": "healthy"
        }
    }


@router.get("/health/db")
async def database_health():
    """Database-specific health check"""
    healthy = test_connection()
    
    return {
        "status": "healthy" if healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat()
    }
